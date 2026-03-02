from flask.views import MethodView
from flask import render_template, session, redirect, url_for, request, jsonify
import pymysql
import logging
from src.config import SecurityConfig
from src.utils.password_utils import hash_password
from src.utils.security import (
    SecurityValidation, PasswordValidator, handle_db_error, AuditLogger, require_login
)

logger = logging.getLogger(__name__)


def require_admin(f):
    """Decorator to require admin access"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            logger.warning(f"Unauthorized admin access attempt by user {session.get('user_id')}")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


class AdminController(MethodView):
    @require_admin
    @handle_db_error
    def get(self):
        user_id = session.get('user_id')
        
        # Parâmetros de filtro para logs
        filter_action = request.args.get('filter_action', '').strip()
        filter_user = request.args.get('filter_user', '').strip()
        
        try:
            mysql = pymysql.connect(**SecurityConfig.get_db_config())
            cursor = mysql.cursor()
            
            # Busca todas as requisições de manutenção
            query = """
                SELECT mr.id, mr.description, mr.status, mr.priority, 
                       u.name, e.name, mr.created_at
                FROM maintenance_requests mr
                JOIN users u ON mr.user_id = u.id
                JOIN equipments e ON mr.equipment_id = e.id
                ORDER BY mr.created_at DESC
            """
            cursor.execute(query)
            requests_data = cursor.fetchall()
            
            # Busca todos os usuários
            user_query = "SELECT id, name, email, is_admin, created_at FROM users ORDER BY created_at DESC"
            cursor.execute(user_query)
            users_data = cursor.fetchall()
            
            # Busca todos os equipamentos com informações do usuário associado
            equipment_query = """
                SELECT 
                    ue.id as user_equipment_id,
                    e.id as equipment_id,
                    e.name as equipment_name,
                    e.description as equipment_description,
                    ue.serial_number,
                    ue.type,
                    ue.user_id,
                    u.name as user_name
                FROM equipments e
                LEFT JOIN user_equipments ue ON e.id = ue.equipment_id
                LEFT JOIN users u ON ue.user_id = u.id
                ORDER BY e.name, u.name
            """
            cursor.execute(equipment_query)
            equipment_data = cursor.fetchall()
            
            # Busca logs de auditoria com filtros
            logs_query = """
                SELECT 
                    al.id,
                    al.created_at,
                    al.action,
                    al.details,
                    al.ip_address,
                    COALESCE(u.name, 'Sistema') as user_name
                FROM audit_logs al
                LEFT JOIN users u ON al.user_id = u.id
                WHERE 1=1
            """
            params = []
            
            if filter_action:
                logs_query += " AND al.action LIKE %s"
                params.append(f"%{filter_action}%")
            
            if filter_user:
                logs_query += " AND u.name LIKE %s"
                params.append(f"%{filter_user}%")
            
            logs_query += " ORDER BY al.created_at DESC LIMIT 200"
            
            cursor.execute(logs_query, params)
            audit_logs = cursor.fetchall()
            
            # Busca lista de ações distintas para o filtro
            cursor.execute("SELECT DISTINCT action FROM audit_logs ORDER BY action")
            available_actions = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            mysql.close()
            
            logger.info(f"Admin user {user_id} accessed admin panel")
            return render_template('admin.html', 
                                 requests=requests_data,
                                 users=users_data,
                                 user_equipments=equipment_data,
                                 user_name=session.get('user_name'),
                                 audit_logs=audit_logs,
                                 available_actions=available_actions,
                                 filter_action=filter_action,
                                 filter_user=filter_user)
        
        except pymysql.Error as e:
            logger.error(f"Database error retrieving admin data: {str(e)}")
            return render_template('admin.html', error='Erro ao buscar dados. Tente novamente.')
    
    @require_admin
    @handle_db_error
    def post(self):
        user_id = session.get('user_id')
        action = request.form.get('action', '').strip()
        
        if action == 'update_request':
            return self._update_request(user_id)
        elif action == 'create_user':
            return self._create_user(user_id)
        elif action == 'edit_user':
            return self._edit_user(user_id)
        elif action == 'delete_user':
            return self._delete_user(user_id)
        elif action == 'create_equipment':
            return self._create_equipment(user_id)
        elif action == 'edit_equipment':
            return self._edit_equipment(user_id)
        elif action == 'delete_equipment':
            return self._delete_equipment(user_id)
        else:
            logger.warning(f"Admin {user_id} attempted unknown action: {action}")
            return render_template('admin.html', error='Ação desconhecida')
    
    def _update_request(self, admin_id):
        """Update maintenance request status"""
        request_id = request.form.get('request_id', '').strip()
        new_status = request.form.get('status', '').strip()
        
        # Validações
        if not request_id or not new_status:
            return render_template('admin.html', error='ID da requisição e status são obrigatórios')
        
        # Validar status
        if not SecurityValidation.validate_status(new_status):
            return render_template('admin.html', error='Status inválido')
        
        try:
            mysql = pymysql.connect(**SecurityConfig.get_db_config())
            cursor = mysql.cursor()
            
            # Atualiza o status da requisição
            query = "UPDATE maintenance_requests SET status = %s WHERE id = %s"
            cursor.execute(query, (new_status, request_id))
            mysql.commit()
            
            # Audit log
            AuditLogger.log_maintenance_request_updated(admin_id, request_id, new_status, request.remote_addr)
            
            cursor.close()
            mysql.close()
            
            logger.info(f"Admin {admin_id} updated maintenance request {request_id} status to {new_status}")
            return redirect(url_for('admin'))
        
        except pymysql.Error as e:
            logger.error(f"Database error updating request: {str(e)}")
            return render_template('admin.html', error='Erro ao atualizar requisição. Tente novamente.')
    
    def _create_user(self, admin_id):
        """Create new user with password strength validation"""
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        is_admin = request.form.get('is_admin') == 'on'
        
        # Validações básicas
        if not name or not email or not password:
            return render_template('admin.html', error='Nome, email e senha são obrigatórios')
        
        # Validar força da senha
        is_valid, message = PasswordValidator.validate(password)
        if not is_valid:
            return render_template('admin.html', error=f'Senha fraca: {message}')
        
        try:
            mysql = pymysql.connect(**SecurityConfig.get_db_config())
            cursor = mysql.cursor()
            
            # Verifica se email já existe
            check_query = "SELECT id FROM users WHERE email = %s OR name = %s"
            cursor.execute(check_query, (email, name))
            if cursor.fetchone():
                cursor.close()
                mysql.close()
                logger.warning(f"Admin {admin_id} tried to create user with duplicate email/name: {email}")
                return render_template('admin.html', error='Email ou nome de usuário já registrado')
            
            # Insere novo usuário
            hashed_password = hash_password(password)
            insert_query = "INSERT INTO users (name, email, password, is_admin) VALUES (%s, %s, %s, %s)"
            cursor.execute(insert_query, (name, email, hashed_password, is_admin))
            new_user_id = cursor.lastrowid
            mysql.commit()
            
            # Audit log
            admin_role = "admin" if is_admin else "user"
            AuditLogger.log_action(admin_id, 'USER_CREATED_BY_ADMIN', 
                                  f'Created user {new_user_id} ({admin_role})', request.remote_addr)
            
            cursor.close()
            mysql.close()
            
            logger.info(f"Admin {admin_id} created new user {new_user_id}")
            return redirect(url_for('admin'))
        
        except pymysql.IntegrityError as e:
            logger.warning(f"Database integrity error creating user by admin {admin_id}: {str(e)}")
            return render_template('admin.html', error='Erro ao criar usuário. Email/nome pode estar duplicado.')
        except pymysql.Error as e:
            logger.error(f"Database error creating user: {str(e)}")
            return render_template('admin.html', error='Erro ao criar usuário. Tente novamente.')
    
    def _edit_user(self, admin_id):
        """Edit user details"""
        user_id = request.form.get('user_id', '').strip()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        new_password = request.form.get('password', '').strip()
        is_admin = request.form.get('is_admin') == 'on'
        
        if not user_id or not name or not email:
            return render_template('admin.html', error='ID, nome e email são obrigatórios')
        
        if new_password:
            is_valid, message = PasswordValidator.validate(new_password)
            if not is_valid:
                return render_template('admin.html', error=f'Senha fraca: {message}')
        
        try:
            mysql = pymysql.connect(**SecurityConfig.get_db_config())
            cursor = mysql.cursor()
            
            check_query = "SELECT id FROM users WHERE email = %s AND id != %s"
            cursor.execute(check_query, (email, user_id))
            if cursor.fetchone():
                cursor.close()
                mysql.close()
                return render_template('admin.html', error='Email já está em uso por outro usuário')
            
            if new_password:
                hashed_password = hash_password(new_password)
                update_query = "UPDATE users SET name = %s, email = %s, password = %s, is_admin = %s WHERE id = %s"
                cursor.execute(update_query, (name, email, hashed_password, is_admin, user_id))
            else:
                update_query = "UPDATE users SET name = %s, email = %s, is_admin = %s WHERE id = %s"
                cursor.execute(update_query, (name, email, is_admin, user_id))
            
            mysql.commit()
            AuditLogger.log_action(admin_id, 'USER_UPDATED', f'Updated user {user_id}: {name} ({email})', request.remote_addr)
            
            cursor.close()
            mysql.close()
            
            logger.info(f"Admin {admin_id} updated user {user_id}")
            return redirect(url_for('admin'))
        
        except pymysql.Error as e:
            logger.error(f"Database error updating user: {str(e)}")
            return render_template('admin.html', error='Erro ao atualizar usuário. Tente novamente.')
        except Exception as e:
            logger.error(f"Unexpected error updating user: {str(e)}")
            return render_template('admin.html', error='Erro ao processar requisição.')
    
    def _delete_user(self, admin_id):
        """Delete a user"""
        user_id = request.form.get('user_id', '').strip()
        
        if not user_id:
            return render_template('admin.html', error='ID do usuário é obrigatório')
        
        if str(user_id) == str(admin_id):
            return render_template('admin.html', error='Você não pode excluir seu próprio usuário')
        
        try:
            mysql = pymysql.connect(**SecurityConfig.get_db_config())
            cursor = mysql.cursor()
            
            check_query = "SELECT name FROM users WHERE id = %s"
            cursor.execute(check_query, (user_id,))
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                mysql.close()
                return render_template('admin.html', error='Usuário não encontrado')
            
            cursor.execute("DELETE FROM user_equipments WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM maintenance_requests WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            
            mysql.commit()
            AuditLogger.log_action(admin_id, 'USER_DELETED', f'Deleted user {user_id}: {user[0]}', request.remote_addr)
            
            cursor.close()
            mysql.close()
            
            logger.info(f"Admin {admin_id} deleted user {user_id}")
            return redirect(url_for('admin'))
        
        except pymysql.Error as e:
            logger.error(f"Database error deleting user: {str(e)}")
            return render_template('admin.html', error='Erro ao excluir usuário. Tente novamente.')
        except Exception as e:
            logger.error(f"Unexpected error deleting user: {str(e)}")
            return render_template('admin.html', error='Erro ao processar requisição.')
    
    def _create_equipment(self, admin_id):
        """Create new equipment (generic, optionally related to user)"""
        equipment_name = request.form.get('equipment_name', '').strip()
        equipment_description = request.form.get('equipment_description', '').strip()
        user_id_equipment = request.form.get('user_id_equipment', '').strip()
        equipment_type = request.form.get('equipment_type', 'personal').strip()
        serial_number = request.form.get('serial_number', '').strip()
        
        # Validações
        if not equipment_name:
            return render_template('admin.html', error='Nome do equipamento é obrigatório')
        
        # Validar tipo de equipamento
        if equipment_type not in ['rental', 'personal']:
            equipment_type = 'personal'
        
        try:
            mysql = pymysql.connect(**SecurityConfig.get_db_config())
            cursor = mysql.cursor()
            
            # Insere novo equipamento genérico
            insert_query = """
                INSERT INTO equipments (name, description, created_at) 
                VALUES (%s, %s, NOW())
            """
            cursor.execute(insert_query, (equipment_name, equipment_description if equipment_description else None))
            equipment_id = cursor.lastrowid
            mysql.commit()
            
            # Se um usuário foi selecionado, cria relação na tabela user_equipments
            if user_id_equipment:
                # Verifica se o usuário existe
                check_user = "SELECT id FROM users WHERE id = %s"
                cursor.execute(check_user, (user_id_equipment,))
                if cursor.fetchone():
                    # Insere relação na tabela user_equipments (agora permite duplicatas)
                    relation_query = """
                        INSERT INTO user_equipments (user_id, equipment_id, type, serial_number, added_at)
                        VALUES (%s, %s, %s, %s, NOW())
                    """
                    cursor.execute(relation_query, (user_id_equipment, equipment_id, equipment_type, serial_number if serial_number else None))
                    mysql.commit()
                    logger.info(f"Admin {admin_id} assigned {equipment_type} equipment {equipment_id} to user {user_id_equipment} with serial {serial_number}")
            
            # Audit log
            audit_msg = f'Created equipment {equipment_id}: {equipment_name}'
            if user_id_equipment:
                audit_msg += f' (assigned to user {user_id_equipment} as personal)'
            AuditLogger.log_action(admin_id, 'EQUIPMENT_CREATED', audit_msg, request.remote_addr)
            
            cursor.close()
            mysql.close()
            
            logger.info(f"Admin {admin_id} created equipment {equipment_id}")
            return redirect(url_for('admin'))
        
        except pymysql.Error as e:
            logger.error(f"Database error creating equipment: {str(e)}")
            return render_template('admin.html', error='Erro ao criar equipamento. Tente novamente.')
        except Exception as e:
            logger.error(f"Unexpected error creating equipment: {str(e)}")
            return render_template('admin.html', error='Erro ao processar requisição.')
    
    def _edit_equipment(self, admin_id):
        """Edit equipment details"""
        user_equipment_id = request.form.get('user_equipment_id', '').strip()
        equipment_id = request.form.get('equipment_id', '').strip()
        equipment_name = request.form.get('equipment_name', '').strip()
        equipment_description = request.form.get('equipment_description', '').strip()
        serial_number = request.form.get('serial_number', '').strip()
        equipment_type = request.form.get('equipment_type', 'personal').strip()
        user_id = request.form.get('user_id', '').strip()
        
        if not equipment_id or not equipment_name:
            return render_template('admin.html', error='ID e nome do equipamento são obrigatórios')
        
        try:
            mysql = pymysql.connect(**SecurityConfig.get_db_config())
            cursor = mysql.cursor()
            
            # Atualiza informações do equipamento na tabela equipments
            update_equipment_query = """
                UPDATE equipments SET name = %s, description = %s WHERE id = %s
            """
            cursor.execute(update_equipment_query, (equipment_name, equipment_description if equipment_description else None, equipment_id))
            
            # Atualiza ou insere relação na tabela user_equipments
            if user_equipment_id:
                # Atualiza relação existente
                update_relation_query = """
                    UPDATE user_equipments SET type = %s, serial_number = %s, user_id = %s WHERE id = %s
                """
                cursor.execute(update_relation_query, (equipment_type, serial_number if serial_number else None, user_id if user_id else None, user_equipment_id))
            elif user_id:
                # Cria nova relação
                insert_relation_query = """
                    INSERT INTO user_equipments (user_id, equipment_id, type, serial_number, added_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """
                cursor.execute(insert_relation_query, (user_id, equipment_id, equipment_type, serial_number if serial_number else None))
            
            mysql.commit()
            
            # Audit log
            AuditLogger.log_action(admin_id, 'EQUIPMENT_UPDATED', f'Updated equipment {equipment_id}: {equipment_name}', request.remote_addr)
            
            cursor.close()
            mysql.close()
            
            logger.info(f"Admin {admin_id} updated equipment {equipment_id}")
            return redirect(url_for('admin'))
        
        except pymysql.Error as e:
            logger.error(f"Database error updating equipment: {str(e)}")
            return render_template('admin.html', error='Erro ao atualizar equipamento. Tente novamente.')
        except Exception as e:
            logger.error(f"Unexpected error updating equipment: {str(e)}")
            return render_template('admin.html', error='Erro ao processar requisição.')
    
    def _delete_equipment(self, admin_id):
        """Delete equipment or remove user-equipment relation"""
        user_equipment_id = request.form.get('user_equipment_id', '').strip()
        equipment_id = request.form.get('equipment_id', '').strip()
        
        if not equipment_id:
            return render_template('admin.html', error='ID do equipamento é obrigatório')
        
        try:
            mysql = pymysql.connect(**SecurityConfig.get_db_config())
            cursor = mysql.cursor()
            
            # Se tem user_equipment_id, remove apenas a relação
            if user_equipment_id:
                delete_relation_query = "DELETE FROM user_equipments WHERE id = %s"
                cursor.execute(delete_relation_query, (user_equipment_id,))
                mysql.commit()
                logger.info(f"Admin {admin_id} removed user-equipment relation {user_equipment_id}")
            else:
                # Remove o equipamento e suas relações
                cursor.execute("DELETE FROM user_equipments WHERE equipment_id = %s", (equipment_id,))
                cursor.execute("DELETE FROM equipments WHERE id = %s", (equipment_id,))
                mysql.commit()
                logger.info(f"Admin {admin_id} deleted equipment {equipment_id}")
            
            # Audit log
            AuditLogger.log_action(admin_id, 'EQUIPMENT_DELETED', f'Deleted equipment {equipment_id}', request.remote_addr)
            
            cursor.close()
            mysql.close()
            
            return redirect(url_for('admin'))
        
        except pymysql.Error as e:
            logger.error(f"Database error deleting equipment: {str(e)}")
            return render_template('admin.html', error='Erro ao excluir equipamento. Tente novamente.')
        except Exception as e:
            logger.error(f"Unexpected error deleting equipment: {str(e)}")
            return render_template('admin.html', error='Erro ao processar requisição.')


def get_user_equipments(user_id):
    """Retorna os equipamentos de um usuário em formato JSON (protegido contra IDOR)"""
    # Verificar se usuário está logado
    if 'user_id' not in session:
        logger.warning(f"Unauthorized access attempt to get_user_equipments")
        return jsonify({'error': 'Unauthorized'}), 401
    
    logged_user_id = session.get('user_id')
    is_admin = session.get('is_admin', False)
    requested_user_id = str(user_id).strip()
    
    # Proteger contra IDOR: só admin pode ver equipamentos de outros usuários
    if not is_admin and str(logged_user_id) != requested_user_id:
        logger.warning(f"User {logged_user_id} tried to access equipments of user {requested_user_id} - IDOR attack prevented")
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        mysql = pymysql.connect(**SecurityConfig.get_db_config())
        cursor = mysql.cursor()
        
        # Busca equipamentos do usuário (corrigido para usar user_equipments)
        query = """
            SELECT e.id, e.name 
            FROM equipments e
            JOIN user_equipments ue ON e.id = ue.equipment_id
            WHERE ue.user_id = %s 
            ORDER BY e.name
        """
        cursor.execute(query, (requested_user_id,))
        equipments = cursor.fetchall()
        
        cursor.close()
        mysql.close()
        
        logger.info(f"Retrieved equipments for user {requested_user_id}")
        return jsonify({'equipments': equipments})
    
    except pymysql.Error as e:
        logger.error(f"Database error fetching equipments: {str(e)}")
        return jsonify({'error': 'Erro ao buscar equipamentos'}), 500
    except Exception as e:
        logger.error(f"Unexpected error fetching equipments: {str(e)}")
        return jsonify({'error': 'Erro ao processar requisição'}), 500
