from flask.views import MethodView
from flask import render_template, session, redirect, url_for, request
import pymysql
import logging
from src.config import SecurityConfig
from src.utils.security import (
    SecurityValidation, handle_db_error, AuditLogger, require_login
)

logger = logging.getLogger(__name__)


class DashboardController(MethodView):
    @require_login
    @handle_db_error
    def get(self):
        user_id = session.get('user_id')
        user_name = session.get('user_name')
        user_email = session.get('user_email')
        is_admin = session.get('is_admin', False)
        
        try:
            mysql = pymysql.connect(**SecurityConfig.get_db_config())
            cursor = mysql.cursor()
            
            if is_admin:
                # ADMIN: Equipamentos de ALUGUEL (busca todos com type=rental)
                rental_query = """
                    SELECT e.id, e.name, e.description, ue.serial_number, ue.type, ue.user_id, u.name
                    FROM user_equipments ue
                    JOIN equipments e ON ue.equipment_id = e.id
                    LEFT JOIN users u ON ue.user_id = u.id
                    WHERE ue.type = 'rental'
                    ORDER BY e.name
                """
                cursor.execute(rental_query)
                rental_equipments = cursor.fetchall()
                
                logger.info(f"DEBUG - Rental equipments: {rental_equipments}")
                
                # ADMIN: Equipamentos PESSOAIS
                personal_query = """
                    SELECT e.id, e.name, e.description, ue.serial_number, ue.type, ue.user_id, u.name
                    FROM user_equipments ue
                    JOIN equipments e ON ue.equipment_id = e.id
                    LEFT JOIN users u ON ue.user_id = u.id
                    WHERE ue.type = 'personal'
                    ORDER BY e.name
                """
                cursor.execute(personal_query)
                personal_equipments = cursor.fetchall()
                
                logger.info(f"DEBUG - Personal equipments: {personal_equipments}")
                
                # ADMIN: Chamados PENDENTES
                pending_query = """
                    SELECT mr.id, mr.description, mr.status, e.name, mr.created_at, mr.priority, u.name
                    FROM maintenance_requests mr
                    JOIN equipments e ON mr.equipment_id = e.id
                    JOIN users u ON mr.user_id = u.id
                    WHERE mr.status = 'pendente'
                    ORDER BY mr.created_at DESC
                """
                cursor.execute(pending_query)
                pending_requests_list = cursor.fetchall()
                
                logger.info(f"DEBUG - Pending requests: {pending_requests_list}")
                
                # ADMIN: Chamados EM ANDAMENTO
                in_progress_query = """
                    SELECT mr.id, mr.description, mr.status, e.name, mr.created_at, mr.priority, u.name
                    FROM maintenance_requests mr
                    JOIN equipments e ON mr.equipment_id = e.id
                    JOIN users u ON mr.user_id = u.id
                    WHERE mr.status = 'em_andamento'
                    ORDER BY mr.created_at DESC
                """
                cursor.execute(in_progress_query)
                in_progress_requests_list = cursor.fetchall()
                
                logger.info(f"DEBUG - In progress requests: {in_progress_requests_list}")
                
                # Conta chamados pendentes (todos)
                cursor.execute(
                    "SELECT COUNT(*) FROM maintenance_requests WHERE status = 'pendente'"
                )
                pending_count = cursor.fetchone()[0]
                
                # Conta chamados em andamento (todos)
                cursor.execute(
                    "SELECT COUNT(*) FROM maintenance_requests WHERE status = 'em_andamento'"
                )
                in_progress_count = cursor.fetchone()[0]
                
                # Conta total de equipamentos
                total_equipments = len(rental_equipments) + len(personal_equipments)
                
                cursor.close()
                mysql.close()
                
                logger.info(f"Admin {user_id} accessed dashboard")
                return render_template('dashboard.html', 
                                     user_name=user_name,
                                     user_email=user_email,
                                     is_admin=is_admin,
                                     rental_equipments=rental_equipments,
                                     personal_equipments=personal_equipments,
                                     pending_requests_list=pending_requests_list,
                                     in_progress_requests_list=in_progress_requests_list,
                                     pending_requests=pending_count,
                                     in_progress_requests=in_progress_count,
                                     total_equipments=total_equipments)
            else:
                # CLIENTE: Busca equipamentos de ALUGUEL (rental) do usuário com serial
                rental_query = """
                    SELECT e.id, e.name, e.description, ue.serial_number, ue.type
                    FROM equipments e
                    JOIN user_equipments ue ON e.id = ue.equipment_id
                    WHERE ue.user_id = %s AND ue.type = 'rental'
                    ORDER BY e.name
                """
                cursor.execute(rental_query, (user_id,))
                rental_equipments = cursor.fetchall()
                
                # CLIENTE: Busca equipamentos PESSOAIS do usuário com serial
                personal_query = """
                    SELECT e.id, e.name, e.description, ue.serial_number, ue.type
                    FROM equipments e
                    JOIN user_equipments ue ON e.id = ue.equipment_id
                    WHERE ue.user_id = %s AND ue.type = 'personal'
                    ORDER BY e.name
                """
                cursor.execute(personal_query, (user_id,))
                personal_equipments = cursor.fetchall()
                
                # CLIENTE: Busca chamados ABERTOS (pendente + em_andamento) do usuário
                query_open_requests = """
                    SELECT mr.id, mr.description, mr.status, e.name, mr.created_at, mr.priority
                    FROM maintenance_requests mr
                    JOIN equipments e ON mr.equipment_id = e.id
                    WHERE mr.user_id = %s AND mr.status IN ('pendente', 'em_andamento')
                    ORDER BY mr.created_at DESC
                """
                cursor.execute(query_open_requests, (user_id,))
                open_requests = cursor.fetchall()
                
                # Conta chamados pendentes do usuário
                cursor.execute(
                    "SELECT COUNT(*) FROM maintenance_requests WHERE user_id = %s AND status = 'pendente'",
                    (user_id,)
                )
                pending_count = cursor.fetchone()[0]
                
                # Conta chamados em andamento do usuário
                cursor.execute(
                    "SELECT COUNT(*) FROM maintenance_requests WHERE user_id = %s AND status = 'em_andamento'",
                    (user_id,)
                )
                in_progress_count = cursor.fetchone()[0]
                
                # Conta equipamentos de aluguel do usuário
                total_rental = len(rental_equipments)
                
                cursor.close()
                mysql.close()
                
                logger.info(f"User {user_id} accessed dashboard")
                return render_template('dashboard.html', 
                                     user_name=user_name,
                                     user_email=user_email,
                                     is_admin=is_admin,
                                     rental_equipments=rental_equipments,
                                     personal_equipments=personal_equipments,
                                     open_requests=open_requests,
                                     pending_requests=pending_count,
                                     in_progress_requests=in_progress_count,
                                     total_rental_equipments=total_rental)
        
        except pymysql.Error as e:
            logger.error(f"Database error retrieving dashboard data: {str(e)}")
            return render_template('dashboard.html', 
                                 user_name=user_name,
                                 user_email=user_email,
                                 is_admin=is_admin,
                                 error='Erro ao buscar dados. Tente novamente.')
    
    @require_login
    @handle_db_error
    def post(self):
        user_id = session.get('user_id')
        user_name = session.get('user_name')
        user_email = session.get('user_email')
        
        action = request.form.get('action', 'create_request').strip()
        
        if action == 'create_request':
            return self._create_request(user_id, user_name, user_email)
        else:
            return render_template('dashboard.html',
                                 user_name=user_name,
                                 user_email=user_email,
                                 error='Ação desconhecida')
    
    def _create_request(self, user_id, user_name, user_email):
        """Create maintenance request"""
        equipment_id = request.form.get('equipment_id', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'media').strip()
        
        # Validações
        if not equipment_id or not description:
            return render_template('dashboard.html',
                                 user_name=user_name,
                                 user_email=user_email,
                                 error='Equipamento e descrição são obrigatórios')
        
        # Validar prioridade
        if not SecurityValidation.validate_priority(priority):
            return render_template('dashboard.html',
                                 user_name=user_name,
                                 user_email=user_email,
                                 error='Prioridade inválida')
        
        # Validar se o equipamento pertence ao usuário
        is_owner, equipment_data = SecurityValidation.validate_equipment_ownership(equipment_id, user_id)
        if not is_owner:
            logger.warning(f"User {user_id} tried to access equipment {equipment_id} they don't own")
            return render_template('dashboard.html',
                                 user_name=user_name,
                                 user_email=user_email,
                                 error='Equipamento não encontrado')
        
        try:
            mysql = pymysql.connect(**SecurityConfig.get_db_config())
            cursor = mysql.cursor()
            
            # Insere nova requisição de manutenção
            query = """
                INSERT INTO maintenance_requests (user_id, equipment_id, description, status, priority, created_at)
                VALUES (%s, %s, %s, 'pendente', %s, NOW())
            """
            cursor.execute(query, (user_id, equipment_id, description, priority))
            request_id = cursor.lastrowid
            mysql.commit()
            
            # Log de auditoria
            AuditLogger.log_maintenance_request_created(user_id, request_id, request.remote_addr)
            
            cursor.close()
            mysql.close()
            
            logger.info(f"User {user_id} created maintenance request {request_id} from dashboard")
            return redirect(url_for('dashboard'))
        
        except pymysql.Error as e:
            logger.error(f"Database error creating maintenance request: {str(e)}")
            return render_template('dashboard.html',
                                 user_name=user_name,
                                 user_email=user_email,
                                 error='Erro ao criar chamado. Tente novamente.')
        except Exception as e:
            logger.error(f"Unexpected error creating maintenance request: {str(e)}")
            return render_template('dashboard.html',
                                 user_name=user_name,
                                 user_email=user_email,
                                 error='Erro ao processar requisição.')
