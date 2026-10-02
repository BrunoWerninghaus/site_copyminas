"""
Utilitários de segurança: validação, logging de auditoria, etc.
"""

import re
import logging
import pymysql
from functools import wraps
from flask import session, request, render_template
from datetime import datetime
from src.config import SecurityConfig

# Configurar logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PasswordValidator:
    """Valida força de senhas"""
    
    @staticmethod
    def validate(password):
        """
        Valida se a senha atende aos requisitos de segurança
        
        Retorna: (is_valid: bool, message: str)
        """
        if len(password) < SecurityConfig.PASSWORD_MIN_LENGTH:
            return False, f"Mínimo {SecurityConfig.PASSWORD_MIN_LENGTH} caracteres"
        
        if SecurityConfig.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False, "Requer letra maiúscula (A-Z)"
        
        if SecurityConfig.PASSWORD_REQUIRE_DIGITS and not re.search(r'[0-9]', password):
            return False, "Requer número (0-9)"
        
        if SecurityConfig.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*\-_=+]', password):
            return False, "Requer caractere especial (!@#$%^&*-_=+)"
        
        return True, "Senha válida"


class AuditLogger:
    """Log de auditoria para rastrear ações importantes"""
    
    @staticmethod
    def log_action(user_id, action, details, ip_address=None):
        """
        Registra uma ação no log de auditoria
        
        Args:
            user_id: ID do usuário
            action: Ação realizada (LOGIN, LOGOUT, CREATE_REQUEST, UPDATE_REQUEST, etc)
            details: Detalhes da ação (JSON string)
            ip_address: IP do cliente
        """
        try:
            mysql = pymysql.connect(**SecurityConfig.get_db_config())
            cursor = mysql.cursor()
            
            query = """
                INSERT INTO audit_logs (user_id, action, details, ip_address, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                user_id,
                action,
                details,
                ip_address,
                datetime.now()
            ))
            
            mysql.commit()
            cursor.close()
            mysql.close()
            
            # Log também em arquivo
            logger.info(f"AUDIT: user={user_id} action={action} ip={ip_address}")
            
        except Exception as e:
            logger.error(f"Erro ao registrar auditoria: {str(e)}")
    
    @staticmethod
    def log_login(user_id, ip_address):
        """Log de login"""
        AuditLogger.log_action(user_id, 'LOGIN', 'User logged in', ip_address)
    
    @staticmethod
    def log_logout(user_id, ip_address):
        """Log de logout"""
        AuditLogger.log_action(user_id, 'LOGOUT', 'User logged out', ip_address)
    
    @staticmethod
    def log_maintenance_request_created(user_id, request_id, ip_address):
        """Log de criação de requisição"""
        AuditLogger.log_action(
            user_id,
            'CREATE_MAINTENANCE_REQUEST',
            f'Maintenance request {request_id} created',
            ip_address
        )
    
    @staticmethod
    def log_maintenance_request_updated(user_id, request_id, new_status, ip_address):
        """Log de atualização de requisição"""
        AuditLogger.log_action(
            user_id,
            'UPDATE_MAINTENANCE_REQUEST',
            f'Request {request_id} updated to {new_status}',
            ip_address
        )
    
    @staticmethod
    def log_user_created(admin_user_id, new_user_id, ip_address):
        """Log de criação de usuário"""
        AuditLogger.log_action(
            admin_user_id,
            'CREATE_USER',
            f'User {new_user_id} created',
            ip_address
        )


class SecurityValidation:
    """Validações de segurança"""
    
    @staticmethod
    def get_db_connection():
        """Retorna conexão segura com banco de dados"""
        try:
            return pymysql.connect(**SecurityConfig.get_db_config())
        except Exception as e:
            logger.error(f"Erro ao conectar ao banco: {str(e)}")
            raise
    
    @staticmethod
    def validate_equipment_ownership(equipment_id, user_id):
        """
        Verifica se o usuário tem acesso ao equipamento (rental ou personal)
        
        Retorna: (is_owner: bool, equipment_data: tuple or None)
        """
        try:
            mysql = SecurityValidation.get_db_connection()
            cursor = mysql.cursor()
            
            # Verifica se existe relacionamento user-equipment
            query = """
                SELECT e.id, e.name, ue.type 
                FROM equipments e
                JOIN user_equipments ue ON e.id = ue.equipment_id
                WHERE e.id = %s AND ue.user_id = %s
            """
            cursor.execute(query, (equipment_id, user_id))
            result = cursor.fetchone()
            
            cursor.close()
            mysql.close()
            
            if result:
                return True, result
            return False, None
            
        except Exception as e:
            logger.error(f"Erro ao validar propriedade do equipamento: {str(e)}")
            return False, None
    
    @staticmethod
    def validate_request_ownership(request_id, user_id):
        """
        Verifica se a requisição pertence ao usuário
        
        Retorna: (is_owner: bool, request_data: tuple or None)
        """
        try:
            mysql = SecurityValidation.get_db_connection()
            cursor = mysql.cursor()
            
            query = """
                SELECT mr.id, mr.user_id 
                FROM maintenance_requests mr
                WHERE mr.id = %s AND mr.user_id = %s
            """
            cursor.execute(query, (request_id, user_id))
            result = cursor.fetchone()
            
            cursor.close()
            mysql.close()
            
            return result is not None, result
            
        except Exception as e:
            logger.error(f"Erro ao validar propriedade da requisição: {str(e)}")
            return False, None
    
    @staticmethod
    def validate_priority(priority):
        """Valida se a prioridade é válida"""
        valid_priorities = ['baixa', 'media', 'alta']
        return priority in valid_priorities
    
    @staticmethod
    def validate_status(status):
        """Valida se o status é válido"""
        valid_statuses = ['pendente', 'em_andamento', 'concluida', 'cancelada']
        return status in valid_statuses


def handle_db_error(func):
    """
    Decorator para tratamento seguro de erros de banco de dados
    Remove informações sensíveis de erros
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except pymysql.IntegrityError as e:
            logger.error(f"Database integrity error: {str(e)}")
            return render_template(
                'error.html' if 'error.html' else 'index.html',
                error='Erro ao processar dados. Por favor, tente novamente.'
            )
        except pymysql.ProgrammingError as e:
            logger.error(f"Database programming error: {str(e)}")
            return render_template(
                'error.html' if 'error.html' else 'index.html',
                error='Erro ao acessar banco de dados.'
            )
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            return render_template(
                'error.html' if 'error.html' else 'index.html',
                error='Erro ao processar requisição.'
            )
    return wrapper


def require_login(func):
    """Decorator para exigir login"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return render_template('login.html', error='Por favor, faça login primeiro')
        return func(*args, **kwargs)
    return wrapper


def require_admin(func):
    """Decorator para exigir privilégios de admin"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return render_template('login.html', error='Por favor, faça login primeiro')
        
        if not session.get('is_admin'):
            return render_template('error.html', error='Acesso negado. Privilégios de administrador necessários.')
        
        return func(*args, **kwargs)
    return wrapper
