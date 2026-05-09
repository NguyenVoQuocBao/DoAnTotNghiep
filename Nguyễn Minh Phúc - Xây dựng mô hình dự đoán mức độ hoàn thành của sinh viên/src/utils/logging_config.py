"""Logging configuration for the Learning Analytics System"""

import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import BASE_DIR

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'student_id'):
            log_entry['student_id'] = record.student_id
        if hasattr(record, 'user_type'):
            log_entry['user_type'] = record.user_type
        if hasattr(record, 'processing_time'):
            log_entry['processing_time'] = record.processing_time
        if hasattr(record, 'completion_score'):
            log_entry['completion_score'] = record.completion_score
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)

def setup_logging():
    """Setup logging configuration"""
    
    # Create logs directory
    logs_dir = BASE_DIR / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with simple format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with JSON format
    file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / 'learning_analytics.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        logs_dir / 'errors.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(error_handler)
    
    # Analytics specific logger
    analytics_logger = logging.getLogger('analytics')
    analytics_handler = logging.handlers.RotatingFileHandler(
        logs_dir / 'analytics.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    analytics_handler.setFormatter(JSONFormatter())
    analytics_logger.addHandler(analytics_handler)
    analytics_logger.setLevel(logging.INFO)
    
    # Security logger
    security_logger = logging.getLogger('security')
    security_handler = logging.handlers.RotatingFileHandler(
        logs_dir / 'security.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    security_handler.setFormatter(JSONFormatter())
    security_logger.addHandler(security_handler)
    security_logger.setLevel(logging.INFO)
    
    return root_logger

def get_logger(name: str):
    """Get logger with specified name"""
    return logging.getLogger(name)

# Performance monitoring decorator
def log_performance(logger_name: str = 'performance'):
    """Decorator to log function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            logger = get_logger(logger_name)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                processing_time = time.time() - start_time
                
                logger.info(
                    f"Function {func.__name__} completed successfully",
                    extra={
                        'function': func.__name__,
                        'processing_time': processing_time,
                        'args_count': len(args),
                        'kwargs_count': len(kwargs)
                    }
                )
                return result
            except Exception as e:
                processing_time = time.time() - start_time
                logger.error(
                    f"Function {func.__name__} failed",
                    extra={
                        'function': func.__name__,
                        'processing_time': processing_time,
                        'error': str(e),
                        'args_count': len(args),
                        'kwargs_count': len(kwargs)
                    },
                    exc_info=True
                )
                raise
        return wrapper
    return decorator

# Security event logger
def log_security_event(event_type: str, username: str = None, ip_address: str = None, details: dict = None):
    """Log security events"""
    logger = get_logger('security')
    
    extra_data = {
        'event_type': event_type,
        'username': username,
        'ip_address': ip_address
    }
    
    if details:
        extra_data.update(details)
    
    logger.warning(f"Security event: {event_type}", extra=extra_data)

# Analytics event logger
def log_analytics_event(student_id: str, event_type: str, completion_score: float = None, details: dict = None):
    """Log analytics events"""
    logger = get_logger('analytics')
    
    extra_data = {
        'student_id': student_id,
        'event_type': event_type,
        'completion_score': completion_score
    }
    
    if details:
        extra_data.update(details)
    
    logger.info(f"Analytics event: {event_type}", extra=extra_data)