import io
import json
import shutil
from pathlib import Path
from uuid import uuid4

from flask import current_app
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename


class AdminAssetError(RuntimeError):
    pass


_ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
_ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/webp"}
_EDITOR_SIZE = (1200, 1200)
_EDITOR_MAX_RAW_BYTES = 20 * 1024 * 1024
_EDITOR_MAX_DIMENSION = 4096


def _static_root():
    return Path(current_app.static_folder).resolve()


def normalize_static_path(value):
    raw = (value or "").strip().replace("\\", "/").lstrip("/")
    if raw.startswith("static/"):
        raw = raw[len("static/"):]

    if not raw:
        return ""

    static_root = _static_root()
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

    return (_static_root() / relative).is_file()


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
    target_dir = _static_root() / relative_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    target = target_dir / filename
    file_storage.save(target)

    if not target.is_file() or target.stat().st_size == 0:
        target.unlink(missing_ok=True)
        raise AdminAssetError("Não foi possível salvar a imagem enviada.")

    return (relative_dir / filename).as_posix()


def _editor_metadata_path(relative_path):
    relative = normalize_static_path(relative_path)
    target = _static_root() / relative
    return target.with_suffix(target.suffix + ".json")


def resolve_editor_source(value):
    relative = normalize_static_path(value)
    if not relative:
        raise AdminAssetError("O slot não possui uma imagem para editar.")

    target = _static_root() / relative
    if not target.is_file():
        raise AdminAssetError("A imagem deste slot não existe no armazenamento local.")

    edited_root = (_static_root() / "images" / "products" / "edited").resolve()
    try:
        target.resolve().relative_to(edited_root)
    except ValueError:
        return relative

    metadata_path = _editor_metadata_path(relative)
    if not metadata_path.is_file():
        return relative

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        original = normalize_static_path(metadata.get("original", ""))
    except (OSError, ValueError, TypeError, json.JSONDecodeError, AdminAssetError):
        return relative

    if original and (_static_root() / original).is_file():
        return original

    return relative


def _ensure_original_copy(source_path, product_id, slot):
    source_relative = resolve_editor_source(source_path)
    originals_root = (_static_root() / "images" / "products" / "originals").resolve()
    source = (_static_root() / source_relative).resolve()

    try:
        source.relative_to(originals_root)
    except ValueError:
        extension = source.suffix.lower()
        if extension not in _ALLOWED_EXTENSIONS:
            extension = ".png"

        originals_root.mkdir(parents=True, exist_ok=True)
        filename = (
            f"product-{int(product_id)}-slot-{int(slot)}-"
            f"{uuid4().hex[:12]}{extension}"
        )
        target = originals_root / filename
        shutil.copy2(source, target)
        return target.relative_to(_static_root()).as_posix()

    return source_relative


def _decode_editor_upload(file_storage):
    if file_storage is None or not file_storage.filename:
        raise AdminAssetError("A edição enviada não contém um arquivo de imagem.")

    mimetype = (file_storage.mimetype or "").lower()
    if mimetype and mimetype != "image/png":
        raise AdminAssetError("A imagem editada precisa ser enviada em PNG.")

    stream = file_storage.stream
    try:
        stream.seek(0, 2)
        size = stream.tell()
        stream.seek(0)
    except (OSError, AttributeError) as exc:
        raise AdminAssetError("Não foi possível ler a imagem editada.") from exc

    if size <= 0:
        raise AdminAssetError("A edição enviada está vazia.")
    if size > _EDITOR_MAX_RAW_BYTES:
        raise AdminAssetError("A imagem editada excede o limite permitido.")

    try:
        with Image.open(stream) as image:
            image.load()
            if image.width > _EDITOR_MAX_DIMENSION or image.height > _EDITOR_MAX_DIMENSION:
                raise AdminAssetError("A imagem editada possui dimensões excessivas.")
            if image.size != _EDITOR_SIZE:
                raise AdminAssetError(
                    "A imagem editada precisa ser exportada em 1200 × 1200 pixels."
                )
            return image.convert("RGBA")
    except AdminAssetError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise AdminAssetError("A edição enviada não pôde ser validada como imagem.") from exc
    finally:
        try:
            stream.seek(0)
        except (OSError, AttributeError):
            pass


def save_edited_product_image(file_storage, source_path, product_id, slot):
    if int(slot) not in range(1, 6):
        raise AdminAssetError("Slot de imagem inválido.")

    original_relative = _ensure_original_copy(source_path, product_id, slot)
    image = _decode_editor_upload(file_storage)

    relative_dir = Path("images") / "products" / "edited"
    target_dir = _static_root() / relative_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = (
        f"product-{int(product_id)}-slot-{int(slot)}-"
        f"{uuid4().hex[:12]}.png"
    )
    target = target_dir / filename

    try:
        image.save(target, format="PNG", optimize=True)
    except OSError as exc:
        target.unlink(missing_ok=True)
        raise AdminAssetError("Não foi possível salvar a versão editada.") from exc

    relative = (relative_dir / filename).as_posix()
    metadata = {
        "original": original_relative,
        "product_id": int(product_id),
        "slot": int(slot),
    }

    try:
        _editor_metadata_path(relative).write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        target.unlink(missing_ok=True)
        raise AdminAssetError("Não foi possível registrar a origem da imagem editada.")

    return relative, original_relative


def cleanup_editor_output(relative_path):
    if not relative_path:
        return

    try:
        relative = normalize_static_path(relative_path)
    except AdminAssetError:
        return

    target = (_static_root() / relative).resolve()
    edited_root = (_static_root() / "images" / "products" / "edited").resolve()

    try:
        target.relative_to(edited_root)
    except ValueError:
        return

    target.unlink(missing_ok=True)
    _editor_metadata_path(relative).unlink(missing_ok=True)


def cleanup_new_uploads(relative_paths):
    static_root = _static_root()

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
