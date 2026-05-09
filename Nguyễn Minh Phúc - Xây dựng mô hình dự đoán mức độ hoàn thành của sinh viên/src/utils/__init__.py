"""Utility functions"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .auth import AuthHelper

__all__ = ['AuthHelper']
