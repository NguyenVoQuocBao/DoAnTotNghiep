"""Learning recommendation system"""

import copy

class LearningRecommendationSystem:
    """System for recommending next learning level"""
    
    RECOMMENDATIONS = {
        "Thấp": {
            "level": "Cơ bản",
            "suggestions": [
                "Học lại kiến thức cơ bản",
                "Làm bài tập cơ bản",
                "Xem lại video bài giảng",
                "Tham gia các buổi ôn tập"
            ]
        },
        "Trung bình": {
            "level": "Củng cố",
            "suggestions": [
                "Củng cố kiến thức đã học",
                "Luyện tập thêm bài tập",
                "Tham gia thảo luận nhóm",
                "Làm bài tập nâng cao vừa phải"
            ]
        },
        "Cao": {
            "level": "Nâng cao",
            "suggestions": [
                "Học nâng cao và mở rộng kiến thức",
                "Làm bài tập khó",
                "Tham gia dự án thực tế",
                "Học các chủ đề mở rộng"
            ]
        }
    }
    
    def get_recommendation(self, completion_level, behavior_group=None):
        """Get learning recommendation based on completion level and behavior"""
        base_recommendation = copy.deepcopy(
            self.RECOMMENDATIONS.get(completion_level, self.RECOMMENDATIONS["Trung bình"])
        )
        
        # Adjust recommendations based on behavior
        if behavior_group == 1:  # Passive
            base_recommendation["suggestions"].insert(
                0, "Tăng cường tương tác với hệ thống học tập"
            )
        elif behavior_group == 2:  # Procrastinating
            base_recommendation["suggestions"].insert(
                0, "Lập kế hoạch học tập và tuân thủ deadline"
            )
        
        return base_recommendation
