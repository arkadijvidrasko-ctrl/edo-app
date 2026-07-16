from flask import Blueprint, render_template_string
from auth import login_required

docs_bp = Blueprint('docs', __name__)

@docs_bp.route('/documents')
@login_required
def my_documents():
    return "<h2>Скоро здесь будут документы</h2>"
