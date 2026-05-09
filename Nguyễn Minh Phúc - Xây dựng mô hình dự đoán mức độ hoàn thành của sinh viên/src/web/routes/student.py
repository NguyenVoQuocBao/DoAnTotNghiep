"""Student routes"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from datetime import datetime
from src.services import DataService

bp = Blueprint('student', __name__, url_prefix='/student')

def require_student_auth(f):
    """Decorator to require student authentication"""
    def wrapper(*args, **kwargs):
        if 'username' not in session or session.get('user_type') != 'student':
            flash('Vui lòng đăng nhập với tài khoản sinh viên!', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def get_analytics_system():
    """Get analytics system from app config"""
    return current_app.config.get('ANALYTICS_SYSTEM')

def get_student_data():
    """Get current student data"""
    students = DataService.load_students()
    username = session['username']
    return students.get(username)

@bp.route('/dashboard')
@require_student_auth
def dashboard():
    """Student dashboard"""
    student = get_student_data()
    analytics = get_analytics_system()
    
    result = analytics.process_student_data(student.raw_data)
    
    data = {
        'student_name': student.name,
        'student_id': student.student_id,
        'completion_level': result['completion_assessment']['completion_level'],
        'completion_score': result['completion_assessment']['completion_score'],
        'behavior_label': result['behavior_label'],
        'recommendation': result['recommendation'],
        'test_score': result['completion_assessment']['test_score'],
        'assignment_score': result['completion_assessment']['assignment_score'],
        'access_score': result['completion_assessment']['access_score'],
        'study_time_score': result['completion_assessment']['study_time_score'],
        'raw_test_score': student.raw_data.get('test_scores', 0),
        'raw_completion_rate': student.raw_data.get('assignment_completion_rate', 0),
        'raw_access_count': student.raw_data.get('access_count', 0),
        'raw_study_time': student.raw_data.get('study_time_minutes', 0)
    }
    
    return render_template('dashboard.html', data=data)

@bp.route('/analyze')
@require_student_auth
def analyze():
    """Detailed analysis"""
    student = get_student_data()
    analytics = get_analytics_system()
    
    result = analytics.process_student_data(student.raw_data)
    prediction = analytics.predict_completion_level(result['normalized_data'])
    
    data = {
        'student_name': student.name,
        'student_id': student.student_id,
        'normalized_data': result['normalized_data'],
        'behavior_group': result['behavior_group'],
        'behavior_label': result['behavior_label'],
        'completion_assessment': result['completion_assessment'],
        'recommendation': result['recommendation'],
        'prediction': prediction,
        'raw_data': student.raw_data
    }
    
    return render_template('analysis.html', data=data)

@bp.route('/history')
@require_student_auth
def history():
    """Learning history"""
    student = get_student_data()
    history_data = DataService.load_history().get(student.student_id, [])
    history_data.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template('history.html', 
                         student_name=student.name,
                         history=history_data)

@bp.route('/api/analyze')
@require_student_auth
def api_analyze():
    """API endpoint for analysis"""
    student = get_student_data()
    analytics = get_analytics_system()
    
    result = analytics.process_student_data(student.raw_data)
    prediction = analytics.predict_completion_level(result['normalized_data'])
    
    return jsonify({
        'student_id': student.student_id,
        'completion_level': result['completion_assessment']['completion_level'],
        'completion_score': result['completion_assessment']['completion_score'],
        'behavior_label': result['behavior_label'],
        'recommendation': result['recommendation'],
        'prediction': prediction
    })

@bp.route('/save_history', methods=['POST'])
@require_student_auth
def save_history():
    """Save learning history"""
    student = get_student_data()
    analytics = get_analytics_system()
    
    result = analytics.process_student_data(student.raw_data)
    
    entry = {
        'timestamp': datetime.now().isoformat(),
        'student_id': student.student_id,
        'completion_level': result['completion_assessment']['completion_level'],
        'completion_score': result['completion_assessment']['completion_score'],
        'behavior_label': result['behavior_label'],
        'recommendation_level': result['recommendation']['level']
    }
    
    DataService.add_history_entry(student.student_id, entry)
    
    return jsonify({'success': True, 'message': 'Đã lưu lịch sử học tập'})


