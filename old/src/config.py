"""
Configurações de segurança para a aplicação Flask - CopyMinas
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Carregar variáveis de ambiente IMEDIATAMENTE
load_dotenv('.env')
load_dotenv('venv/.env')


class SecurityConfig:
    """Configurações de segurança da aplicação"""
    
    # ── CHAVE SECRETA ─────────────────────────────────────
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in environment variables")
    
    # ── BANCO DE DADOS ────────────────────────────────────
    DATABASE_CONFIG = {
        'host': os.getenv('DATABASE_HOST', 'localhost'),
        'user': os.getenv('DATABASE_USER', 'root'),
        'password': os.getenv('DATABASE_PASSWORD', ''),
        'database': os.getenv('DATABASE_NAME', 'main_bd'),
        'port': int(os.getenv('DATABASE_PORT', 3306)),
    }
    
    # ── SESSÃO ────────────────────────────────────────────
    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=int(os.getenv('SESSION_TIMEOUT_MINUTES', 30))
    )
    # Em produção, SESSION_COOKIE_SECURE deve ser True
    _env = os.getenv('FLASK_ENV', 'development')
    _cookie_secure = os.getenv('SESSION_COOKIE_SECURE', '').lower()
    SESSION_COOKIE_SECURE = _cookie_secure == 'true' or (_env == 'production' and _cookie_secure != 'false')
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    
    # ── CSRF ──────────────────────────────────────────────
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # Sem expiração para tokens CSRF
    WTF_CSRF_SSL_STRICT = False  # True em produção com HTTPS
    
    # ── SEGURANÇA ─────────────────────────────────────────
    # Headers de segurança
    PREFERRED_URL_SCHEME = 'https'
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = 'memory://'  # Para produção, usar Redis
    RATELIMIT_STRATEGY = 'fixed-window'
    RATELIMIT_DEFAULT = os.getenv('API_RATE_LIMIT', '200 per day, 50 per hour')
    
    # ── VALIDAÇÃO DE SENHA ────────────────────────────────
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_DIGITS = True
    PASSWORD_REQUIRE_SPECIAL = True
    
    # ── LOGGING ───────────────────────────────────────────
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    # ── AMBIENTE ──────────────────────────────────────────
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    @classmethod
    def get_db_config(cls):
        """Retorna configuração do banco de dados"""
        return cls.DATABASE_CONFIG
