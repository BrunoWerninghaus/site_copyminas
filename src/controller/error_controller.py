from flask.views import MethodView
from flask import render_template
import logging

logger = logging.getLogger(__name__)


def NotFoundController(error):
    """Handle 404 errors safely without exposing details"""
    logger.warning(f"404 error: {str(error)}")
    return render_template('error.html', 
                         error='Página não encontrada', 
                         details='A página que você está procurando não existe.'), 404