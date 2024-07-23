from flask import Flask, request, jsonify, send_from_directory, send_file
import os
import psycopg2
from werkzeug.utils import secure_filename
import random
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
import io
from PIL import Image
import base64
import bcrypt
import jwt
import datetime
from functools import wraps


load_dotenv()

app = Flask(__name__, static_folder='../frontend/build', static_url_path='/')
CORS(app)

DATABASE_URL = os.getenv('DATABASE_URL')

UPLOAD_FOLDER = 'backend/uploads'
PROFILE_PIC_FOLDER = os.path.join(app.root_path, '../frontend/public/profile_pics')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROFILE_PIC_FOLDER'] = PROFILE_PIC_FOLDER

os.makedirs(PROFILE_PIC_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

openai_client = OpenAI(api_key=os.getenv("OPENAI_AI_KEY"))

def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_random_profile_pic():
    profile_pics = [f for f in os.listdir(app.config['PROFILE_PIC_FOLDER']) if allowed_file(f)]
    if profile_pics:
        selected_pic = random.choice(profile_pics)
        return selected_pic  # Changed to just the filename
    return None

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def generate_token(user_id):
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
        'iat': datetime.datetime.utcnow(),
        'sub': user_id
    }
    return jwt.encode(payload, os.getenv('SECRET_KEY'), algorithm='HS256')

def decode_token(token):
    try:
        payload = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=['HS256'])
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"message": "Token is missing!"}), 403
        try:
            user_id = decode_token(token.split(" ")[1])
            if not user_id:
                return jsonify({"message": "Token is invalid!"}), 403
        except Exception as e:
            return jsonify({"message": "Token is invalid!"}), 403
        return f(user_id, *args, **kwargs)
    return decorated


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
    password = data.get('password')
    hashed_password = hash_password(password)
    profile_pic = get_random_profile_pic()

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (email, password, profile_pic) VALUES (%s, %s, %s) RETURNING id", (email, hashed_password, profile_pic))
        user_id = cursor.fetchone()[0]
        conn.commit()
        token = generate_token(user_id)
        return jsonify({"message": "User registered successfully", "user_id": user_id, "token": token}), 201
    except psycopg2.IntegrityError:
        return jsonify({"message": "Email already exists"}), 409
    except Exception as e:
        print(f"Error during registration: {e}")
        return jsonify({"message": "An error occurred"}), 500
    finally:
        cursor.close()
        conn.close()



@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and check_password(password, user[2]):
            token = generate_token(user[0])
            return jsonify({"token": token, "user_id": user[0]}), 200
        else:
            return jsonify({"message": "Invalid credentials"}), 401
    except Exception as e:
        print(f"Error during login: {e}")
        return jsonify({"message": "An error occurred"}), 500
    finally:
        cursor.close()
        conn.close()


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

    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=500,
        temperature=0.3
    )
    return response.choices[0].message.content

@app.route('/api/posts', methods=['GET', 'POST'])
@token_required
def posts(user_id):
    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'GET':
        try:
            cursor.execute("""
                SELECT posts.*, users.email AS user_email, users.profile_pic AS user_profile_pic
                FROM posts
                JOIN users ON posts.user_id = users.id
                ORDER BY posts.created_at DESC
            """)
            posts = cursor.fetchall()
            posts_list = []
            for post in posts:
                post_dict = {
                    "id": post[0],
                    "title": post[1],
                    "text": post[2],
                    "category": post[3],
                    "tags": post[4],
                    "image": post[5],
                    "ai_response": post[6],
                    "user_id": post[7],
                    "created_at": post[8],
                    "user_email": post[9],
                    "user_profile_pic": post[10],
                }
                cursor.execute("""
                    SELECT comments.*, users.email AS user_email, users.profile_pic AS user_profile_pic
                    FROM comments
                    JOIN users ON comments.user_id = users.id
                    WHERE comments.post_id = %s
                    ORDER BY comments.created_at DESC
                """, (post[0],))
                comments = cursor.fetchall()
                post_dict['comments'] = [
                    {
                        "id": comment[0],
                        "text": comment[1],
                        "post_id": comment[2],
                        "user_id": comment[3],
                        "created_at": comment[4],
                        "user_email": comment[5],
                        "user_profile_pic": comment[6]
                    } for comment in comments
                ]
                posts_list.append(post_dict)

            return jsonify(posts_list)
        except Exception as e:
            print(f"Error fetching posts: {e}")
            return jsonify({"message": "An error occurred"}), 500
        finally:
            cursor.close()
            conn.close()
    elif request.method == 'POST':
        title = request.form.get('title')
        text = request.form.get('text')
        category = request.form.get('category')
        tags = request.form.get('tags')
        image = request.files.get('image')
        image_url = None
        image_base64 = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            image_url = f'uploads/{filename}'
            image_base64 = resize_image(image_path)

        ai_response = "Looks like a Human question, I'll leave it to you guys!"
        if category == "question":
            ai_response = get_ai_response(text, image_base64)

        try:
            cursor.execute("INSERT INTO posts (title, text, category, tags, image, ai_response, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                           (title, text, category, tags, image_url, ai_response, user_id))
            conn.commit()
            return jsonify({"message": "Post created successfully"}), 201
        except Exception as e:
            print(f"Error creating post: {e}")
            return jsonify({"message": "An error occurred"}), 500
        finally:
            cursor.close()
            conn.close()

@app.route('/api/comments', methods=['POST'])
def comments():
    data = request.json
    text = data.get('text')
    post_id = data.get('post_id')
    user_id = data.get('user_id')
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO comments (text, post_id, user_id) VALUES (%s, %s, %s)", (text, post_id, user_id))
        conn.commit()
        return jsonify({"message": "Comment added successfully"}), 201
    except Exception as e:
        print(f"Error adding comment: {e}")
        return jsonify({"message": "An error occurred"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react_app(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_file(os.path.join(app.static_folder, path))
    else:
        return send_file(os.path.join(app.static_folder, 'index.html'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)


