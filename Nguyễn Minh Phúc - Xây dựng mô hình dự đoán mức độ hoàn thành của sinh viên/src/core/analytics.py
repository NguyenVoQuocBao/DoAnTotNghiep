"""Main analytics system orchestrator"""

import numpy as np
from .normalizer import DataNormalizer
from .classifier import LearningBehaviorClassifier
from .assessment import CompletionAssessmentModel
from .recommendation import LearningRecommendationSystem
from .predictor import RandomForestPredictor
from .neural_predictor import NeuralNetworkPredictor
from .simple_analytics import SimpleAnalyticsEngine
from ..services.cache_service import cached_analytics

class LearningAnalyticsSystem:
    """Main system orchestrating all analytics components"""
    
    def __init__(self, optimize_model=False, use_neural_network=True):
        self.normalizer = DataNormalizer()
        self.behavior_classifier = LearningBehaviorClassifier()
        self.completion_model = CompletionAssessmentModel()
        self.recommendation_system = LearningRecommendationSystem()
        self.predictor = RandomForestPredictor(optimize_params=optimize_model)
        
        # Advanced components
        self.neural_predictor = NeuralNetworkPredictor() if use_neural_network else None
        self.advanced_analytics = SimpleAnalyticsEngine()
        self.use_neural_network = use_neural_network
    
    @cached_analytics(timeout=300)  # Cache for 5 minutes
    def process_student_data(self, raw_data):
        """Process raw student data through the analytics pipeline"""
        # Create a hashable key from raw_data for caching
        cache_key = str(sorted(raw_data.items())) if isinstance(raw_data, dict) else str(raw_data)
        
        # Normalize data
        normalized_data = {
            'test_scores': self.normalizer.normalize_score(
                raw_data.get('test_scores', 0),
                raw_data.get('max_test_score', 10)
            ),
            'assignment_completion': self.normalizer.normalize_completion_rate(
                raw_data.get('assignment_completion_rate', 0)
            ),
            'access_frequency': self.normalizer.normalize_frequency(
                raw_data.get('access_count', 0),
                raw_data.get('max_access_count', 100)
            ),
            'study_time': self.normalizer.normalize_time(
                raw_data.get('study_time_minutes', 0),
                raw_data.get('max_study_time', 1000)
            ),
            'submission_timing': self.normalizer.normalize_score(
                raw_data.get('submission_timing_score', 5),
                10
            )
        }
        
        # Classify behavior
        behavior_group = self.behavior_classifier.classify_behavior(normalized_data)
        behavior_label = self.behavior_classifier.get_behavior_label(behavior_group)
        
        # Assess completion
        completion_result = self.completion_model.calculate_completion_level(normalized_data)
        
        # Get recommendation
        recommendation = self.recommendation_system.get_recommendation(
            completion_result['completion_level'],
            behavior_group
        )
        
        return {
            'student_id': raw_data.get('student_id', 'Unknown'),
            'normalized_data': normalized_data,
            'behavior_group': behavior_group,
            'behavior_label': behavior_label,
            'completion_assessment': completion_result,
            'recommendation': recommendation
        }
    
    def train_prediction_model(self, training_data, labels):
        """Train both Random Forest and Neural Network prediction models"""
        X = self.predictor.prepare_features(training_data)
        y = np.array(labels)
        
        # Train Random Forest
        rf_performance = self.predictor.train(X, y)
        self.predictor.print_performance_summary()
        
        # Train Neural Network if enabled
        nn_performance = {}
        if self.use_neural_network and self.neural_predictor:
            try:
                X_nn = self.neural_predictor.prepare_features(training_data)
                nn_performance = self.neural_predictor.train(X_nn, y)
                print(f"Neural Network trained - Validation Accuracy: {nn_performance.get('val_accuracy', 0):.4f}")
            except Exception as e:
                print(f"Neural Network training failed: {e}")
                self.use_neural_network = False
        
        return {
            'random_forest': rf_performance,
            'neural_network': nn_performance,
            'models_trained': ['Random Forest'] + (['Neural Network'] if nn_performance else [])
        }
    
    def predict_completion_level(self, student_data):
        """Predict completion level using both models and ensemble"""
        # Random Forest prediction
        X_rf = self.predictor.prepare_features([student_data])
        rf_prediction = self.predictor.predict(X_rf)[0]
        rf_probabilities = self.predictor.predict_proba(X_rf)[0]
        
        rf_result = {
            'predicted_level': self.predictor.LEVEL_MAP[rf_prediction],
            'confidence': round(max(rf_probabilities) * 100, 2),
            'probabilities': {
                'Thấp': round(rf_probabilities[0] * 100, 2),
                'Trung bình': round(rf_probabilities[1] * 100, 2),
                'Cao': round(rf_probabilities[2] * 100, 2)
            }
        }
        
        # Neural Network prediction if available
        nn_result = {}
        if self.use_neural_network and self.neural_predictor and self.neural_predictor.is_trained:
            try:
                nn_result = self.neural_predictor.predict_single(student_data)
            except Exception as e:
                print(f"Neural Network prediction failed: {e}")
        
        # Ensemble prediction if both models available
        ensemble_result = {}
        if nn_result:
            # Simple averaging ensemble
            rf_probs = [rf_probabilities[0], rf_probabilities[1], rf_probabilities[2]]
            nn_probs = [
                nn_result['probabilities']['Thấp'],
                nn_result['probabilities']['Trung bình'],
                nn_result['probabilities']['Cao']
            ]
            
            ensemble_probs = [(rf + nn) / 2 for rf, nn in zip(rf_probs, nn_probs)]
            ensemble_prediction = np.argmax(ensemble_probs)
            
            ensemble_result = {
                'predicted_level': ['Thấp', 'Trung bình', 'Cao'][ensemble_prediction],
                'confidence': round(max(ensemble_probs) * 100, 2),
                'probabilities': {
                    'Thấp': round(ensemble_probs[0] * 100, 2),
                    'Trung bình': round(ensemble_probs[1] * 100, 2),
                    'Cao': round(ensemble_probs[2] * 100, 2)
                }
            }
        
        return {
            'random_forest': rf_result,
            'neural_network': nn_result,
            'ensemble': ensemble_result,
            'recommended': ensemble_result if ensemble_result else rf_result
        }
    
    def get_model_performance(self):
        """Get comprehensive model performance metrics"""
        return self.predictor.get_model_performance()
    def get_advanced_analytics(self, students_data, learning_history=None):
        """Get comprehensive advanced analytics"""
        if not students_data:
            return {'error': 'No student data available'}
        
        # Convert students to list format for advanced analytics
        student_list = []
        for student in students_data.values():
            processed = self.process_student_data(student.raw_data)
            student_data = processed['normalized_data'].copy()
            student_data['student_id'] = student.student_id
            student_data['completion_level'] = processed['completion_assessment']['completion_level']
            student_list.append(student_data)
        
        # Generate comprehensive report
        return self.advanced_analytics.generate_comprehensive_report(
            student_list, 
            learning_history or []
        )
    
    def get_clustering_analysis(self, students_data, n_clusters=4):
        """Get student clustering analysis"""
        student_list = []
        for student in students_data.values():
            processed = self.process_student_data(student.raw_data)
            student_data = processed['normalized_data'].copy()
            student_data['student_id'] = student.student_id
            student_list.append(student_data)
        
        return self.advanced_analytics.cluster_students(student_list, n_clusters)
    
    def detect_at_risk_students(self, students_data):
        """Detect students at risk using anomaly detection"""
        student_list = []
        for student in students_data.values():
            processed = self.process_student_data(student.raw_data)
            student_data = processed['normalized_data'].copy()
            student_data['student_id'] = student.student_id
            student_list.append(student_data)
        
        return self.advanced_analytics.detect_anomalies(student_list)