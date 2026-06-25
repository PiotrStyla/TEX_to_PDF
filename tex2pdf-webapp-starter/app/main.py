from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from jinja2 import Template
from pathlib import Path
import shutil
import subprocess
import uuid

from app.security import (
    MAX_UPLOAD_BYTES,
    extract_zip_safely,
    validate_tex_text,
)
from app.templates import INDEX_HTML, RESULT_HTML

BASE_DIR = Path(__file__).resolve().parent.parent
JOBS_DIR = BASE_DIR / 'storage' / 'jobs'
OUTPUT_DIR = BASE_DIR / 'storage' / 'output'
LOGS_DIR = BASE_DIR / 'storage' / 'logs'

app = FastAPI(title='TeX to PDF Builder')


def render(html: str, **context) -> HTMLResponse:
    return HTMLResponse(Template(html).render(**context))


def write_plain_tex(upload_path: Path, workdir: Path) -> Path:
    text = upload_path.read_text(encoding='utf-8', errors='ignore')
    validate_tex_text(text)
    main_tex = workdir / 'main.tex'
    main_tex.write_text(text, encoding='utf-8')
    return main_tex


def prepare_slayer_mode(workdir: Path) -> None:
    """
    Placeholder for your Slayer template mode.
    In v0.1 this assumes uploaded main.tex already exists.
    In v0.2 we can auto-inject main.tex, slayer.sty, title page and content files.
    """
    # Kept intentionally simple for MVP.
    return None


def find_main_tex(workdir: Path) -> Path:
    direct = workdir / 'main.tex'
    if direct.exists():
        return direct
    matches = list(workdir.rglob('main.tex'))
    if matches:
        return matches[0]
    raise ValueError('Nie znaleziono main.tex w projekcie.')


def compile_pdf(job_id: str, workdir: Path, main_tex: Path) -> tuple[bool, str]:
    log_path = LOGS_DIR / f'{job_id}.log'
    output_pdf = OUTPUT_DIR / f'{job_id}.pdf'

    # The docker image is built from ./compiler/Dockerfile as tex2pdf-compiler.
    # --network none blocks internet access during compilation.
    cmd = [
        'docker', 'run', '--rm',
        '--network', 'none',
        '--memory', '768m',
        '--cpus', '1',
        '-v', f'{workdir}:/work',
        'tex2pdf-compiler',
        'latexmk', '-pdf', '-interaction=nonstopmode', '-halt-on-error', '-shell-escape-', main_tex.name,
    ]

    try:
        proc = subprocess.run(
            cmd,
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        log = (proc.stdout or '') + '\n' + (proc.stderr or '')
        log_path.write_text(log, encoding='utf-8')

        generated = workdir / main_tex.with_suffix('.pdf').name
        success = proc.returncode == 0 and generated.exists()
        if success:
            shutil.copyfile(generated, output_pdf)
        return success, log
    except subprocess.TimeoutExpired:
        log = 'Compilation timeout after 60 seconds.'
        log_path.write_text(log, encoding='utf-8')
        return False, log
    except FileNotFoundError:
        log = 'Docker nie jest dostępny. Uruchom Docker Desktop albo zmień backend kompilacji.'
        log_path.write_text(log, encoding='utf-8')
        return False, log


@app.get('/', response_class=HTMLResponse)
def index():
    return render(INDEX_HTML)


@app.post('/compile', response_class=HTMLResponse)
async def compile_upload(file: UploadFile = File(...), mode: str = Form('plain')):
    job_id = uuid.uuid4().hex
    workdir = JOBS_DIR / job_id
    workdir.mkdir(parents=True, exist_ok=True)

    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail='Upload too large.')

    suffix = Path(file.filename or '').suffix.lower()
    upload_path = workdir / f'upload{suffix}'
    upload_path.write_bytes(raw)

    try:
        if suffix == '.zip':
            extract_zip_safely(upload_path, workdir)
            upload_path.unlink(missing_ok=True)
            main_tex = find_main_tex(workdir)
            # latexmk runs in workdir, so ensure main.tex is at root for v0.1.
            if main_tex.parent != workdir:
                shutil.copyfile(main_tex, workdir / 'main.tex')
                main_tex = workdir / 'main.tex'
        elif suffix == '.tex':
            main_tex = write_plain_tex(upload_path, workdir)
            upload_path.unlink(missing_ok=True)
        else:
            raise ValueError('Obsługiwane są tylko pliki .tex oraz .zip.')

        if mode == 'slayer':
            prepare_slayer_mode(workdir)

        success, log = compile_pdf(job_id, workdir, main_tex)
        return render(RESULT_HTML, title='Wynik kompilacji', success=success, job_id=job_id, log=log[-12000:])
    except Exception as exc:
        log = str(exc)
        (LOGS_DIR / f'{job_id}.log').write_text(log, encoding='utf-8')
        return render(RESULT_HTML, title='Błąd', success=False, job_id=job_id, log=log)


@app.get('/download/{job_id}')
def download(job_id: str):
    pdf = OUTPUT_DIR / f'{job_id}.pdf'
    if not pdf.exists():
        raise HTTPException(status_code=404, detail='PDF not found.')
    return FileResponse(pdf, media_type='application/pdf', filename='main.pdf')
