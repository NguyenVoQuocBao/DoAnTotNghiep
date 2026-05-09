"""
Learning Analytics System - Refactored Entry Point
Main application entry point with improved architecture
"""

import sys
import warnings
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

warnings.filterwarnings('ignore')

from src.web import create_app
from src.core import LearningAnalyticsSystem
from src.services import DataService, SampleDataService
from src.services.real_data_service import RealDataService
from src.models import Student
from src.utils.logging_config import setup_logging, get_logger, log_performance
from config import DEBUG, HOST, PORT

# Setup logging
setup_logging()
logger = get_logger(__name__)

@log_performance('startup')
def initialize_sample_data():
    """Initialize student data from real Excel files or generate sample data"""
    logger.info("Initializing student data...")
    students = DataService.load_students()
    
    if not students:
        logger.info("No existing students found, loading from Excel files...")
        
        # Try to load real data first
        real_data = RealDataService.load_real_student_data()
        
        if real_data:
            logger.info(f"Found {len(real_data)} students in Excel files")
            students = {}
            
            for data in real_data:
                mssv = data['student_id']
                students[mssv] = Student(
                    username=mssv,
                    student_id=data['student_id'],
                    name=data.get('full_name', f"Sinh viên {mssv}"),
                    password='123456',
                    raw_data=data
                )
            
            logger.info(f"Created {len(students)} students from real data")
        else:
            logger.info("No Excel files found, generating sample data...")
            sample_data = SampleDataService.generate_sample_data(50)
            students = {}
            
            for i, data in enumerate(sample_data):
                mssv = data['student_id']  # Use MSSV as username
                students[mssv] = Student(
                    username=mssv,
                    student_id=data['student_id'],
                    name=f"Sinh viên {mssv}",
                    password='123456',
                    raw_data=data
                )
            
            logger.info(f"Created {len(students)} sample students")
        
        DataService.save_students(students)
    else:
        logger.info(f"Loaded {len(students)} existing students")
    
    return students

@log_performance('model_training')
def train_model(analytics_system, students):
    """Train the Random Forest model with enhanced evaluation"""
    logger.info("Training Random Forest model with cross-validation...")
    
    normalized_data = []
    labels = []
    
    for student in students.values():
        result = analytics_system.process_student_data(student.raw_data)
        normalized_data.append(result['normalized_data'])
        
        level = result['completion_assessment']['completion_level']
        label = {'Thấp': 0, 'Trung bình': 1, 'Cao': 2}[level]
        labels.append(label)
    
    # Train model and get performance metrics
    # Only train if we have all 3 classes
    unique_labels = set(labels)
    if len(unique_labels) < 3:
        logger.warning(f"Only {len(unique_labels)} classes found, skipping model training")
        return {}

    performance = analytics_system.train_prediction_model(normalized_data, labels)
    
    logger.info("Model training completed", extra={
        'model_accuracy': performance.get('cv_mean', 0),
        'training_samples': len(normalized_data)
    })
    
    # Store performance in app config for later use
    return performance

def main():
    """Main entry point"""
    logger.info("Starting Learning Analytics System...")
    
    print("=" * 60)
    print("HỆ THỐNG PHÂN TÍCH VÀ GỢI Ý HỌC TẬP")
    print("=" * 60)
    print()
    
    try:
        # Initialize analytics system
        analytics_system = LearningAnalyticsSystem()
        
        # Initialize data
        students = initialize_sample_data()
        
        # Train model
        model_performance = train_model(analytics_system, students)
        
        # Create Flask app
        app = create_app()
        
        # Store analytics system and performance in app config
        app.config['ANALYTICS_SYSTEM'] = analytics_system
        app.config['MODEL_PERFORMANCE'] = model_performance
        
        # Get SocketIO instance
        socketio = app.config.get('SOCKETIO')
        
        print()
        print("Starting web server...")
        print(f"Access: http://127.0.0.1:{PORT}")
        print()
        print("Sample accounts:")
        print("  Student:")
        print("    - Username: <MSSV thật> (e.g., 122000002, 122000015, 122000057, ...)")
        print("    - Password: 123456")
        print("    - Run 'python show_real_accounts.py' to see full list")
        print("  Teacher:")
        print("    - Username: teacher001 (or teacher002, admin)")
        print("    - Password: teacher123 (admin: admin123)")
        print("=" * 60)
        print()
        
        logger.info(f"Web server starting on {HOST}:{PORT}")
        app.run(debug=DEBUG, host=HOST, port=PORT)
        
    except Exception as e:
        logger.error("Failed to start application", exc_info=True)
        raise

if __name__ == '__main__':
    main()
