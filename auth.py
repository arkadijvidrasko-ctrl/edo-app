from flask import Blueprint, session, redirect, url_for, request
from models import db, User
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if get_current_user() is None:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if get_current_user().role != 'admin':
            return 'Требуется роль администратора. <a href="/">На главную</a>', 403
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)
        if user:
            session['user_id'] = user.id
            return redirect(url_for('hello'))
        return 'Пользователь не найден. <a href="/login">Попробовать снова</a>'
    all_users = User.query.all()
    if not all_users:
        return 'В системе нет пользователей. <a href="/add_test_user">Добавить тестового администратора</a>'
    html = '<h2>Вход в систему ЭДО</h2><p>Выберите пользователя:</p><form method="post"><ul>'
    for user in all_users:
        html += f'<li><button type="submit" name="user_id" value="{user.id}">{user.username} ({user.role})</button></li>'
    html += '</ul></form><p><a href="/add_test_user">Добавить тестового администратора</a></p>'
    return html

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('auth.login'))

@auth_bp.route('/add_test_user')
def add_test_user():
    if User.query.filter_by(username='admin').first():
        return 'Пользователь admin уже существует. <a href="/users">Назад к списку</a>'
    admin = User(username='admin', email='admin@example.com', role='admin')
    db.session.add(admin)
    db.session.commit()
    return '✅ Тестовый пользователь admin добавлен. <a href="/users">Посмотреть список</a>'

@auth_bp.route('/users')
@login_required
def users():
    all_users = User.query.all()
    html = '<h2>Список пользователей</h2><ul>'
    for user in all_users:
        html += f'<li>{user.username} ({user.email}) — {user.role}</li>'
    html += '</ul><a href="/add_test_user">➕ Добавить</a> | <a href="/">🔙 Главная</a>'
    return html
