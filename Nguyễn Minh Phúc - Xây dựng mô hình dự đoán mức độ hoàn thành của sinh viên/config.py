"""Configuration settings for the Learning Analytics System"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
STATIC_DIR = BASE_DIR / 'static'
TEMPLATES_DIR = BASE_DIR / 'templates'

# Data files
DATA_FILE = DATA_DIR / 'students_data.json'
HISTORY_FILE = DATA_DIR / 'learning_history.json'
TEACHERS_FILE = DATA_DIR / 'teachers_data.json'
EXCEL_FILE = BASE_DIR / 'Copy of Danh sách sinh viên_ 410 SV.xlsx'
EXCEL_FALLBACK = BASE_DIR / 'Danh sách sinh viên_with_attributes.xlsx'

# Flask settings
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY or SECRET_KEY == 'your-secret-key-change-in-production':
    import secrets
    SECRET_KEY = secrets.token_hex(32)
    print("⚠️ WARNING: Using generated SECRET_KEY. Set SECRET_KEY environment variable for production!")

DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5001))

# Redis settings
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# Model settings
RANDOM_FOREST_ESTIMATORS = 100
RANDOM_FOREST_SEED = 42
MAX_HISTORY_RECORDS = 50

# Normalization defaults
DEFAULT_MAX_ACCESS_COUNT = 100
DEFAULT_MAX_STUDY_TIME = 1000  # minutes
DEFAULT_SUBMISSION_TIMING = 5

# Completion weights
COMPLETION_WEIGHTS = {
    'test_scores': 0.3,
    'assignment_completion': 0.25,
    'access_frequency': 0.15,
    'study_time': 0.15,
    'submission_timing': 0.15
}

# Completion thresholds
COMPLETION_THRESHOLDS = {
    'low': 4,
    'medium': 7
}

# Sample data distribution
SAMPLE_DATA_DISTRIBUTION = {
    'passive': 0.3,
    'procrastinating': 0.3,
    'proactive': 0.4
}

def ensure_directories():
    """Create necessary directories if they don't exist"""
    DATA_DIR.mkdir(exist_ok=True)
    STATIC_DIR.mkdir(exist_ok=True)
    (STATIC_DIR / 'css').mkdir(exist_ok=True)
    TEMPLATES_DIR.mkdir(exist_ok=True)
