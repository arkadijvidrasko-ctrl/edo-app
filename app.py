from flask import Flask, render_template_string, session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import os

app = Flask(__name__)

# Секретный ключ для сессий
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')

# Настройка базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------- Модели данных ----------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), default='initiator')  # initiator, approver, admin

    def __repr__(self):
        return f'<User {self.username}>'

class DocumentType(db.Model):
    """Вид документа (шаблон)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # например, "УКТП"
    description = db.Column(db.Text, default='')
    # Связь с полями (один вид документа -> много полей)
    fields = db.relationship('Field', backref='document_type', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<DocumentType {self.name}>'

class Field(db.Model):
    """Поле в шаблоне документа"""
    id = db.Column(db.Integer, primary_key=True)
    document_type_id = db.Column(db.Integer, db.ForeignKey('document_type.id'), nullable=False)
    field_name = db.Column(db.String(100), nullable=False)   # название поля, например "Наименование товара"
    field_type = db.Column(db.String(20), nullable=False)    # string, number, date, text, file, list
    is_required = db.Column(db.Boolean, default=False)       # обязательное?
    order = db.Column(db.Integer, default=0)                 # порядок отображения

    def __repr__(self):
        return f'<Field {self.field_name} ({self.field_type})>'

# Создаём все таблицы (если ещё не созданы)
with app.app_context():
    db.create_all()

# ---------- Вспомогательные функции ----------
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if get_current_user() is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Доступ только для роли admin"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if user.role != 'admin':
            return 'Доступ запрещён: требуется роль администратора. <a href="/">На главную</a>', 403
        return f(*args, **kwargs)
    return decorated_function

# ---------- Аутентификация ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)
        if user:
            session['user_id'] = user.id
            return redirect(url_for('hello'))
        else:
            return 'Пользователь не найден. <a href="/login">Попробовать снова</a>'

    all_users = User.query.all()
    if not all_users:
        return 'В системе нет пользователей. <a href="/add_test_user">Добавить тестового администратора</a>'
    html = '''
        <h2>Вход в систему ЭДО</h2>
        <p>Выберите пользователя:</p>
        <form method="post">
            <ul>
    '''
    for user in all_users:
        html += f'<li><button type="submit" name="user_id" value="{user.id}">{user.username} ({user.role})</button></li>'
    html += '''
            </ul>
        </form>
        <p><a href="/add_test_user">Добавить тестового администратора</a></p>
    '''
    return html

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# ---------- Главная страница ----------
@app.route('/')
@login_required
def hello():
    user = get_current_user()
    html = f'''
        <h1>Привет, {user.username}!</h1>
        <p>Ваша роль: {user.role}</p>
        <ul>
            <li><a href="/users">Список пользователей</a></li>
            <li><a href="/add_test_user">Добавить тестового пользователя</a></li>
    '''
    if user.role == 'admin':
        html += '<li><a href="/admin/document_types">Управление видами документов (админ)</a></li>'
    html += '''
        </ul>
        <p><a href="/logout">Выйти</a></p>
    '''
    return html

# ---------- Пользователи (старое) ----------
@app.route('/users')
@login_required
def users():
    all_users = User.query.all()
    html = '<h2>Список пользователей</h2><ul>'
    for user in all_users:
        html += f'<li>{user.username} ({user.email}) — роль: {user.role}</li>'
    html += '</ul><a href="/add_test_user">➕ Добавить тестового пользователя</a>'
    html += '<br><a href="/">🔙 На главную</a>'
    return html

@app.route('/add_test_user')
def add_test_user():
    existing = User.query.filter_by(username='admin').first()
    if existing:
        return 'Пользователь admin уже существует. <a href="/users">Назад к списку</a>'

    admin = User(username='admin', email='admin@example.com', role='admin')
    db.session.add(admin)
    db.session.commit()
    return '✅ Тестовый пользователь admin добавлен. <a href="/users">Посмотреть список</a>'

# ---------- Конструктор видов документов (только для админа) ----------
@app.route('/admin/document_types')
@admin_required
def list_document_types():
    types = DocumentType.query.all()
    html = '<h2>Виды документов</h2>'
    if types:
        html += '<ul>'
        for dt in types:
            html += f'<li><strong>{dt.name}</strong> — {dt.description or "нет описания"} '
            html += f'<a href="/admin/document_type/{dt.id}">(редактировать / добавить поля)</a></li>'
        html += '</ul>'
    else:
        html += '<p>Пока нет ни одного вида документа.</p>'
    html += '''
        <h3>Создать новый вид документа</h3>
        <form method="post" action="/admin/create_document_type">
            <label>Название: <input type="text" name="name" required></label><br><br>
            <label>Описание: <textarea name="description"></textarea></label><br><br>
            <button type="submit">Создать</button>
        </form>
        <br><a href="/">🔙 На главную</a>
    '''
    return html

@app.route('/admin/create_document_type', methods=['POST'])
@admin_required
def create_document_type():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    if not name:
        return 'Название не может быть пустым. <a href="/admin/document_types">Назад</a>'
    # Проверка на уникальность
    if DocumentType.query.filter_by(name=name).first():
        return f'Вид документа с названием "{name}" уже существует. <a href="/admin/document_types">Назад</a>'
    new_type = DocumentType(name=name, description=description)
    db.session.add(new_type)
    db.session.commit()
    return redirect(url_for('list_document_types'))

@app.route('/admin/document_type/<int:type_id>', methods=['GET', 'POST'])
@admin_required
def edit_document_type(type_id):
    doc_type = DocumentType.query.get_or_404(type_id)
    if request.method == 'POST':
        # Добавление нового поля
        field_name = request.form.get('field_name', '').strip()
        field_type = request.form.get('field_type')
        is_required = request.form.get('is_required') == 'on'
        order = request.form.get('order', 0, type=int)
        if not field_name or not field_type:
            return 'Название и тип поля обязательны. <a href="javascript:history.back()">Назад</a>'
        new_field = Field(
            document_type_id=doc_type.id,
            field_name=field_name,
            field_type=field_type,
            is_required=is_required,
            order=order
        )
        db.session.add(new_field)
        db.session.commit()
        return redirect(url_for('edit_document_type', type_id=type_id))

    # Показ текущих полей и формы добавления
    html = f'<h2>Вид документа: {doc_type.name}</h2>'
    html += f'<p>Описание: {doc_type.description or "—"}</p>'
    fields = Field.query.filter_by(document_type_id=doc_type.id).order_by(Field.order).all()
    if fields:
        html += '<h3>Поля:</h3><ul>'
        for f in fields:
            req = '⭐' if f.is_required else ''
            html += f'<li>{f.order}. {f.field_name} ({f.field_type}) {req}</li>'
        html += '</ul>'
    else:
        html += '<p>Пока нет полей.</p>'

    # Форма добавления поля
    html += '''
        <h3>Добавить новое поле</h3>
        <form method="post">
            <label>Название поля: <input type="text" name="field_name" required></label><br><br>
            <label>Тип поля:
                <select name="field_type">
                    <option value="string">Строка</option>
                    <option value="number">Число</option>
                    <option value="date">Дата</option>
                    <option value="text">Текст</option>
                    <option value="file">Файл</option>
                    <option value="list">Список</option>
                </select>
            </label><br><br>
            <label>Обязательное? <input type="checkbox" name="is_required"></label><br><br>
            <label>Порядковый номер: <input type="number" name="order" value="0"></label><br><br>
            <button type="submit">Добавить поле</button>
        </form>
    '''
    html += '<br><a href="/admin/document_types">🔙 К списку видов</a>'
    return html

# ---------- Запуск ----------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
