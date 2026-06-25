# TeX → PDF Web App Starter

Minimalna aplikacja webowa do workflow:

```text
upload .tex / .zip → kompilacja LaTeX w Dockerze → PDF preview/download
```

## 1. Wymagania

Na Windows:

- Python 3.11+
- Docker Desktop
- PowerShell albo terminal w VS Code/Windsurf

## 2. Instalacja

```powershell
cd tex2pdf-webapp-starter
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 3. Zbuduj obraz kompilatora LaTeX

```powershell
docker build -t tex2pdf-compiler -f compiler/Dockerfile .
```

Pierwszy build może pobierać duży obraz TeX Live.

## 4. Uruchom web app

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Otwórz:

```text
http://127.0.0.1:8000
```

## 5. Testowy plik TEX

Utwórz plik `test.tex`:

```tex
\documentclass{article}
\begin{document}
Hello TeX to PDF.
\end{document}
```

Wrzuć go w UI i kliknij **Generate PDF**.

## 6. ZIP projektu LaTeX

ZIP powinien zawierać na górze `main.tex`:

```text
project.zip
├── main.tex
├── references.bib
├── formatka/slayer.sty
└── tresc/10-tresc.tex
```

## 7. Co jest już gotowe

- upload `.tex`
- upload `.zip`
- podstawowa walidacja plików
- sandbox przez Docker
- `--network none`
- limit pamięci i CPU
- timeout kompilacji
- log błędu kompilacji
- preview PDF w iframe
- download `main.pdf`

## 8. Co dodać w następnej wersji

- prawdziwy `Slayer Paper Mode`
- formularz: tytuł, autor, branch, repo, treść raportu
- automatyczne generowanie `papers/<paper-name>/`
- zapisywanie historii buildów
- publiczny link do PDF
- API endpoint dla automatyzacji z GitHub/Windsurf

## 9. Ważna uwaga bezpieczeństwa

To jest MVP. Nie wystawiaj publicznie bez dodatkowego hardeningu:

- limit liczby jobów na IP
- osobny worker do kompilacji
- okresowe czyszczenie `storage/`
- krótsze timeouty
- skanowanie ZIP
- allowlista komend LaTeX
- izolacja kontenerów per job
