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
    profile_pic = get_random_profile_pic()

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (email, password, profile_pic) VALUES (%s, %s, %s) RETURNING id", (email, password, profile_pic))
        user_id = cursor.fetchone()[0]
        conn.commit()
        return jsonify({"message": "User registered successfully", "user_id": user_id}), 201
    except psycopg2.IntegrityError:
        return jsonify({"message": "Email already exists"}), 409
    except Exception as e:
        print(f"Error during registration: {e}")
        return jsonify({"message": "An error occurred"}), 500
    finally:
        cursor.close()
        conn.close()

# The rest of your code remains the same



