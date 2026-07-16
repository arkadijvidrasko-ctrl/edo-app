from flask import Flask, render_template_string
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Настройка базы данных (SQLite, файл users.db в папке приложения)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Модель пользователя (первая сущность)
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

# Главная страница (пока приветствие)
@app.route('/')
def hello():
    return "<h1>Привет! ЭДО с БД работает!</h1>"

# Страница со списком всех пользователей
@app.route('/users')
def users():
    all_users = User.query.all()
    html = '<h2>Список пользователей</h2><ul>'
    for user in all_users:
        html += f'<li>{user.username} ({user.email}) — роль: {user.role}</li>'
    html += '</ul><a href="/add_test_user">➕ Добавить тестового пользователя</a>'
    return html

# Добавление одного тестового пользователя (для проверки БД)
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
    app.run(host='0.0.0.0', port=5000)
