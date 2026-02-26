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
    { id: '1', name: 'Deepak Raj', email: 'deepak@student.edu', rollNo: 'CS2022001', department: 'Computer Science', year: 4, faceData: null, password: 'student123' },
    { id: '2', name: 'Priya Sharma', email: 'priya@student.edu', rollNo: 'CS2022002', department: 'Computer Science', year: 4, faceData: null, password: 'student123' },
    { id: '3', name: 'Arjun Kumar', email: 'arjun@student.edu', rollNo: 'EC2022003', department: 'Electronics', year: 4, faceData: null, password: 'student123' },
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


  // Papers are now served from the backend API (SQLite database)

  // Announcements from management
  const announcements = [
    { id: 'ann1', title: 'End Semester Exams Schedule Released', message: 'The end semester examination schedule for April 2026 has been published. Students are advised to download their hall tickets and verify their details. Any discrepancies should be reported to the examination cell before March 15.', priority: 'urgent', author: 'Examination Cell', date: '2026-02-22', icon: '🚨' },
    { id: 'ann2', title: 'Project Submission Deadline Extended', message: 'The final year project submission deadline has been extended to March 30, 2026. Students must submit both the project report and working demo. Late submissions will not be accepted.', priority: 'important', author: 'HOD - Computer Science', date: '2026-02-20', icon: '📋' },
    { id: 'ann3', title: 'Annual Tech Fest - InnoVerse 2026', message: 'Registrations are open for InnoVerse 2026, our annual technical festival. Events include hackathon, paper presentation, coding contest, and robotics challenge. Register through the college portal by March 5.', priority: 'info', author: 'Student Affairs', date: '2026-02-18', icon: '🎉' },
    { id: 'ann4', title: 'Library Hours Extended During Exams', message: 'The central library will remain open from 8 AM to 10 PM during the examination period (April 10 - April 30). Digital library resources are available 24/7 with your student login.', priority: 'info', author: 'Central Library', date: '2026-02-15', icon: '📚' },
    { id: 'ann5', title: 'Placement Drive - TCS & Infosys', message: 'TCS and Infosys will be conducting on-campus placement drives on March 10-12. Eligible students (CGPA ≥ 7.0) must register with the placement cell by March 3. Carry your updated resume and ID card.', priority: 'important', author: 'Placement Cell', date: '2026-02-14', icon: '💼' },
  ];
  DB.set('announcements', announcements);

  // Don't auto-login — users must login via login page
}

// --- Navbar HTML ---
function renderNavbar(activePage) {
  const user = getCurrentUser();
  const isAdmin = DB.getOne('adminUser');
  const links = [
    { href: 'index.html', label: 'Home', id: 'home' },
    { href: 'dashboard.html', label: 'Dashboard', id: 'dashboard' },
    { href: 'hall-ticket.html', label: 'Hall Ticket', id: 'hall-ticket' },
    { href: 'papers.html', label: 'Papers', id: 'papers' },
    { href: 'mood-check.html', label: 'Mood Check', id: 'mood-check' },
  ];
  if (isAdmin) {
    links.push({ href: 'admin.html', label: '⚙ Admin', id: 'admin' });
  }

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
