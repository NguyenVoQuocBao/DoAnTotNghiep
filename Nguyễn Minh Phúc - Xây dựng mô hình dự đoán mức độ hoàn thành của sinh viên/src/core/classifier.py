"""Learning behavior classification"""

class LearningBehaviorClassifier:
    """Classify student learning behavior into 3 groups"""
    
    BEHAVIOR_LABELS = {
        1: "Thụ động hoặc ít tham gia",
        2: "Học tập chưa ổn định / có xu hướng trì hoãn",
        3: "Học tập tích cực và có chiến lược"
    }
    
    @staticmethod
    def classify_behavior(student_data):
        """
        Classify learning behavior into 3 groups:
        1. Passive/low engagement
        2. Unstable/procrastinating
        3. Active and strategic
        """
        access_freq = student_data.get('access_frequency', 0)
        completion_rate = student_data.get('assignment_completion', 
                                          student_data.get('completion_rate', 0))
        study_time = student_data.get('study_time', 0)
        submission_timing = student_data.get('submission_timing', 0)
        
        avg_score = (access_freq + completion_rate + study_time) / 3
        
        # Group 1: Passive/low engagement
        if avg_score < 4 or completion_rate < 4:
            return 1
        
        # Group 2: Unstable/procrastinating (high submission_timing = late)
        if submission_timing > 7 and avg_score < 7:
            return 2
        
        # Group 3: Active and strategic
        return 3
    
    @classmethod
    def get_behavior_label(cls, behavior_group):
        """Get descriptive label for behavior group"""
        return cls.BEHAVIOR_LABELS.get(behavior_group, "Không xác định")
