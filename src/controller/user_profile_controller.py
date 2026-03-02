from flask.views import MethodView
from flask import render_template, session, redirect, url_for, request
import pymysql
import logging
from src.config import SecurityConfig
from src.utils.security import handle_db_error, AuditLogger

logger = logging.getLogger(__name__)


class UserProfileController(MethodView):
    def get(self, user_id):
        # Verifica se é admin
        if 'user_id' not in session or not session.get('is_admin'):
            logger.warning(f"Unauthorized user profile access attempt by user {session.get('user_id')} for user {user_id}")
            return redirect(url_for('login'))
        
        admin_id = session.get('user_id')
        user_id = str(user_id).strip()
        
        try:
            mysql = pymysql.connect(**SecurityConfig.get_db_config())
            cursor = mysql.cursor()
            
            # Busca informações do usuário
            user_query = "SELECT id, name, email, is_admin, created_at FROM users WHERE id = %s"
            cursor.execute(user_query, (user_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                cursor.close()
                mysql.close()
                logger.warning(f"Admin {admin_id} tried to view profile for non-existent user {user_id}")
                return render_template('user_profile.html', error='Usuário não encontrado')
            
            # Busca equipamentos de ALUGUEL (rental) do usuário
            rental_query = """
                SELECT e.id, e.name, e.description, ue.added_at
                FROM user_equipments ue
                JOIN equipments e ON ue.equipment_id = e.id
                WHERE ue.user_id = %s AND ue.type = 'rental'
                ORDER BY ue.added_at DESC
            """
            cursor.execute(rental_query, (user_id,))
            rental_equipments = cursor.fetchall()
            
            # Busca equipamentos PESSOAIS (personal) do usuário
            personal_query = """
                SELECT e.id, e.name, e.description, ue.added_at
                FROM user_equipments ue
                JOIN equipments e ON ue.equipment_id = e.id
                WHERE ue.user_id = %s AND ue.type = 'personal'
                ORDER BY ue.added_at DESC
            """
            cursor.execute(personal_query, (user_id,))
            personal_equipments = cursor.fetchall()
            
            # Busca equipamentos disponíveis para atribuir (não relacionados ao usuário)
            available_query = """
                SELECT id, name, description FROM equipments
                WHERE id NOT IN (
                    SELECT equipment_id FROM user_equipments WHERE user_id = %s
                )
                ORDER BY name
            """
            cursor.execute(available_query, (user_id,))
            available_equipments = cursor.fetchall()
            
            # Busca requisições de manutenção do usuário
            requests_query = """
                SELECT mr.id, e.name, mr.description, mr.status, mr.priority, mr.created_at, mr.updated_at
                FROM maintenance_requests mr
                JOIN equipments e ON mr.equipment_id = e.id
                WHERE mr.user_id = %s
                ORDER BY mr.created_at DESC
            """
            cursor.execute(requests_query, (user_id,))
            requests_data = cursor.fetchall()
            
            cursor.close()
            mysql.close()
            
            logger.info(f"Admin {admin_id} viewed profile for user {user_id}")
            return render_template('user_profile.html', 
                                 user=user_data,
                                 rental_equipments=rental_equipments,
                                 personal_equipments=personal_equipments,
                                 available_equipments=available_equipments,
                                 requests=requests_data)
        
        except pymysql.Error as e:
            logger.error(f"Database error retrieving user profile: {str(e)}")
            return render_template('user_profile.html', error='Erro ao buscar dados do usuário. Tente novamente.')
        except Exception as e:
            logger.error(f"Unexpected error retrieving user profile: {str(e)}")
            return render_template('user_profile.html', error='Erro ao processar requisição.')    
    def post(self, user_id):
        """Add equipment to user with type (rental or personal)"""
        # Verifica se é admin
        if 'user_id' not in session or not session.get('is_admin'):
            logger.warning(f"Unauthorized user profile access attempt by user {session.get('user_id')} for user {user_id}")
            return redirect(url_for('login'))
        
        admin_id = session.get('user_id')
        user_id = str(user_id).strip()
        equipment_id = request.form.get('equipment_id', '').strip()
        equipment_type = request.form.get('equipment_type', 'personal').strip()
        
        # Validações
        if not equipment_id:
            return render_template('user_profile.html', user={'id': user_id}, error='Equipamento não selecionado')
        
        # Validar tipo de equipamento
        if equipment_type not in ['rental', 'personal']:
            logger.warning(f"Admin {admin_id} tried invalid equipment type: {equipment_type}")
            return render_template('user_profile.html', user={'id': user_id}, error='Tipo de equipamento inválido')
        
        try:
            mysql = pymysql.connect(**SecurityConfig.get_db_config())
            cursor = mysql.cursor()
            
            # Verifica se o usuário existe
            check_user = "SELECT id FROM users WHERE id = %s"
            cursor.execute(check_user, (user_id,))
            if not cursor.fetchone():
                cursor.close()
                mysql.close()
                logger.warning(f"Admin {admin_id} tried to add equipment to non-existent user {user_id}")
                return render_template('user_profile.html', error='Usuário não encontrado')
            
            # Verifica se o equipamento existe
            check_eq = "SELECT id FROM equipments WHERE id = %s"
            cursor.execute(check_eq, (equipment_id,))
            if not cursor.fetchone():
                cursor.close()
                mysql.close()
                logger.warning(f"Admin {admin_id} tried to add non-existent equipment {equipment_id} to user {user_id}")
                return render_template('user_profile.html', user={'id': user_id}, 
                                     error='Equipamento não encontrado')
            
            # Insere ou atualiza relacionamento na tabela user_equipments
            insert_query = """
                INSERT INTO user_equipments (user_id, equipment_id, type, added_at) 
                VALUES (%s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE type = %s, added_at = NOW()
            """
            cursor.execute(insert_query, (user_id, equipment_id, equipment_type, equipment_type))
            mysql.commit()
            
            # Audit log
            AuditLogger.log_action(admin_id, 'EQUIPMENT_ASSIGNED_TO_USER',
                                  f'Admin {admin_id} assigned {equipment_type} equipment {equipment_id} to user {user_id}', 
                                  request.remote_addr)
            
            cursor.close()
            mysql.close()
            
            logger.info(f"Admin {admin_id} assigned {equipment_type} equipment {equipment_id} to user {user_id}")
            return redirect(url_for('user_profile', user_id=user_id))
        
        except pymysql.Error as e:
            logger.error(f"Database error adding equipment to user: {str(e)}")
            return render_template('user_profile.html', user={'id': user_id}, 
                                 error='Erro ao adicionar equipamento. Tente novamente.')
        except Exception as e:
            logger.error(f"Unexpected error adding equipment to user: {str(e)}")
            return render_template('user_profile.html', user={'id': user_id}, 
                                 error='Erro ao processar requisição.')