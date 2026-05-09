"""Sample data generation service"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np
from typing import List, Dict
from config import SAMPLE_DATA_DISTRIBUTION

class SampleDataService:
    """Service for generating sample student data"""
    
    @staticmethod
    def generate_sample_data(n_students: int = 50, seed: int = 42) -> List[Dict]:
        """Generate sample student data with realistic patterns"""
        np.random.seed(seed)
        sample_data = []
        
        # Calculate distribution
        n_passive = int(n_students * SAMPLE_DATA_DISTRIBUTION['passive'])
        n_procrastinating = int(n_students * SAMPLE_DATA_DISTRIBUTION['procrastinating'])
        n_proactive = n_students - n_passive - n_procrastinating
        
        for i in range(n_students):
            # Determine student type
            if i < n_passive:
                data = SampleDataService._generate_passive_student(i)
            elif i < n_passive + n_procrastinating:
                data = SampleDataService._generate_procrastinating_student(i)
            else:
                data = SampleDataService._generate_proactive_student(i)
            
            sample_data.append(data)
        
        return sample_data
    
    @staticmethod
    def _generate_passive_student(index: int) -> Dict:
        """Generate data for passive student"""
        # Generate realistic MSSV (Vietnamese student ID format)
        year = np.random.choice(['20', '21', '22', '23'])  # Enrollment year
        major_code = np.random.choice(['IT', 'CS', 'SE', 'IS', 'AI'])  # Major codes
        student_number = f"{index+1:04d}"  # 4-digit student number
        mssv = f"{year}{major_code}{student_number}"
        
        return {
            'student_id': mssv,
            'test_scores': round(np.random.uniform(3, 6), 2),
            'max_test_score': 10,
            'assignment_completion_rate': round(np.random.uniform(0.2, 0.5), 2),
            'access_count': np.random.randint(5, 30),
            'max_access_count': 100,
            'study_time_minutes': round(np.random.uniform(50, 300), 2),
            'max_study_time': 1000,
            'submission_timing_score': round(np.random.uniform(6, 10), 2)
        }
    
    @staticmethod
    def _generate_procrastinating_student(index: int) -> Dict:
        """Generate data for procrastinating student"""
        # Generate realistic MSSV (Vietnamese student ID format)
        year = np.random.choice(['20', '21', '22', '23'])  # Enrollment year
        major_code = np.random.choice(['IT', 'CS', 'SE', 'IS', 'AI'])  # Major codes
        student_number = f"{index+1:04d}"  # 4-digit student number
        mssv = f"{year}{major_code}{student_number}"
        
        return {
            'student_id': mssv,
            'test_scores': round(np.random.uniform(5, 8), 2),
            'max_test_score': 10,
            'assignment_completion_rate': round(np.random.uniform(0.4, 0.7), 2),
            'access_count': np.random.randint(20, 60),
            'max_access_count': 100,
            'study_time_minutes': round(np.random.uniform(200, 600), 2),
            'max_study_time': 1000,
            'submission_timing_score': round(np.random.uniform(7, 10), 2)
        }
    
    @staticmethod
    def _generate_proactive_student(index: int) -> Dict:
        """Generate data for proactive student"""
        # Generate realistic MSSV (Vietnamese student ID format)
        year = np.random.choice(['20', '21', '22', '23'])  # Enrollment year
        major_code = np.random.choice(['IT', 'CS', 'SE', 'IS', 'AI'])  # Major codes
        student_number = f"{index+1:04d}"  # 4-digit student number
        mssv = f"{year}{major_code}{student_number}"
        
        return {
            'student_id': mssv,
            'test_scores': round(np.random.uniform(7, 10), 2),
            'max_test_score': 10,
            'assignment_completion_rate': round(np.random.uniform(0.7, 1.0), 2),
            'access_count': np.random.randint(50, 100),
            'max_access_count': 100,
            'study_time_minutes': round(np.random.uniform(500, 1000), 2),
            'max_study_time': 1000,
            'submission_timing_score': round(np.random.uniform(1, 5), 2)
        }
