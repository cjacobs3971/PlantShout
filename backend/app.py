from flask import Flask, request, jsonify, send_from_directory, send_file
import sqlite3
import bcrypt
from werkzeug.utils import secure_filename
import os
import openai
from dotenv import load_dotenv
import base64
from PIL import Image
import io
from flask_cors import CORS
import random

load_dotenv()

app = Flask(__name__, static_folder='../frontend/build', static_url_path='/')
CORS(app)

DATABASE = 'plantshout.db'
UPLOAD_FOLDER = 'uploads'
PROFILE_PIC_FOLDER = 'profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROFILE_PIC_FOLDER'] = PROFILE_PIC_FOLDER

if not os.path.exists(PROFILE_PIC_FOLDER):
    os.makedirs(PROFILE_PIC_FOLDER)

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_random_profile_pic():
    profile_pics = [f for f in os.listdir(app.config['PROFILE_PIC_FOLDER']) if allowed_file(f)]
    return random.choice(profile_pics) if profile_pics else None


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/profile_pics/<filename>')
def uploaded_profile_pic(filename):
    return send_from_directory(app.config['PROFILE_PIC_FOLDER'], filename)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password').encode('utf-8')
    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
    profile_pic = get_random_profile_pic()

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (email, password, profile_pic) VALUES (?, ?, ?)", (email, hashed_password, profile_pic))
        conn.commit()
        user_id = cursor.lastrowid
        return jsonify({"message": "User registered successfully", "user_id": user_id}), 201
    except sqlite3.IntegrityError:
        return jsonify({"message": "Email already exists"}), 409
    except Exception as e:
        return jsonify({"message": "An error occurred"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password').encode('utf-8')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if user and bcrypt.checkpw(password, user['password']):
        return jsonify({"token": "your_jwt_token", "user_id": user['id']}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

def resize_image(image_path, max_size=(500, 500)):
    with Image.open(image_path) as img:
        img.thumbnail(max_size)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

def get_ai_response(prompt, image_base64=None):
    messages = [
        {"role": "system", "content": "you are a helpful assistant."},
        {"role": "user", "content": prompt}
    ]

    if image_base64:
        messages.append({"role": "user", "content": f"![image](data:image/png;base64,{image_base64})"})

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=500,
        temperature=0.3
    )
    return response.choices[0].message.content

@app.route('/api/posts', methods=['GET', 'POST'])
def posts():
    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'GET':
        cursor.execute("""
            SELECT posts.*, users.email AS user_email, users.profile_pic AS user_profile_pic
            FROM posts
            JOIN users ON posts.user_id = users.id
            ORDER BY posts.created_at DESC
        """)
        posts = cursor.fetchall()
        posts_list = [dict(post) for post in posts]

        for post in posts_list:
            cursor.execute("""
                SELECT comments.*, users.email AS user_email, users.profile_pic AS user_profile_pic
                FROM comments
                JOIN users ON comments.user_id = users.id
                WHERE comments.post_id = ?
                ORDER BY comments.created_at DESC
            """, (post['id'],))
            post['comments'] = [dict(comment) for comment in cursor.fetchall()]

        return jsonify(posts_list)
    elif request.method == 'POST':
        title = request.form.get('title')
        text = request.form.get('text')
        category = request.form.get('category')
        tags = request.form.get('tags')
        user_id = request.form.get("user_id")
        image = request.files.get('image')
        image_url = None
        image_base64 = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            image_url = f'uploads/{filename}'
            image_base64 = resize_image(image_path)

        ai_response = "Looks like a Human question, ill leave it to you guys!"
        if category == "question":
            ai_response = get_ai_response(text, image_base64)

        cursor.execute("INSERT INTO posts (title, text, category, tags, image, ai_response, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (title, text, category, tags, image_url, ai_response, user_id))
        conn.commit()
        return jsonify({"message": "Post created successfully"}), 201

@app.route('/api/comments', methods=['POST'])
def comments():
    data = request.json
    text = data.get('text')
    post_id = data.get('post_id')
    user_id = data.get('user_id')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO comments (text, post_id, user_id) VALUES (?, ?, ?)", (text, post_id, user_id))
    conn.commit()
    return jsonify({"message": "Comment added successfully"}), 201

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react_app(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_file(os.path.join(app.static_folder, path))
    else:
        return send_file(os.path.join(app.static_folder, 'index.html'))

if __name__ == '__main__':
    app.run(debug=True)

