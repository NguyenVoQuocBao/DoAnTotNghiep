"""Data persistence service"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models import Student, Teacher
from config import DATA_FILE, TEACHERS_FILE, HISTORY_FILE, MAX_HISTORY_RECORDS

class DataService:
    """Service for loading and saving data"""
    
    @staticmethod
    def load_json(file_path: Path) -> Dict:
        """Load JSON file"""
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    @staticmethod
    def save_json(file_path: Path, data: Dict):
        """Save JSON file"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_students(cls) -> Dict[str, Student]:
        """Load students from file"""
        data = cls.load_json(DATA_FILE)
        return {
            username: Student.from_dict(student_data)
            for username, student_data in data.items()
        }
    
    @classmethod
    def save_students(cls, students: Dict[str, Student]):
        """Save students to file"""
        data = {
            username: student.to_dict()
            for username, student in students.items()
        }
        cls.save_json(DATA_FILE, data)
    
    @classmethod
    def load_teachers(cls) -> Dict[str, Teacher]:
        """Load teachers from file"""
        data = cls.load_json(TEACHERS_FILE)
        if not data:
            # Create default teachers
            data = cls._create_default_teachers()
            cls.save_json(TEACHERS_FILE, data)
        
        return {
            username: Teacher.from_dict(teacher_data)
            for username, teacher_data in data.items()
        }
    
    @classmethod
    def save_teachers(cls, teachers: Dict[str, Teacher]):
        """Save teachers to file"""
        data = {
            username: teacher.to_dict()
            for username, teacher in teachers.items()
        }
        cls.save_json(TEACHERS_FILE, data)
    
    @classmethod
    def load_history(cls) -> Dict:
        """Load learning history"""
        return cls.load_json(HISTORY_FILE)
    
    @classmethod
    def save_history(cls, history: Dict):
        """Save learning history"""
        cls.save_json(HISTORY_FILE, history)
    
    @classmethod
    def add_history_entry(cls, student_id: str, entry: Dict):
        """Add entry to student's learning history"""
        history = cls.load_history()
        
        if student_id not in history:
            history[student_id] = []
        
        history[student_id].append(entry)
        
        # Keep only recent records
        history[student_id] = history[student_id][-MAX_HISTORY_RECORDS:]
        
        cls.save_history(history)
    
    @staticmethod
    def _create_default_teachers() -> Dict:
        """Create default teacher accounts"""
        return {
            'teacher001': {
                'username': 'teacher001',
                'password': 'teacher123',
                'name': 'Giáo viên 001',
                'email': 'teacher001@university.edu.vn'
            },
            'teacher002': {
                'username': 'teacher002',
                'password': 'teacher123',
                'name': 'Giáo viên 002',
                'email': 'teacher002@university.edu.vn'
            },
            'admin': {
                'username': 'admin',
                'password': 'admin123',
                'name': 'Quản trị viên',
                'email': 'admin@university.edu.vn'
            }
        }
