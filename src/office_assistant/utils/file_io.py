from __future__ import annotations

from pathlib import Path


def read_text(file_path: Path, encoding: str | None = None) -> str:
    """Read text file with automatic encoding detection."""
    if encoding:
        return file_path.read_text(encoding=encoding)

    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        import chardet
        raw = file_path.read_bytes()
        detected = chardet.detect(raw)
        enc = detected.get("encoding", "utf-8")
        return raw.decode(enc or "utf-8")


def write_text(file_path: Path, content: str, encoding: str = "utf-8") -> None:
    """Write text to file, creating parent directories if needed."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding=encoding)


def ensure_dir(path: Path) -> Path:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_output_path(
    output_dir: Path,
    filename: str,
    extension: str = ".md",
) -> Path:
    """Resolve output path ensuring uniqueness (append counter if exists)."""
    ensure_dir(output_dir)
    base = filename.rsplit(".", 1)[0]
    output_path = output_dir / f"{base}{extension}"
    counter = 1
    while output_path.exists():
        output_path = output_dir / f"{base}_{counter}{extension}"
        counter += 1
    return output_path
