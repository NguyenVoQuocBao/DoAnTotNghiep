"""Teacher routes"""

from flask import Blueprint, render_template, redirect, url_for, session, flash, send_file, current_app, jsonify
import pandas as pd
import numpy as np
from pathlib import Path
from src.services import DataService, ExcelService
from src.models import Student

bp = Blueprint('teacher', __name__, url_prefix='/teacher')

def require_teacher_auth(f):
    """Decorator to require teacher authentication"""
    def wrapper(*args, **kwargs):
        if 'username' not in session or session.get('user_type') != 'teacher':
            flash('Vui lòng đăng nhập với tài khoản giáo viên!', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def get_analytics_system():
    """Get analytics system from app config"""
    return current_app.config.get('ANALYTICS_SYSTEM')

@bp.route('/dashboard')
@require_teacher_auth
def dashboard():
    """Teacher dashboard"""
    students = DataService.load_students()
    analytics = get_analytics_system()
    
    all_students_analysis = []
    level_counts = {"Thấp": 0, "Trung bình": 0, "Cao": 0}
    behavior_counts = {1: 0, 2: 0, 3: 0}
    
    for username, student in students.items():
        result = analytics.process_student_data(student.raw_data)
        
        analysis = {
            'username': username,
            'student_id': student.student_id,
            'name': student.name,
            'completion_level': result['completion_assessment']['completion_level'],
            'completion_score': result['completion_assessment']['completion_score'],
            'behavior_group': result['behavior_group'],
            'behavior_label': result['behavior_label'],
            'test_score': result['completion_assessment']['test_score'],
            'assignment_score': result['completion_assessment']['assignment_score'],
            'raw_test_score': student.raw_data.get('test_scores', 0),
            'raw_completion_rate': student.raw_data.get('assignment_completion_rate', 0),
            'raw_access_count': student.raw_data.get('access_count', 0),
            'raw_study_time': student.raw_data.get('study_time_minutes', 0)
        }
        
        all_students_analysis.append(analysis)
        level_counts[result['completion_assessment']['completion_level']] += 1
        behavior_counts[result['behavior_group']] += 1
    
    all_students_analysis.sort(key=lambda x: x['completion_score'], reverse=True)
    
    total = len(all_students_analysis)
    stats = {
        'total_students': total,
        'level_counts': level_counts,
        'level_percentages': {
            level: (count / total * 100) if total > 0 else 0
            for level, count in level_counts.items()
        },
        'behavior_counts': behavior_counts,
        'behavior_percentages': {
            group: (count / total * 100) if total > 0 else 0
            for group, count in behavior_counts.items()
        },
        'avg_completion_score': sum(s['completion_score'] for s in all_students_analysis) / total if total > 0 else 0
    }
    
    return render_template('teacher_dashboard.html', 
                         students=all_students_analysis,
                         stats=stats,
                         teacher_name=session.get('teacher_name', 'Giáo viên'))

@bp.route('/student/<username>')
@require_teacher_auth
def student_detail(username):
    """View student details"""
    students = DataService.load_students()
    
    if username not in students:
        flash('Không tìm thấy sinh viên!', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    student = students[username]
    analytics = get_analytics_system()
    
    result = analytics.process_student_data(student.raw_data)
    prediction = analytics.predict_completion_level(result['normalized_data'])
    
    history_data = DataService.load_history().get(student.student_id, [])
    history_data.sort(key=lambda x: x['timestamp'], reverse=True)
    
    data = {
        'student_name': student.name,
        'student_id': student.student_id,
        'username': username,
        'normalized_data': result['normalized_data'],
        'behavior_group': result['behavior_group'],
        'behavior_label': result['behavior_label'],
        'completion_assessment': result['completion_assessment'],
        'recommendation': result['recommendation'],
        'prediction': prediction,
        'raw_data': student.raw_data,
        'history': history_data[:10]
    }
    
    return render_template('teacher_student_detail.html', data=data)

@bp.route('/statistics')
@require_teacher_auth
def statistics():
    """Class statistics"""
    students = DataService.load_students()
    analytics = get_analytics_system()
    
    all_stats = {
        'completion_levels': {"Thấp": 0, "Trung bình": 0, "Cao": 0},
        'behavior_groups': {1: 0, 2: 0, 3: 0},
        'test_scores': [],
        'completion_scores': [],
        'access_counts': [],
        'study_times': []
    }
    
    behavior_labels = {
        1: "Thụ động hoặc ít tham gia",
        2: "Học tập chưa ổn định / có xu hướng trì hoãn",
        3: "Học tập tích cực và có chiến lược"
    }
    
    for student in students.values():
        result = analytics.process_student_data(student.raw_data)
        
        all_stats['completion_levels'][result['completion_assessment']['completion_level']] += 1
        all_stats['behavior_groups'][result['behavior_group']] += 1
        all_stats['test_scores'].append(student.raw_data.get('test_scores', 0))
        all_stats['completion_scores'].append(result['completion_assessment']['completion_score'])
        all_stats['access_counts'].append(student.raw_data.get('access_count', 0))
        all_stats['study_times'].append(student.raw_data.get('study_time_minutes', 0))
    
    total = len(students)
    
    stats_summary = {
        'total_students': total,
        'completion_levels': all_stats['completion_levels'],
        'completion_levels_pct': {
            level: (count / total * 100) if total > 0 else 0
            for level, count in all_stats['completion_levels'].items()
        },
        'behavior_groups': {
            group: {
                'count': count,
                'percentage': (count / total * 100) if total > 0 else 0,
                'label': behavior_labels[group]
            }
            for group, count in all_stats['behavior_groups'].items()
        },
        'avg_test_score': sum(all_stats['test_scores']) / total if total > 0 else 0,
        'avg_completion_score': sum(all_stats['completion_scores']) / total if total > 0 else 0,
        'avg_access_count': sum(all_stats['access_counts']) / total if total > 0 else 0,
        'avg_study_time': sum(all_stats['study_times']) / total if total > 0 else 0,
        # Distribution data for charts
        'score_distribution': {
            '0-2': sum(1 for s in all_stats['completion_scores'] if s < 2),
            '2-4': sum(1 for s in all_stats['completion_scores'] if 2 <= s < 4),
            '4-6': sum(1 for s in all_stats['completion_scores'] if 4 <= s < 6),
            '6-8': sum(1 for s in all_stats['completion_scores'] if 6 <= s < 8),
            '8-10': sum(1 for s in all_stats['completion_scores'] if s >= 8),
        },
        'test_distribution': {
            '0-2': sum(1 for s in all_stats['test_scores'] if s < 2),
            '2-4': sum(1 for s in all_stats['test_scores'] if 2 <= s < 4),
            '4-6': sum(1 for s in all_stats['test_scores'] if 4 <= s < 6),
            '6-8': sum(1 for s in all_stats['test_scores'] if 6 <= s < 8),
            '8-10': sum(1 for s in all_stats['test_scores'] if s >= 8),
        },
        'top_students': sorted(
            [{'id': s.student_id, 'name': s.name,
              'score': analytics.process_student_data(s.raw_data)['completion_assessment']['completion_score']}
             for s in students.values()],
            key=lambda x: x['score'], reverse=True
        )[:10],
    }
    
    return render_template('teacher_statistics.html', stats=stats_summary)

@bp.route('/export_excel')
@require_teacher_auth
def export_excel():
    """Export Excel with analysis"""
    import os
    import tempfile
    from datetime import datetime
    
    try:
        students = DataService.load_students()
        analytics = get_analytics_system()
        
        export_data = []
        
        for username, student in students.items():
            result = analytics.process_student_data(student.raw_data)
            
            row_data = {
                'Mã sinh viên': student.student_id,
                'Họ và tên': student.name,
                'Tên đăng nhập': username,
                'Điểm thi (gốc)': student.raw_data.get('test_scores', 0),
                'Tỷ lệ hoàn thành BT (gốc)': student.raw_data.get('assignment_completion_rate', 0),
                'Số lần truy cập (gốc)': student.raw_data.get('access_count', 0),
                'Thời gian học phút (gốc)': student.raw_data.get('study_time_minutes', 0),
                'Điểm thời điểm nộp (gốc)': student.raw_data.get('submission_timing_score', 5.0),
                'Điểm thi (chuẩn hóa)': round(result['normalized_data']['test_scores'], 2),
                'Hoàn thành BT (chuẩn hóa)': round(result['normalized_data']['assignment_completion'], 2),
                'Tần suất truy cập (chuẩn hóa)': round(result['normalized_data']['access_frequency'], 2),
                'Thời gian học (chuẩn hóa)': round(result['normalized_data']['study_time'], 2),
                'Thời điểm nộp (chuẩn hóa)': round(result['normalized_data']['submission_timing'], 2),
                'Nhóm hành vi': result['behavior_group'],
                'Mô tả hành vi': result['behavior_label'],
                'Mức độ hoàn thành': result['completion_assessment']['completion_level'],
                'Điểm hoàn thành tổng hợp': round(result['completion_assessment']['completion_score'], 2),
                'Cấp độ gợi ý': result['recommendation']['level'],
                'Gợi ý cụ thể': '; '.join(result['recommendation']['suggestions'])
            }
            
            export_data.append(row_data)
        
        df_export = pd.DataFrame(export_data)
        df_export = df_export.sort_values('Điểm hoàn thành tổng hợp', ascending=False)
        
        # Use absolute path in temp directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'student_analysis_{timestamp}.xlsx'
        output_file = Path(tempfile.gettempdir()) / filename
        
        df_export.to_excel(output_file, index=False, engine='openpyxl')
        ExcelService.format_excel_file(output_file)
        
        flash(f'Đã xuất file Excel thành công!', 'success')
        return send_file(
            output_file, 
            as_attachment=True, 
            download_name='Danh_sach_sinh_vien_phan_tich.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        flash(f'Lỗi khi xuất file Excel: {str(e)}', 'error')
        return redirect(url_for('teacher.dashboard'))

@bp.route('/export_csv')
@require_teacher_auth
def export_csv():
    """Export student data as CSV"""
    import tempfile
    from datetime import datetime
    try:
        students = DataService.load_students()
        analytics = get_analytics_system()
        export_data = []
        for username, student in students.items():
            result = analytics.process_student_data(student.raw_data)
            export_data.append({
                'Mã sinh viên': student.student_id,
                'Họ và tên': student.name,
                'Điểm thi': student.raw_data.get('test_scores', 0),
                'Tỷ lệ hoàn thành BT': student.raw_data.get('assignment_completion_rate', 0),
                'Số lần truy cập': student.raw_data.get('access_count', 0),
                'Thời gian học (phút)': student.raw_data.get('study_time_minutes', 0),
                'Điểm nộp bài': student.raw_data.get('submission_timing_score', 5.0),
                'Mức độ hoàn thành': result['completion_assessment']['completion_level'],
                'Điểm hoàn thành': round(result['completion_assessment']['completion_score'], 2),
                'Nhóm hành vi': result['behavior_group'],
            })
        df = pd.DataFrame(export_data).sort_values('Điểm hoàn thành', ascending=False)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = Path(tempfile.gettempdir()) / f'students_{timestamp}.csv'
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        return send_file(output_file, as_attachment=True,
                        download_name='danh_sach_sinh_vien.csv',
                        mimetype='text/csv')
    except Exception as e:
        flash(f'Lỗi khi xuất CSV: {str(e)}', 'error')
        return redirect(url_for('teacher.dashboard'))

@bp.route('/import_data', methods=['GET'])
@require_teacher_auth
def import_data_page():
    """Import data page"""
    return render_template('teacher/import_data.html')

@bp.route('/import_data', methods=['POST'])
@require_teacher_auth
def import_data():
    """Import student data from Excel/CSV"""
    from flask import request
    import tempfile
    from werkzeug.utils import secure_filename

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Không có file được chọn'}), 400

    file = request.files['file']
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        return jsonify({'success': False, 'error': 'Chỉ chấp nhận .xlsx, .xls, .csv'}), 400

    try:
        filename = secure_filename(file.filename)
        temp_path = Path(tempfile.gettempdir()) / filename
        file.save(temp_path)

        # Read file
        if filename.endswith('.csv'):
            df = pd.read_csv(temp_path, encoding='utf-8-sig')
        else:
            df = pd.read_excel(temp_path)

        # Column mapping — flexible
        # Normalize column names first (strip whitespace)
        df.columns = [str(c).strip() for c in df.columns]

        import logging as _log
        _log.getLogger(__name__).info(f"CSV columns after strip: {list(df.columns)}")

        col_map = {
            'Mã sinh viên': 'student_id', 'MSSV': 'student_id', 'student_id': 'student_id',
            'Mã SV': 'student_id', 'MaSV': 'student_id',
            'Họ và tên': 'name', 'Tên': 'name', 'name': 'name', 'Ho Ten': 'name', 'Họ tên': 'name',
            'Điểm thi': 'test_scores', 'test_scores': 'test_scores', 'Diem TB': 'test_scores', 'Điểm TB': 'test_scores',
            'Tỷ lệ hoàn thành BT': 'assignment_completion_rate', 'assignment_completion_rate': 'assignment_completion_rate',
            'Tham Gia (%)': 'tham_gia_pct',
            'Số lần truy cập': 'access_count', 'access_count': 'access_count',
            'Thời gian học (phút)': 'study_time_minutes', 'study_time_minutes': 'study_time_minutes',
            'Thoi Gian TB (h)': 'study_time_hours',
            'Điểm nộp bài': 'submission_timing_score', 'submission_timing_score': 'submission_timing_score',
            'Nop Muon': 'nop_muon',
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

        # Convert special columns
        if 'tham_gia_pct' in df.columns:
            df['assignment_completion_rate'] = pd.to_numeric(df['tham_gia_pct'], errors='coerce').fillna(0) / 100.0
        if 'study_time_hours' in df.columns:
            df['study_time_minutes'] = pd.to_numeric(df['study_time_hours'], errors='coerce').fillna(0) * 60
        if 'nop_muon' in df.columns:
            df['submission_timing_score'] = pd.to_numeric(df['nop_muon'], errors='coerce').fillna(0).apply(
                lambda x: 3.0 if x == 0 else min(10.0, 3.0 + float(x))
            )

        # Convert all numeric columns
        for col in ['test_scores', 'assignment_completion_rate', 'access_count', 'study_time_minutes', 'submission_timing_score']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        if 'student_id' not in df.columns:
            return jsonify({'success': False, 'error': 'File thiếu cột Mã sinh viên / student_id'}), 400

        students = DataService.load_students()
        updated, created = 0, 0

        # Check if replace mode
        replace_mode = request.form.get('replace_mode') == '1'
        if replace_mode:
            students = {}  # Clear all existing students

        def safe_float(val, default=0.0):
            try:
                if val is None or str(val).strip() in ('', 'nan', 'None'):
                    return default
                return float(str(val).replace(',', '.'))
            except:
                return default

        def safe_int(val, default=0):
            try:
                return int(float(str(val).replace(',', '.')))
            except:
                return default

        # Auto-detect max values from data
        def col_max(col_name, default):
            if col_name in df.columns:
                vals = pd.to_numeric(df[col_name], errors='coerce').dropna()
                return float(vals.max()) if len(vals) > 0 and vals.max() > 0 else default
            return default

        max_study = col_max('study_time_minutes', 1000.0)
        max_access = col_max('access_count', 100.0)
        max_test = col_max('test_scores', 10.0)

        # Debug log
        import logging
        logging.getLogger(__name__).info(f"Import max values: test={max_test}, study={max_study}, access={max_access}")

        for _, row in df.iterrows():
            sid = str(row.get('student_id', '')).strip()
            if not sid or sid in ('nan', 'None', ''):
                continue

            raw_data = {
                'student_id': sid,
                'test_scores': safe_float(row.get('test_scores')),
                'max_test_score': max_test,
                'assignment_completion_rate': safe_float(row.get('assignment_completion_rate')),
                'access_count': safe_int(row.get('access_count')),
                'max_access_count': max_access,
                'study_time_minutes': safe_float(row.get('study_time_minutes')),
                'max_study_time': max_study,
                'submission_timing_score': safe_float(row.get('submission_timing_score'), 5.0),
            }

            if sid in students:
                students[sid].raw_data.update(raw_data)
                if 'name' in row and pd.notna(row['name']):
                    students[sid].name = str(row['name'])
                updated += 1
            else:
                name = str(row.get('name', f'Sinh viên {sid}') or f'Sinh viên {sid}')
                students[sid] = Student(
                    username=sid, student_id=sid, name=name,
                    password='123456', raw_data=raw_data
                )
                created += 1

        DataService.save_students(students)
        temp_path.unlink(missing_ok=True)

        return jsonify({
            'success': True,
            'message': f'Đã cập nhật {updated} sinh viên, thêm mới {created} sinh viên.',
            'updated': updated, 'created': created,
            'total': updated + created
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/import_template')
@require_teacher_auth
def import_template():
    """Download import template"""
    import tempfile
    df = pd.DataFrame([{
        'Mã sinh viên': '122000001',
        'Họ và tên': 'Nguyễn Văn A',
        'Điểm thi': 8.5,
        'Tỷ lệ hoàn thành BT': 0.9,
        'Số lần truy cập': 45,
        'Thời gian học (phút)': 300,
        'Điểm nộp bài': 7.0,
    }])
    output = Path(tempfile.gettempdir()) / 'import_template.xlsx'
    df.to_excel(output, index=False)
    return send_file(output, as_attachment=True,
                    download_name='mau_import_sinh_vien.xlsx',
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@bp.route('/class_report')
@require_teacher_auth
def class_report():
    """Class summary report - printable"""
    from datetime import datetime
    students = DataService.load_students()
    analytics = get_analytics_system()

    all_data = []
    level_counts = {"Thấp": 0, "Trung bình": 0, "Cao": 0}
    behavior_counts = {1: 0, 2: 0, 3: 0}
    behavior_labels = {
        1: "Thụ động", 2: "Chưa ổn định", 3: "Tích cực"
    }
    scores, test_scores, study_times = [], [], []

    for username, student in students.items():
        result = analytics.process_student_data(student.raw_data)
        score = float(result['completion_assessment']['completion_score'])
        level = result['completion_assessment']['completion_level']
        bg = int(result['behavior_group'])

        all_data.append({
            'username': username,
            'student_id': student.student_id,
            'name': student.name,
            'level': level,
            'score': round(score, 2),
            'behavior_group': bg,
            'behavior_label': behavior_labels[bg],
            'test_score': round(float(student.raw_data.get('test_scores', 0)), 2),
            'study_time': int(student.raw_data.get('study_time_minutes', 0)),
            'recommendation': result['recommendation']['level'],
        })
        level_counts[level] += 1
        behavior_counts[bg] += 1
        scores.append(score)
        test_scores.append(float(student.raw_data.get('test_scores', 0)))
        study_times.append(float(student.raw_data.get('study_time_minutes', 0)))

    all_data.sort(key=lambda x: x['score'], reverse=True)
    total = len(all_data)

    at_risk = [s for s in all_data if s['level'] == 'Thấp']
    top10 = all_data[:10]

    report = {
        'generated_at': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'total': total,
        'level_counts': level_counts,
        'level_pct': {k: round(v/total*100, 1) if total else 0 for k, v in level_counts.items()},
        'behavior_counts': behavior_counts,
        'behavior_pct': {k: round(v/total*100, 1) if total else 0 for k, v in behavior_counts.items()},
        'behavior_labels': behavior_labels,
        'avg_score': round(sum(scores)/total, 2) if total else 0,
        'avg_test': round(sum(test_scores)/total, 2) if total else 0,
        'avg_study_time': round(sum(study_times)/total, 0) if total else 0,
        'max_score': round(max(scores), 2) if scores else 0,
        'min_score': round(min(scores), 2) if scores else 0,
        'top10': top10,
        'at_risk': at_risk,
        'at_risk_count': len(at_risk),
    }

    return render_template('teacher/class_report.html', report=report,
                           teacher_name=session.get('teacher_name', 'Giáo viên'))

@bp.route('/compare')
@require_teacher_auth
def compare_students():
    """Compare multiple students side by side"""
    from flask import request
    usernames = request.args.getlist('u')
    students = DataService.load_students()
    analytics = get_analytics_system()

    comparison = []
    for username in usernames[:4]:  # max 4
        if username in students:
            student = students[username]
            result = analytics.process_student_data(student.raw_data)
            comparison.append({
                'username': username,
                'name': student.name,
                'student_id': student.student_id,
                'normalized': {k: round(float(v), 2) for k, v in result['normalized_data'].items()},
                'level': result['completion_assessment']['completion_level'],
                'score': round(float(result['completion_assessment']['completion_score']), 2),
                'behavior': result['behavior_label'],
                'behavior_group': int(result['behavior_group']),
                'recommendation': result['recommendation']['level'],
            })

    all_students = [
        {'username': u, 'name': s.name, 'student_id': s.student_id}
        for u, s in sorted(students.items(), key=lambda x: x[1].name)
    ]

    return render_template('teacher/compare_students.html',
                           comparison=comparison,
                           all_students=all_students,
                           selected=usernames)

@bp.route('/model_performance')
@require_teacher_auth
def model_performance():
    """Display model performance metrics"""
    import json
    performance = current_app.config.get('MODEL_PERFORMANCE', {})
    analytics_system = get_analytics_system()

    # Get rich performance data from predictor
    rf_perf = {}
    confusion = []
    class_report = {}
    feature_importance = {}

    if analytics_system and analytics_system.predictor.is_trained:
        rf_perf = analytics_system.predictor.get_model_performance()
        fi = analytics_system.predictor.get_feature_importance()
        feature_importance = dict(sorted(fi.items(), key=lambda x: x[1], reverse=True))

        if analytics_system.predictor.classification_metrics:
            cm = analytics_system.predictor.classification_metrics.get('confusion_matrix')
            if cm is not None:
                confusion = cm.tolist()
            report = analytics_system.predictor.classification_metrics.get('classification_report', {})
            for level in ['Thấp', 'Trung bình', 'Cao']:
                if level in report:
                    class_report[level] = {
                        'precision': round(report[level]['precision'], 3),
                        'recall': round(report[level]['recall'], 3),
                        'f1': round(report[level]['f1-score'], 3),
                        'support': int(report[level]['support'])
                    }

    cv_scores = []
    cv_mean = 0
    cv_std = 0
    if rf_perf.get('cross_validation'):
        cv_scores = [round(s, 4) for s in rf_perf['cross_validation'].get('individual_scores', [])]
        cv_mean = round(rf_perf['cross_validation'].get('mean_accuracy', 0), 4)
        cv_std = round(rf_perf['cross_validation'].get('std_accuracy', 0), 4)

    return render_template('teacher/model_performance.html',
                         performance=performance,
                         rf_perf=rf_perf,
                         cv_scores=cv_scores,
                         cv_mean=cv_mean,
                         cv_std=cv_std,
                         confusion=confusion,
                         class_report=class_report,
                         feature_importance=feature_importance,
                         analytics_system=analytics_system)

@bp.route('/api/model_performance')
@require_teacher_auth  
def api_model_performance():
    """API endpoint for model performance data"""
    performance = current_app.config.get('MODEL_PERFORMANCE', {})
    return jsonify(performance)


@bp.route('/edit_student/<username>')
@require_teacher_auth
def edit_student(username):
    """Edit student data page"""
    students = DataService.load_students()
    
    if username not in students:
        flash('Không tìm thấy sinh viên!', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    student = students[username]
    
    return render_template('teacher_edit_student.html', student=student)

@bp.route('/update_student/<username>', methods=['POST'])
@require_teacher_auth
def update_student(username):
    """Update student data"""
    from flask import request
    
    students = DataService.load_students()
    
    if username not in students:
        flash('Không tìm thấy sinh viên!', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    student = students[username]
    
    # Get form data
    test_scores = float(request.form.get('test_scores', 5.0))
    assignment_completion = float(request.form.get('assignment_completion', 50)) / 100
    access_count = int(request.form.get('access_count', 50))
    study_time = int(request.form.get('study_time', 500))
    submission_timing = float(request.form.get('submission_timing', 5))
    
    # Validate
    if not (0 <= test_scores <= 10):
        flash('Điểm thi phải từ 0 đến 10', 'error')
        return redirect(url_for('teacher.edit_student', username=username))
    
    # Update student data
    student.raw_data['test_scores'] = test_scores
    student.raw_data['assignment_completion_rate'] = assignment_completion
    student.raw_data['access_count'] = access_count
    student.raw_data['study_time_minutes'] = study_time
    student.raw_data['submission_timing'] = submission_timing
    
    # Save
    students[username] = student
    DataService.save_students(students)
    
    flash(f'Đã cập nhật dữ liệu cho sinh viên {student.name}!', 'success')
    return redirect(url_for('teacher.student_detail', username=username))

@bp.route('/excel_manager')
@require_teacher_auth
def excel_manager():
    """Excel file manager - upload and sort"""
    return render_template('teacher_excel_manager.html')

@bp.route('/upload_excel', methods=['POST'])
@require_teacher_auth
def upload_excel():
    """Upload and process external Excel file"""
    from flask import request, jsonify
    from werkzeug.utils import secure_filename
    import os
    import tempfile
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Không có file được chọn'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Không có file được chọn'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        return jsonify({'success': False, 'error': 'Chỉ chấp nhận file Excel (.xlsx, .xls) hoặc CSV (.csv)'}), 400
    
    try:
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = Path(tempfile.gettempdir()) / filename
        file.save(temp_path)
        
        # Load Excel data
        df = ExcelService.load_external_excel(temp_path)
        
        if df is None:
            return jsonify({'success': False, 'error': 'Không thể đọc file Excel'}), 400
        
        # Convert NaN/NaT to None for JSON compatibility
        df = df.replace({np.nan: None})
        
        # Get column names and full file data
        columns = df.columns.tolist()
        preview_data = df.to_dict('records')
        
        # Store file path in session for later use
        session['uploaded_excel_path'] = str(temp_path)
        session['uploaded_excel_filename'] = filename
        
        return jsonify({
            'success': True,
            'columns': columns,
            'preview': preview_data,
            'total_rows': len(df),
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Lỗi xử lý file: {str(e)}'}), 500

@bp.route('/sort_excel', methods=['POST'])
@require_teacher_auth
def sort_excel():
    """Sort uploaded Excel file"""
    from flask import request, jsonify
    from datetime import datetime
    
    if 'uploaded_excel_path' not in session:
        return jsonify({'success': False, 'error': 'Chưa có file Excel nào được tải lên'}), 400
    
    try:
        data = request.get_json()
        sort_column = data.get('sort_column')
        ascending = data.get('ascending', True)
        
        # Load the uploaded file
        file_path = Path(session['uploaded_excel_path'])
        df = ExcelService.load_external_excel(file_path)
        
        if df is None:
            return jsonify({'success': False, 'error': 'Không thể đọc file Excel'}), 400
        
        # Sort data
        df_sorted = ExcelService.sort_excel_data(df, sort_column, ascending)
        
        # Export sorted file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_name = session.get('uploaded_excel_filename', 'file.xlsx')
        base_name = original_name.rsplit('.', 1)[0]
        output_filename = f"{base_name}_sorted_{timestamp}.xlsx"
        output_path = Path(tempfile.gettempdir()) / output_filename
        
        ExcelService.export_sorted_excel(df_sorted, str(output_path))
        
        # Store sorted file path
        session['sorted_excel_path'] = str(output_path)
        session['sorted_excel_filename'] = output_filename
        
        # Convert NaN/NaT to None for JSON compatibility
        df_sorted = df_sorted.replace({np.nan: None})
        
        # Get preview of sorted data (full file)
        preview_data = df_sorted.to_dict('records')
        
        return jsonify({
            'success': True,
            'preview': preview_data,
            'filename': output_filename,
            'total_rows': len(df_sorted)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Lỗi sắp xếp: {str(e)}'}), 500

@bp.route('/download_sorted_excel')
@require_teacher_auth
def download_sorted_excel():
    """Download sorted Excel file"""
    if 'sorted_excel_path' not in session:
        flash('Không có file đã sắp xếp để tải xuống', 'error')
        return redirect(url_for('teacher.excel_manager'))
    
    try:
        file_path = Path(session['sorted_excel_path'])
        filename = session.get('sorted_excel_filename', 'sorted_file.xlsx')
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        flash(f'Lỗi tải file: {str(e)}', 'error')
        return redirect(url_for('teacher.excel_manager'))

@bp.route('/filter_excel', methods=['POST'])
@require_teacher_auth
def filter_excel():
    """Filter uploaded Excel file"""
    from flask import request, jsonify
    
    if 'uploaded_excel_path' not in session:
        return jsonify({'success': False, 'error': 'Chưa có file Excel nào được tải lên'}), 400
    
    try:
        data = request.get_json()
        filter_column = data.get('filter_column')
        filter_value = data.get('filter_value')
        filter_type = data.get('filter_type', 'contains')
        
        # Load the uploaded file
        file_path = Path(session['uploaded_excel_path'])
        df = ExcelService.load_external_excel(file_path)
        
        if df is None:
            return jsonify({'success': False, 'error': 'Không thể đọc file Excel'}), 400
        
        # Filter data
        df_filtered = ExcelService.filter_excel_data(df, filter_column, filter_value, filter_type)
        
        # Convert NaN/NaT to None for JSON compatibility
        df_filtered = df_filtered.replace({np.nan: None})
        
        # Get preview of filtered data (full file)
        preview_data = df_filtered.to_dict('records')
        
        return jsonify({
            'success': True,
            'preview': preview_data,
            'total_rows': len(df_filtered),
            'filtered_from': len(df)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Lỗi lọc dữ liệu: {str(e)}'}), 500

@bp.route('/get_column_stats', methods=['POST'])
@require_teacher_auth
def get_column_stats():
    """Get statistics for a column"""
    from flask import request, jsonify
    
    if 'uploaded_excel_path' not in session:
        return jsonify({'success': False, 'error': 'Chưa có file Excel nào được tải lên'}), 400
    
    try:
        data = request.get_json()
        column = data.get('column')
        
        # Load the uploaded file
        file_path = Path(session['uploaded_excel_path'])
        df = ExcelService.load_external_excel(file_path)
        
        if df is None:
            return jsonify({'success': False, 'error': 'Không thể đọc file Excel'}), 400
        
        # Get statistics
        stats = ExcelService.get_column_statistics(df, column)
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Lỗi tính toán thống kê: {str(e)}'}), 500

@bp.route('/excel_export_csv')
@require_teacher_auth
def excel_export_csv():
    """Export uploaded Excel file to CSV (Excel Manager)"""
    if 'uploaded_excel_path' not in session:
        flash('Chưa có file Excel nào được tải lên', 'error')
        return redirect(url_for('teacher.excel_manager'))
    
    try:
        from datetime import datetime
        import tempfile
        
        # Load the current file (sorted or filtered if applicable)
        file_path = Path(session.get('sorted_excel_path', session['uploaded_excel_path']))
        df = ExcelService.load_external_excel(file_path)
        
        if df is None:
            flash('Không thể đọc file Excel', 'error')
            return redirect(url_for('teacher.excel_manager'))
        
        # Export to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_name = session.get('uploaded_excel_filename', 'file.xlsx')
        base_name = original_name.rsplit('.', 1)[0]
        csv_filename = f"{base_name}_export_{timestamp}.csv"
        csv_path = Path(tempfile.gettempdir()) / csv_filename
        
        ExcelService.export_to_csv(df, str(csv_path))
        
        return send_file(
            csv_path,
            as_attachment=True,
            download_name=csv_filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        flash(f'Lỗi xuất CSV: {str(e)}', 'error')
        return redirect(url_for('teacher.excel_manager'))

@bp.route('/export_json')
@require_teacher_auth
def export_json():
    """Export current data to JSON"""
    if 'uploaded_excel_path' not in session:
        flash('Chưa có file Excel nào được tải lên', 'error')
        return redirect(url_for('teacher.excel_manager'))
    
    try:
        from datetime import datetime
        import tempfile
        
        # Load the current file
        file_path = Path(session.get('sorted_excel_path', session['uploaded_excel_path']))
        df = ExcelService.load_external_excel(file_path)
        
        if df is None:
            flash('Không thể đọc file Excel', 'error')
            return redirect(url_for('teacher.excel_manager'))
        
        # Export to JSON
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_name = session.get('uploaded_excel_filename', 'file.xlsx')
        base_name = original_name.rsplit('.', 1)[0]
        json_filename = f"{base_name}_export_{timestamp}.json"
        json_path = Path(tempfile.gettempdir()) / json_filename
        
        ExcelService.export_to_json(df, str(json_path))
        
        return send_file(
            json_path,
            as_attachment=True,
            download_name=json_filename,
            mimetype='application/json'
        )
        
    except Exception as e:
        flash(f'Lỗi xuất JSON: {str(e)}', 'error')
        return redirect(url_for('teacher.excel_manager'))

@bp.route('/excel_import_data', methods=['POST'])
@require_teacher_auth
def excel_import_data():
    """Import data from CSV or JSON into Excel Manager"""
    from flask import request, jsonify
    from werkzeug.utils import secure_filename
    import tempfile
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Không có file được chọn'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Không có file được chọn'}), 400
    
    # Check file extension
    filename = secure_filename(file.filename)
    file_ext = filename.rsplit('.', 1)[-1].lower()
    
    if file_ext not in ['csv', 'json']:
        return jsonify({'success': False, 'error': 'Chỉ chấp nhận file CSV hoặc JSON'}), 400
    
    try:
        # Save uploaded file
        temp_path = Path(tempfile.gettempdir()) / filename
        file.save(temp_path)
        
        # Import based on file type
        if file_ext == 'csv':
            df = ExcelService.import_from_csv(temp_path)
        else:  # json
            df = ExcelService.import_from_json(temp_path)
        
        if df is None:
            return jsonify({'success': False, 'error': 'Không thể đọc file'}), 400
        
        # Convert to Excel for consistency
        excel_filename = filename.rsplit('.', 1)[0] + '.xlsx'
        excel_path = Path(tempfile.gettempdir()) / excel_filename
        df.to_excel(excel_path, index=False, engine='openpyxl')
        
        # Store in session
        session['uploaded_excel_path'] = str(excel_path)
        session['uploaded_excel_filename'] = excel_filename
        
        # Get preview
        columns = df.columns.tolist()
        preview_data = df.head(10).to_dict('records')
        
        return jsonify({
            'success': True,
            'columns': columns,
            'preview': preview_data,
            'total_rows': len(df),
            'filename': excel_filename,
            'imported_from': file_ext.upper()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Lỗi import: {str(e)}'}), 500
