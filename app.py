from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "<h1>Привет! Это наше приложение ЭДО работает!</h1><p>Поздравляю! Деплой удался.</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
