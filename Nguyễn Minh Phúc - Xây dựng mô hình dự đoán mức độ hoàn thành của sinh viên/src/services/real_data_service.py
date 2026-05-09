"""
Real Data Service - Load actual student data from Excel files
"""

import sys
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
import logging

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

class RealDataService:
    """Service for loading real student data from Excel files"""
    
    @staticmethod
    def load_real_student_data() -> List[Dict]:
        """Load real student data from Excel file"""
        try:
            # Try different Excel files in order of preference
            excel_files = [
                'danh_sach_sinh_vien_2026-04-24.csv',
                'Danh_sach_sinh_vien_phan_tich (1).xlsx',
                'Danh_sach_sinh_vien_FULL_TiengViet.xlsx',
                'Danh_sach_sinh_vien_FULL.xlsx',
                'Danh_sach_sinh_vien_with_attributes_export.xlsx'
            ]
            
            df = None
            used_file = None
            
            for file_path in excel_files:
                if Path(file_path).exists():
                    try:
                        if file_path.endswith('.csv'):
                            df = pd.read_csv(file_path, encoding='utf-8-sig')
                        else:
                            df = pd.read_excel(file_path)
                        used_file = file_path
                        logger.info(f"Successfully loaded data from {file_path}")
                        break
                    except Exception as e:
                        logger.warning(f"Failed to load {file_path}: {e}")
                        continue
            
            if df is None:
                logger.warning("No Excel files found, falling back to sample data")
                return []
            
            # Process the data based on file format
            df.columns = [str(c).strip() for c in df.columns]  # normalize
            if 'MaSV' in df.columns:  # Vietnamese format
                return RealDataService._process_vietnamese_format(df)
            elif 'StudentID' in df.columns:  # English format
                return RealDataService._process_english_format(df)
            elif 'Mã sinh viên' in df.columns or 'Mã sinh   viên' in df.columns:  # Export format
                return RealDataService._process_export_format(df)
            elif 'MSSV' in df.columns:  # CSV format
                return RealDataService._process_csv_format(df)
            else:
                logger.error(f"Unknown format in {used_file}: columns={list(df.columns)}")
                return []
                
        except Exception as e:
            logger.error(f"Error loading real student data: {e}")
            return []
    
    @staticmethod
    def _process_vietnamese_format(df: pd.DataFrame) -> List[Dict]:
        """Process Vietnamese format Excel file"""
        student_data = []
        
        for _, row in df.iterrows():
            try:
                # Extract MSSV (MaSV)
                mssv = str(row['MaSV']).strip()
                
                # Get student info
                ho = str(row.get('Ho', '')).strip()
                ten = str(row.get('Ten', '')).strip()
                full_name = f"{ho} {ten}".strip()
                
                # Get learning metrics
                data = {
                    'student_id': mssv,
                    'full_name': full_name,
                    'class_id': str(row.get('MaLop', '')).strip(),
                    'test_scores': float(row.get('DiemKiemTra', 0)),
                    'max_test_score': 10,
                    'assignment_completion_rate': float(row.get('TyLeHoanThanhBaiTap', 0)),
                    'access_count': int(row.get('SoLanTruyCapHeThong', 0)),
                    'max_access_count': 100,
                    'study_time_minutes': float(row.get('ThoiGianHocTap_Phut', 0)),
                    'max_study_time': 1000,
                    'submission_timing_score': RealDataService._calculate_submission_timing(row)
                }
                
                student_data.append(data)
                
            except Exception as e:
                logger.warning(f"Error processing row {row.get('STT', 'unknown')}: {e}")
                continue
        
        logger.info(f"Processed {len(student_data)} students from Vietnamese format")
        return student_data
    
    @staticmethod
    def _process_english_format(df: pd.DataFrame) -> List[Dict]:
        """Process English format Excel file"""
        student_data = []
        
        for _, row in df.iterrows():
            try:
                # Extract StudentID
                student_id = str(row['StudentID']).strip()
                
                # Get student info
                full_name = str(row.get('Name', f'Student {student_id}')).strip()
                
                # Get learning metrics
                data = {
                    'student_id': student_id,
                    'full_name': full_name,
                    'class_id': str(row.get('LopID', '')).strip(),
                    'test_scores': float(row.get('test_scores', 0)),
                    'max_test_score': 10,
                    'assignment_completion_rate': float(row.get('assignment_completion_rate', 0)),
                    'access_count': int(row.get('access_count', 0)),
                    'max_access_count': 100,
                    'study_time_minutes': float(row.get('study_time_minutes', 0)),
                    'max_study_time': 1000,
                    'submission_timing_score': RealDataService._calculate_submission_timing(row)
                }
                
                student_data.append(data)
                
            except Exception as e:
                logger.warning(f"Error processing row for {row.get('StudentID', 'unknown')}: {e}")
                continue
        
        logger.info(f"Processed {len(student_data)} students from English format")
        return student_data
    
    @staticmethod
    def _process_export_format(df: pd.DataFrame) -> List[Dict]:
        """Process exported analysis format"""
        student_data = []

        # Normalize column names
        df.columns = [str(c).replace('\n', ' ').replace('   ', ' ').replace('  ', ' ').strip() for c in df.columns]

        col_map = {}
        for col in df.columns:
            c = col.lower()
            if 'mã sinh' in c: col_map['student_id'] = col
            elif 'họ và tên' in c: col_map['name'] = col
            elif 'điểm thi (gốc)' in c: col_map['test_scores'] = col
            elif 'tỷ lệ hoàn thành bt (gốc)' in c: col_map['assignment_completion_rate'] = col
            elif 'số lần truy cập (gốc)' in c: col_map['access_count'] = col
            elif 'thời gian học phút (gốc)' in c: col_map['study_time_minutes'] = col
            elif 'điểm thời điểm nộp (gốc)' in c: col_map['submission_timing_score'] = col

        if 'student_id' not in col_map:
            logger.error("Cannot find student ID column in export format")
            return []

        for _, row in df.iterrows():
            try:
                sid = str(row[col_map['student_id']]).strip()
                if not sid or sid == 'nan':
                    continue
                data = {
                    'student_id': sid,
                    'full_name': str(row.get(col_map.get('name', ''), f'Sinh viên {sid}')).strip(),
                    'test_scores': float(row.get(col_map.get('test_scores', ''), 0) or 0),
                    'max_test_score': 10,
                    'assignment_completion_rate': float(row.get(col_map.get('assignment_completion_rate', ''), 0) or 0),
                    'access_count': int(float(row.get(col_map.get('access_count', ''), 0) or 0)),
                    'max_access_count': 100,
                    'study_time_minutes': float(row.get(col_map.get('study_time_minutes', ''), 0) or 0),
                    'max_study_time': 1000,
                    'submission_timing_score': float(row.get(col_map.get('submission_timing_score', ''), 5.0) or 5.0),
                }
                student_data.append(data)
            except Exception as e:
                logger.warning(f"Error processing export row: {e}")
                continue

        logger.info(f"Processed {len(student_data)} students from export format")
        return student_data

    @staticmethod
    def _process_csv_format(df: pd.DataFrame) -> List[Dict]:
        """Process CSV format: STT,MSSV,Ho Ten,Lop,Khoa,Diem TB,Thoi Gian TB (h),Tham Gia (%),Nop Muon,..."""
        student_data = []
        max_diem = float(pd.to_numeric(df.get('Diem TB', pd.Series([10])), errors='coerce').max() or 10)
        max_time = float(pd.to_numeric(df.get('Thoi Gian TB (h)', pd.Series([5])), errors='coerce').max() or 5)

        for _, row in df.iterrows():
            try:
                mssv = str(row['MSSV']).strip()
                if not mssv or mssv == 'nan':
                    continue

                diem = float(str(row.get('Diem TB', 0)).replace(',', '.') or 0)
                thoi_gian_h = float(str(row.get('Thoi Gian TB (h)', 0)).replace(',', '.') or 0)
                tham_gia = float(str(row.get('Tham Gia (%)', 0)).replace(',', '.') or 0)
                nop_muon = int(float(str(row.get('Nop Muon', 0)).replace(',', '.') or 0))

                data = {
                    'student_id': mssv,
                    'full_name': str(row.get('Ho Ten', f'Sinh viên {mssv}')).strip(),
                    'class_id': str(row.get('Lop', '')).strip(),
                    'test_scores': round(diem / max_diem * 10, 2),
                    'max_test_score': 10,
                    'assignment_completion_rate': tham_gia / 100.0,
                    'access_count': int(tham_gia),
                    'max_access_count': 100,
                    'study_time_minutes': round(thoi_gian_h * 60, 1),
                    'max_study_time': round(max_time * 60, 1),
                    'submission_timing_score': 3.0 if nop_muon == 0 else min(10.0, 3.0 + nop_muon),
                }
                student_data.append(data)
            except Exception as e:
                logger.warning(f"Error processing CSV row: {e}")
                continue

        logger.info(f"Processed {len(student_data)} students from CSV format")
        return student_data

    @staticmethod
    def _calculate_submission_timing(row) -> float:
        """Calculate submission timing score from available data"""
        # If we have existing submission timing data, use it
        if 'submission_timing_score' in row and pd.notna(row['submission_timing_score']):
            return float(row['submission_timing_score'])
        
        # Otherwise, estimate based on other metrics
        # Students with higher completion rates tend to submit earlier
        completion_rate = float(row.get('TyLeHoanThanhBaiTap', row.get('assignment_completion_rate', 0.5)))
        
        if completion_rate >= 0.8:
            return 2.0  # Early submission
        elif completion_rate >= 0.6:
            return 4.0  # On time
        elif completion_rate >= 0.4:
            return 6.0  # Slightly late
        else:
            return 8.0  # Late submission
    
    @staticmethod
    def get_available_mssv_list() -> List[str]:
        """Get list of available MSSV for testing"""
        student_data = RealDataService.load_real_student_data()
        return [data['student_id'] for data in student_data]
    
    @staticmethod
    def get_student_info_by_mssv(mssv: str) -> Optional[Dict]:
        """Get student information by MSSV"""
        student_data = RealDataService.load_real_student_data()
        
        for data in student_data:
            if data['student_id'] == mssv:
                return data
        
        return None