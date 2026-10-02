import hmac
import re
import secrets
import time
import unicodedata
from functools import wraps

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from src.copyminas.admin_assets import (
    AdminAssetError,
    cleanup_new_uploads,
    normalize_static_path,
    save_product_image,
    static_asset_exists,
)
from src.copyminas.admin_catalog import (
    AdminCatalogError,
    create_category,
    create_product,
    get_category,
    get_product,
    list_categories,
    list_products,
    set_category_active,
    set_product_active,
    update_category,
    update_product,
)
from src.copyminas.catalog import (
    get_public_categories,
    get_public_products,
    get_public_slug,
)
from src.copyminas.db import DatabaseUnavailable


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

_ADMIN_SESSION_KEY = "copyminas_admin_authenticated"
_ADMIN_CSRF_KEY = "copyminas_admin_csrf"
_ADMIN_FAILURES_KEY = "copyminas_admin_failures"
_ADMIN_LOCKED_UNTIL_KEY = "copyminas_admin_locked_until"

_MAX_ATTEMPTS = 5
_LOCK_SECONDS = 60


def _configured():
    return bool(
        current_app.config.get("ADMIN_USERNAME", "").strip()
        and current_app.config.get("ADMIN_PASSWORD", "")
    )


def _csrf_token():
    token = session.get(_ADMIN_CSRF_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[_ADMIN_CSRF_KEY] = token
    return token


def _csrf_valid(token):
    expected = session.get(_ADMIN_CSRF_KEY, "")
    return bool(
        token
        and expected
        and hmac.compare_digest(str(token), str(expected))
    )


def _locked_seconds():
    locked_until = float(session.get(_ADMIN_LOCKED_UNTIL_KEY, 0) or 0)
    remaining = int(locked_until - time.time())
    if remaining <= 0:
        session.pop(_ADMIN_LOCKED_UNTIL_KEY, None)
        session.pop(_ADMIN_FAILURES_KEY, None)
        return 0
    return remaining


def _register_failure():
    failures = int(session.get(_ADMIN_FAILURES_KEY, 0) or 0) + 1
    session[_ADMIN_FAILURES_KEY] = failures

    if failures >= _MAX_ATTEMPTS:
        session[_ADMIN_LOCKED_UNTIL_KEY] = time.time() + _LOCK_SECONDS


def _clear_failures():
    session.pop(_ADMIN_FAILURES_KEY, None)
    session.pop(_ADMIN_LOCKED_UNTIL_KEY, None)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get(_ADMIN_SESSION_KEY):
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)

    return wrapped


def _admin_error(title, message, status=400):
    return (
        render_template(
            "admin/error.html",
            title=title,
            message=message,
        ),
        status,
    )


def _normalized_name(value):
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.casefold()).strip()


def _duplicate_ids(products):
    groups = {}
    for product in products:
        key = _normalized_name(product.get("nome", ""))
        if not key:
            continue
        groups.setdefault(key, []).append(product["id"])

    duplicates = set()
    for ids in groups.values():
        if len(ids) > 1:
            duplicates.update(ids)
    return duplicates


def _decorate_products(products):
    duplicates = _duplicate_ids(products)
    decorated = []

    for source in products:
        product = dict(source)
        product["duplicate_warning"] = product["id"] in duplicates
        product["preview_image"] = (
            normalize_static_path(product.get("imagem1"))
            if static_asset_exists(product.get("imagem1"))
            else None
        )
        product["public_slug"] = (
            get_public_slug(product["id"], product["nome"])
            if product.get("ativo") and product.get("categoria_ativa")
            else None
        )
        decorated.append(product)

    return decorated


def _possible_duplicates(name, exclude_id=None):
    if not name:
        return []

    target = _normalized_name(name)
    if not target:
        return []

    products = list_products()
    return [
        product
        for product in products
        if product["id"] != exclude_id
        and _normalized_name(product.get("nome", "")) == target
    ]


def _safe_possible_duplicates(name, exclude_id=None):
    try:
        return _possible_duplicates(name, exclude_id=exclude_id)
    except (DatabaseUnavailable, AdminCatalogError) as exc:
        current_app.logger.warning("Duplicate check unavailable: %s", exc)
        return []


def _image_previews(data):
    previews = {}
    for index in range(1, 6):
        key = f"imagem{index}"
        value = data.get(key, "")
        previews[key] = (
            normalize_static_path(value)
            if static_asset_exists(value)
            else None
        )
    return previews


def _parse_product_form():
    raw_quantity = request.form.get("qtd", "").strip()
    raw_category = request.form.get("categoria_id", "").strip()

    data = {
        "nome": request.form.get("nome", "").strip(),
        "descricao": request.form.get("descricao", "").strip(),
        "imagem1": request.form.get("imagem1", "").strip(),
        "imagem2": request.form.get("imagem2", "").strip(),
        "imagem3": request.form.get("imagem3", "").strip(),
        "imagem4": request.form.get("imagem4", "").strip(),
        "imagem5": request.form.get("imagem5", "").strip(),
        "espec": request.form.get("espec", "").strip(),
        "ativo": 1 if request.form.get("ativo") == "1" else 0,
        "categoria_id": None,
        "qtd": None,
    }
    errors = []

    if not data["nome"]:
        errors.append("Informe o nome do produto.")
    elif len(data["nome"]) > 255:
        errors.append("O nome do produto deve ter no máximo 255 caracteres.")

    if not raw_category:
        errors.append("Selecione uma categoria.")
    else:
        try:
            data["categoria_id"] = int(raw_category)
        except ValueError:
            errors.append("Selecione uma categoria válida.")
        else:
            if data["categoria_id"] < 1:
                errors.append("Selecione uma categoria válida.")

    if raw_quantity:
        try:
            data["qtd"] = int(raw_quantity)
        except ValueError:
            errors.append("A quantidade deve ser um número inteiro.")
        else:
            if data["qtd"] < 0:
                errors.append("A quantidade não pode ser negativa.")

    for key in ("imagem1", "imagem2", "imagem3", "imagem4", "imagem5"):
        if len(data[key]) > 500:
            errors.append(f"{key} deve ter no máximo 500 caracteres.")
            continue
        if data[key]:
            try:
                data[key] = normalize_static_path(data[key])
            except AdminAssetError as exc:
                errors.append(f"{key}: {exc}")

    return data, errors


def _apply_product_uploads(data):
    saved = []

    for index in range(1, 6):
        file_storage = request.files.get(f"upload{index}")
        if file_storage is None or not file_storage.filename:
            continue

        relative_path = save_product_image(file_storage)
        if relative_path:
            data[f"imagem{index}"] = relative_path
            saved.append(relative_path)

    return saved


def _parse_category_form():
    name = request.form.get("nome", "").strip()
    data = {
        "nome": name,
        "ativo": 1 if request.form.get("ativo") == "1" else 0,
    }
    errors = []

    if not name:
        errors.append("Informe o nome da categoria.")
    elif len(name) > 120:
        errors.append("O nome da categoria deve ter no máximo 120 caracteres.")

    return data, errors


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get(_ADMIN_SESSION_KEY):
        return redirect(url_for("admin.dashboard"))

    if not _configured():
        return (
            render_template(
                "admin/login.html",
                admin_unconfigured=True,
                login_error=None,
                locked_seconds=0,
                csrf_token=_csrf_token(),
            ),
            503,
        )

    locked_seconds = _locked_seconds()
    login_error = None
    status = 200

    if request.method == "POST":
        if not _csrf_valid(request.form.get("csrf_token", "")):
            login_error = "Sessão de login expirada. Recarregue a página e tente novamente."
            status = 400
        elif locked_seconds:
            login_error = (
                "Muitas tentativas inválidas. "
                f"Tente novamente em aproximadamente {locked_seconds} segundos."
            )
            status = 429
        else:
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            valid_username = hmac.compare_digest(
                username,
                current_app.config["ADMIN_USERNAME"],
            )
            valid_password = hmac.compare_digest(
                password,
                current_app.config["ADMIN_PASSWORD"],
            )

            if valid_username and valid_password:
                session.clear()
                session[_ADMIN_SESSION_KEY] = True
                session[_ADMIN_CSRF_KEY] = secrets.token_urlsafe(32)
                return redirect(url_for("admin.dashboard"))

            _register_failure()
            login_error = "Credenciais inválidas."
            status = 401
            locked_seconds = _locked_seconds()

    return (
        render_template(
            "admin/login.html",
            admin_unconfigured=False,
            login_error=login_error,
            locked_seconds=locked_seconds,
            csrf_token=_csrf_token(),
        ),
        status,
    )


@admin_bp.get("")
@login_required
def dashboard():
    catalog_available = True
    products = []
    categories = []

    try:
        products = get_public_products()
        categories = get_public_categories(products)
    except DatabaseUnavailable as exc:
        catalog_available = False
        current_app.logger.error("Admin catalog summary unavailable: %s", exc)

    return render_template(
        "admin/dashboard.html",
        catalog_available=catalog_available,
        product_count=len(products),
        category_count=len(categories),
        csrf_token=_csrf_token(),
    )


@admin_bp.get("/produtos")
@login_required
def products():
    try:
        catalog_products = _decorate_products(list_products())
    except (DatabaseUnavailable, AdminCatalogError, AdminAssetError) as exc:
        current_app.logger.error("Admin product list unavailable: %s", exc)
        return _admin_error(
            "Catálogo indisponível",
            "Não foi possível consultar os produtos no banco neste momento.",
            503,
        )

    active_count = sum(1 for product in catalog_products if product["ativo"])
    duplicate_count = sum(1 for product in catalog_products if product["duplicate_warning"])

    return render_template(
        "admin/products.html",
        products=catalog_products,
        active_count=active_count,
        inactive_count=len(catalog_products) - active_count,
        duplicate_count=duplicate_count,
        csrf_token=_csrf_token(),
    )


@admin_bp.route("/produtos/novo", methods=["GET", "POST"])
@login_required
def product_new():
    try:
        categories = list_categories()
    except (DatabaseUnavailable, AdminCatalogError) as exc:
        current_app.logger.error("Admin categories unavailable: %s", exc)
        return _admin_error(
            "Categorias indisponíveis",
            "Não foi possível consultar as categorias do banco.",
            503,
        )

    form_data = {
        "nome": "",
        "descricao": "",
        "imagem1": "",
        "imagem2": "",
        "imagem3": "",
        "imagem4": "",
        "imagem5": "",
        "espec": "",
        "ativo": 1,
        "categoria_id": "",
        "qtd": "",
    }
    errors = []
    duplicates = []

    if request.method == "POST":
        if not _csrf_valid(request.form.get("csrf_token", "")):
            return _admin_error(
                "Sessão inválida",
                "Recarregue o formulário antes de salvar o produto.",
                400,
            )

        form_data, errors = _parse_product_form()
        saved_uploads = []

        if not errors:
            try:
                saved_uploads = _apply_product_uploads(form_data)
                duplicates = _safe_possible_duplicates(form_data["nome"])
                product_id = create_product(form_data)
            except (DatabaseUnavailable, AdminCatalogError, AdminAssetError) as exc:
                cleanup_new_uploads(saved_uploads)
                errors.append(str(exc))
            else:
                flash("Produto criado com sucesso.", "admin-success")
                if duplicates:
                    flash(
                        "Atenção: existem registros com nome equivalente. Revise possíveis duplicidades.",
                        "admin-warning",
                    )
                return redirect(url_for("admin.product_edit", product_id=product_id))

    return (
        render_template(
            "admin/product_form.html",
            mode="new",
            product=None,
            form_data=form_data,
            categories=categories,
            form_errors=errors,
            duplicates=duplicates,
            public_slug=None,
            image_previews=_image_previews(form_data),
            csrf_token=_csrf_token(),
        ),
        422 if errors else 200,
    )


@admin_bp.route("/produtos/<int:product_id>", methods=["GET", "POST"])
@login_required
def product_edit(product_id):
    try:
        product = get_product(product_id)
        categories = list_categories()
    except (DatabaseUnavailable, AdminCatalogError) as exc:
        current_app.logger.error("Admin product lookup unavailable: %s", exc)
        return _admin_error(
            "Produto indisponível",
            "Não foi possível consultar este produto no banco.",
            503,
        )

    if product is None:
        return _admin_error(
            "Produto não encontrado",
            "O registro solicitado não existe no banco.",
            404,
        )

    form_data = {
        "nome": product["nome"] or "",
        "descricao": product["descricao"] or "",
        "imagem1": product["imagem1"] or "",
        "imagem2": product["imagem2"] or "",
        "imagem3": product["imagem3"] or "",
        "imagem4": product["imagem4"] or "",
        "imagem5": product["imagem5"] or "",
        "espec": product["espec"] or "",
        "ativo": int(bool(product["ativo"])),
        "categoria_id": product["categoria_id"],
        "qtd": "" if product["qtd"] is None else product["qtd"],
    }
    errors = []
    duplicates = []

    duplicates = _safe_possible_duplicates(form_data["nome"], exclude_id=product_id)

    if request.method == "POST":
        if not _csrf_valid(request.form.get("csrf_token", "")):
            return _admin_error(
                "Sessão inválida",
                "Recarregue o formulário antes de salvar o produto.",
                400,
            )

        form_data, errors = _parse_product_form()
        saved_uploads = []

        if not errors:
            try:
                saved_uploads = _apply_product_uploads(form_data)
                duplicates = _safe_possible_duplicates(form_data["nome"], exclude_id=product_id)
                update_product(product_id, form_data)
            except (DatabaseUnavailable, AdminCatalogError, AdminAssetError) as exc:
                cleanup_new_uploads(saved_uploads)
                errors.append(str(exc))
            else:
                flash("Produto atualizado com sucesso.", "admin-success")
                if duplicates:
                    flash(
                        "Atenção: existem registros com nome equivalente. Revise possíveis duplicidades.",
                        "admin-warning",
                    )
                return redirect(url_for("admin.product_edit", product_id=product_id))

    public_slug = (
        get_public_slug(product_id, form_data["nome"])
        if form_data["ativo"] and product.get("categoria_ativa")
        else None
    )

    return (
        render_template(
            "admin/product_form.html",
            mode="edit",
            product=product,
            form_data=form_data,
            categories=categories,
            form_errors=errors,
            duplicates=duplicates,
            public_slug=public_slug,
            image_previews=_image_previews(form_data),
            csrf_token=_csrf_token(),
        ),
        422 if errors else 200,
    )


@admin_bp.post("/produtos/<int:product_id>/status")
@login_required
def product_status(product_id):
    if not _csrf_valid(request.form.get("csrf_token", "")):
        return _admin_error(
            "Sessão inválida",
            "Não foi possível alterar o status com este formulário.",
            400,
        )

    active = request.form.get("active") == "1"

    try:
        set_product_active(product_id, active)
    except (DatabaseUnavailable, AdminCatalogError) as exc:
        current_app.logger.error("Admin product status failed: %s", exc)
        return _admin_error(
            "Não foi possível alterar o produto",
            str(exc),
            503 if isinstance(exc, DatabaseUnavailable) else 400,
        )

    flash(
        "Produto ativado no catálogo." if active else "Produto desativado do catálogo.",
        "admin-success",
    )
    return redirect(url_for("admin.products"))


@admin_bp.get("/categorias")
@login_required
def categories():
    try:
        rows = list_categories()
    except (DatabaseUnavailable, AdminCatalogError) as exc:
        current_app.logger.error("Admin category list unavailable: %s", exc)
        return _admin_error(
            "Categorias indisponíveis",
            "Não foi possível consultar as categorias no banco neste momento.",
            503,
        )

    return render_template(
        "admin/categories.html",
        categories=rows,
        active_count=sum(1 for category in rows if category["ativo"]),
        csrf_token=_csrf_token(),
    )


@admin_bp.route("/categorias/nova", methods=["GET", "POST"])
@login_required
def category_new():
    form_data = {"nome": "", "ativo": 1}
    errors = []

    if request.method == "POST":
        if not _csrf_valid(request.form.get("csrf_token", "")):
            return _admin_error(
                "Sessão inválida",
                "Recarregue o formulário antes de salvar a categoria.",
                400,
            )

        form_data, errors = _parse_category_form()
        if not errors:
            try:
                category_id = create_category(form_data)
            except (DatabaseUnavailable, AdminCatalogError) as exc:
                errors.append(str(exc))
            else:
                flash("Categoria criada com sucesso.", "admin-success")
                return redirect(url_for("admin.category_edit", category_id=category_id))

    return (
        render_template(
            "admin/category_form.html",
            mode="new",
            category=None,
            form_data=form_data,
            form_errors=errors,
            csrf_token=_csrf_token(),
        ),
        422 if errors else 200,
    )


@admin_bp.route("/categorias/<int:category_id>", methods=["GET", "POST"])
@login_required
def category_edit(category_id):
    try:
        category = get_category(category_id)
    except (DatabaseUnavailable, AdminCatalogError) as exc:
        current_app.logger.error("Admin category lookup unavailable: %s", exc)
        return _admin_error(
            "Categoria indisponível",
            "Não foi possível consultar esta categoria.",
            503,
        )

    if category is None:
        return _admin_error(
            "Categoria não encontrada",
            "O registro solicitado não existe no banco.",
            404,
        )

    form_data = {
        "nome": category["nome"] or "",
        "ativo": int(bool(category["ativo"])),
    }
    errors = []

    if request.method == "POST":
        if not _csrf_valid(request.form.get("csrf_token", "")):
            return _admin_error(
                "Sessão inválida",
                "Recarregue o formulário antes de salvar a categoria.",
                400,
            )

        form_data, errors = _parse_category_form()
        if not errors:
            try:
                update_category(category_id, form_data)
            except (DatabaseUnavailable, AdminCatalogError) as exc:
                errors.append(str(exc))
            else:
                flash("Categoria atualizada com sucesso.", "admin-success")
                return redirect(url_for("admin.category_edit", category_id=category_id))

    return (
        render_template(
            "admin/category_form.html",
            mode="edit",
            category=category,
            form_data=form_data,
            form_errors=errors,
            csrf_token=_csrf_token(),
        ),
        422 if errors else 200,
    )


@admin_bp.post("/categorias/<int:category_id>/status")
@login_required
def category_status(category_id):
    if not _csrf_valid(request.form.get("csrf_token", "")):
        return _admin_error(
            "Sessão inválida",
            "Não foi possível alterar o status com este formulário.",
            400,
        )

    active = request.form.get("active") == "1"

    try:
        set_category_active(category_id, active)
    except (DatabaseUnavailable, AdminCatalogError) as exc:
        return _admin_error(
            "Não foi possível alterar a categoria",
            str(exc),
            503 if isinstance(exc, DatabaseUnavailable) else 400,
        )

    flash(
        "Categoria ativada." if active else "Categoria desativada. Seus produtos deixam de ser publicados enquanto ela estiver inativa.",
        "admin-success",
    )
    return redirect(url_for("admin.categories"))


@admin_bp.post("/logout")
@login_required
def logout():
    if not _csrf_valid(request.form.get("csrf_token", "")):
        return _admin_error(
            "Sessão inválida",
            "Não foi possível encerrar a sessão com este formulário.",
            400,
        )

    session.clear()
    return redirect(url_for("admin.login"))
