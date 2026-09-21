from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


def normalize_name(value: str) -> str:
    stem = Path(value).stem.lower().strip()
    stem = re.sub(r"(?:[ _-]*\d+)$", "", stem)
    return re.sub(r"[^a-z0-9]+", "", stem)


def display_name(value: str) -> str:
    return re.sub(r"[_-]+", " ", value).strip().title()


@dataclass(frozen=True)
class Asset:
    letter: str
    key: str
    name: str
    image: Path
    teacher_voice: Path | None
    student_voice: Path | None


def _files_by_key(folder: Path) -> dict[str, Path]:
    if not folder.exists():
        return {}
    result: dict[str, Path] = {}
    for path in folder.iterdir():
        if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".wav", ".mp3", ".m4a"}:
            result.setdefault(normalize_name(path.stem), path)
    return result


def _letter_folder(root: Path, letter: str) -> Path:
    """Resolve asset folders on both case-sensitive and case-insensitive hosts."""
    for candidate in (root / letter, root / letter.upper()):
        if candidate.is_dir():
            return candidate
    return root / letter


def scan_assets(project_root: Path) -> list[Asset]:
    root = project_root / "assets"
    image_root = root / "real_png"
    teacher_root = root / "voices" / "teacher"
    student_root = root / "voices" / "student_voice"
    assets: list[Asset] = []
    letter_dirs = [
        path for path in image_root.iterdir()
        if path.is_dir() and len(path.name) == 1 and path.name.isalpha()
    ] if image_root.is_dir() else []
    for letter_dir in sorted(letter_dirs, key=lambda path: path.name.lower()):
        letter = letter_dir.name.lower()
        teachers = _files_by_key(_letter_folder(teacher_root, letter))
        students = _files_by_key(_letter_folder(student_root, letter))
        for image in sorted(letter_dir.iterdir()):
            if not image.is_file() or image.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                continue
            key = normalize_name(image.stem)
            assets.append(Asset(letter, key, display_name(image.stem), image, teachers.get(key), students.get(key)))
    return assets
