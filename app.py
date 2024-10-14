from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from PIL import Image  # For image processing
from werkzeug.utils import secure_filename  # For secure file uploads
import psycopg2

# Try to connect to the PostgreSQL database
try:
    conn = psycopg2.connect("postgresql://postgres:09031993@localhost/image_uploads")
    print("Connection successful")
except Exception as e:
    print(f"Error: {e}")

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:09031993@localhost/image_uploads'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Model to store task history
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False)

# Create the database
with app.app_context():
    db.create_all()

# Folder to store uploaded images
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed file formats
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Function to check if file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Maximum file size (in MB) and max dimensions for images
MAX_FILE_SIZE_MB = 10
MAX_IMAGE_DIMENSIONS = (4000, 4000)

# Function to check if file size is allowed
def allowed_file_size(filepath):
    return os.stat(filepath).st_size <= MAX_FILE_SIZE_MB * 1024 * 1024

# Function to check if image dimensions are allowed
def allowed_image_dimensions(image):
    return image.width <= MAX_IMAGE_DIMENSIONS[0] and image.height <= MAX_IMAGE_DIMENSIONS[1]

# Route for uploading files
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if a file is present in the request
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        
        # If no file is selected
        if file.filename == '':
            return redirect(request.url)
        
        # If the file is of an allowed format
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Check file size and dimensions
            if not allowed_file_size(filepath):
                return "File size exceeds the limit."
            
            image = Image.open(filepath)
            if not allowed_image_dimensions(image):
                return "Image dimensions are too large."

            # Scale the image (reduce size by 50%)
            scaled_image = image.resize((int(image.width * 0.5), int(image.height * 0.5)))
            scaled_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'scaled_' + filename)
            scaled_image.save(scaled_filepath)

            # Add task to the database
            new_task = Task(image_path=scaled_filepath, status='Completed')
            db.session.add(new_task)
            db.session.commit()

            return redirect(url_for('home'))  # Redirect to home after successful upload
    return render_template('upload.html')  # Render the upload form

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True, port=8080)
