from flask import Flask, redirect, url_for
from config import Config
from models import db, DocumentType, Field, User
from auth import auth_bp
from routes_admin import admin_bp
from routes_documents import docs_bp
from routes_approval import approval_bp

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(docs_bp)
app.register_blueprint(approval_bp)

@app.route('/')
def hello():
    from auth import get_current_user
    user = get_current_user()
    if user:
        html = f'<h1>Привет, {user.username}!</h1><p>Роль: {user.role}</p><ul>'
        html += '<li><a href="/users">Список пользователей</a></li>'
        html += '<li><a href="/add_test_user">Добавить тестового администратора</a></li>'
        if user.role == 'admin':
            html += '<li><a href="/admin/document_types">Управление видами документов (админ)</a></li>'
        html += '<li><a href="/documents">Мои документы</a></li>'
        if user.role == 'approver':
            html += '<li><a href="/approval">На согласование</a></li>'
        html += '</ul><p><a href="/logout">Выйти</a></p>'
        return html
    else:
        return redirect(url_for('auth.login'))

with app.app_context():
    db.create_all()

    # Создаём тестовых пользователей, если их нет
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@example.com', role='admin')
        db.session.add(admin)
    if not User.query.filter_by(username='approver').first():
        approver = User(username='approver', email='approver@example.com', role='approver')
        db.session.add(approver)
    db.session.commit()

    # Создаём УКТП
    if not DocumentType.query.filter_by(name='УКТП').first():
        uktp = DocumentType(name='УКТП', description='Универсальная карточка товара и поставщика')
        db.session.add(uktp)
        db.session.flush()
        fields_data = [
            ('Наименование продукта', 'string', True, 1),
            ('Применение', 'text', True, 2),
            ('Источник идеи', 'string', False, 3),
            ('Инициатор (ФИО)', 'string', True, 4),
            ('Контакты инициатора', 'string', False, 5),
            ('Дата регистрации идеи', 'date', False, 6),
            ('Геометрические характеристики', 'text', False, 7),
            ('Технические характеристики', 'text', False, 8),
            ('Требования к упаковке', 'text', False, 9),
            ('Требования к маркировке', 'text', False, 10),
            ('Объём первой партии', 'number', False, 11),
            ('Ежемесячный объём', 'number', False, 12),
            ('Конкуренты', 'text', False, 13),
            ('Предполагаемая цена продажи', 'number', False, 14),
            ('Целевая маржинальность (%)', 'number', False, 15),
            ('Решение СД №1 (одобрено/доработка/отказ)', 'string', False, 16),
            ('Экспресс-тест: заключение', 'text', False, 17),
            ('Юридические препятствия', 'text', False, 18),
            ('Объём пилотной партии', 'number', False, 19),
            ('Дата ввода в ассортимент', 'date', False, 20),
            ('Статус завершения', 'string', False, 21),
        ]
        for fname, ftype, req, order in fields_data:
            db.session.add(Field(
                document_type_id=uktp.id,
                field_name=fname,
                field_type=ftype,
                is_required=req,
                order=order
            ))
        db.session.commit()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
