"""
Simple Neural Network Predictor (without TensorFlow for compatibility)
Uses scikit-learn MLPClassifier as a neural network alternative
"""

import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import logging
from typing import List, Dict, Tuple, Optional
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)

class NeuralNetworkPredictor:
    """
    Simple Neural Network using scikit-learn MLPClassifier
    Alternative to TensorFlow for better compatibility
    """
    
    def __init__(self, 
                 hidden_layer_sizes: Tuple = (64, 32, 16),
                 learning_rate: float = 0.001,
                 max_iter: int = 500,
                 random_state: int = 42):
        """
        Initialize Neural Network Predictor
        
        Args:
            hidden_layer_sizes: Tuple of neurons in each hidden layer
            learning_rate: Learning rate for optimizer
            max_iter: Maximum number of iterations
            random_state: Random seed for reproducibility
        """
        self.hidden_layer_sizes = hidden_layer_sizes
        self.learning_rate = learning_rate
        self.max_iter = max_iter
        self.random_state = random_state
        
        self.model = MLPClassifier(
            hidden_layer_sizes=hidden_layer_sizes,
            learning_rate_init=learning_rate,
            max_iter=max_iter,
            random_state=random_state,
            early_stopping=True,
            validation_fraction=0.2,
            n_iter_no_change=20
        )
        
        self.scaler = StandardScaler()
        self.is_trained = False
        self.training_history = {}
    
    def prepare_features(self, student_data_list: List[Dict]) -> np.ndarray:
        """
        Prepare features from student data for neural network
        
        Args:
            student_data_list: List of normalized student data dictionaries
            
        Returns:
            Feature matrix as numpy array
        """
        features = []
        
        for data in student_data_list:
            # Basic features
            feature_vector = [
                data.get('test_scores', 0),
                data.get('assignment_completion', 0),
                data.get('access_frequency', 0),
                data.get('study_time', 0),
                data.get('submission_timing', 0)
            ]
            
            # Engineered features
            avg_score = np.mean([data.get('test_scores', 0), data.get('assignment_completion', 0)])
            engagement = (data.get('access_frequency', 0) + data.get('study_time', 0)) / 2
            consistency = 1 / (1 + abs(data.get('submission_timing', 5) - 5))  # Closer to 5 is better
            
            feature_vector.extend([avg_score, engagement, consistency])
            
            # Interaction features
            score_engagement = avg_score * engagement
            score_consistency = avg_score * consistency
            engagement_consistency = engagement * consistency
            
            feature_vector.extend([score_engagement, score_consistency, engagement_consistency])
            
            features.append(feature_vector)
        
        return np.array(features)
    
    def train(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """
        Train the neural network model
        
        Args:
            X: Feature matrix
            y: Target labels (0: Low, 1: Medium, 2: High)
            
        Returns:
            Training metrics
        """
        logger.info("Training Neural Network model (MLPClassifier)...")
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X_scaled, y, test_size=0.2, random_state=self.random_state, stratify=y
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Evaluate model
        train_pred = self.model.predict(X_train)
        val_pred = self.model.predict(X_val)
        
        train_acc = accuracy_score(y_train, train_pred)
        val_acc = accuracy_score(y_val, val_pred)
        
        # Store training history
        self.training_history = {
            'n_iter': self.model.n_iter_,
            'loss_curve': getattr(self.model, 'loss_curve_', []),
            'validation_scores': getattr(self.model, 'validation_scores_', [])
        }
        
        metrics = {
            'train_accuracy': train_acc,
            'val_accuracy': val_acc,
            'classification_report': classification_report(y_val, val_pred, output_dict=True),
            'confusion_matrix': confusion_matrix(y_val, val_pred).tolist(),
            'training_samples': len(X_train),
            'validation_samples': len(X_val),
            'iterations': self.model.n_iter_
        }
        
        logger.info(f"Neural Network trained - Val Accuracy: {val_acc:.4f}")
        
        return metrics
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Make predictions with the trained model
        
        Args:
            X: Feature matrix
            
        Returns:
            Tuple of (predicted_classes, prediction_probabilities)
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        X_scaled = self.scaler.transform(X)
        predicted_classes = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)
        
        return predicted_classes, probabilities
    
    def predict_single(self, student_data: Dict) -> Dict:
        """
        Predict completion level for a single student
        
        Args:
            student_data: Normalized student data dictionary
            
        Returns:
            Prediction results with probabilities
        """
        features = self.prepare_features([student_data])
        predicted_class, probabilities = self.predict(features)
        
        class_labels = ['Thấp', 'Trung bình', 'Cao']
        
        return {
            'predicted_level': class_labels[predicted_class[0]],
            'confidence': float(np.max(probabilities[0]) * 100),
            'probabilities': {
                'Thấp': float(probabilities[0][0] * 100),
                'Trung bình': float(probabilities[0][1] * 100),
                'Cao': float(probabilities[0][2] * 100)
            }
        }
    
    def get_feature_importance(self) -> Dict:
        """
        Get feature importance (simplified for MLPClassifier)
        """
        if not self.is_trained:
            return {}
        
        feature_names = [
            'test_scores', 'assignment_completion', 'access_frequency', 
            'study_time', 'submission_timing', 'avg_score', 'engagement', 
            'consistency', 'score_engagement', 'score_consistency', 'engagement_consistency'
        ]
        
        # For MLP, we can't get direct feature importance like tree-based models
        # Return uniform importance as placeholder
        return {name: 1.0/len(feature_names) for name in feature_names}
    
    def save_model(self, filepath: str):
        """Save the trained model and scaler"""
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")
        
        model_path = Path(filepath)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save model
        joblib.dump(self.model, f"{filepath}_model.pkl")
        
        # Save scaler
        joblib.dump(self.scaler, f"{filepath}_scaler.pkl")
        
        # Save metadata
        metadata = {
            'hidden_layer_sizes': self.hidden_layer_sizes,
            'learning_rate': self.learning_rate,
            'max_iter': self.max_iter,
            'random_state': self.random_state,
            'training_history': self.training_history
        }
        joblib.dump(metadata, f"{filepath}_metadata.pkl")
        
        logger.info(f"Neural Network model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load a trained model and scaler"""
        # Load model
        self.model = joblib.load(f"{filepath}_model.pkl")
        
        # Load scaler
        self.scaler = joblib.load(f"{filepath}_scaler.pkl")
        
        # Load metadata
        metadata = joblib.load(f"{filepath}_metadata.pkl")
        self.hidden_layer_sizes = metadata['hidden_layer_sizes']
        self.learning_rate = metadata['learning_rate']
        self.max_iter = metadata['max_iter']
        self.random_state = metadata['random_state']
        self.training_history = metadata.get('training_history', {})
        
        self.is_trained = True
        logger.info(f"Neural Network model loaded from {filepath}")