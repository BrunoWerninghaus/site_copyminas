import os
import logging
from datetime import timedelta
from flask import Flask, session
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from src.config import SecurityConfig
from src.routes.routes import routes
from src.controller.error_controller import NotFoundController
from src.controller.admin_controller import get_user_equipments
from src.controller.user_profile_controller import UserProfileController

# Criar diretório de logs se não existir
os.makedirs('logs', exist_ok=True)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
    static_folder=os.path.join(os.path.dirname(__file__), 'static'),
    template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

@app.after_request
def add_ngrok_header(response):
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response

# ── CONFIGURAÇÕES DE SEGURANÇA ────────────────────────────
app.config.from_object(SecurityConfig)

# Chave secreta para sessões e CSRF
app.secret_key = SecurityConfig.SECRET_KEY

# ── SESSÃO ────────────────────────────────────────────────
app.config['PERMANENT_SESSION_LIFETIME'] = SecurityConfig.PERMANENT_SESSION_LIFETIME
app.config['SESSION_COOKIE_SECURE'] = SecurityConfig.SESSION_COOKIE_SECURE
app.config['SESSION_COOKIE_HTTPONLY'] = SecurityConfig.SESSION_COOKIE_HTTPONLY
app.config['SESSION_COOKIE_SAMESITE'] = SecurityConfig.SESSION_COOKIE_SAMESITE

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = SecurityConfig.PERMANENT_SESSION_LIFETIME

# ── CSRF PROTECTION ───────────────────────────────────────
csrf = CSRFProtect(app)

# ── RATE LIMITING ─────────────────────────────────────────
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[SecurityConfig.RATELIMIT_DEFAULT],
    storage_uri=SecurityConfig.RATELIMIT_STORAGE_URL
)

logger.info("Segurança Flask configurada com sucesso")

# ── REGISTRAR ROTAS COM RATE LIMITING ─────────────────────
# Rate limiting on login (5 attempts per minute)
login_view = limiter.limit("5 per minute")(routes["login_controller"])
app.add_url_rule(routes["login_route"], view_func=login_view, methods=['GET', 'POST'], endpoint='login')

# Rate limiting on register (3 per minute)
register_view = limiter.limit("3 per minute")(routes["register_controller"])
app.add_url_rule(routes["register_route"], view_func=register_view, methods=['GET', 'POST'], endpoint='register')

# Outras rotas sem rate limiting específico (usam padrão global)
app.add_url_rule(routes["main_route"], view_func=routes["main_controller"], endpoint='main')
app.add_url_rule(routes["dashboard_route"], view_func=routes["dashboard_controller"], methods=['GET', 'POST'], endpoint='dashboard')
app.add_url_rule(routes["logout_route"], view_func=routes["logout_controller"], endpoint='logout')
app.add_url_rule(routes["admin_route"], view_func=routes["admin_controller"], methods=['GET', 'POST'], endpoint='admin')
app.add_url_rule(routes["maintenance_route"], view_func=routes["maintenance_controller"], methods=['GET', 'POST'], endpoint='maintenance')
app.add_url_rule('/get_user_equipments/<int:user_id>', view_func=get_user_equipments, endpoint='get_user_equipments')
app.add_url_rule('/user/<int:user_id>', view_func=UserProfileController.as_view('user_profile'), endpoint='user_profile')

@app.errorhandler(404)
def handle_404(error):
    return NotFoundController(error)

