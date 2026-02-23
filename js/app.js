// ===== Shared Utilities for Student Portal =====

// --- LocalStorage-based Demo Database ---
const DB = {
  get(key) {
    try { return JSON.parse(localStorage.getItem(key)) || []; }
    catch { return []; }
  },
  set(key, data) { localStorage.setItem(key, JSON.stringify(data)); },
  getOne(key) {
    try { return JSON.parse(localStorage.getItem(key)); }
    catch { return null; }
  },
  setOne(key, data) { localStorage.setItem(key, JSON.stringify(data)); }
};

// --- Current User Session ---
function getCurrentUser() {
  return DB.getOne('currentUser');
}

function setCurrentUser(user) {
  DB.setOne('currentUser', user);
}

function logout() {
  localStorage.removeItem('currentUser');
  window.location.href = 'login.html';
}

function requireAuth() {
  if (!getCurrentUser()) {
    window.location.href = 'login.html';
    return false;
  }
  return true;
}

// --- Toast Notifications ---
function showToast(message, type = 'info') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const icons = { success: '✓', error: '✗', info: 'ℹ' };
  toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span> ${message}`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// --- Generate Demo / Seed Data ---
function seedDemoData() {
  if (DB.get('students').length > 0) return; // already seeded

  const students = [
    { id: '1', name: 'Deepak Raj', email: 'deepak@student.edu', rollNo: 'CS2022001', department: 'Computer Science', year: 4, faceData: null },
    { id: '2', name: 'Priya Sharma', email: 'priya@student.edu', rollNo: 'CS2022002', department: 'Computer Science', year: 4, faceData: null },
    { id: '3', name: 'Arjun Kumar', email: 'arjun@student.edu', rollNo: 'EC2022003', department: 'Electronics', year: 4, faceData: null },
  ];
  DB.set('students', students);

  // Generate attendance for past 30 days
  const subjects = ['Machine Learning', 'Cloud Computing', 'Cyber Security', 'Software Eng.'];
  const attendance = [];
  for (let i = 0; i < 30; i++) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split('T')[0];
    students.forEach(s => {
      subjects.forEach(sub => {
        if (Math.random() > 0.15) { // 85% attendance chance
          attendance.push({
            id: `att-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
            studentId: s.id,
            subject: sub,
            date: dateStr,
            status: Math.random() > 0.9 ? 'late' : 'present',
            confidence: (85 + Math.random() * 15).toFixed(1)
          });
        }
      });
    });
  }
  DB.set('attendance', attendance);

  // Hall tickets
  const hallTickets = [
    { id: 'ht1', studentId: '1', examName: 'End Sem - Machine Learning', examDate: '2026-04-15', seatNo: 'A-12', verified: false },
    { id: 'ht2', studentId: '1', examName: 'End Sem - Cloud Computing', examDate: '2026-04-18', seatNo: 'B-07', verified: false },
    { id: 'ht3', studentId: '2', examName: 'End Sem - Machine Learning', examDate: '2026-04-15', seatNo: 'A-15', verified: false },
  ];
  DB.set('hallTickets', hallTickets);

  // Papers
  const papers = [
    { id: 'p1', studentId: '1', title: 'Face Recognition Attendance System using LBPH', abstract: 'A lightweight face recognition system built with OpenCV for automatic attendance marking in classrooms.', tags: ['AI', 'OpenCV', 'Python'], published: true, date: '2026-01-15' },
    { id: 'p2', studentId: '2', title: 'Depression Detection through Facial Expression Analysis', abstract: 'Using deep learning to analyze facial micro-expressions and detect early signs of depression in students.', tags: ['Deep Learning', 'Health'], published: true, date: '2026-02-01' },
  ];
  DB.set('papers', papers);

  // Set default user
  setCurrentUser(students[0]);
}

// --- Navbar HTML ---
function renderNavbar(activePage) {
  const user = getCurrentUser();
  const links = [
    { href: 'index.html', label: 'Home', id: 'home' },
    { href: 'dashboard.html', label: 'Dashboard', id: 'dashboard' },
    { href: 'hall-ticket.html', label: 'Hall Ticket', id: 'hall-ticket' },
    { href: 'papers.html', label: 'Papers', id: 'papers' },
    { href: 'mood-check.html', label: 'Mood Check', id: 'mood-check' },
  ];

  return `
    <nav class="navbar" id="navbar">
      <div class="nav-container">
        <a href="index.html" class="nav-logo">
          <span class="logo-icon">🎓</span>
          <span>EduFace</span>
        </a>
        <ul class="nav-links" id="navLinks">
          ${links.map(l => `<li><a href="${l.href}" class="${activePage === l.id ? 'active' : ''}">${l.label}</a></li>`).join('')}
          ${user
            ? `<li><a href="#" onclick="logout()" class="nav-cta">Logout</a></li>`
            : `<li><a href="login.html" class="nav-cta">Login</a></li>`
          }
        </ul>
        <button class="nav-toggle" onclick="document.getElementById('navLinks').classList.toggle('open')">☰</button>
      </div>
    </nav>
  `;
}

// --- Background glow HTML ---
function renderGlow() {
  return `<div class="bg-glow glow-1"></div><div class="bg-glow glow-2"></div><div class="bg-glow glow-3"></div>`;
}

// --- Footer HTML ---
function renderFooter() {
  return `<footer class="footer"><p>© 2026 EduFace — Student Portal | Final Year Project</p></footer>`;
}

// --- Scroll navbar effect ---
window.addEventListener('scroll', () => {
  const nav = document.getElementById('navbar');
  if (nav) nav.classList.toggle('scrolled', window.scrollY > 20);
});

// --- Seed data on load ---
seedDemoData();
