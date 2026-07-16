from flask import Blueprint, request, redirect, url_for
from models import db, DocumentType, Field, DocumentInstance, DocumentFieldValue, User, ApprovalStep
from auth import login_required, get_current_user
from datetime import datetime

docs_bp = Blueprint('docs', __name__)

@docs_bp.route('/documents')
@login_required
def my_documents():
    user = get_current_user()
    instances = DocumentInstance.query.filter_by(creator_id=user.id).order_by(DocumentInstance.created_at.desc()).all()
    html = '<h2>Мои документы</h2>'
    if not instances:
        html += '<p>У вас пока нет документов.</p>'
    else:
        html += '<ul>'
        for doc in instances:
            dt_name = doc.document_type.name
            created = doc.created_at.strftime('%d.%m.%Y %H:%M')
            html += f'<li><a href="/document/{doc.id}">{dt_name} от {created}</a> — статус: {doc.status}</li>'
        html += '</ul>'
    html += '<h3>Создать новый документ</h3><ul>'
    types = DocumentType.query.all()
    for t in types:
        html += f'<li><a href="/create_document/{t.id}">{t.name}</a> — {t.description or ""}</li>'
    html += '</ul><p><a href="/">🔙 На главную</a></p>'
    return html

@docs_bp.route('/create_document/<int:type_id>', methods=['GET', 'POST'])
@login_required
def create_document(type_id):
    doc_type = DocumentType.query.get_or_404(type_id)
    fields = Field.query.filter_by(document_type_id=type_id).order_by(Field.order).all()
    user = get_current_user()

    if request.method == 'POST':
        instance = DocumentInstance(document_type_id=type_id, creator_id=user.id, status='draft')
        db.session.add(instance)
        db.session.flush()
        for field in fields:
            value = request.form.get(f'field_{field.id}', '')
            db.session.add(DocumentFieldValue(document_id=instance.id, field_id=field.id, value=value))
        db.session.commit()
        return redirect(url_for('docs.view_document', doc_id=instance.id))

    html = f'<h2>Создание документа: {doc_type.name}</h2>'
    html += '<form method="post">'
    for field in fields:
        req_attr = ' required' if field.is_required else ''
        html += f'<label>{field.field_name} ({field.field_type}){" *" if field.is_required else ""}:<br>'
        if field.field_type == 'text':
            html += f'<textarea name="field_{field.id}"{req_attr}></textarea>'
        elif field.field_type == 'date':
            html += f'<input type="date" name="field_{field.id}"{req_attr}>'
        else:
            html += f'<input type="text" name="field_{field.id}"{req_attr}>'
        html += '</label><br><br>'
    html += '<button type="submit">Сохранить</button></form>'
    html += '<p><a href="/documents">🔙 К списку документов</a></p>'
    return html

@docs_bp.route('/document/<int:doc_id>')
@login_required
def view_document(doc_id):
    doc = DocumentInstance.query.get_or_404(doc_id)
    if doc.creator_id != get_current_user().id and get_current_user().role != 'admin':
        return 'Доступ запрещён.', 403
    fields = Field.query.filter_by(document_type_id=doc.document_type_id).order_by(Field.order).all()
    values = {fv.field_id: fv.value for fv in doc.field_values}
    html = f'<h2>Документ: {doc.document_type.name}</h2>'
    html += f'<p>Статус: {doc.status} | Создатель: {doc.creator.username} | Создан: {doc.created_at.strftime("%d.%m.%Y %H:%M")}</p>'
    html += '<table border="1" cellpadding="5"><tr><th>Поле</th><th>Значение</th></tr>'
    for field in fields:
        val = values.get(field.id, '—')
        html += f'<tr><td>{field.field_name}</td><td>{val}</td></tr>'
    html += '</table>'

    # Показываем историю решений
    steps = ApprovalStep.query.filter_by(document_id=doc.id).order_by(ApprovalStep.created_at).all()
    if steps:
        html += '<h3>История согласования:</h3><ul>'
        for step in steps:
            dec = step.decision if step.decision else 'Ожидает решения'
            date_info = step.decided_at.strftime('%d.%m.%Y %H:%M') if step.decided_at else ''
            html += f'<li>{step.approver.username}: {dec} ({date_info}) — {step.comment or ""}</li>'
        html += '</ul>'

    # Кнопка отправки на согласование, если документ в статусе draft
    if doc.status == 'draft':
        html += f'<br><a href="/send_for_approval/{doc.id}" onclick="return confirm(\'Отправить на согласование?\')">📤 Отправить на согласование</a>'

    html += '<br><a href="/documents">🔙 Мои документы</a>'
    return html

@docs_bp.route('/send_for_approval/<int:doc_id>')
@login_required
def send_for_approval(doc_id):
    doc = DocumentInstance.query.get_or_404(doc_id)
    if doc.creator_id != get_current_user().id:
        return 'Вы не можете отправить чужой документ.', 403
    if doc.status != 'draft':
        return 'Документ уже отправлен.', 400

    # Находим всех пользователей с ролью approver
    approvers = User.query.filter_by(role='approver').all()
    if not approvers:
        return 'В системе нет подписантов. Обратитесь к администратору.', 400

    # Создаём шаги согласования
    for approver in approvers:
        step = ApprovalStep(document_id=doc.id, approver_id=approver.id)
        db.session.add(step)
    doc.status = 'pending_approval'
    db.session.commit()
    return redirect(url_for('docs.view_document', doc_id=doc.id))
