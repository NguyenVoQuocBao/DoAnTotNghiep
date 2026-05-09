"""Completion assessment model"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import COMPLETION_WEIGHTS, COMPLETION_THRESHOLDS

class CompletionAssessmentModel:
    """Model for assessing learning completion level"""
    
    def __init__(self, weights=None):
        self.weights = weights or COMPLETION_WEIGHTS
    
    def calculate_completion_level(self, student_data):
        """Calculate completion level from normalized data"""
        test_score = student_data.get('test_scores', 1.0)
        assignment_comp = student_data.get('assignment_completion', 1.0)
        access_freq = student_data.get('access_frequency', 1.0)
        study_time = student_data.get('study_time', 1.0)
        submission_timing = student_data.get('submission_timing', 1.0)
        
        # Invert submission timing: early (low value) is better
        submission_score = max(1.0, min(10.0, 11 - submission_timing)) if submission_timing > 0 else 1.0
        
        # Calculate weighted total score
        total_score = (
            test_score * self.weights['test_scores'] +
            assignment_comp * self.weights['assignment_completion'] +
            access_freq * self.weights['access_frequency'] +
            study_time * self.weights['study_time'] +
            submission_score * self.weights['submission_timing']
        )
        
        # Determine completion level
        if total_score < COMPLETION_THRESHOLDS['low']:
            level = "Thấp"
        elif total_score < COMPLETION_THRESHOLDS['medium']:
            level = "Trung bình"
        else:
            level = "Cao"
        
        return {
            'completion_score': round(total_score, 2),
            'completion_level': level,
            'test_score': round(test_score, 2),
            'assignment_score': round(assignment_comp, 2),
            'access_score': round(access_freq, 2),
            'study_time_score': round(study_time, 2),
            'submission_score': round(submission_score, 2)
        }
