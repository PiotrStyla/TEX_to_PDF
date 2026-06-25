from pathlib import Path
import zipfile

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {'.tex', '.bib', '.sty', '.cls', '.png', '.jpg', '.jpeg', '.pdf'}
BLOCKED_TEX_TOKENS = [
    r'\\write18',
    r'\\input\|',
    r'\\openout',
    r'\\read',
    r'\\usepackage{shellesc}',
]


def ensure_safe_filename(name: str) -> str:
    cleaned = name.replace('\\', '/').strip('/').strip()
    if not cleaned or '..' in Path(cleaned).parts:
        raise ValueError('Unsafe filename in upload.')
    return cleaned


def validate_tex_text(text: str) -> None:
    lowered = text.lower()
    for token in BLOCKED_TEX_TOKENS:
        if token.lower() in lowered:
            raise ValueError(f'Blocked potentially unsafe TeX command: {token}')


def extract_zip_safely(zip_path: Path, target_dir: Path) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            safe_name = ensure_safe_filename(info.filename)
            suffix = Path(safe_name).suffix.lower()
            if suffix not in ALLOWED_EXTENSIONS:
                raise ValueError(f'File type not allowed in ZIP: {safe_name}')
            dest = target_dir / safe_name
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(dest, 'wb') as out:
                data = src.read(MAX_UPLOAD_BYTES + 1)
                if len(data) > MAX_UPLOAD_BYTES:
                    raise ValueError(f'File too large in ZIP: {safe_name}')
                out.write(data)
            if suffix in {'.tex', '.sty', '.cls', '.bib'}:
                validate_tex_text(dest.read_text(encoding='utf-8', errors='ignore'))
