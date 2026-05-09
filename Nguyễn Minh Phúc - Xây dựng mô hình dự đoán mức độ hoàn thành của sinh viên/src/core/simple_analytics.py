"""
Simple Analytics Engine (without heavy dependencies)
Basic analytics with clustering and anomaly detection
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class SimpleAnalyticsEngine:
    """
    Simple analytics engine for learning data
    Provides basic clustering and anomaly detection
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.kmeans = None
        self.isolation_forest = None
        
    def cluster_students(self, students_data: List[Dict], n_clusters: int = 4) -> Dict:
        """
        Cluster students based on learning patterns
        """
        logger.info(f"Clustering {len(students_data)} students into {n_clusters} groups...")
        
        # Prepare features
        features = []
        student_ids = []
        
        for data in students_data:
            features.append([
                data.get('test_scores', 0),
                data.get('assignment_completion', 0),
                data.get('access_frequency', 0),
                data.get('study_time', 0),
                data.get('submission_timing', 0)
            ])
            student_ids.append(data.get('student_id', 'unknown'))
        
        X = np.array(features)
        X_scaled = self.scaler.fit_transform(X)
        
        # Perform clustering
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = self.kmeans.fit_predict(X_scaled)
        
        # Calculate silhouette score
        silhouette_avg = silhouette_score(X_scaled, cluster_labels)
        
        # Analyze clusters
        df = pd.DataFrame(X, columns=['test_scores', 'assignment_completion', 
                                    'access_frequency', 'study_time', 'submission_timing'])
        df['cluster'] = cluster_labels
        df['student_id'] = student_ids
        
        cluster_analysis = {}
        cluster_names = ['Xuất sắc', 'Khá', 'Trung bình', 'Cần cải thiện']
        
        for i in range(n_clusters):
            cluster_data = df[df['cluster'] == i]
            cluster_analysis[i] = {
                'name': cluster_names[i] if i < len(cluster_names) else f'Nhóm {i+1}',
                'size': len(cluster_data),
                'percentage': len(cluster_data) / len(df) * 100,
                'characteristics': {
                    'avg_test_scores': float(cluster_data['test_scores'].mean()),
                    'avg_assignment_completion': float(cluster_data['assignment_completion'].mean()),
                    'avg_access_frequency': float(cluster_data['access_frequency'].mean()),
                    'avg_study_time': float(cluster_data['study_time'].mean()),
                    'avg_submission_timing': float(cluster_data['submission_timing'].mean())
                },
                'students': cluster_data['student_id'].tolist()
            }
        
        return {
            'cluster_labels': cluster_labels.tolist(),
            'cluster_analysis': cluster_analysis,
            'silhouette_score': silhouette_avg,
            'n_clusters': n_clusters,
            'total_students': len(students_data)
        }
    
    def detect_anomalies(self, students_data: List[Dict], contamination: float = 0.1) -> Dict:
        """
        Detect anomalous learning patterns
        """
        logger.info(f"Detecting anomalies in {len(students_data)} students...")
        
        # Prepare features
        features = []
        student_ids = []
        
        for data in students_data:
            features.append([
                data.get('test_scores', 0),
                data.get('assignment_completion', 0),
                data.get('access_frequency', 0),
                data.get('study_time', 0),
                data.get('submission_timing', 0)
            ])
            student_ids.append(data.get('student_id', 'unknown'))
        
        X = np.array(features)
        X_scaled = self.scaler.fit_transform(X)
        
        # Detect anomalies
        self.isolation_forest = IsolationForest(
            contamination=contamination, 
            random_state=42,
            n_estimators=100
        )
        anomaly_labels = self.isolation_forest.fit_predict(X_scaled)
        anomaly_scores = self.isolation_forest.decision_function(X_scaled)
        
        # Analyze anomalies
        anomalies = []
        normal_students = []
        
        for i, (label, score) in enumerate(zip(anomaly_labels, anomaly_scores)):
            student_info = {
                'student_id': student_ids[i],
                'anomaly_score': float(score),
                'features': {
                    'test_scores': features[i][0],
                    'assignment_completion': features[i][1],
                    'access_frequency': features[i][2],
                    'study_time': features[i][3],
                    'submission_timing': features[i][4]
                }
            }
            
            if label == -1:  # Anomaly
                anomalies.append(student_info)
            else:
                normal_students.append(student_info)
        
        return {
            'anomalies': sorted(anomalies, key=lambda x: x['anomaly_score']),
            'normal_students': normal_students,
            'n_anomalies': len(anomalies),
            'anomaly_rate': len(anomalies) / len(students_data) * 100,
            'contamination': contamination
        }
    
    def generate_comprehensive_report(self, students_data: List[Dict], 
                                    learning_history: List[Dict] = None) -> Dict:
        """
        Generate basic analytics report
        """
        logger.info("Generating basic analytics report...")
        
        # Perform analyses
        cluster_results = self.cluster_students(students_data)
        anomaly_results = self.detect_anomalies(students_data)
        
        # Summary statistics
        performance_levels = [data.get('completion_level', 'Trung bình') for data in students_data]
        level_counts = {
            'Cao': performance_levels.count('Cao'),
            'Trung bình': performance_levels.count('Trung bình'),
            'Thấp': performance_levels.count('Thấp')
        }
        
        return {
            'summary': {
                'total_students': len(students_data),
                'performance_distribution': level_counts,
                'high_performers_percentage': level_counts['Cao'] / len(students_data) * 100 if len(students_data) > 0 else 0,
                'anomaly_rate': anomaly_results['anomaly_rate'],
                'trend_direction': 'stable'  # Simplified
            },
            'clustering': cluster_results,
            'anomalies': anomaly_results,
            'trends': {'trend_direction': 'stable'},  # Simplified
            'visualizations': {
                'heatmap': '',
                'clusters': '',
                'trends': ''
            },
            'generated_at': datetime.now().isoformat()
        }