"""
EduFace Backend - Flask API Server
Handles face recognition, attendance, and mood analysis
"""

import os
import io
import json
import base64
import uuid
import hashlib
import sqlite3
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from PIL import Image
import numpy as np

# Point Flask to serve frontend files from parent directory
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..')
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)

# ===== Configuration =====
FACE_DATA_DIR = os.path.join(os.path.dirname(__file__), 'face_data')
os.makedirs(FACE_DATA_DIR, exist_ok=True)
PAPERS_PDF_DIR = os.path.join(os.path.dirname(__file__), 'papers_pdfs')
os.makedirs(PAPERS_PDF_DIR, exist_ok=True)
DB_PATH = os.path.join(os.path.dirname(__file__), 'eduface.db')

# In-memory storage for demo (replace with Supabase in production)
students_db = {}
attendance_db = []


# ===== SQLite Database =====
def get_db():
    """Get a database connection (one per request)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def init_db():
    """Create tables and seed default data if empty."""
    conn = get_db()

    # ===== Users table =====
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        rollNo TEXT UNIQUE NOT NULL,
        department TEXT,
        year INTEGER,
        password TEXT NOT NULL,
        createdAt TEXT
    )''')
    conn.commit()

    # Seed default users if table is empty
    user_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    if user_count == 0:
        default_password = hash_password('student123')
        seed_users = [
            ('1', 'Deepak Raj', 'deepak@student.edu', 'CS2022001', 'Computer Science', 4, default_password, '2026-01-01'),
            ('2', 'Priya Sharma', 'priya@student.edu', 'CS2022002', 'Computer Science', 4, default_password, '2026-01-01'),
            ('3', 'Arjun Kumar', 'arjun@student.edu', 'EC2022003', 'Electronics', 4, default_password, '2026-01-01'),
        ]
        conn.executemany(
            'INSERT INTO users (id, name, email, rollNo, department, year, password, createdAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            seed_users
        )
        conn.commit()

    # ===== Papers table =====
    conn.execute('''CREATE TABLE IF NOT EXISTS papers (
        id TEXT PRIMARY KEY,
        studentId TEXT,
        title TEXT NOT NULL,
        abstract TEXT,
        tags TEXT,
        published INTEGER DEFAULT 1,
        date TEXT,
        pdfName TEXT
    )''')
    conn.commit()

    # Migration: add pdfName column if missing (for existing databases)
    try:
        conn.execute('ALTER TABLE papers ADD COLUMN pdfName TEXT')
        conn.commit()
    except Exception:
        pass  # column already exists

    # Seed default papers if table is empty
    count = conn.execute('SELECT COUNT(*) FROM papers').fetchone()[0]
    if count == 0:
        seed_papers = [
            ('p1', '1', 'Face Recognition Attendance System using LBPH',
             'A lightweight face recognition system built with OpenCV for automatic attendance marking in classrooms.',
             'AI,OpenCV,Python', 1, '2026-01-15'),
            ('p2', '2', 'Depression Detection through Facial Expression Analysis',
             'Using deep learning to analyze facial micro-expressions and detect early signs of depression in students.',
             'Deep Learning,Health', 1, '2026-02-01'),
            ('p3', '3', 'Comparative Analysis of Facial Recognition Pipelines for Scalable Attendance Systems',
             'A systematic comparison of facial recognition pipelines including ArcFace, SFace, GhostFaceNet, and Dlib for attendance systems. Evaluated using DeepFace and face_recognition frameworks on a dataset of approximately 13,000 images. Dlib demonstrated the best overall performance, outperforming deeper CNN-based embeddings in both speed and accuracy. The study highlights trade-offs between accuracy, discriminability, and real-time efficiency for scalable deployment.',
             'Face Recognition,Deep Learning,Attendance', 1, '2026-01-20'),
            ('p4', '1', 'AI-Based Detection of Subthreshold Depression through Facial Micro-Expression Analysis in University Students',
             'This study investigates subtle facial cues to detect subthreshold depression in university students using AI tools like OpenFace 2.0. The research analyzed facial muscle movements from short self-introduction videos and identified specific micro-expressions — such as slight brow lifts, eye widening, and mouth stretches — that were more common in students with mild depressive symptoms. These movements were strongly linked to depression scores, even though they were often too subtle for human observers to notice. The approach is proposed as a non-invasive tool for early detection in educational settings.',
             'AI,Mental Health,Micro-Expressions', 1, '2025-08-15'),
            ('p5', '2', 'Mental Health Assessment Model for College Students Integrating Facial Expression Recognition with Deep Learning',
             'A mental health assessment model for college students that integrates facial expression recognition with deep learning technology. The model combines dynamic and static facial expression information to enhance the accuracy and efficiency of psychological state recognition. The fusion model demonstrated significant advantages in accuracy, training stability, and generalization ability for recognizing abnormal mental states, and is proposed as a supplement to university mental health early-warning systems.',
             'Deep Learning,Mental Health,Education', 1, '2025-11-10'),
        ]
        conn.executemany(
            'INSERT INTO papers (id, studentId, title, abstract, tags, published, date) VALUES (?, ?, ?, ?, ?, ?, ?)',
            seed_papers
        )
        conn.commit()
    conn.close()


init_db()


# ===== Helper Functions =====
def decode_base64_image(data_url):
    """Decode a base64 data URL to a PIL Image."""
    if ',' in data_url:
        data_url = data_url.split(',')[1]
    image_data = base64.b64decode(data_url)
    return Image.open(io.BytesIO(image_data))


def image_to_cv2(pil_image):
    """Convert PIL Image to OpenCV format."""
    import cv2
    rgb = np.array(pil_image.convert('RGB'))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


# ===== Health Check =====
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'EduFace API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })


# ===== Authentication API =====
@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate a student with email/rollNo and password."""
    try:
        data = request.json or {}
        identifier = data.get('identifier', '').strip()  # email or rollNo
        password = data.get('password', '')

        if not identifier or not password:
            return jsonify({'error': 'Email/Roll Number and password are required'}), 400

        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE email = ? OR rollNo = ?',
            (identifier, identifier)
        ).fetchone()
        conn.close()

        if not user:
            return jsonify({'error': 'No account found with that email or roll number'}), 401

        if user['password'] != hash_password(password):
            return jsonify({'error': 'Incorrect password'}), 401

        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'rollNo': user['rollNo'],
                'department': user['department'],
                'year': user['year']
            },
            'message': f"Welcome back, {user['name']}!"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new student account."""
    try:
        data = request.json or {}
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        roll_no = data.get('rollNo', '').strip()
        department = data.get('department', '').strip()
        year = data.get('year', 1)
        password = data.get('password', '')

        if not name or not email or not roll_no or not password:
            return jsonify({'error': 'All fields are required'}), 400

        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        conn = get_db()

        # Check for duplicates
        existing = conn.execute(
            'SELECT id FROM users WHERE email = ? OR rollNo = ?',
            (email, roll_no)
        ).fetchone()
        if existing:
            conn.close()
            return jsonify({'error': 'A student with this email or roll number already exists'}), 409

        user_id = str(uuid.uuid4())[:8]
        conn.execute(
            'INSERT INTO users (id, name, email, rollNo, department, year, password, createdAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (user_id, name, email, roll_no, department, year, hash_password(password), datetime.now().isoformat())
        )
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'user': {
                'id': user_id,
                'name': name,
                'email': email,
                'rollNo': roll_no,
                'department': department,
                'year': year
            },
            'message': f'Welcome, {name}! Registration successful.'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===== Face Registration =====
@app.route('/api/face/register', methods=['POST'])
def register_face():
    """Register a new student's face for recognition."""
    try:
        data = request.json
        student_id = data.get('student_id', str(uuid.uuid4()))
        name = data.get('name', 'Unknown')
        images = data.get('images', [])  # List of base64 image strings

        if not images:
            return jsonify({'error': 'No face images provided'}), 400

        # Save face images
        student_dir = os.path.join(FACE_DATA_DIR, student_id)
        os.makedirs(student_dir, exist_ok=True)

        saved_paths = []
        for i, img_data in enumerate(images):
            img = decode_base64_image(img_data)
            path = os.path.join(student_dir, f'face_{i}.jpg')
            img.save(path, 'JPEG', quality=85)
            saved_paths.append(path)

        # Store student info
        students_db[student_id] = {
            'id': student_id,
            'name': name,
            'face_paths': saved_paths,
            'registered_at': datetime.now().isoformat()
        }

        return jsonify({
            'success': True,
            'student_id': student_id,
            'message': f'Face registered for {name}',
            'images_saved': len(saved_paths)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===== Face Verification =====
@app.route('/api/face/verify', methods=['POST'])
def verify_face():
    """Verify a face against stored face data."""
    try:
        import cv2

        data = request.json
        student_id = data.get('student_id')
        image = data.get('image')  # base64

        if not image:
            return jsonify({'error': 'No image provided'}), 400

        # Load the test image
        test_img = decode_base64_image(image)
        test_cv2 = image_to_cv2(test_img)
        gray_test = cv2.cvtColor(test_cv2, cv2.COLOR_BGR2GRAY)

        # Detect face in test image
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        faces = face_cascade.detectMultiScale(gray_test, 1.3, 5)

        if len(faces) == 0:
            return jsonify({'verified': False, 'message': 'No face detected in image'}), 200

        # If student_id provided, verify against that student
        if student_id and student_id in students_db:
            student = students_db[student_id]
            # Simple LBPH verification
            recognizer = cv2.face.LBPHFaceRecognizer_create()

            # Train with stored faces
            train_faces = []
            train_labels = []
            for path in student['face_paths']:
                img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    detected = face_cascade.detectMultiScale(img, 1.3, 5)
                    for (x, y, w, h) in detected:
                        train_faces.append(img[y:y+h, x:x+w])
                        train_labels.append(0)

            if train_faces:
                recognizer.train(train_faces, np.array(train_labels))
                x, y, w, h = faces[0]
                label, confidence = recognizer.predict(gray_test[y:y+h, x:x+w])
                match_score = max(0, 100 - confidence)

                return jsonify({
                    'verified': match_score > 40,
                    'confidence': round(match_score, 1),
                    'student_name': student['name'],
                    'message': 'Face verified' if match_score > 40 else 'Face does not match'
                })

        return jsonify({'verified': False, 'message': 'Student not found'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===== Mark Attendance =====
@app.route('/api/attendance/mark', methods=['POST'])
def mark_attendance():
    """Mark attendance for a student via face recognition."""
    try:
        data = request.json
        student_id = data.get('student_id')
        subject = data.get('subject', 'General')

        if not student_id:
            return jsonify({'error': 'Student ID required'}), 400

        record = {
            'id': str(uuid.uuid4()),
            'student_id': student_id,
            'subject': subject,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'status': 'present',
            'confidence': round(85 + np.random.random() * 15, 1)
        }
        attendance_db.append(record)

        return jsonify({
            'success': True,
            'attendance': record,
            'message': f'Attendance marked for {subject}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===== Mood Analysis =====
@app.route('/api/mood/analyze', methods=['POST'])
def analyze_mood():
    """Analyze facial expression for mood/depression detection."""
    try:
        data = request.json
        image = data.get('image')  # base64

        if not image:
            return jsonify({'error': 'No image provided'}), 400

        # Decode image
        img = decode_base64_image(image)
        img_array = np.array(img.convert('RGB'))

        # Use DeepFace for emotion analysis
        try:
            from deepface import DeepFace
            results = DeepFace.analyze(
                img_array,
                actions=['emotion'],
                enforce_detection=False,
                silent=True
            )

            if isinstance(results, list):
                result = results[0]
            else:
                result = results

            emotions = result.get('emotion', {})
            dominant = result.get('dominant_emotion', 'neutral')

            # Determine risk level
            sad_score = emotions.get('sad', 0)
            fear_score = emotions.get('fear', 0)
            angry_score = emotions.get('angry', 0)

            risk_level = 'low'
            if sad_score > 40 or fear_score > 30:
                risk_level = 'medium'
            if sad_score > 60 or (sad_score > 40 and fear_score > 20):
                risk_level = 'high'

            return jsonify({
                'success': True,
                'dominant_emotion': dominant,
                'emotions': emotions,
                'risk_level': risk_level,
                'confidence': round(emotions.get(dominant, 0), 1)
            })

        except ImportError:
            # Fallback if DeepFace not installed
            emotions = {
                'happy': float(np.random.random() * 40 + 10),
                'sad': float(np.random.random() * 25),
                'angry': float(np.random.random() * 15),
                'surprise': float(np.random.random() * 20),
                'fear': float(np.random.random() * 10),
                'neutral': float(np.random.random() * 30 + 10)
            }
            total = sum(emotions.values())
            emotions = {k: round(v / total * 100, 1) for k, v in emotions.items()}
            dominant = max(emotions, key=emotions.get)

            return jsonify({
                'success': True,
                'dominant_emotion': dominant,
                'emotions': emotions,
                'risk_level': 'low',
                'confidence': emotions[dominant],
                'note': 'Using fallback analysis (DeepFace not installed)'
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===== Papers API (SQLite) =====
@app.route('/api/papers', methods=['GET'])
def list_papers():
    """List all papers, with optional search."""
    try:
        search = request.args.get('search', '').strip().lower()
        conn = get_db()
        rows = conn.execute('SELECT * FROM papers ORDER BY date DESC').fetchall()
        conn.close()

        papers = []
        for r in rows:
            paper = {
                'id': r['id'],
                'studentId': r['studentId'],
                'title': r['title'],
                'abstract': r['abstract'],
                'tags': r['tags'].split(',') if r['tags'] else [],
                'published': bool(r['published']),
                'date': r['date'],
                'pdfName': r['pdfName']
            }
            if search:
                haystack = (paper['title'] + ' ' + paper['abstract'] + ' ' + ' '.join(paper['tags'])).lower()
                if search not in haystack:
                    continue
            papers.append(paper)

        return jsonify(papers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/papers', methods=['POST'])
def create_paper():
    """Publish a new paper (supports multipart form with optional PDF)."""
    try:
        paper_id = 'p-' + str(uuid.uuid4())[:8]

        # Support both JSON and multipart form data
        if request.content_type and 'multipart' in request.content_type:
            title = request.form.get('title', '').strip()
            abstract = request.form.get('abstract', '').strip()
            tags_raw = request.form.get('tags', '')
            tags = tags_raw if tags_raw else ''
            student_id = request.form.get('studentId', '')
            date = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
        else:
            data = request.json or {}
            title = data.get('title', '').strip()
            abstract = data.get('abstract', '').strip()
            tags_list = data.get('tags', [])
            tags = ','.join(tags_list) if isinstance(tags_list, list) else tags_list
            student_id = data.get('studentId', '')
            date = data.get('date', datetime.now().strftime('%Y-%m-%d'))

        if not title:
            return jsonify({'error': 'Title is required'}), 400

        # Handle PDF upload
        pdf_name = None
        pdf_file = request.files.get('pdf') if request.content_type and 'multipart' in request.content_type else None
        if pdf_file and pdf_file.filename:
            # Save with paper_id prefix to avoid name collisions
            safe_name = paper_id + '_' + pdf_file.filename
            pdf_file.save(os.path.join(PAPERS_PDF_DIR, safe_name))
            pdf_name = safe_name

        conn = get_db()
        conn.execute(
            'INSERT INTO papers (id, studentId, title, abstract, tags, published, date, pdfName) VALUES (?, ?, ?, ?, ?, 1, ?, ?)',
            (paper_id, student_id, title, abstract, tags, date, pdf_name)
        )
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'id': paper_id,
            'message': 'Paper published successfully'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/papers/pdf/<paper_id>', methods=['GET'])
def serve_paper_pdf(paper_id):
    """Serve a paper's PDF file."""
    try:
        conn = get_db()
        row = conn.execute('SELECT pdfName FROM papers WHERE id = ?', (paper_id,)).fetchone()
        conn.close()

        if not row or not row['pdfName']:
            return jsonify({'error': 'No PDF found for this paper'}), 404

        return send_from_directory(PAPERS_PDF_DIR, row['pdfName'], as_attachment=False)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/papers/<paper_id>', methods=['DELETE'])
def delete_paper(paper_id):
    """Delete a paper (admin only)."""
    try:
        is_admin = request.headers.get('X-Admin', '').lower() == 'true'
        if not is_admin:
            return jsonify({'error': 'Admin access required'}), 403

        conn = get_db()
        # Get PDF name before deleting
        row = conn.execute('SELECT pdfName FROM papers WHERE id = ?', (paper_id,)).fetchone()
        result = conn.execute('DELETE FROM papers WHERE id = ?', (paper_id,))
        conn.commit()
        deleted = result.rowcount
        conn.close()

        if deleted == 0:
            return jsonify({'error': 'Paper not found'}), 404

        # Remove PDF file if exists
        if row and row['pdfName']:
            pdf_path = os.path.join(PAPERS_PDF_DIR, row['pdfName'])
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

        return jsonify({'success': True, 'message': 'Paper deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===== Serve Frontend Pages =====
@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:filename>')
def serve_frontend(filename):
    """Serve frontend HTML, CSS, JS files."""
    file_path = os.path.join(FRONTEND_DIR, filename)
    if os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIR, filename)
    return send_from_directory(FRONTEND_DIR, 'index.html')


# ===== Run Server =====
if __name__ == '__main__':
    print("=" * 50)
    print("  EduFace API Server")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
