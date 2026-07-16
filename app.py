from flask import Flask, render_template_string, session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Секретный ключ для работы сессий (нужен для хранения вошедшего пользователя)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')

# Настройка базы данных (SQLite, файл users.db в папке приложения)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), default='initiator')  # initiator, approver, admin

    def __repr__(self):
        return f'<User {self.username}>'

# Создаём таблицы при первом запуске
with app.app_context():
    db.create_all()

# ---------- Вспомогательные функции ----------
def get_current_user():
    """Возвращает объект User, если пользователь в сессии, иначе None."""
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

def login_required(f):
    """Декоратор для маршрутов, требующих входа."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if get_current_user() is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ---------- Маршруты аутентификации ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Получаем выбранного пользователя по ID из формы
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)
        if user:
            session['user_id'] = user.id
            return redirect(url_for('hello'))
        else:
            return 'Пользователь не найден. <a href="/login">Попробовать снова</a>'

    # GET-запрос: показать форму со списком пользователей
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

# ---------- Главная страница (теперь с именем пользователя) ----------
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
            <!-- Сюда позже добавим ссылки на конструктор документов -->
        </ul>
        <p><a href="/logout">Выйти</a></p>
    '''
    return html

# ---------- Остальные маршруты ----------
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
    # Проверяем, есть ли уже admin
    existing = User.query.filter_by(username='admin').first()
    if existing:
        return 'Пользователь admin уже существует. <a href="/users">Назад к списку</a>'

    admin = User(username='admin', email='admin@example.com', role='admin')
    db.session.add(admin)
    db.session.commit()
    return '✅ Тестовый пользователь admin добавлен. <a href="/users">Посмотреть список</a>'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
