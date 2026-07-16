from flask import Blueprint, request, redirect, url_for
from models import db, DocumentType, Field, DocumentInstance, DocumentFieldValue
from auth import login_required, get_current_user

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
        # Создаём экземпляр
        instance = DocumentInstance(document_type_id=type_id, creator_id=user.id, status='draft')
        db.session.add(instance)
        db.session.flush()  # получаем instance.id
        # Сохраняем значения полей
        for field in fields:
            value = request.form.get(f'field_{field.id}', '')
            db.session.add(DocumentFieldValue(document_id=instance.id, field_id=field.id, value=value))
        db.session.commit()
        return redirect(url_for('docs.view_document', doc_id=instance.id))

    # GET: показываем форму
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
    # Проверка прав: только создатель или админ
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
    html += '<br><a href="/documents">🔙 Мои документы</a>'
    return html
