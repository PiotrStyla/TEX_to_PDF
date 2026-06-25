# TeX → PDF Web App

MVP aplikacji webowej do kompilacji TEX/LaTeX do PDF.

## Funkcje

- upload `.tex` → PDF
- upload `.zip` z `main.tex` → PDF
- Slayer Paper Mode: formularz → projekt LaTeX → PDF
- download PDF
- download ZIP źródeł LaTeX
- download logu kompilacji
- historia ostatnich 50 buildów pod `/history`
- kompilacja w Dockerze bez dostępu do sieci
- `pdflatex -no-shell-escape`

## Uruchomienie lokalne

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker build -t tex2pdf-compiler -f compiler/Dockerfile .
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Otwórz:

```text
http://127.0.0.1:8000
```

Historia buildów:

```text
http://127.0.0.1:8000/history
```
