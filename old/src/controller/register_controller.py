from flask.views import MethodView
from flask import render_template, request, session, redirect, url_for
import pymysql
import logging
from src.config import SecurityConfig
from src.utils.password_utils import hash_password
from src.utils.security import PasswordValidator, handle_db_error, AuditLogger

logger = logging.getLogger(__name__)


class RegisterController(MethodView):
    def get(self):
        return render_template('register.html')
    
    @handle_db_error
    def post(self):
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validação básica
        if not name or not email or not password or not confirm_password:
            return render_template('register.html', error='Todos os campos são obrigatórios')
        
        if password != confirm_password:
            return render_template('register.html', error='As senhas não correspondem')
        
        # Validar força de senha
        is_valid, message = PasswordValidator.validate(password)
        if not is_valid:
            return render_template('register.html', error=f'Senha fraca: {message}')
        
        try:
            mysql = pymysql.connect(**SecurityConfig.get_db_config())
            cursor = mysql.cursor()
            
            # Verifica se o email já existe
            check_query = "SELECT id FROM users WHERE email = %s OR name = %s"
            cursor.execute(check_query, (email, name))
            if cursor.fetchone():
                cursor.close()
                mysql.close()
                logger.warning(f"Registration attempt with existing email/username: {email}")
                return render_template('register.html', error='Este email ou usuário já está registrado')
            
            # Insere novo usuário
            hashed_password = hash_password(password)
            insert_query = "INSERT INTO users (name, email, password, is_admin, created_at) VALUES (%s, %s, %s, FALSE, NOW())"
            cursor.execute(insert_query, (name, email, hashed_password))
            
            new_user_id = cursor.lastrowid
            mysql.commit()
            
            # Log de auditoria
            AuditLogger.log_action(
                new_user_id,
                'USER_REGISTERED',
                f'New user registered: {email}',
                request.remote_addr
            )
            
            cursor.close()
            mysql.close()
            
            logger.info(f"New user registered: {email}")
            return render_template('register.html', success='Usuário registrado com sucesso! Faça login agora.')
        
        except pymysql.IntegrityError:
            logger.error(f"Integrity error during registration: {email}")
            return render_template('register.html', error='Erro ao registrar usuário. Email pode já estar em uso.')
        
        except pymysql.Error as e:
            logger.error(f"Database error during registration: {str(e)}")
            return render_template('register.html', error='Erro ao processar registro. Tente novamente.')
        
        except Exception as e:
            logger.error(f"Unexpected error during registration: {str(e)}")
            return render_template('register.html', error='Erro ao processar registro.')
