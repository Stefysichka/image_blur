from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from PIL import Image  # Для обробки зображень
from werkzeug.utils import secure_filename  # Для безпечного завантаження файлів
import psycopg2

try:
    conn = psycopg2.connect("postgresql://postgres:09031993@localhost/image_uploads")
    print("Connection successful")
except Exception as e:
    print(f"Error: {e}")


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:09031993@localhost/image_uploads'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Модель для збереження історії задач
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False)

# Створення бази даних, обернуте в контекст додатку
with app.app_context():
    db.create_all()  # Створення бази даних

# Папка для завантажених зображень
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Дозволені формати файлів
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Функція для перевірки, чи дозволений формат файлу
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Маршрут для завантаження зображення
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Перевіряємо, чи є файл у запиті
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        
        # Якщо файл не обрано
        if file.filename == '':
            return redirect(request.url)
        
        # Якщо файл правильного формату
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = f'static/uploads/{filename}'
            file.save(filepath)

            # Масштабування зображення (наприклад, зменшуємо розмір до 50%)
            image = Image.open(filepath)
            scaled_image = image.resize((int(image.width * 0.5), int(image.height * 0.5)))
            scaled_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'scaled_' + filename)
            scaled_image.save(scaled_filepath)

            # Додаємо запис у базу даних про виконане завдання
            new_task = Task(image_path=scaled_filepath, status='Completed')
            db.session.add(new_task)
            db.session.commit()

            return redirect(url_for('home'))  # Переадресація на домашню сторінку після завантаження
    return render_template('upload.html')  # Форма для завантаження файлу

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True, port=8080)
