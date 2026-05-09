"""Random Forest prediction model with cross-validation"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from config import RANDOM_FOREST_ESTIMATORS, RANDOM_FOREST_SEED
from ..services.model_service import model_service
from ..utils.logging_config import get_logger, log_performance

logger = get_logger(__name__)

class RandomForestPredictor:
    """Random Forest model for completion level prediction with cross-validation"""
    
    FEATURE_NAMES = [
        'test_scores', 'assignment_completion', 'access_frequency',
        'study_time', 'submission_timing'
    ]
    
    LEVEL_MAP = {0: "Thấp", 1: "Trung bình", 2: "Cao"}
    
    def __init__(self, n_estimators=None, random_state=None, optimize_params=False):
        self.n_estimators = n_estimators or RANDOM_FOREST_ESTIMATORS
        self.random_state = random_state or RANDOM_FOREST_SEED
        self.optimize_params = optimize_params
        
        # Try to load existing model first
        self.model = model_service.load_model('random_forest')
        
        if self.model is None:
            logger.info("No existing model found, creating new RandomForestClassifier")
            self.model = RandomForestClassifier(
                n_estimators=self.n_estimators,
                random_state=self.random_state,
                max_depth=10,
                min_samples_split=5
            )
            self.is_trained = False
        else:
            logger.info("Loaded existing trained model")
            self.is_trained = True
        
        self.cv_scores = None
        self.best_params = None
        self.classification_metrics = None
    
    def prepare_features(self, student_data_list):
        """Prepare features from student data"""
        features = [
            [
                data.get('test_scores', 0),
                data.get('assignment_completion', 0),
                data.get('access_frequency', 0),
                data.get('study_time', 0),
                data.get('submission_timing', 0)
            ]
            for data in student_data_list
        ]
        
        return pd.DataFrame(features, columns=self.FEATURE_NAMES)
    
    @log_performance('model_training')
    def train(self, X, y):
        """Train the model with cross-validation"""
        logger.info("Training Random Forest with cross-validation...")
        
        # Hyperparameter optimization if requested
        if self.optimize_params:
            self._optimize_hyperparameters(X, y)
        
        # Cross-validation evaluation
        self._perform_cross_validation(X, y)
        
        # Train final model on full dataset
        self.model.fit(X, y)
        self.is_trained = True
        
        # Generate classification metrics
        y_pred = self.model.predict(X)
        self._generate_classification_metrics(y, y_pred)
        
        # Save the trained model
        metadata = {
            'training_samples': len(X),
            'features': self.FEATURE_NAMES,
            'cv_scores': self.cv_scores.tolist() if self.cv_scores is not None else None,
            'cv_mean': self.cv_scores.mean() if self.cv_scores is not None else None,
            'cv_std': self.cv_scores.std() if self.cv_scores is not None else None,
            'best_params': self.best_params,
            'n_estimators': self.n_estimators,
            'random_state': self.random_state
        }
        
        model_service.save_model(self.model, 'random_forest', metadata)
        
        # Clean up old models (keep only 3 most recent)
        model_service.delete_old_models('random_forest', keep_count=3)
        
        logger.info("Model trained and saved successfully")
        print(f"✅ Model trained successfully!")
        print(f"📊 Cross-validation accuracy: {self.cv_scores.mean():.3f} (+/- {self.cv_scores.std() * 2:.3f})")
        
    def _optimize_hyperparameters(self, X, y):
        """Optimize hyperparameters using GridSearchCV"""
        logger.info("🔍 Optimizing hyperparameters...")
        print("🔍 Optimizing hyperparameters...")
        
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [5, 10, 15, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4]
        }
        
        grid_search = GridSearchCV(
            RandomForestClassifier(random_state=self.random_state),
            param_grid,
            cv=5,
            scoring='accuracy',
            n_jobs=-1,
            verbose=0
        )
        
        grid_search.fit(X, y)
        self.best_params = grid_search.best_params_
        
        # Update model with best parameters
        self.model = grid_search.best_estimator_
        
        print(f"✅ Best parameters: {self.best_params}")
        print(f"📈 Best CV score: {grid_search.best_score_:.3f}")
    
    def _perform_cross_validation(self, X, y):
        """Perform stratified k-fold cross-validation"""
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=self.random_state)
        self.cv_scores = cross_val_score(self.model, X, y, cv=cv, scoring='accuracy')
        
        print(f"📊 Cross-validation scores: {[f'{score:.3f}' for score in self.cv_scores]}")
    
    def _generate_classification_metrics(self, y_true, y_pred):
        """Generate detailed classification metrics"""
        present_labels = sorted(set(y_true))
        present_names = [self.LEVEL_MAP[l] for l in present_labels if l in self.LEVEL_MAP]

        self.classification_metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'classification_report': classification_report(
                y_true, y_pred,
                labels=present_labels,
                target_names=present_names,
                output_dict=True
            ),
            'confusion_matrix': confusion_matrix(y_true, y_pred, labels=present_labels)
        }
    
    def predict(self, X):
        """Predict completion level"""
        if not self.is_trained:
            raise ValueError("Model not trained yet!")
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """Predict probability"""
        if not self.is_trained:
            raise ValueError("Model not trained yet!")
        return self.model.predict_proba(X)
    
    def get_feature_importance(self):
        """Get feature importance"""
        if not self.is_trained:
            return {}
        
        importances = self.model.feature_importances_
        return dict(zip(self.FEATURE_NAMES, importances))
    
    def get_model_performance(self):
        """Get comprehensive model performance metrics"""
        if not self.is_trained or not self.classification_metrics:
            return {}
        
        return {
            'cross_validation': {
                'mean_accuracy': self.cv_scores.mean(),
                'std_accuracy': self.cv_scores.std(),
                'individual_scores': self.cv_scores.tolist()
            },
            'training_metrics': self.classification_metrics,
            'feature_importance': self.get_feature_importance(),
            'best_parameters': self.best_params
        }
    
    def print_performance_summary(self):
        """Print a comprehensive performance summary"""
        if not self.is_trained:
            print("❌ Model not trained yet!")
            return
        
        print("\n" + "="*60)
        print("🎯 RANDOM FOREST PERFORMANCE SUMMARY")
        print("="*60)
        
        # Cross-validation results
        print(f"\n📊 Cross-Validation Results:")
        print(f"   Mean Accuracy: {self.cv_scores.mean():.3f}")
        print(f"   Std Deviation: {self.cv_scores.std():.3f}")
        print(f"   95% Confidence: {self.cv_scores.mean():.3f} (+/- {self.cv_scores.std() * 2:.3f})")
        
        # Feature importance
        print(f"\n🔍 Feature Importance:")
        importance = self.get_feature_importance()
        for feature, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True):
            print(f"   {feature:20}: {imp:.3f}")
        
        # Classification metrics
        if self.classification_metrics:
            print(f"\n📈 Training Set Performance:")
            print(f"   Overall Accuracy: {self.classification_metrics['accuracy']:.3f}")
            
            print(f"\n📋 Per-Class Performance:")
            report = self.classification_metrics['classification_report']
            for level_name in self.LEVEL_MAP.values():
                if level_name in report:
                    metrics = report[level_name]
                    print(f"   {level_name:12}: Precision={metrics['precision']:.3f}, "
                          f"Recall={metrics['recall']:.3f}, F1={metrics['f1-score']:.3f}")
        
        # Best parameters (if optimization was used)
        if self.best_params:
            print(f"\n⚙️ Optimized Parameters:")
            for param, value in self.best_params.items():
                print(f"   {param:20}: {value}")
        
        print("="*60)
