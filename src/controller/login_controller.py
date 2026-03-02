from flask.views import MethodView
from flask import render_template, request, redirect, session, url_for
import pymysql
import logging
from src.config import SecurityConfig
from src.utils.password_utils import check_password
from src.utils.security import AuditLogger, handle_db_error

logger = logging.getLogger(__name__)


class LoginController(MethodView):
    def get(self):
        return render_template('login.html')
    
    @handle_db_error
    def post(self):
        user = request.form.get('user', '').strip()
        password = request.form.get('password', '')
        
        # Validação básica
        if not user or not password:
            return render_template('login.html', error='Usuário e senha são obrigatórios')
        
        try:
            mysql = pymysql.connect(**SecurityConfig.get_db_config())
            cursor = mysql.cursor()
            
            # Busca usuário no banco por email ou username
            query = "SELECT id, name, email, password, is_admin FROM users WHERE name = %s OR email = %s"
            cursor.execute(query, (user, user))
            result = cursor.fetchone()
            
            cursor.close()
            mysql.close()
            
            if result and check_password(result[3], password):
                # Usuário encontrado e senha correta
                user_id = result[0]
                session['user_id'] = user_id
                session['user_name'] = result[1]
                session['user_email'] = result[2]
                session['is_admin'] = result[4]
                
                # Log de auditoria
                AuditLogger.log_login(user_id, request.remote_addr)
                logger.info(f"User {user_id} logged in successfully")
                
                if result[4]:  # Se é admin, redireciona para admin
                    return redirect(url_for('admin'))
                else:
                    return redirect(url_for('dashboard'))
            else:
                # Usuário não encontrado ou senha incorreta
                logger.warning(f"Failed login attempt for user: {user}")
                return render_template('login.html', error='Usuário ou senha incorretos')
        
        except pymysql.Error as e:
            logger.error(f"Database error during login: {str(e)}")
            return render_template('login.html', error='Erro ao processar login. Tente novamente.')
        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}")
            return render_template('login.html', error='Erro ao processar login.')
