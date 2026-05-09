"""Authentication helper utilities"""

from typing import Optional, Tuple
from werkzeug.security import generate_password_hash, check_password_hash
from src.models import Student, Teacher
from src.services import ExcelService, DataService

class AuthHelper:
    """Helper for authentication operations"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password for storing"""
        return generate_password_hash(password)
    
    @staticmethod
    def verify_password(stored_password: str, provided_password: str) -> bool:
        """Verify a stored password against provided password"""
        # For development: use plain text comparison
        return stored_password == provided_password
    
    @staticmethod
    def upgrade_password_if_needed(user_data: dict, provided_password: str, user_type: str = 'student') -> bool:
        """Upgrade legacy plain text password to hashed version"""
        # Skip password hashing for development
        return False
    
    @staticmethod
    def find_student_by_mssv(
        username: str, 
        students_data: dict,
        excel_df=None,
        mssv_mapping=None
    ) -> Tuple[Optional[dict], Optional[str]]:
        """
        Find student by MSSV (student ID) with multiple lookup strategies
        Returns: (student_dict, actual_username)
        """
        # Strategy 1: Look up in Excel first
        if excel_df is not None and mssv_mapping:
            mssv_upper = username.upper().strip()
            if mssv_upper in mssv_mapping:
                excel_idx = mssv_mapping[mssv_upper]
                excel_row = excel_df.iloc[excel_idx]
                
                # Get MSSV from Excel
                mssv_columns = [
                    col for col in excel_df.columns 
                    if 'StudentID' in str(col) or 'MSSV' in str(col).upper()
                ]
                excel_mssv = str(
                    excel_row.get(mssv_columns[0] if mssv_columns else '', '')
                ).strip()
                
                # Find in students_data by Excel MSSV
                for user_key, student_info in students_data.items():
                    if str(student_info.get('student_id', '')).upper() == excel_mssv.upper():
                        return student_info, user_key
        
        # Strategy 2: Direct username lookup
        if username in students_data:
            return students_data[username], username
        
        # Strategy 3: Search by student_id in students_data
        for user_key, student_info in students_data.items():
            if str(student_info.get('student_id', '')).upper() == username.upper():
                return student_info, user_key
        
        return None, None
    
    @staticmethod
    def authenticate_teacher(username: str, password: str, teachers_data: dict) -> Optional[Teacher]:
        """Authenticate teacher with password hashing support"""
        if username in teachers_data:
            teacher = teachers_data[username]
            teacher_dict = teacher.to_dict() if isinstance(teacher, Teacher) else teacher
            
            if AuthHelper.verify_password(teacher_dict.get('password', ''), password):
                # Upgrade password if needed
                AuthHelper.upgrade_password_if_needed(teacher_dict, password, 'teacher')
                
                return teacher if isinstance(teacher, Teacher) else Teacher.from_dict(teacher_dict)
        return None
    
    @staticmethod
    def authenticate_student(
        username: str, 
        password: str, 
        students_data: dict
    ) -> Tuple[Optional[dict], Optional[str]]:
        """
        Authenticate student with password hashing support
        Returns: (student_dict, actual_username)
        """
        excel_df, mssv_mapping = ExcelService.load_excel_data()
        student_found, actual_username = AuthHelper.find_student_by_mssv(
            username, students_data, excel_df, mssv_mapping
        )
        
        if student_found and AuthHelper.verify_password(student_found.get('password', ''), password):
            # Upgrade password if needed
            AuthHelper.upgrade_password_if_needed(student_found, password, 'student')
            return student_found, actual_username
        
        return None, None
