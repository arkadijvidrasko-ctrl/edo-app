from flask import Blueprint, request, redirect, url_for
from models import db, DocumentType, Field
from auth import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/document_types')
@admin_required
def list_document_types():
    types = DocumentType.query.all()
    html = '<h2>Виды документов</h2>'
    if types:
        html += '<ul>'
        for dt in types:
            html += f'<li><strong>{dt.name}</strong> — {dt.description or ""} '
            html += f'<a href="/admin/document_type/{dt.id}">(редактировать/поля)</a></li>'
        html += '</ul>'
    else:
        html += '<p>Пока нет видов документов.</p>'
    html += '''
        <h3>Создать новый вид</h3>
        <form method="post" action="/admin/create_document_type">
            <input type="text" name="name" placeholder="Название" required>
            <textarea name="description" placeholder="Описание"></textarea>
            <button type="submit">Создать</button>
        </form>
        <br><a href="/">🔙 Главная</a>
    '''
    return html

@admin_bp.route('/create_document_type', methods=['POST'])
@admin_required
def create_document_type():
    name = request.form.get('name', '').strip()
    if not name or DocumentType.query.filter_by(name=name).first():
        return 'Ошибка: пустое или неуникальное имя. <a href="/admin/document_types">Назад</a>'
    desc = request.form.get('description', '').strip()
    db.session.add(DocumentType(name=name, description=desc))
    db.session.commit()
    return redirect(url_for('admin.list_document_types'))

@admin_bp.route('/document_type/<int:type_id>', methods=['GET', 'POST'])
@admin_required
def edit_document_type(type_id):
    doc_type = DocumentType.query.get_or_404(type_id)
    if request.method == 'POST':
        fname = request.form.get('field_name', '').strip()
        ftype = request.form.get('field_type')
        req = request.form.get('is_required') == 'on'
        order = request.form.get('order', 0, type=int)
        if fname and ftype:
            db.session.add(Field(document_type_id=doc_type.id, field_name=fname, field_type=ftype, is_required=req, order=order))
            db.session.commit()
        return redirect(url_for('admin.edit_document_type', type_id=type_id))
    fields = Field.query.filter_by(document_type_id=doc_type.id).order_by(Field.order).all()
    html = f'<h2>Вид: {doc_type.name}</h2><p>{doc_type.description or ""}</p>'
    if fields:
        html += '<h3>Поля:</h3><ul>'
        for f in fields:
            req = '⭐' if f.is_required else ''
            html += f'<li>{f.order}. {f.field_name} ({f.field_type}) {req}</li>'
        html += '</ul>'
    html += '''
        <h3>Добавить поле</h3>
        <form method="post">
            <input type="text" name="field_name" placeholder="Название" required>
            <select name="field_type">
                <option value="string">Строка</option><option value="number">Число</option>
                <option value="date">Дата</option><option value="text">Текст</option>
                <option value="file">Файл</option><option value="list">Список</option>
            </select>
            <label>Обязательное: <input type="checkbox" name="is_required"></label>
            <input type="number" name="order" value="0" placeholder="Порядок">
            <button type="submit">Добавить</button>
        </form>
    '''
    html += '<br><a href="/admin/document_types">🔙 К списку видов</a>'
    return html
