from pathlib import Path
from uuid import uuid4

from flask import current_app
from werkzeug.utils import secure_filename


class AdminAssetError(RuntimeError):
    pass


_ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
_ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/webp"}


def normalize_static_path(value):
    raw = (value or "").strip().replace("\\", "/").lstrip("/")
    if raw.startswith("static/"):
        raw = raw[len("static/"):]

    if not raw:
        return ""

    static_root = Path(current_app.static_folder).resolve()
    candidate = (static_root / raw).resolve()

    try:
        candidate.relative_to(static_root)
    except ValueError as exc:
        raise AdminAssetError("O caminho da imagem precisa permanecer dentro de static.") from exc

    return candidate.relative_to(static_root).as_posix()


def static_asset_exists(value):
    try:
        relative = normalize_static_path(value)
    except AdminAssetError:
        return False

    if not relative:
        return False

    return (Path(current_app.static_folder).resolve() / relative).is_file()


def save_product_image(file_storage):
    if file_storage is None or not file_storage.filename:
        return None

    safe_name = secure_filename(file_storage.filename)
    if not safe_name:
        raise AdminAssetError("O arquivo enviado não possui um nome válido.")

    extension = Path(safe_name).suffix.lower()
    if extension not in _ALLOWED_EXTENSIONS:
        raise AdminAssetError(
            "Formato de imagem não permitido. Use PNG, JPG, JPEG ou WEBP."
        )

    mimetype = (file_storage.mimetype or "").lower()
    if mimetype and mimetype not in _ALLOWED_MIME_TYPES:
        raise AdminAssetError("O arquivo enviado não foi reconhecido como imagem válida.")

    stem = secure_filename(Path(safe_name).stem)[:72] or "produto"
    filename = f"{stem}-{uuid4().hex[:12]}{extension}"

    relative_dir = Path("images") / "products"
    target_dir = Path(current_app.static_folder) / relative_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    target = target_dir / filename
    file_storage.save(target)

    if not target.is_file() or target.stat().st_size == 0:
        target.unlink(missing_ok=True)
        raise AdminAssetError("Não foi possível salvar a imagem enviada.")

    return (relative_dir / filename).as_posix()


def cleanup_new_uploads(relative_paths):
    static_root = Path(current_app.static_folder).resolve()

    for value in relative_paths:
        try:
            relative = normalize_static_path(value)
        except AdminAssetError:
            continue

        if not relative:
            continue

        target = (static_root / relative).resolve()
        try:
            target.relative_to(static_root / "images" / "products")
        except ValueError:
            continue

        target.unlink(missing_ok=True)
