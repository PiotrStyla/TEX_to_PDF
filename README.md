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
- health check pod `/health`
- kompilacja w Dockerze bez dostępu do sieci
- `pdflatex -no-shell-escape`

## Uruchomienie lokalne na Windows

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

Health check:

```text
http://127.0.0.1:8000/health
```

## Deploy MVP na VPS przez Docker Compose

Założenie: repo jest sklonowane np. do `/opt/tex2pdf`.

```bash
sudo apt update
sudo apt install -y git docker.io docker-compose-plugin
sudo systemctl enable --now docker

sudo mkdir -p /opt/tex2pdf
sudo chown $USER:$USER /opt/tex2pdf
git clone https://github.com/PiotrStyla/TEX_to_PDF.git /opt/tex2pdf
cd /opt/tex2pdf

mkdir -p storage/jobs storage/output storage/logs
docker compose -f docker-compose.prod.yml up -d --build
```

Aplikacja będzie dostępna pod:

```text
http://SERVER_IP:8000
```

Test logów:

```bash
docker compose -f docker-compose.prod.yml logs -f tex2pdf-app
```

Zatrzymanie:

```bash
docker compose -f docker-compose.prod.yml down
```

## Ważna uwaga bezpieczeństwa

To nadal jest MVP. Do publicznego internetu dodaj przed produkcją:

- reverse proxy Nginx/Caddy + HTTPS
- limit uploadów per IP
- auth albo token API
- regularne czyszczenie `storage/`
- osobnego użytkownika systemowego
- monitoring miejsca na dysku

W `docker-compose.prod.yml` aplikacja używa `/var/run/docker.sock`, żeby uruchamiać izolowany kontener kompilatora LaTeX. To jest wygodne dla MVP, ale w produkcji warto wydzielić osobny worker albo użyć kolejki z bardziej restrykcyjną izolacją.
