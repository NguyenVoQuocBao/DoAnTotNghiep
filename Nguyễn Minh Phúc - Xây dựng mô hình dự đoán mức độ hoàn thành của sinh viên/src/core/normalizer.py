"""Data normalization to 1-10 scale"""

class DataNormalizer:
    """Normalize learning data to 1-10 scale"""
    
    @staticmethod
    def normalize_score(score, max_score=10):
        """Normalize score to 1-10 scale"""
        if max_score == 0:
            return 1.0
        normalized = (score / max_score) * 10
        return max(1.0, min(10.0, normalized))
    
    @staticmethod
    def normalize_frequency(count, max_count=None):
        """Normalize frequency (access count) to 1-10 scale"""
        if max_count is None:
            max_count = 100
        
        if max_count == 0:
            return 1.0
        
        normalized = (count / max_count) * 10
        return max(1.0, min(10.0, normalized))
    
    @staticmethod
    def normalize_time(minutes, max_minutes=None):
        """Normalize study time to 1-10 scale"""
        if max_minutes is None:
            max_minutes = 1000
        
        if max_minutes == 0:
            return 1.0
        
        normalized = (minutes / max_minutes) * 10
        return max(1.0, min(10.0, normalized))
    
    @staticmethod
    def normalize_completion_rate(rate):
        """Normalize completion rate to 1-10 scale"""
        if rate > 1:
            rate = rate / 100
        
        normalized = rate * 10
        return max(1.0, min(10.0, normalized))
