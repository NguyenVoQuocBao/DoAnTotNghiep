"""Authentication routes"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from src.services import DataService
from src.utils import AuthHelper

bp = Blueprint('auth', __name__)

# Load data on module import
students_data = {}
teachers_data = {}

def init_data():
    """Initialize data"""
    global students_data, teachers_data
    students_dict = DataService.load_students()
    students_data = {k: v.to_dict() for k, v in students_dict.items()}
    teachers_dict = DataService.load_teachers()
    teachers_data = {k: v for k, v in teachers_dict.items()}

init_data()

@bp.route('/')
def index():
    """Landing page"""
    if 'username' in session:
        if session.get('user_type') == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        return redirect(url_for('student.dashboard'))
    return render_template('login.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login handler"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Try teacher authentication
        teacher = AuthHelper.authenticate_teacher(username, password, teachers_data)
        if teacher:
            session['username'] = username
            session['user_type'] = 'teacher'
            session['teacher_name'] = teacher.name
            flash('Đăng nhập thành công với tư cách giáo viên!', 'success')
            return redirect(url_for('teacher.dashboard'))
        
        # Try student authentication
        student, actual_username = AuthHelper.authenticate_student(
            username, password, students_data
        )
        if student:
            session['username'] = actual_username
            session['user_type'] = 'student'
            session['student_id'] = student['student_id']
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('student.dashboard'))
        
        flash('MSSV hoặc mật khẩu không đúng!', 'error')
        return render_template('login.html')
    
    # GET request
    if 'username' in session:
        if session.get('user_type') == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        return redirect(url_for('student.dashboard'))
    return render_template('login.html')

@bp.route('/logout')
def logout():
    """Logout handler"""
    session.clear()
    flash('Đã đăng xuất thành công!', 'success')
    return redirect(url_for('auth.index'))
