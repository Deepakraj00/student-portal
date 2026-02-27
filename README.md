# 🚀 EduFace — Smart Student Portal

EduFace is a modern, AI-powered student portal designed to streamline academic administrative tasks. Built with a robust Python backend and a sleek, glassmorphic frontend, it leverages computer vision to automate attendance, enhance security, and support student well-being.

---

## ✨ Key Features

- **📸 Face Recognition Attendance:** Mark attendance instantly using real-time webcam processing. Eliminates manual entry and prevents proxy marking.
- **🎫 Secure Hall Ticket Verification:** AI-driven facial matching to verify student identity for exams, ensuring high-security standards.
- **📊 Interactive Analytics:** Beautiful, interactive charts showing attendance trends, subject-wise breakdowns, and academic progress.
- **📄 Research Management:** A dedicated module for students to publish and share research papers, fostering an academic community.
- **🧠 Mood & Well-being Analysis:** An AI module that analyzes facial expressions to detect early signs of stress or depression, providing gentle prompts for mental health checks.

---

## 🛠️ Tech Stack

### Backend
- **Core:** Python, Flask
- **AI/ML:** OpenCV (LBPH for Face Recognition), DeepFace (Emotion Analysis), NumPy
- **Database:** SQLite3 (Local storage for student profiles and attendance logs)
- **Security:** Password hashing (SHA-256), Base64 Image Processing

### Frontend
- **Structure:** Semantic HTML5
- **Style:** Vanilla CSS3 (Custom Glassmorphism UI, Responsive Design)
- **Logic:** Vanilla JavaScript (ES6+, asynchronous API integration)
- **Visuals:** Canvas API for real-time video processing overlays

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Webcam (for AI features)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/student-portal.git
   cd student-portal
   ```

2. **Set up a Virtual Environment (Recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the Application:**
   ```bash
   python backend/app.py
   ```
   Open `http://localhost:5000` in your browser.

---

## 🛡️ Architecture & Security
EduFace follows a client-server architecture. The frontend captures raw image data from the webcam, which is transmitted as Base64 strings to the Flask API. The backend processes these images using OpenCV to extract facial features and matches them against the SQLite database using the LBPH (Local Binary Patterns Histograms) algorithm for efficient, local recognition.

---

## 🗺️ Roadmap
- [ ] Integration with Supabase for cloud database management.
- [ ] Notification system for low attendance alerts.
- [ ] Mobile app version using React Native.
- [ ] Advanced biometric encryption.

---

### 📄 License
Distributed under the MIT License. See `LICENSE` for more information.
