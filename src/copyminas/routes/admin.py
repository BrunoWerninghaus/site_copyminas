import hmac
import re
import secrets
import time
import unicodedata
from datetime import datetime
from functools import wraps

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from src.copyminas.admin_assets import (
    AdminAssetError,
    cleanup_editor_output,
    cleanup_new_uploads,
    normalize_static_path,
    resolve_editor_source,
    save_edited_product_image,
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
    update_product_image_slot,
)
from src.copyminas.admin_contacts import (
    AdminContactError,
    CONTACT_PREFERENCE_LABELS,
    CONTACT_SERVICE_LABELS,
    CONTACT_STATUS_LABELS,
    CONTACT_STATUSES,
    contact_summary,
    get_contact,
    list_contacts,
    update_contact_status,
)
from src.copyminas.catalog import (
    get_public_categories,
    get_public_products,
    get_public_slug,
)
from src.copyminas.db import DatabaseUnavailable
from src.copyminas.company import COPY_MINAS_COMPANY
from src.copyminas.home_content import (
    HomeContentError,
    HomeContentNotInitialized,
    create_home_news,
    get_home_config,
    get_home_news,
    home_schema_ready,
    initialize_home_schema,
    list_home_news,
    set_home_news_active,
    update_home_config,
    update_home_news,
)


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


def _valid_home_url(value):
    value = (value or "").strip()
    if not value:
        return True

    lowered = value.casefold()
    if lowered.startswith(("javascript:", "data:", "vbscript:")):
        return False

    if value.startswith("/") and not value.startswith("//"):
        return True

    return lowered.startswith(("https://", "http://", "mailto:", "tel:"))


def _default_home_admin_config():
    return {
        "announcement_active": False,
        "announcement_label": "AVISO",
        "announcement_text": "",
        "announcement_link_label": "",
        "announcement_link_url": "",
        "hero_kicker": "Copy Minas · Elói Mendes / MG",
        "hero_title": COPY_MINAS_COMPANY["headline"],
        "hero_summary": COPY_MINAS_COMPANY["summary"],
        "primary_cta_label": "Conhecer soluções",
        "primary_cta_url": "/solucoes",
        "secondary_cta_label": "Ver produtos",
        "secondary_cta_url": "/produtos",
        "featured_product_ids": [],
        "show_solutions": True,
        "show_company": True,
        "show_location": True,
    }


def _parse_home_config_form(public_product_ids):
    data = {
        "announcement_active": request.form.get("announcement_active") == "1",
        "announcement_label": request.form.get("announcement_label", "").strip(),
        "announcement_text": request.form.get("announcement_text", "").strip(),
        "announcement_link_label": request.form.get("announcement_link_label", "").strip(),
        "announcement_link_url": request.form.get("announcement_link_url", "").strip(),
        "hero_kicker": request.form.get("hero_kicker", "").strip(),
        "hero_title": request.form.get("hero_title", "").strip(),
        "hero_summary": request.form.get("hero_summary", "").strip(),
        "primary_cta_label": request.form.get("primary_cta_label", "").strip(),
        "primary_cta_url": request.form.get("primary_cta_url", "").strip(),
        "secondary_cta_label": request.form.get("secondary_cta_label", "").strip(),
        "secondary_cta_url": request.form.get("secondary_cta_url", "").strip(),
        "featured_product_ids": [],
        "show_solutions": request.form.get("show_solutions") == "1",
        "show_company": request.form.get("show_company") == "1",
        "show_location": request.form.get("show_location") == "1",
    }
    errors = []

    limits = (
        ("announcement_label", 80, "O rótulo da mensagem"),
        ("announcement_text", 255, "A mensagem"),
        ("announcement_link_label", 80, "O texto do link da mensagem"),
        ("announcement_link_url", 255, "O link da mensagem"),
        ("hero_kicker", 180, "A linha superior do hero"),
        ("hero_title", 255, "O título do hero"),
        ("primary_cta_label", 80, "O texto do CTA principal"),
        ("primary_cta_url", 255, "O link do CTA principal"),
        ("secondary_cta_label", 80, "O texto do CTA secundário"),
        ("secondary_cta_url", 255, "O link do CTA secundário"),
    )

    for key, limit, label in limits:
        if len(data[key]) > limit:
            errors.append(f"{label} deve ter no máximo {limit} caracteres.")

    if not data["hero_kicker"]:
        errors.append("Informe a linha superior do hero.")
    if not data["hero_title"]:
        errors.append("Informe o título principal da Home.")
    if not data["hero_summary"]:
        errors.append("Informe o texto principal da Home.")
    elif len(data["hero_summary"]) > 5000:
        errors.append("O texto principal deve ter no máximo 5000 caracteres.")

    if not data["primary_cta_label"] or not data["primary_cta_url"]:
        errors.append("Informe o CTA principal e seu link.")
    if not data["secondary_cta_label"] or not data["secondary_cta_url"]:
        errors.append("Informe o CTA secundário e seu link.")

    for key in (
        "announcement_link_url",
        "primary_cta_url",
        "secondary_cta_url",
    ):
        if data[key] and not _valid_home_url(data[key]):
            errors.append(f"{key}: informe um link interno ou URL permitida.")

    featured = []
    for position in range(1, 7):
        raw = request.form.get(f"featured_product_{position}", "").strip()
        if not raw:
            continue
        try:
            product_id = int(raw)
        except ValueError:
            errors.append(f"Destaque {position}: produto inválido.")
            continue

        if product_id not in public_product_ids:
            errors.append(
                f"Destaque {position}: selecione um produto atualmente publicável."
            )
            continue

        if product_id in featured:
            errors.append(
                f"Destaque {position}: o mesmo produto não pode aparecer duas vezes."
            )
            continue

        featured.append(product_id)

    data["featured_product_ids"] = featured
    return data, errors


def _parse_home_news_form():
    raw_order = request.form.get("sort_order", "0").strip()
    data = {
        "label": request.form.get("label", "").strip() or "NOVIDADE",
        "title": request.form.get("title", "").strip(),
        "body": request.form.get("body", "").strip(),
        "link_label": request.form.get("link_label", "").strip(),
        "link_url": request.form.get("link_url", "").strip(),
        "active": request.form.get("active") == "1",
        "sort_order": 0,
    }
    errors = []

    if len(data["label"]) > 80:
        errors.append("O rótulo deve ter no máximo 80 caracteres.")
    if not data["title"]:
        errors.append("Informe o título da novidade.")
    elif len(data["title"]) > 180:
        errors.append("O título deve ter no máximo 180 caracteres.")
    if not data["body"]:
        errors.append("Informe o conteúdo da novidade.")
    elif len(data["body"]) > 5000:
        errors.append("O conteúdo deve ter no máximo 5000 caracteres.")
    if len(data["link_label"]) > 80:
        errors.append("O texto do link deve ter no máximo 80 caracteres.")
    if len(data["link_url"]) > 255:
        errors.append("O link deve ter no máximo 255 caracteres.")
    elif data["link_url"] and not _valid_home_url(data["link_url"]):
        errors.append("Informe um link interno ou URL permitida.")

    try:
        data["sort_order"] = int(raw_order or "0")
    except ValueError:
        errors.append("A ordem deve ser um número inteiro.")
    else:
        if data["sort_order"] < 0 or data["sort_order"] > 65535:
            errors.append("A ordem deve estar entre 0 e 65535.")

    return data, errors


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


def _record_datetime(record, *keys):
    for key in keys:
        value = record.get(key)
        if isinstance(value, datetime):
            return value
    return datetime.min


@admin_bp.get("/busca")
@login_required
def global_search():
    query = request.args.get("q", "").strip()
    normalized_query = _normalized_name(query)

    if not normalized_query:
        return jsonify(
            {
                "query": query,
                "results": [],
                "sources": {
                    "products": True,
                    "categories": True,
                    "contacts": True,
                },
            }
        )

    results = []
    sources = {
        "products": True,
        "categories": True,
        "contacts": True,
    }

    try:
        products = list_products()
    except (DatabaseUnavailable, AdminCatalogError) as exc:
        sources["products"] = False
        current_app.logger.warning("Admin global search products unavailable: %s", exc)
    else:
        for product in products:
            haystack = _normalized_name(
                " ".join(
                    str(value or "")
                    for value in (
                        product.get("id"),
                        product.get("nome"),
                        product.get("categoria"),
                        product.get("descricao"),
                    )
                )
            )
            if normalized_query not in haystack:
                continue

            results.append(
                {
                    "kind": "product",
                    "kind_label": "Produto",
                    "title": product.get("nome") or f"Produto #{product['id']}",
                    "meta": (
                        f"#{product['id']} · "
                        f"{product.get('categoria') or 'Sem categoria'} · "
                        f"{'Ativo' if product.get('ativo') else 'Inativo'}"
                    ),
                    "href": url_for("admin.product_edit", product_id=product["id"]),
                }
            )
            if sum(1 for item in results if item["kind"] == "product") >= 6:
                break

    try:
        categories = list_categories()
    except (DatabaseUnavailable, AdminCatalogError) as exc:
        sources["categories"] = False
        current_app.logger.warning("Admin global search categories unavailable: %s", exc)
    else:
        for category in categories:
            haystack = _normalized_name(
                f"{category.get('id', '')} {category.get('nome', '')}"
            )
            if normalized_query not in haystack:
                continue

            results.append(
                {
                    "kind": "category",
                    "kind_label": "Categoria",
                    "title": category.get("nome") or f"Categoria #{category['id']}",
                    "meta": (
                        f"#{category['id']} · "
                        f"{category.get('product_count', 0)} produto(s) · "
                        f"{'Ativa' if category.get('ativo') else 'Inativa'}"
                    ),
                    "href": url_for(
                        "admin.category_edit",
                        category_id=category["id"],
                    ),
                }
            )
            if sum(1 for item in results if item["kind"] == "category") >= 6:
                break

    try:
        contacts = list_contacts()
    except (DatabaseUnavailable, AdminContactError) as exc:
        sources["contacts"] = False
        current_app.logger.warning("Admin global search contacts unavailable: %s", exc)
    else:
        for contact in contacts:
            haystack = _normalized_name(
                " ".join(
                    str(value or "")
                    for value in (
                        contact.get("id"),
                        contact.get("protocol"),
                        contact.get("name"),
                        contact.get("company"),
                        contact.get("email"),
                        contact.get("phone"),
                        contact.get("city"),
                        CONTACT_SERVICE_LABELS.get(
                            contact.get("service_type"),
                            contact.get("service_type"),
                        ),
                    )
                )
            )
            if normalized_query not in haystack:
                continue

            results.append(
                {
                    "kind": "contact",
                    "kind_label": "Contato",
                    "title": contact.get("name") or contact.get("protocol"),
                    "meta": " · ".join(
                        part
                        for part in (
                            contact.get("protocol"),
                            CONTACT_SERVICE_LABELS.get(
                                contact.get("service_type"),
                                contact.get("service_type"),
                            ),
                            CONTACT_STATUS_LABELS.get(
                                contact.get("status"),
                                contact.get("status"),
                            ),
                        )
                        if part
                    ),
                    "href": url_for(
                        "admin.contact_detail",
                        contact_id=contact["id"],
                    ),
                }
            )
            if sum(1 for item in results if item["kind"] == "contact") >= 6:
                break

    return jsonify(
        {
            "query": query,
            "results": results[:18],
            "sources": sources,
        }
    )


@admin_bp.get("")
@login_required
def dashboard():
    catalog_available = True
    contacts_available = True
    products = []
    categories = []
    contact_rows = []

    try:
        products = _decorate_products(list_products())
        categories = list_categories()
    except (DatabaseUnavailable, AdminCatalogError, AdminAssetError) as exc:
        catalog_available = False
        current_app.logger.error("Admin catalog summary unavailable: %s", exc)

    try:
        contact_rows = list_contacts()
    except (DatabaseUnavailable, AdminContactError) as exc:
        contacts_available = False
        current_app.logger.error("Admin contact summary unavailable: %s", exc)

    published_products = [
        product
        for product in products
        if product.get("ativo") and product.get("categoria_ativa")
    ]
    inactive_products = [
        product
        for product in products
        if not product.get("ativo")
    ]

    contact_counts = {
        status: sum(1 for contact in contact_rows if contact.get("status") == status)
        for status in CONTACT_STATUSES
    }
    contact_counts["total"] = len(contact_rows)

    duplicate_records = [
        product
        for product in products
        if product.get("duplicate_warning")
    ]
    published_without_image = [
        product
        for product in published_products
        if not product.get("preview_image")
    ]
    inactive_categories_with_active_products = [
        category
        for category in categories
        if not category.get("ativo")
        and int(category.get("active_product_count") or 0) > 0
    ]

    alerts = []
    if duplicate_records:
        alerts.append(
            {
                "level": "warning",
                "title": "Possíveis duplicidades",
                "detail": (
                    f"{len(duplicate_records)} registro(s) possuem nome equivalente "
                    "a outro produto."
                ),
                "href": url_for("admin.products"),
                "action": "Revisar produtos",
            }
        )

    if published_without_image:
        alerts.append(
            {
                "level": "warning",
                "title": "Produtos publicados sem imagem",
                "detail": (
                    f"{len(published_without_image)} produto(s) publicado(s) não "
                    "possuem uma imagem válida no Site 3."
                ),
                "href": url_for("admin.products"),
                "action": "Revisar imagens",
            }
        )

    if inactive_categories_with_active_products:
        alerts.append(
            {
                "level": "warning",
                "title": "Categoria inativa com produtos ativos",
                "detail": (
                    f"{len(inactive_categories_with_active_products)} categoria(s) "
                    "inativa(s) ainda possuem produtos marcados como ativos."
                ),
                "href": url_for("admin.categories"),
                "action": "Revisar categorias",
            }
        )

    if contacts_available and contact_counts.get("novo", 0):
        alerts.append(
            {
                "level": "info",
                "title": "Novos contatos aguardando triagem",
                "detail": (
                    f"{contact_counts['novo']} solicitação(ões) ainda estão com "
                    "status Novo."
                ),
                "href": url_for("admin.contacts"),
                "action": "Abrir contatos",
            }
        )

    recent_products = sorted(
        products,
        key=lambda product: _record_datetime(product, "updated_at", "created_at"),
        reverse=True,
    )[:5]
    recent_contacts = sorted(
        contact_rows,
        key=lambda contact: _record_datetime(contact, "created_at", "updated_at"),
        reverse=True,
    )[:5]

    return render_template(
        "admin/dashboard.html",
        catalog_available=catalog_available,
        contacts_available=contacts_available,
        product_total=len(products),
        product_published=len(published_products),
        product_inactive=len(inactive_products),
        category_total=len(categories),
        contact_counts=contact_counts,
        recent_products=recent_products,
        recent_contacts=recent_contacts,
        alerts=alerts,
        status_labels=CONTACT_STATUS_LABELS,
        service_labels=CONTACT_SERVICE_LABELS,
        csrf_token=_csrf_token(),
    )


@admin_bp.route("/home", methods=["GET", "POST"])
@login_required
def home_manager():
    try:
        initialized = home_schema_ready()
    except (DatabaseUnavailable, HomeContentError) as exc:
        current_app.logger.error("Admin Home schema check failed: %s", exc)
        return _admin_error(
            "Home indisponível",
            "Não foi possível consultar a configuração da Home.",
            503,
        )

    if not initialized:
        return render_template(
            "admin/home.html",
            initialized=False,
            csrf_token=_csrf_token(),
        )

    try:
        config = get_home_config()
        news = list_home_news()
        products = _decorate_products(list_products())
    except (
        DatabaseUnavailable,
        HomeContentError,
        AdminCatalogError,
        AdminAssetError,
    ) as exc:
        current_app.logger.error("Admin Home unavailable: %s", exc)
        return _admin_error(
            "Home indisponível",
            "Não foi possível consultar a configuração da Home.",
            503,
        )

    public_products = [
        product
        for product in products
        if product.get("ativo") and product.get("categoria_ativa")
    ]
    public_product_ids = {int(product["id"]) for product in public_products}
    errors = []

    if request.method == "POST":
        if not _csrf_valid(request.form.get("csrf_token", "")):
            return _admin_error(
                "Sessão inválida",
                "Recarregue a configuração da Home antes de salvar.",
                400,
            )

        config, errors = _parse_home_config_form(public_product_ids)
        if not errors:
            try:
                update_home_config(config)
            except (DatabaseUnavailable, HomeContentError) as exc:
                errors.append(str(exc))
            else:
                flash("Home atualizada com sucesso.", "admin-success")
                return redirect(url_for("admin.home_manager"))

    return (
        render_template(
            "admin/home.html",
            initialized=True,
            home_config=config,
            news=news,
            public_products=public_products,
            form_errors=errors,
            csrf_token=_csrf_token(),
        ),
        422 if errors else 200,
    )


@admin_bp.post("/home/inicializar")
@login_required
def home_initialize():
    if not _csrf_valid(request.form.get("csrf_token", "")):
        return _admin_error(
            "Sessão inválida",
            "Recarregue a página antes de inicializar a Home.",
            400,
        )

    try:
        products = list_products()
        initial_ids = [
            int(product["id"])
            for product in products
            if product.get("ativo") and product.get("categoria_ativa")
        ][:3]
        initialize_home_schema(
            _default_home_admin_config(),
            featured_product_ids=initial_ids,
        )
    except (
        DatabaseUnavailable,
        AdminCatalogError,
        HomeContentError,
    ) as exc:
        current_app.logger.error("Admin Home initialization failed: %s", exc)
        return _admin_error(
            "Não foi possível inicializar a Home",
            str(exc),
            503 if isinstance(exc, DatabaseUnavailable) else 400,
        )

    flash("Módulo Home inicializado no main_bd.", "admin-success")
    return redirect(url_for("admin.home_manager"))


@admin_bp.route("/home/novidades/nova", methods=["GET", "POST"])
@login_required
def home_news_new():
    form_data = {
        "label": "NOVIDADE",
        "title": "",
        "body": "",
        "link_label": "",
        "link_url": "",
        "active": True,
        "sort_order": 0,
    }
    errors = []

    try:
        if not home_schema_ready():
            return redirect(url_for("admin.home_manager"))
    except (DatabaseUnavailable, HomeContentError) as exc:
        return _admin_error("Home indisponível", str(exc), 503)

    if request.method == "POST":
        if not _csrf_valid(request.form.get("csrf_token", "")):
            return _admin_error(
                "Sessão inválida",
                "Recarregue a novidade antes de salvar.",
                400,
            )

        form_data, errors = _parse_home_news_form()
        if not errors:
            try:
                news_id = create_home_news(form_data)
            except (DatabaseUnavailable, HomeContentError) as exc:
                errors.append(str(exc))
            else:
                flash("Novidade criada com sucesso.", "admin-success")
                return redirect(
                    url_for("admin.home_news_edit", news_id=news_id)
                )

    return (
        render_template(
            "admin/home_news_form.html",
            mode="new",
            news=None,
            form_data=form_data,
            form_errors=errors,
            csrf_token=_csrf_token(),
        ),
        422 if errors else 200,
    )


@admin_bp.route("/home/novidades/<int:news_id>", methods=["GET", "POST"])
@login_required
def home_news_edit(news_id):
    try:
        news = get_home_news(news_id)
    except (DatabaseUnavailable, HomeContentError) as exc:
        return _admin_error("Novidade indisponível", str(exc), 503)

    if news is None:
        return _admin_error(
            "Novidade não encontrada",
            "O registro solicitado não existe.",
            404,
        )

    form_data = {
        "label": news["label"] or "NOVIDADE",
        "title": news["title"] or "",
        "body": news["body"] or "",
        "link_label": news["link_label"] or "",
        "link_url": news["link_url"] or "",
        "active": bool(news["active"]),
        "sort_order": news["sort_order"] or 0,
    }
    errors = []

    if request.method == "POST":
        if not _csrf_valid(request.form.get("csrf_token", "")):
            return _admin_error(
                "Sessão inválida",
                "Recarregue a novidade antes de salvar.",
                400,
            )

        form_data, errors = _parse_home_news_form()
        if not errors:
            try:
                update_home_news(news_id, form_data)
            except (DatabaseUnavailable, HomeContentError) as exc:
                errors.append(str(exc))
            else:
                flash("Novidade atualizada com sucesso.", "admin-success")
                return redirect(
                    url_for("admin.home_news_edit", news_id=news_id)
                )

    return (
        render_template(
            "admin/home_news_form.html",
            mode="edit",
            news=news,
            form_data=form_data,
            form_errors=errors,
            csrf_token=_csrf_token(),
        ),
        422 if errors else 200,
    )


@admin_bp.post("/home/novidades/<int:news_id>/status")
@login_required
def home_news_status(news_id):
    if not _csrf_valid(request.form.get("csrf_token", "")):
        return _admin_error(
            "Sessão inválida",
            "Não foi possível alterar esta novidade.",
            400,
        )

    active = request.form.get("active") == "1"
    try:
        set_home_news_active(news_id, active)
    except (DatabaseUnavailable, HomeContentError) as exc:
        return _admin_error(
            "Não foi possível alterar a novidade",
            str(exc),
            503 if isinstance(exc, DatabaseUnavailable) else 400,
        )

    flash(
        "Novidade publicada." if active else "Novidade desativada.",
        "admin-success",
    )
    return redirect(url_for("admin.home_manager"))


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


@admin_bp.get("/produtos/<int:product_id>/imagem/<int:slot>/editar")
@login_required
def product_image_editor(product_id, slot):
    if slot not in range(1, 6):
        return _admin_error(
            "Slot de imagem inválido",
            "Escolha uma das cinco imagens do produto.",
            404,
        )

    try:
        product = get_product(product_id)
    except (DatabaseUnavailable, AdminCatalogError) as exc:
        current_app.logger.error("Admin image editor product lookup failed: %s", exc)
        return _admin_error(
            "Produto indisponível",
            "Não foi possível consultar este produto.",
            503,
        )

    if product is None:
        return _admin_error(
            "Produto não encontrado",
            "O registro solicitado não existe no banco.",
            404,
        )

    key = f"imagem{slot}"
    current_value = product.get(key) or ""
    if not static_asset_exists(current_value):
        return _admin_error(
            "Imagem indisponível",
            "Este slot ainda não possui uma imagem local para editar.",
            404,
        )

    try:
        current_image = normalize_static_path(current_value)
        source_image = resolve_editor_source(current_value)
    except AdminAssetError as exc:
        return _admin_error("Imagem indisponível", str(exc), 400)

    return render_template(
        "admin/product_image_editor.html",
        product=product,
        slot=slot,
        current_image=current_image,
        source_image=source_image,
        csrf_token=_csrf_token(),
    )


@admin_bp.post("/produtos/<int:product_id>/imagem/<int:slot>/salvar")
@login_required
def product_image_editor_save(product_id, slot):
    if slot not in range(1, 6):
        return jsonify({"ok": False, "error": "Slot de imagem inválido."}), 400

    if not _csrf_valid(request.form.get("csrf_token", "")):
        return jsonify(
            {
                "ok": False,
                "error": "Sessão inválida. Recarregue o editor antes de salvar.",
            }
        ), 400

    try:
        product = get_product(product_id)
    except (DatabaseUnavailable, AdminCatalogError) as exc:
        current_app.logger.error("Admin image editor lookup failed: %s", exc)
        return jsonify(
            {"ok": False, "error": "Não foi possível consultar o produto agora."}
        ), 503

    if product is None:
        return jsonify({"ok": False, "error": "Produto não encontrado."}), 404

    key = f"imagem{slot}"
    current_value = product.get(key) or ""
    if not static_asset_exists(current_value):
        return jsonify(
            {"ok": False, "error": "A imagem atual deste slot não está disponível."}
        ), 400

    edited_path = None
    try:
        image_file = request.files.get("image_file")
        edited_path, _original_path = save_edited_product_image(
            image_file,
            current_value,
            product_id,
            slot,
        )
        update_product_image_slot(product_id, slot, edited_path)
    except (DatabaseUnavailable, AdminCatalogError, AdminAssetError) as exc:
        cleanup_editor_output(edited_path)
        current_app.logger.error("Admin image editor save failed: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), (
            503 if isinstance(exc, DatabaseUnavailable) else 400
        )

    flash(
        f"Imagem {slot} editada e aplicada ao produto. A original foi preservada.",
        "admin-success",
    )
    return jsonify(
        {
            "ok": True,
            "path": edited_path,
            "redirect": url_for("admin.product_edit", product_id=product_id),
        }
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


@admin_bp.get("/contatos")
@login_required
def contacts():
    try:
        rows = list_contacts()
    except (DatabaseUnavailable, AdminContactError) as exc:
        current_app.logger.error("Admin contacts unavailable: %s", exc)
        return _admin_error(
            "Contatos indisponíveis",
            "Não foi possível consultar as solicitações no banco neste momento.",
            503,
        )

    summary = {
        "total": len(rows),
        "novo": sum(1 for row in rows if row["status"] == "novo"),
        "em_atendimento": sum(1 for row in rows if row["status"] == "em_atendimento"),
        "convertido": sum(1 for row in rows if row["status"] == "convertido"),
        "encerrado": sum(1 for row in rows if row["status"] == "encerrado"),
        "spam": sum(1 for row in rows if row["status"] == "spam"),
    }

    return render_template(
        "admin/contacts.html",
        contacts=rows,
        summary=summary,
        status_labels=CONTACT_STATUS_LABELS,
        service_labels=CONTACT_SERVICE_LABELS,
        csrf_token=_csrf_token(),
    )


@admin_bp.get("/contatos/<int:contact_id>")
@login_required
def contact_detail(contact_id):
    try:
        contact = get_contact(contact_id)
    except (DatabaseUnavailable, AdminContactError) as exc:
        current_app.logger.error("Admin contact lookup unavailable: %s", exc)
        return _admin_error(
            "Contato indisponível",
            "Não foi possível consultar esta solicitação.",
            503,
        )

    if contact is None:
        return _admin_error(
            "Contato não encontrado",
            "A solicitação informada não existe no banco.",
            404,
        )

    return render_template(
        "admin/contact_detail.html",
        contact=contact,
        status_labels=CONTACT_STATUS_LABELS,
        service_labels=CONTACT_SERVICE_LABELS,
        preference_labels=CONTACT_PREFERENCE_LABELS,
        contact_statuses=CONTACT_STATUSES,
        csrf_token=_csrf_token(),
    )


@admin_bp.post("/contatos/<int:contact_id>/status")
@login_required
def contact_status(contact_id):
    if not _csrf_valid(request.form.get("csrf_token", "")):
        return _admin_error(
            "Sessão inválida",
            "Não foi possível alterar o status com este formulário.",
            400,
        )

    status = request.form.get("status", "").strip()

    try:
        update_contact_status(contact_id, status)
    except (DatabaseUnavailable, AdminContactError) as exc:
        current_app.logger.error("Admin contact status failed: %s", exc)
        return _admin_error(
            "Não foi possível alterar o contato",
            str(exc),
            503 if isinstance(exc, DatabaseUnavailable) else 400,
        )

    flash("Status do contato atualizado.", "admin-success")
    return redirect(url_for("admin.contact_detail", contact_id=contact_id))


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
