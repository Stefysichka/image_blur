from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import psycopg2
import os
from werkzeug.utils import secure_filename
from PIL import Image, ImageFilter
import io
import threading
import time
import logging
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['PROCESSED_FOLDER'] = 'static/processed_images/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True) 

processing_thread = None
cancel_processing = False
progress_percentage = 0  
image_status = {} 


def connect_db():
    return psycopg2.connect(
        host="localhost",
        database="image_uploads",
        user="postgres",  
        password="09031993"  
    )

@app.route('/')
def index():
    if 'username' not in session: 
        return redirect(url_for('login'))  
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM uploads ORDER BY created_at DESC")
    tasks = cur.fetchall()
    conn.close()
    return render_template('index.html', tasks=tasks)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session['username'] = username
            return redirect(url_for('upload'))
        else:
            flash('Invalid credentials. Please try again.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = connect_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        existing_user = cur.fetchone()
        
        if existing_user:
            flash('Username already exists. Please choose a different one.')
            return redirect(url_for('register'))

        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        conn.close()
        flash('Registration successful! You can now log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

logging.basicConfig(level=logging.DEBUG)

def process_image(filepath, blur_amount, filter_type):
    global cancel_processing, progress_percentage, image_status
    image = Image.open(filepath)
    processed_image = image

    task_id = os.path.basename(filepath)  # Unique ID based on the file name
    image_status[task_id] = {'progress': 0, 'path': None}  # Initialize status

    for i in range(1, blur_amount + 1):
        if cancel_processing:
            image_status[task_id]['progress'] = 'Cancelled'
            return None
        
        time.sleep(0.1)
        progress_percentage = int((i / blur_amount) * 100)
        image_status[task_id]['progress'] = progress_percentage  # Update progress

        if filter_type == 'gaussian':
            processed_image = processed_image.filter(ImageFilter.GaussianBlur(i))
        elif filter_type == 'median':
            processed_image = processed_image.filter(ImageFilter.MedianFilter(size=i))

    final_image_path = os.path.join(app.config['PROCESSED_FOLDER'], f'processed_{task_id}')
    processed_image.save(final_image_path)

    image_status[task_id] = {'progress': 100, 'path': final_image_path}  # Final status
    logging.debug(f'Processed image path: {final_image_path}')
    return final_image_path


@app.route('/status/<task_id>', methods=['GET'])
def status(task_id):
    global image_status
    if task_id in image_status:
        status = image_status[task_id]
        return jsonify({
            'processing': status['progress'] < 100,
            'progress': status['progress'],
            'image_path': status['path']
        })
    return jsonify({'error': 'Task not found'})

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    global processing_thread, cancel_processing
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            blur_amount = request.form.get('blurLevel', type=int)
            filter_type = request.form.get('filter', type=str)

            task_id = filename 
            cancel_processing = False
            processing_thread = threading.Thread(target=process_image, args=(filepath, blur_amount, filter_type))
            processing_thread.start()

            return jsonify({'status': 'Processing started', 'task_id': task_id})
    return render_template('upload.html')

@app.route('/cancel', methods=['POST'])
def cancel():
    global cancel_processing
    cancel_processing = True
    return jsonify(success=True)

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/routes')
def show_routes():
    output = []
    for rule in app.url_map.iter_rules():
        output.append(f"{rule.endpoint}: {rule.rule}")
    return "<br>".join(output)

if __name__ == '__main__':
    app.run(debug=True, port=8080)