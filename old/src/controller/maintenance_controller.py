from flask.views import MethodView
from flask import render_template, session, redirect, url_for, request
import pymysql
import logging
from src.config import SecurityConfig
from src.utils.security import (
    SecurityValidation, handle_db_error, AuditLogger, require_login, require_admin
)

logger = logging.getLogger(__name__)


class MaintenanceController(MethodView):
    @require_login
    @handle_db_error
    def get(self):
        user_id = session.get('user_id')
        is_admin = session.get('is_admin', False)
        
        try:
            mysql = pymysql.connect(**SecurityConfig.get_db_config())
            cursor = mysql.cursor()
            
            # ─── ADMIN: Acesso total ───
            if is_admin:
                # Busca TODOS os usuários para dropdown
                users_query = "SELECT id, name FROM users ORDER BY name"
                cursor.execute(users_query)
                users = cursor.fetchall()
                
                # Busca TODOS os equipamentos genéricos
                equipments_query = "SELECT id, name FROM equipments ORDER BY name"
                cursor.execute(equipments_query)
                equipments = cursor.fetchall()
                
            # ─── CLIENTE: Acesso restrito aos seus equipamentos ───
            else:
                users = []
                
                # Busca equipamentos RENTAL atribuídos ao usuário (nova estrutura)
                equipments_query = """
                    SELECT e.id, e.name FROM equipments e
                    JOIN user_equipments ue ON e.id = ue.equipment_id
                    WHERE ue.user_id = %s AND ue.type = 'rental'
                    ORDER BY e.name
                """
                cursor.execute(equipments_query, (user_id,))
                equipments = cursor.fetchall()
            
            cursor.close()
            mysql.close()
            
            logger.info(f"User {user_id} accessed maintenance page (admin: {is_admin})")
            return render_template('maintenance.html', 
                                 equipments=equipments,
                                 users=users,
                                 is_admin=is_admin)
        
        except pymysql.Error as e:
            logger.error(f"Database error retrieving maintenance data: {str(e)}")
            return render_template('maintenance.html', error='Erro ao buscar dados. Tente novamente.')
    
    @require_login
    @handle_db_error
    def post(self):
        user_id = session.get('user_id')
        is_admin = session.get('is_admin', False)
        equipment_id = request.form.get('equipment_id', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'media').strip()
        target_user_id = request.form.get('user_id', user_id).strip() if is_admin else user_id
        
        # Validações
        if not equipment_id or not description:
            return render_template('maintenance.html', error='Equipamento e descrição são obrigatórios')
        
        # Validar prioridade
        if not SecurityValidation.validate_priority(priority):
            return render_template('maintenance.html', error='Prioridade inválida')
        
        try:
            mysql = pymysql.connect(**SecurityConfig.get_db_config())
            cursor = mysql.cursor()
            
            # ─── ADMIN: Pode criar para qualquer usuário ───
            if is_admin:
                # Valida se o equipamento existe (genérico)
                check_equipment = "SELECT id, name FROM equipments WHERE id = %s"
                cursor.execute(check_equipment, (equipment_id,))
                equipment_data = cursor.fetchone()
                
                if not equipment_data:
                    cursor.close()
                    mysql.close()
                    logger.warning(f"Admin {user_id} tried to use non-existent equipment {equipment_id}")
                    return render_template('maintenance.html', error='Equipamento não encontrado')
                
                # Valida se o usuário-alvo existe
                check_user = "SELECT id, name FROM users WHERE id = %s"
                cursor.execute(check_user, (target_user_id,))
                target_user = cursor.fetchone()
                
                if not target_user:
                    cursor.close()
                    mysql.close()
                    logger.warning(f"Admin {user_id} tried to create request for non-existent user {target_user_id}")
                    return render_template('maintenance.html', error='Usuário não encontrado')
            
            # ─── CLIENTE: Só para equipamentos próprios rental ───
            else:
                # Verifica se o equipamento é RENTAL e pertence ao usuário
                check_equipment = """
                    SELECT e.id, e.name FROM equipments e
                    JOIN user_equipments ue ON e.id = ue.equipment_id
                    WHERE e.id = %s AND ue.user_id = %s AND ue.type = 'rental'
                """
                cursor.execute(check_equipment, (equipment_id, user_id))
                equipment_data = cursor.fetchone()
                
                if not equipment_data:
                    cursor.close()
                    mysql.close()
                    logger.warning(f"User {user_id} tried to create request for equipment {equipment_id} they don't own as rental")
                    return render_template('maintenance.html', error='Equipamento não encontrado ou não é tipo rental')
            
            # Insere nova requisição de manutenção
            insert_query = """
                INSERT INTO maintenance_requests (user_id, equipment_id, description, status, priority, created_at)
                VALUES (%s, %s, %s, 'pendente', %s, NOW())
            """
            cursor.execute(insert_query, (target_user_id, equipment_id, description, priority))
            request_id = cursor.lastrowid
            mysql.commit()
            
            # Log de auditoria
            action_msg = f'Created maintenance request {request_id} for equipment {equipment_id} (user: {target_user_id})'
            if is_admin and target_user_id != user_id:
                action_msg = f'[ADMIN] ' + action_msg
            AuditLogger.log_action(user_id, 'MAINTENANCE_REQUEST_CREATED', action_msg, request.remote_addr)
            
            cursor.close()
            mysql.close()
            
            logger.info(f"User {user_id} created maintenance request {request_id} for user {target_user_id}")
            return redirect(url_for('maintenance'))
        
        except pymysql.Error as e:
            logger.error(f"Database error creating maintenance request: {str(e)}")
            return render_template('maintenance.html', error='Erro ao criar requisição. Tente novamente.')
        except Exception as e:
            logger.error(f"Unexpected error creating maintenance request: {str(e)}")
            return render_template('maintenance.html', error='Erro ao processar requisição.')

