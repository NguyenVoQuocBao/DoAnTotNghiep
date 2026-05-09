"""Student data models"""

from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class StudentRawData:
    """Raw student learning data"""
    student_id: str
    test_scores: float = 0.0
    max_test_score: float = 10.0
    assignment_completion_rate: float = 0.0
    access_count: int = 0
    max_access_count: int = 100
    study_time_minutes: float = 0.0
    max_study_time: float = 1000.0
    submission_timing_score: float = 5.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'student_id': self.student_id,
            'test_scores': self.test_scores,
            'max_test_score': self.max_test_score,
            'assignment_completion_rate': self.assignment_completion_rate,
            'access_count': self.access_count,
            'max_access_count': self.max_access_count,
            'study_time_minutes': self.study_time_minutes,
            'max_study_time': self.max_study_time,
            'submission_timing_score': self.submission_timing_score
        }

@dataclass
class Student:
    """Student account information"""
    username: str
    student_id: str
    name: str
    password: str
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'username': self.username,
            'student_id': self.student_id,
            'name': self.name,
            'password': self.password,
            'raw_data': self.raw_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Student':
        """Create from dictionary"""
        return cls(
            username=data.get('username', ''),
            student_id=data.get('student_id', ''),
            name=data.get('name', ''),
            password=data.get('password', ''),
            raw_data=data.get('raw_data', {})
        )

@dataclass
class Teacher:
    """Teacher account information"""
    username: str
    name: str
    password: str
    email: str = ''
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'username': self.username,
            'name': self.name,
            'password': self.password,
            'email': self.email
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Teacher':
        """Create from dictionary"""
        return cls(
            username=data.get('username', ''),
            name=data.get('name', ''),
            password=data.get('password', ''),
            email=data.get('email', '')
        )
