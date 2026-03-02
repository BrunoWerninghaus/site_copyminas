from flask.views import MethodView
from flask import session, redirect, url_for, request
import logging
from src.utils.security import AuditLogger

logger = logging.getLogger(__name__)


class LogoutController(MethodView):
    def get(self):
        user_id = session.get('user_id')
        
        # Log audit trail before clearing session
        if user_id:
            try:
                AuditLogger.log_logout(user_id, request.remote_addr)
                logger.info(f"User {user_id} logged out")
            except Exception as e:
                logger.error(f"Error logging logout action: {str(e)}")
                # Continue with logout even if log fails
        
        session.clear()
        return redirect(url_for('main'))
