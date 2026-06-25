# Render Hobby demo

This deployment uses a single Docker container with Python + FastAPI + LaTeX installed directly in the image.

Why: Render web services do not provide the local Docker daemon needed for the previous Docker-in-Docker compiler flow.

## Render settings

- Service type: Web Service
- Runtime / Language: Docker
- Repository: PiotrStyla/TEX_to_PDF
- Branch: main
- Dockerfile path: `app/Dockerfile.render`
- Health check path: `/health`

## Environment variables

```text
TEX2PDF_COMPILER_MODE=local
TEX2PDF_STORAGE_DIR=/app/storage
TEX2PDF_COMPILE_TIMEOUT=90
```

## Notes

Render filesystem is ephemeral unless a persistent disk is attached. For the demo this is OK: generated PDFs and history may disappear after redeploy/restart.
