from flask import Flask, redirect, url_for
from config import Config
from models import db, DocumentType, Field
from auth import auth_bp
from routes_admin import admin_bp
from routes_documents import docs_bp

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# Регистрируем Blueprint'ы
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(docs_bp)

@app.route('/')
def hello():
    # Перенаправим на главную, если вошёл, иначе на логин
    from auth import get_current_user
    user = get_current_user()
    if user:
        html = f'<h1>Привет, {user.username}!</h1><p>Роль: {user.role}</p><ul>'
        html += '<li><a href="/users">Список пользователей</a></li>'
        html += '<li><a href="/add_test_user">Добавить тестового администратора</a></li>'
        if user.role == 'admin':
            html += '<li><a href="/admin/document_types">Управление видами документов (админ)</a></li>'
        html += '<li><a href="/documents">Мои документы</a></li>'
        html += '</ul><p><a href="/logout">Выйти</a></p>'
        return html
    else:
        return redirect(url_for('auth.login'))

# Создание таблиц и начальных данных
with app.app_context():
    db.create_all()
    if not DocumentType.query.filter_by(name='УКТП').first():
        uktp = DocumentType(name='УКТП', description='Универсальная карточка товара и поставщика')
        db.session.add(uktp)
        db.session.flush()
        fields_data = [
            ('Наименование продукта', 'string', True, 1),
            ('Применение', 'text', True, 2),
            # ... (можешь добавить остальные поля из спецификации, я сократил для примера)
        ]
        for fname, ftype, req, order in fields_data:
            db.session.add(Field(document_type_id=uktp.id, field_name=fname, field_type=ftype, is_required=req, order=order))
        db.session.commit()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
