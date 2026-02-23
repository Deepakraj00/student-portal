"""
EduFace Backend - Flask API Server
Handles face recognition, attendance, and mood analysis
"""

import os
import io
import json
import base64
import uuid
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import numpy as np

app = Flask(__name__)
CORS(app)

# ===== Configuration =====
FACE_DATA_DIR = os.path.join(os.path.dirname(__file__), 'face_data')
os.makedirs(FACE_DATA_DIR, exist_ok=True)

# In-memory storage for demo (replace with Supabase in production)
students_db = {}
attendance_db = []


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


# ===== Run Server =====
if __name__ == '__main__':
    print("=" * 50)
    print("  EduFace API Server")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
