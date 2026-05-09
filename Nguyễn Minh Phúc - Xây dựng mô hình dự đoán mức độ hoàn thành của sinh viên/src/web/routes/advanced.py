"""
Advanced Analytics Routes
Routes for advanced analytics features including clustering, anomaly detection, and visualizations
"""

from flask import Blueprint, render_template, jsonify, session, request, current_app
from functools import wraps
import logging
from src.services.data_service import DataService
from src.services.excel_service import ExcelService

logger = logging.getLogger(__name__)

bp = Blueprint('advanced', __name__)

def require_teacher_auth(f):
    """Decorator to require teacher authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session.get('user_type') != 'teacher':
            from flask import flash, redirect, url_for
            flash('Vui lòng đăng nhập với tài khoản giáo viên!', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_analytics_system():
    """Get analytics system from app config"""
    return current_app.config.get('ANALYTICS_SYSTEM')

@bp.route('/dashboard')
@require_teacher_auth
def advanced_dashboard():
    """Advanced analytics dashboard"""
    try:
        from flask import flash, redirect, url_for
        
        analytics_system = get_analytics_system()
        if not analytics_system:
            flash('Hệ thống phân tích không khả dụng!', 'error')
            return redirect(url_for('teacher.dashboard'))
        
        students = DataService.load_students()
        learning_history = DataService.load_history()
        
        # Get comprehensive analytics
        advanced_analytics = analytics_system.get_advanced_analytics(students, learning_history)
        
        return render_template('advanced/dashboard.html', 
                             analytics=advanced_analytics,
                             total_students=len(students))
    
    except Exception as e:
        from flask import flash, redirect, url_for
        logger.error(f"Error in advanced dashboard: {e}")
        flash(f'Lỗi: {str(e)}', 'error')
        return redirect(url_for('teacher.dashboard'))

@bp.route('/clustering')
@require_teacher_auth
def clustering():
    return render_template('advanced/clustering.html')

@bp.route('/anomalies')
@require_teacher_auth
def anomalies():
    return render_template('advanced/anomalies.html')

@bp.route('/model_comparison')
@require_teacher_auth
def model_comparison():
    return render_template('advanced/model_comparison.html')

@bp.route('/real_time')
@require_teacher_auth
def real_time():
    return render_template('advanced/real_time.html')

@bp.route('/api/clustering')
@require_teacher_auth
def api_clustering():
    """API endpoint for student clustering analysis"""
    try:
        analytics_system = get_analytics_system()
        if not analytics_system:
            return jsonify({'error': 'Analytics system not available'}), 500
        
        students = DataService.load_students()
        n_clusters = request.args.get('clusters', 4, type=int)
        
        clustering_results = analytics_system.get_clustering_analysis(students, n_clusters)
        
        return jsonify({
            'success': True,
            'data': clustering_results
        })
    
    except Exception as e:
        logger.error(f"Error in clustering API: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/anomalies')
@require_teacher_auth
def api_anomalies():
    """API endpoint for anomaly detection"""
    try:
        analytics_system = get_analytics_system()
        if not analytics_system:
            return jsonify({'error': 'Analytics system not available'}), 500
        
        students = DataService.load_students()
        
        anomaly_results = analytics_system.detect_at_risk_students(students)
        
        return jsonify({
            'success': True,
            'data': anomaly_results
        })
    
    except Exception as e:
        logger.error(f"Error in anomaly detection API: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/model_comparison')
@require_teacher_auth
def api_model_comparison():
    """API endpoint for model performance comparison"""
    try:
        analytics_system = get_analytics_system()
        if not analytics_system:
            return jsonify({'error': 'Analytics system not available'}), 500
        
        # Get model performance from app config
        model_performance = current_app.config.get('MODEL_PERFORMANCE', {})
        
        # Get sample predictions for comparison
        students = DataService.load_students()
        sample_predictions = []
        
        for username, student in list(students.items())[:10]:  # Sample 10 students
            result = analytics_system.process_student_data(student.raw_data)
            prediction = analytics_system.predict_completion_level(result['normalized_data'])
            
            sample_predictions.append({
                'student_id': student.student_id,
                'actual_level': result['completion_assessment']['completion_level'],
                'predictions': prediction
            })
        
        return jsonify({
            'success': True,
            'data': {
                'model_performance': model_performance,
                'sample_predictions': sample_predictions
            }
        })
    
    except Exception as e:
        logger.error(f"Error in model comparison API: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/real_time_stats')
@require_teacher_auth
def api_real_time_stats():
    """API endpoint for real-time system statistics"""
    try:
        from datetime import datetime

        analytics_system = get_analytics_system()
        students = DataService.load_students()
        
        # Basic stats
        total_students = len(students)
        completion_levels = {'Cao': 0, 'Trung bình': 0, 'Thấp': 0}
        behavior_groups = {'Tích cực': 0, 'Trì hoãn': 0, 'Thụ động': 0}
        
        for student in students.values():
            result = analytics_system.process_student_data(student.raw_data)
            completion_levels[result['completion_assessment']['completion_level']] += 1
            behavior_groups[result['behavior_label']] += 1
        
        return jsonify({
            'success': True,
            'data': {
                'student_stats': {
                    'total': total_students,
                    'completion_distribution': completion_levels,
                    'behavior_distribution': behavior_groups,
                    'high_performers_percentage': round(completion_levels['Cao'] / total_students * 100, 1) if total_students > 0 else 0
                },
                'connection_stats': {'active_connections': 0},
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    
    except Exception as e:
        logger.error(f"Error in real-time stats API: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/export_advanced_report')
@require_teacher_auth
def api_export_advanced_report():
    """Export comprehensive advanced analytics report"""
    try:
        analytics_system = get_analytics_system()
        if not analytics_system:
            return jsonify({'error': 'Analytics system not available'}), 500
        
        students = DataService.load_students()
        learning_history = DataService.load_history()
        
        # Get comprehensive analytics
        advanced_analytics = analytics_system.get_advanced_analytics(students, learning_history)
        
        # Prepare data for Excel export
        export_data = []
        for username, student in students.items():
            result = analytics_system.process_student_data(student.raw_data)
            prediction = analytics_system.predict_completion_level(result['normalized_data'])
            
            export_data.append({
                'Mã sinh viên': student.student_id,
                'Tên sinh viên': student.name,
                'Điểm thi': result['normalized_data']['test_scores'],
                'Hoàn thành bài tập': result['normalized_data']['assignment_completion'],
                'Tần suất truy cập': result['normalized_data']['access_frequency'],
                'Thời gian học': result['normalized_data']['study_time'],
                'Thời điểm nộp bài': result['normalized_data']['submission_timing'],
                'Mức độ hoàn thành': result['completion_assessment']['completion_level'],
                'Điểm hoàn thành': result['completion_assessment']['completion_score'],
                'Nhóm hành vi': result['behavior_label'],
                'Gợi ý học tập': result['recommendation']['level'],
                'Dự đoán RF': prediction.get('random_forest', {}).get('predicted_level', 'N/A'),
                'Độ tin cậy RF': prediction.get('random_forest', {}).get('confidence', 0),
                'Dự đoán NN': prediction.get('neural_network', {}).get('predicted_level', 'N/A'),
                'Độ tin cậy NN': prediction.get('neural_network', {}).get('confidence', 0),
                'Dự đoán Ensemble': prediction.get('ensemble', {}).get('predicted_level', 'N/A'),
                'Độ tin cậy Ensemble': prediction.get('ensemble', {}).get('confidence', 0)
            })
        
        # Create Excel file
        filename = ExcelService.export_advanced_analysis(export_data, advanced_analytics)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'message': f'Đã xuất báo cáo nâng cao: {filename}'
        })
    
    except Exception as e:
        logger.error(f"Error exporting advanced report: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/clustering')
@require_teacher_auth
def clustering_page():
    """Student clustering analysis page"""
    return render_template('advanced/clustering.html')

@bp.route('/anomalies')
@require_teacher_auth
def anomalies_page():
    """Anomaly detection page"""
    return render_template('advanced/anomalies.html')

@bp.route('/model_comparison')
@require_teacher_auth
def model_comparison_page():
    """Model comparison page"""
    return render_template('advanced/model_comparison.html')

@bp.route('/real_time')
@require_teacher_auth
def real_time_page():
    """Real-time monitoring page"""
    return render_template('advanced/real_time.html')