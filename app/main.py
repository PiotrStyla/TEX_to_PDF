from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from jinja2 import Template
from pathlib import Path
from datetime import datetime
import json
import os
import re
import shutil
import subprocess
import uuid

from app.security import (
    MAX_UPLOAD_BYTES,
    extract_zip_safely,
    validate_tex_text,
)
from app.templates import INDEX_HTML, RESULT_HTML, HISTORY_HTML

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = Path(os.getenv("TEX2PDF_STORAGE_DIR", BASE_DIR / "storage")).resolve()
HOST_STORAGE_DIR = os.getenv("TEX2PDF_HOST_STORAGE_DIR")

JOBS_DIR = STORAGE_DIR / "jobs"
OUTPUT_DIR = STORAGE_DIR / "output"
LOGS_DIR = STORAGE_DIR / "logs"
HISTORY_PATH = STORAGE_DIR / "history.json"

app = FastAPI(title="TeX to PDF Builder")


def render(html: str, **context) -> HTMLResponse:
    return HTMLResponse(Template(html).render(**context))


def load_history() -> list[dict]:
    if not HISTORY_PATH.exists():
        return []

    try:
        return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_history(history: list[dict]) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def record_build(
    job_id: str,
    mode: str,
    title: str,
    success: bool,
    has_source_zip: bool,
) -> None:
    history = load_history()
    history.insert(
        0,
        {
            "job_id": job_id,
            "mode": mode,
            "title": title or "Untitled",
            "success": success,
            "has_pdf": (OUTPUT_DIR / f"{job_id}.pdf").exists(),
            "has_source_zip": has_source_zip,
            "has_log": (LOGS_DIR / f"{job_id}.log").exists(),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    )
    save_history(history[:50])


def get_safe_job_path(base_dir: Path, job_id: str, suffix: str) -> Path:
    if not re.fullmatch(r"[a-f0-9]{32}", job_id):
        raise HTTPException(status_code=400, detail="Invalid job id.")

    return base_dir / f"{job_id}{suffix}"


def latex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in value)


def slugify(value: str, fallback: str = "slayer-paper") -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9_-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or fallback


def write_plain_tex(upload_path: Path, workdir: Path) -> Path:
    text = upload_path.read_text(encoding="utf-8", errors="ignore")
    validate_tex_text(text)

    main_tex = workdir / "main.tex"
    main_tex.write_text(text, encoding="utf-8")

    return main_tex


def normalize_slayer_content(content: str) -> str:
    content = content.strip()

    if not content:
        return r"""
\section{Wprowadzenie}

To jest przykładowa treść raportu wygenerowana w trybie Slayer Paper Mode.

\section{Wyniki}

Wklej tutaj swoje wyniki, tabele albo opis eksperymentu.
""".strip()

    validate_tex_text(content)

    if "\\section" in content or "\\subsection" in content:
        return content

    return "\\section{Treść raportu}\n\n" + content


def create_slayer_paper(
    workdir: Path,
    paper_name: str,
    title: str,
    subtitle: str,
    author: str,
    report_content: str,
) -> Path:
    """
    Tworzy lokalny projekt LaTeX w strukturze zgodnej z workflow Slayer/PES-CoM:

    main.tex
    formatka/slayer.sty
    tresc/00-strona-tytulowa.tex
    tresc/10-tresc.tex

    PDF jest kompilowany z katalogu joba, a ZIP źródeł można pobrać
    endpointem /download-source/{job_id}.
    """
    safe_paper_name = slugify(paper_name)
    safe_title = latex_escape(title.strip() or "Slayer Paper")
    safe_subtitle = latex_escape(subtitle.strip() or "TeX to PDF generated report")
    safe_author = latex_escape(author.strip() or "Piotr Styła")
    normalized_content = normalize_slayer_content(report_content)

    formatka_dir = workdir / "formatka"
    tresc_dir = workdir / "tresc"
    formatka_dir.mkdir(parents=True, exist_ok=True)
    tresc_dir.mkdir(parents=True, exist_ok=True)

    main_tex = workdir / "main.tex"
    slayer_sty = formatka_dir / "slayer.sty"
    title_tex = tresc_dir / "00-strona-tytulowa.tex"
    content_tex = tresc_dir / "10-tresc.tex"

    main_tex.write_text(
        r"""\documentclass[11pt,a4paper]{article}

\usepackage{formatka/slayer}

\begin{document}

\input{tresc/00-strona-tytulowa.tex}
\input{tresc/10-tresc.tex}

\end{document}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    slayer_sty.write_text(
        r"""\NeedsTeXFormat{LaTeX2e}
\ProvidesPackage{formatka/slayer}[2026/06/26 Slayer — web paper style]

% --- Język / kodowanie ---
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[polish]{babel}
\usepackage{lmodern}

% --- Układ strony ---
\usepackage[a4paper,margin=2.5cm]{geometry}
\usepackage{parskip}

% --- Kolory (paleta Slayer) ---
\usepackage{xcolor}
\definecolor{slayerblue}{RGB}{15, 76, 129}
\definecolor{slayercyan}{RGB}{0, 169, 224}
\definecolor{slayerdark}{RGB}{34, 40, 49}
\definecolor{slayergray}{RGB}{245, 245, 245}
\definecolor{slayergreen}{RGB}{46, 125, 50}
\definecolor{slayeramber}{RGB}{245, 124, 0}

% --- Nagłówki kolorowe ---
\usepackage{titlesec}
\titleformat{\section}
  {\normalfont\Large\bfseries\color{slayerblue}}
  {\thesection}{1em}{}
\titleformat{\subsection}
  {\normalfont\large\bfseries\color{slayerdark}}
  {\thesubsection}{1em}{}
\titleformat{\subsubsection}
  {\normalfont\normalsize\bfseries\color{slayerdark}}
  {\thesubsubsection}{1em}{}

% --- Matematyka ---
\usepackage{amsmath,amssymb}
\usepackage{siunitx}

% --- Tabele / grafika / wykresy ---
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}

% --- Podpisy rysunków/tabel ---
\usepackage{caption}
\captionsetup{font=small,labelfont=bf}

% --- Linki ---
\usepackage[hidelinks]{hyperref}
\hypersetup{colorlinks=true, linkcolor=slayerblue, urlcolor=slayercyan}

% --- Box na centralny wniosek ---
\usepackage{tcolorbox}
\tcbuselibrary{skins, breakable}

\newenvironment{slayerinsight}{%
  \begin{center}
  \begin{tcolorbox}[
    width=0.92\textwidth,
    colback=slayergray,
    colframe=slayerblue,
    boxrule=1.2pt,
    arc=4pt,
    left=10pt, right=10pt, top=10pt, bottom=10pt,
    fontupper=\small,
    title={\textbf{Centralny wniosek}},
    coltitle=white,
    colbacktitle=slayerblue,
    fonttitle=\small\bfseries,
    coltext=slayerdark
  ]
  \centering
}{%
  \end{tcolorbox}
  \end{center}
}

% --- Pomocnik strony tytułowej ---
\newcommand{\slayertitle}[3]{%
  {\color{slayerblue}\LARGE\bfseries #1\par}\vspace{0.4cm}%
  {\large #2\par}{\small #3\par}%
}

\newcommand{\SlayerRule}{%
  \vspace{0.5em}%
  \noindent\textcolor{slayercyan}{\rule{\linewidth}{1.2pt}}%
  \vspace{0.8em}%
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    title_tex.write_text(
        rf"""% !TEX root = ../main.tex

\begin{{titlepage}}
\centering

\vspace*{{0.8cm}}

\slayertitle
  {{{safe_title}}}
  {{{safe_author}}}
  {{\today}}

\vspace{{0.4cm}}

{{\large \textcolor{{slayerdark}}{{{safe_subtitle}}}\par}}

\vspace{{1.0cm}}

\SlayerRule

\begin{{center}}
\begin{{tabular}}{{ll}}
\toprule
Project & \texttt{{{latex_escape(safe_paper_name)}}} \\
Generated by & \texttt{{TEX\_to\_PDF}} \\
Mode & \texttt{{Slayer Paper Mode}} \\
\bottomrule
\end{{tabular}}
\end{{center}}

\vfill

{{\small PiotrStyla \quad Slayer Paper Mode \quad TeX to PDF Builder \quad \today\par}}

\end{{titlepage}}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    content_tex.write_text(normalized_content + "\n", encoding="utf-8")

    return main_tex


def find_main_tex(workdir: Path) -> Path:
    direct = workdir / "main.tex"

    if direct.exists():
        return direct

    matches = list(workdir.rglob("main.tex"))

    if matches:
        return matches[0]

    raise ValueError("Nie znaleziono main.tex w projekcie.")


def make_source_zip(job_id: str, workdir: Path) -> Path:
    """
    Tworzy ZIP ze źródłami LaTeX dla danego joba.
    Pomija pliki pomocnicze LaTeX i wygenerowane PDF-y.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source_zip = OUTPUT_DIR / f"{job_id}-source.zip"

    if source_zip.exists():
        source_zip.unlink()

    temp_root = workdir.parent / f"{job_id}_source_export"

    if temp_root.exists():
        shutil.rmtree(temp_root)

    temp_root.mkdir(parents=True, exist_ok=True)

    ignored_suffixes = {
        ".aux",
        ".log",
        ".out",
        ".toc",
        ".fls",
        ".fdb_latexmk",
        ".pdf",
        ".gz",
    }

    for path in workdir.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() in ignored_suffixes:
            continue

        relative = path.relative_to(workdir)
        target = temp_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)

    shutil.make_archive(str(source_zip.with_suffix("")), "zip", temp_root)
    shutil.rmtree(temp_root, ignore_errors=True)

    return source_zip


def docker_workdir_for_job(job_id: str, workdir: Path) -> str:
    """
    Zwraca ścieżkę, którą ma zobaczyć Docker daemon.

    Lokalnie na Windows/Linux zwykle wystarczy realna ścieżka workdir.
    W deployu docker-compose aplikacja działa w kontenerze, ale Docker daemon
    działa na hoście, dlatego trzeba podać hostową ścieżkę storage przez:

    TEX2PDF_HOST_STORAGE_DIR=/opt/tex2pdf/storage
    """
    if HOST_STORAGE_DIR:
        return str(Path(HOST_STORAGE_DIR) / "jobs" / job_id)

    return str(workdir)


def build_compile_command(job_id: str, workdir: Path, main_tex: Path) -> list[str]:
    """
    Zwraca komendę kompilacji.

    Tryby:
    - docker: lokalny Windows/VPS z Docker daemonem, stary bezpieczniejszy sandbox
    - local: Render / pojedynczy kontener, gdzie latexmk jest zainstalowany w obrazie aplikacji

    Na Render nie zakładamy dostępu do Docker daemon wewnątrz kontenera, dlatego używamy
    TEX2PDF_COMPILER_MODE=local.
    """
    compiler_mode = os.getenv("TEX2PDF_COMPILER_MODE", "docker").lower().strip()

    latexmk_args = [
        "latexmk",
        "-pdf",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-pdflatex=pdflatex -no-shell-escape %O %S",
        main_tex.name,
    ]

    if compiler_mode == "local":
        return latexmk_args

    docker_workdir = docker_workdir_for_job(job_id, workdir)

    return [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--memory",
        os.getenv("TEX2PDF_DOCKER_MEMORY", "768m"),
        "--cpus",
        os.getenv("TEX2PDF_DOCKER_CPUS", "1"),
        "-v",
        f"{docker_workdir}:/work",
        os.getenv("TEX2PDF_COMPILER_IMAGE", "tex2pdf-compiler"),
        *latexmk_args,
    ]


def compile_pdf(job_id: str, workdir: Path, main_tex: Path) -> tuple[bool, str]:
    log_path = LOGS_DIR / f"{job_id}.log"
    output_pdf = OUTPUT_DIR / f"{job_id}.pdf"

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cmd = build_compile_command(job_id, workdir, main_tex)

    try:
        proc = subprocess.run(
            cmd,
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=int(os.getenv("TEX2PDF_COMPILE_TIMEOUT", "60")),
        )

        command_log = "Command: " + " ".join(cmd) + "\n\n"
        log = command_log + (proc.stdout or "") + "\n" + (proc.stderr or "")
        log_path.write_text(log, encoding="utf-8")

        generated_pdf = workdir / main_tex.with_suffix(".pdf").name
        success = proc.returncode == 0 and generated_pdf.exists()

        if success:
            shutil.copyfile(generated_pdf, output_pdf)
            make_source_zip(job_id, workdir)

        return success, log

    except subprocess.TimeoutExpired:
        log = f"Compilation timeout after {os.getenv('TEX2PDF_COMPILE_TIMEOUT', '60')} seconds."
        log_path.write_text(log, encoding="utf-8")
        return False, log

    except FileNotFoundError as exc:
        compiler_mode = os.getenv("TEX2PDF_COMPILER_MODE", "docker")
        log = (
            f"Compiler command not found in mode '{compiler_mode}'.\n"
            f"Details: {exc}\n"
            "Local Windows: uruchom Docker Desktop i użyj TEX2PDF_COMPILER_MODE=docker.\n"
            "Render: użyj app/Dockerfile.render i TEX2PDF_COMPILER_MODE=local."
        )
        log_path.write_text(log, encoding="utf-8")
        return False, log


@app.get("/health")
def health():
    return {"status": "ok", "app": "tex2pdf", "storage": str(STORAGE_DIR)}


@app.get("/", response_class=HTMLResponse)
def index():
    return render(INDEX_HTML)


@app.post("/compile", response_class=HTMLResponse)
async def compile_upload(file: UploadFile = File(...), mode: str = Form("plain")):
    job_id = uuid.uuid4().hex
    workdir = JOBS_DIR / job_id
    workdir.mkdir(parents=True, exist_ok=True)

    raw = await file.read(MAX_UPLOAD_BYTES + 1)

    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Upload too large.")

    suffix = Path(file.filename or "").suffix.lower()
    upload_path = workdir / f"upload{suffix}"
    upload_path.write_bytes(raw)

    try:
        if suffix == ".zip":
            extract_zip_safely(upload_path, workdir)
            upload_path.unlink(missing_ok=True)

            main_tex = find_main_tex(workdir)

            if main_tex.parent != workdir:
                shutil.copyfile(main_tex, workdir / "main.tex")
                main_tex = workdir / "main.tex"

        elif suffix == ".tex":
            main_tex = write_plain_tex(upload_path, workdir)
            upload_path.unlink(missing_ok=True)

        else:
            raise ValueError("Obsługiwane są tylko pliki .tex oraz .zip.")

        success, log = compile_pdf(job_id, workdir, main_tex)
        has_source_zip = (OUTPUT_DIR / f"{job_id}-source.zip").exists()
        record_build(
            job_id=job_id,
            mode="plain",
            title=file.filename or "Plain TeX / ZIP",
            success=success,
            has_source_zip=has_source_zip,
        )

        return render(
            RESULT_HTML,
            title="Wynik kompilacji",
            success=success,
            job_id=job_id,
            has_source_zip=has_source_zip,
            log=log[-12000:],
        )

    except Exception as exc:
        log = str(exc)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        (LOGS_DIR / f"{job_id}.log").write_text(log, encoding="utf-8")

        record_build(
            job_id=job_id,
            mode="plain",
            title=file.filename or "Plain TeX / ZIP",
            success=False,
            has_source_zip=False,
        )

        return render(
            RESULT_HTML,
            title="Błąd",
            success=False,
            job_id=job_id,
            has_source_zip=False,
            log=log,
        )


@app.post("/compile-slayer", response_class=HTMLResponse)
async def compile_slayer(
    paper_name: str = Form("slayer-paper"),
    title: str = Form("Slayer Paper"),
    subtitle: str = Form("Generated report"),
    author: str = Form("Piotr Styła"),
    report_content: str = Form(""),
):
    job_id = uuid.uuid4().hex
    workdir = JOBS_DIR / job_id
    workdir.mkdir(parents=True, exist_ok=True)

    try:
        main_tex = create_slayer_paper(
            workdir=workdir,
            paper_name=paper_name,
            title=title,
            subtitle=subtitle,
            author=author,
            report_content=report_content,
        )

        success, log = compile_pdf(job_id, workdir, main_tex)
        has_source_zip = (OUTPUT_DIR / f"{job_id}-source.zip").exists()
        record_build(
            job_id=job_id,
            mode="slayer",
            title=title,
            success=success,
            has_source_zip=has_source_zip,
        )

        return render(
            RESULT_HTML,
            title="Slayer Paper Mode — wynik kompilacji",
            success=success,
            job_id=job_id,
            has_source_zip=has_source_zip,
            log=log[-12000:],
        )

    except Exception as exc:
        log = str(exc)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        (LOGS_DIR / f"{job_id}.log").write_text(log, encoding="utf-8")

        record_build(
            job_id=job_id,
            mode="slayer",
            title=title,
            success=False,
            has_source_zip=False,
        )

        return render(
            RESULT_HTML,
            title="Błąd Slayer Paper Mode",
            success=False,
            job_id=job_id,
            has_source_zip=False,
            log=log,
        )


@app.get("/history", response_class=HTMLResponse)
def history():
    return render(HISTORY_HTML, builds=load_history())


@app.get("/download/{job_id}")
def download(job_id: str):
    pdf = get_safe_job_path(OUTPUT_DIR, job_id, ".pdf")

    if not pdf.exists():
        raise HTTPException(status_code=404, detail="PDF not found.")

    return FileResponse(
        pdf,
        media_type="application/pdf",
        filename="main.pdf",
    )


@app.get("/download-source/{job_id}")
def download_source(job_id: str):
    source_zip = get_safe_job_path(OUTPUT_DIR, job_id, "-source.zip")

    if not source_zip.exists():
        raise HTTPException(status_code=404, detail="Source ZIP not found.")

    return FileResponse(
        source_zip,
        media_type="application/zip",
        filename="tex-source.zip",
    )


@app.get("/download-log/{job_id}")
def download_log(job_id: str):
    log = get_safe_job_path(LOGS_DIR, job_id, ".log")

    if not log.exists():
        raise HTTPException(status_code=404, detail="Log not found.")

    return FileResponse(
        log,
        media_type="text/plain",
        filename="compile.log",
    )
