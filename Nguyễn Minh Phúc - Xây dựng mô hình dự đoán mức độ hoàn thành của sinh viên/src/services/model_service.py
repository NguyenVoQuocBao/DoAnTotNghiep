"""Model persistence service"""

import joblib
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import BASE_DIR
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

class ModelService:
    """Service for saving and loading trained models"""
    
    def __init__(self):
        self.models_dir = BASE_DIR / 'models'
        self.models_dir.mkdir(exist_ok=True)
        
    def save_model(self, model, model_name: str, metadata: Dict[str, Any] = None) -> bool:
        """Save trained model with metadata"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            model_filename = f"{model_name}_{timestamp}.pkl"
            model_path = self.models_dir / model_filename
            
            # Save model
            joblib.dump(model, model_path)
            
            # Save metadata
            if metadata:
                metadata_path = self.models_dir / f"{model_name}_{timestamp}_metadata.json"
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, default=str)
            
            # Update latest model symlink
            latest_path = self.models_dir / f"{model_name}_latest.pkl"
            if latest_path.exists():
                latest_path.unlink()
            latest_path.symlink_to(model_filename)
            
            # Update latest metadata symlink
            if metadata:
                latest_metadata_path = self.models_dir / f"{model_name}_latest_metadata.json"
                if latest_metadata_path.exists():
                    latest_metadata_path.unlink()
                latest_metadata_path.symlink_to(f"{model_name}_{timestamp}_metadata.json")
            
            logger.info(f"Model saved successfully: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save model {model_name}: {e}", exc_info=True)
            return False
    
    def load_model(self, model_name: str, use_latest: bool = True):
        """Load trained model"""
        try:
            if use_latest:
                model_path = self.models_dir / f"{model_name}_latest.pkl"
            else:
                # Find most recent model
                model_files = list(self.models_dir.glob(f"{model_name}_*.pkl"))
                if not model_files:
                    return None
                model_path = max(model_files, key=lambda p: p.stat().st_mtime)
            
            if not model_path.exists():
                logger.warning(f"Model not found: {model_path}")
                return None
            
            model = joblib.load(model_path)
            logger.info(f"Model loaded successfully: {model_path}")
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}", exc_info=True)
            return None
    
    def load_model_metadata(self, model_name: str, use_latest: bool = True) -> Optional[Dict[str, Any]]:
        """Load model metadata"""
        try:
            if use_latest:
                metadata_path = self.models_dir / f"{model_name}_latest_metadata.json"
            else:
                # Find most recent metadata
                metadata_files = list(self.models_dir.glob(f"{model_name}_*_metadata.json"))
                if not metadata_files:
                    return None
                metadata_path = max(metadata_files, key=lambda p: p.stat().st_mtime)
            
            if not metadata_path.exists():
                return None
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Failed to load model metadata {model_name}: {e}", exc_info=True)
            return None
    
    def list_models(self, model_name: str = None) -> list:
        """List available models"""
        try:
            if model_name:
                pattern = f"{model_name}_*.pkl"
            else:
                pattern = "*.pkl"
            
            model_files = list(self.models_dir.glob(pattern))
            
            models = []
            for model_file in model_files:
                if '_latest.pkl' in model_file.name:
                    continue
                    
                # Extract timestamp from filename
                parts = model_file.stem.split('_')
                if len(parts) >= 2:
                    timestamp_str = '_'.join(parts[-2:])
                    try:
                        timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                        models.append({
                            'name': '_'.join(parts[:-2]),
                            'filename': model_file.name,
                            'timestamp': timestamp,
                            'size': model_file.stat().st_size
                        })
                    except ValueError:
                        pass
            
            return sorted(models, key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list models: {e}", exc_info=True)
            return []
    
    def delete_old_models(self, model_name: str, keep_count: int = 5) -> int:
        """Delete old model versions, keeping only the most recent ones"""
        try:
            models = self.list_models(model_name)
            if len(models) <= keep_count:
                return 0
            
            models_to_delete = models[keep_count:]
            deleted_count = 0
            
            for model_info in models_to_delete:
                model_path = self.models_dir / model_info['filename']
                metadata_path = self.models_dir / model_info['filename'].replace('.pkl', '_metadata.json')
                
                if model_path.exists():
                    model_path.unlink()
                    deleted_count += 1
                
                if metadata_path.exists():
                    metadata_path.unlink()
            
            logger.info(f"Deleted {deleted_count} old model versions for {model_name}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete old models: {e}", exc_info=True)
            return 0

# Global model service instance
model_service = ModelService()