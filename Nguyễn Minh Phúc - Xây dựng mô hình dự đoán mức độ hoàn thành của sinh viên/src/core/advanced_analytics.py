"""
Advanced Analytics Engine for Learning Analytics System
Provides clustering, trend analysis, and comparative analytics
"""

from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from datetime import datetime, timedelta
import json

class AdvancedAnalytics:
    """Advanced analytics engine with clustering and trend analysis"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.kmeans = None
        self.cluster_labels = None
        
    def perform_student_clustering(self, students_data: List[Dict]) -> Dict[str, Any]:
        """
        Phân nhóm sinh viên dựa trên patterns học tập
        Returns: Clustering results with insights
        """
        if len(students_data) < 4:
            return {"error": "Cần ít nhất 4 sinh viên để phân nhóm"}
            
        # Prepare features for clustering
        features = []
        student_ids = []
        
        for student in students_data:
            features.append([
                student.get('test_scores', 5.0),
                student.get('assignment_completion', 5.0),
                student.get('access_frequency', 5.0),
                student.get('study_time', 5.0),
                student.get('submission_timing', 5.0)
            ])
            student_ids.append(student.get('username', 'unknown'))
        
        # Standardize features
        features_scaled = self.scaler.fit_transform(features)
        
        # Determine optimal number of clusters (2-4)
        n_clusters = min(4, max(2, len(students_data) // 3))
        
        # Perform K-means clustering
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.cluster_labels = self.kmeans.fit_predict(features_scaled)
        
        # Calculate silhouette score
        silhouette_avg = silhouette_score(features_scaled, self.cluster_labels)
        
        # Analyze clusters
        clusters_analysis = self._analyze_clusters(features, self.cluster_labels, student_ids)
        
        return {
            "n_clusters": n_clusters,
            "silhouette_score": round(silhouette_avg, 3),
            "clusters": clusters_analysis,
            "cluster_centers": self.kmeans.cluster_centers_.tolist(),
            "total_students": len(students_data)
        }
    
    def _analyze_clusters(self, features: List[List[float]], labels: np.ndarray, student_ids: List[str]) -> Dict[int, Dict]:
        """Analyze characteristics of each cluster"""
        clusters = {}
        feature_names = ['test_scores', 'assignment_completion', 'access_frequency', 'study_time', 'submission_timing']
        
        for cluster_id in range(max(labels) + 1):
            cluster_mask = labels == cluster_id
            cluster_features = np.array(features)[cluster_mask]
            cluster_students = np.array(student_ids)[cluster_mask]
            
            # Calculate cluster statistics
            cluster_mean = np.mean(cluster_features, axis=0)
            cluster_std = np.std(cluster_features, axis=0)
            
            # Determine cluster characteristics
            characteristics = self._determine_cluster_characteristics(cluster_mean)
            
            clusters[cluster_id] = {
                "name": characteristics["name"],
                "description": characteristics["description"],
                "students": cluster_students.tolist(),
                "count": len(cluster_students),
                "statistics": {
                    feature_names[i]: {
                        "mean": round(cluster_mean[i], 2),
                        "std": round(cluster_std[i], 2)
                    } for i in range(len(feature_names))
                },
                "recommendations": characteristics["recommendations"]
            }
        
        return clusters
    
    def _determine_cluster_characteristics(self, cluster_mean: np.ndarray) -> Dict[str, Any]:
        """Determine cluster characteristics based on mean values"""
        avg_score = np.mean(cluster_mean)
        
        if avg_score >= 8.0:
            return {
                "name": "Xuất sắc",
                "description": "Sinh viên có hiệu suất học tập rất cao, tích cực tham gia",
                "recommendations": [
                    "Tiếp tục duy trì phong độ",
                    "Có thể hỗ trợ các bạn khác",
                    "Thử thách với bài tập nâng cao"
                ]
            }
        elif avg_score >= 6.0:
            return {
                "name": "Khá",
                "description": "Sinh viên có hiệu suất tốt, cần một số cải thiện",
                "recommendations": [
                    "Tăng cường thời gian học tập",
                    "Cải thiện tần suất truy cập",
                    "Nộp bài đúng hạn"
                ]
            }
        elif avg_score >= 4.0:
            return {
                "name": "Trung bình",
                "description": "Sinh viên cần cải thiện đáng kể",
                "recommendations": [
                    "Tăng thời gian học tập",
                    "Cải thiện điểm số bài kiểm tra",
                    "Hoàn thành đầy đủ bài tập"
                ]
            }
        else:
            return {
                "name": "Cần hỗ trợ",
                "description": "Sinh viên cần sự hỗ trợ đặc biệt",
                "recommendations": [
                    "Cần hỗ trợ học tập cá nhân",
                    "Tham gia lớp học bổ sung",
                    "Gặp gỡ giáo viên thường xuyên"
                ]
            }
    
    def analyze_learning_trends(self, history_data: List[Dict]) -> Dict[str, Any]:
        """
        Phân tích xu hướng học tập theo thời gian
        """
        if not history_data:
            return {"error": "Không có dữ liệu lịch sử"}
        
        # Sort by timestamp
        sorted_history = sorted(history_data, key=lambda x: x.get('timestamp', ''))
        
        # Extract trends
        timestamps = []
        completion_scores = []
        predictions = []
        
        for record in sorted_history:
            timestamps.append(record.get('timestamp', ''))
            completion_scores.append(record.get('completion_score', 0))
            predictions.append(record.get('prediction', 'Trung bình'))
        
        # Calculate trend direction
        if len(completion_scores) >= 2:
            recent_trend = completion_scores[-3:] if len(completion_scores) >= 3 else completion_scores
            trend_direction = "tăng" if recent_trend[-1] > recent_trend[0] else "giảm" if recent_trend[-1] < recent_trend[0] else "ổn định"
        else:
            trend_direction = "không đủ dữ liệu"
        
        # Calculate statistics
        avg_score = np.mean(completion_scores) if completion_scores else 0
        score_variance = np.var(completion_scores) if len(completion_scores) > 1 else 0
        
        return {
            "total_records": len(sorted_history),
            "trend_direction": trend_direction,
            "average_score": round(avg_score, 2),
            "score_variance": round(score_variance, 2),
            "latest_score": completion_scores[-1] if completion_scores else 0,
            "score_history": completion_scores,
            "timestamps": timestamps,
            "predictions_history": predictions
        }
    
    def compare_student_performance(self, student_data: Dict, class_data: List[Dict]) -> Dict[str, Any]:
        """
        So sánh hiệu suất sinh viên với lớp
        """
        if not class_data:
            return {"error": "Không có dữ liệu lớp học"}
        
        # Calculate class statistics
        class_scores = {
            'test_scores': [s.get('test_scores', 5.0) for s in class_data],
            'assignment_completion': [s.get('assignment_completion', 5.0) for s in class_data],
            'access_frequency': [s.get('access_frequency', 5.0) for s in class_data],
            'study_time': [s.get('study_time', 5.0) for s in class_data],
            'submission_timing': [s.get('submission_timing', 5.0) for s in class_data]
        }
        
        # Student scores
        student_scores = {
            'test_scores': student_data.get('test_scores', 5.0),
            'assignment_completion': student_data.get('assignment_completion', 5.0),
            'access_frequency': student_data.get('access_frequency', 5.0),
            'study_time': student_data.get('study_time', 5.0),
            'submission_timing': student_data.get('submission_timing', 5.0)
        }
        
        # Calculate percentiles and comparisons
        comparisons = {}
        for metric, class_values in class_scores.items():
            student_value = student_scores[metric]
            class_mean = np.mean(class_values)
            class_std = np.std(class_values)
            
            # Calculate percentile
            percentile = (sum(1 for x in class_values if x <= student_value) / len(class_values)) * 100
            
            # Calculate z-score
            z_score = (student_value - class_mean) / class_std if class_std > 0 else 0
            
            comparisons[metric] = {
                "student_score": round(student_value, 2),
                "class_average": round(class_mean, 2),
                "percentile": round(percentile, 1),
                "z_score": round(z_score, 2),
                "performance": "trên trung bình" if student_value > class_mean else "dưới trung bình" if student_value < class_mean else "trung bình"
            }
        
        # Overall ranking
        overall_scores = [np.mean([s.get('test_scores', 5.0), s.get('assignment_completion', 5.0), 
                                  s.get('access_frequency', 5.0), s.get('study_time', 5.0), 
                                  s.get('submission_timing', 5.0)]) for s in class_data]
        student_overall = np.mean(list(student_scores.values()))
        overall_percentile = (sum(1 for x in overall_scores if x <= student_overall) / len(overall_scores)) * 100
        
        return {
            "comparisons": comparisons,
            "overall_ranking": {
                "percentile": round(overall_percentile, 1),
                "rank": len(overall_scores) - int(overall_percentile * len(overall_scores) / 100) + 1,
                "total_students": len(overall_scores)
            },
            "strengths": [metric for metric, data in comparisons.items() if data["performance"] == "trên trung bình"],
            "areas_for_improvement": [metric for metric, data in comparisons.items() if data["performance"] == "dưới trung bình"]
        }
    
    def detect_at_risk_students(self, students_data: List[Dict]) -> Dict[str, Any]:
        """
        Phát hiện sinh viên có nguy cơ học tập
        """
        at_risk_students = []
        risk_factors = {
            "low_test_scores": [],
            "poor_assignment_completion": [],
            "low_access_frequency": [],
            "insufficient_study_time": [],
            "late_submissions": []
        }
        
        for student in students_data:
            username = student.get('username', 'unknown')
            risk_score = 0
            student_risks = []
            
            # Check various risk factors
            if student.get('test_scores', 5.0) < 4.0:
                risk_score += 3
                student_risks.append("Điểm kiểm tra thấp")
                risk_factors["low_test_scores"].append(username)
            
            if student.get('assignment_completion', 5.0) < 4.0:
                risk_score += 2
                student_risks.append("Hoàn thành bài tập kém")
                risk_factors["poor_assignment_completion"].append(username)
            
            if student.get('access_frequency', 5.0) < 3.0:
                risk_score += 2
                student_risks.append("Truy cập hệ thống ít")
                risk_factors["low_access_frequency"].append(username)
            
            if student.get('study_time', 5.0) < 3.0:
                risk_score += 1
                student_risks.append("Thời gian học tập không đủ")
                risk_factors["insufficient_study_time"].append(username)
            
            if student.get('submission_timing', 5.0) > 7.0:
                risk_score += 1
                student_risks.append("Thường nộp bài muộn")
                risk_factors["late_submissions"].append(username)
            
            # Classify risk level
            if risk_score >= 5:
                risk_level = "Cao"
            elif risk_score >= 3:
                risk_level = "Trung bình"
            elif risk_score >= 1:
                risk_level = "Thấp"
            else:
                risk_level = "Không có"
            
            if risk_score > 0:
                at_risk_students.append({
                    "username": username,
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "risk_factors": student_risks,
                    "recommendations": self._get_risk_recommendations(student_risks)
                })
        
        return {
            "total_at_risk": len(at_risk_students),
            "at_risk_students": sorted(at_risk_students, key=lambda x: x["risk_score"], reverse=True),
            "risk_distribution": {
                "high_risk": len([s for s in at_risk_students if s["risk_level"] == "Cao"]),
                "medium_risk": len([s for s in at_risk_students if s["risk_level"] == "Trung bình"]),
                "low_risk": len([s for s in at_risk_students if s["risk_level"] == "Thấp"])
            },
            "common_risk_factors": {k: len(v) for k, v in risk_factors.items() if v}
        }
    
    def _get_risk_recommendations(self, risk_factors: List[str]) -> List[str]:
        """Get recommendations based on risk factors"""
        recommendations = []
        
        if "Điểm kiểm tra thấp" in risk_factors:
            recommendations.append("Tăng cường ôn tập và luyện thi")
        
        if "Hoàn thành bài tập kém" in risk_factors:
            recommendations.append("Lập kế hoạch hoàn thành bài tập đúng hạn")
        
        if "Truy cập hệ thống ít" in risk_factors:
            recommendations.append("Tăng tần suất truy cập và tham gia học tập")
        
        if "Thời gian học tập không đủ" in risk_factors:
            recommendations.append("Dành nhiều thời gian hơn cho việc học")
        
        if "Thường nộp bài muộn" in risk_factors:
            recommendations.append("Cải thiện quản lý thời gian và nộp bài đúng hạn")
        
        return recommendations