# Hệ thống Phân tích và Dự đoán Mức độ Hoàn thành Học tập

Đồ án tốt nghiệp — Xây dựng mô hình dự đoán mức độ hoàn thành của sinh viên sử dụng Random Forest và Neural Network.

---

## Cách chạy nhanh

### Windows

1. Double-click `RUN_APP.bat`
2. Truy cập: http://localhost:5001
3. Đăng nhập bằng tài khoản bên dưới

### macOS

```bash
chmod +x RUN_APP_MAC.sh
./RUN_APP_MAC.sh
```

### Thủ công (mọi hệ điều hành)

```bash
# Bước 1: Tạo môi trường ảo
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# Bước 2: Cài dependencies
pip install -r requirements.txt

# Bước 3: Chạy app
python app_new.py
```

---

## Tài khoản đăng nhập

| Loại | Tên đăng nhập | Mật khẩu |
|------|--------------|----------|
| Giảng viên | teacher001 | teacher123 |
| Giảng viên | teacher002 | teacher123 |
| Admin | admin | admin123 |
| Sinh viên | MSSV thật (vd: 122001292) | 123456 |

---

## Tính năng chính

### Giảng viên
- Dashboard tổng quan lớp học với thống kê và biểu đồ
- Tìm kiếm, lọc, sắp xếp danh sách sinh viên
- Xem chi tiết phân tích từng sinh viên
- So sánh tối đa 4 sinh viên cạnh nhau
- Báo cáo tổng kết lớp (có thể in)
- Thống kê với biểu đồ trực quan (histogram, radar, doughnut)
- Import dữ liệu từ Excel/CSV
- Xuất báo cáo Excel/CSV
- Quản lý file Excel (sort, filter, thống kê cột)
- Giải thích mô hình ML (Feature importance, Confusion matrix, CV scores)
- Advanced Analytics: Clustering, Anomaly Detection, Model Comparison, Real-time Stats

### Sinh viên
- Dashboard cá nhân với mức độ hoàn thành và gợi ý học tập
- Phân tích chi tiết với biểu đồ radar
- Dự đoán từ Random Forest và Neural Network
- Lịch sử phân tích

---

## Mô hình Machine Learning

| Mô hình | Mô tả |
|---------|-------|
| Random Forest | 100 cây quyết định, 5-Fold Cross Validation |
| Neural Network | MLPClassifier, validation accuracy ~90% |
| Ensemble | Kết hợp RF + NN |

**5 đặc trưng đầu vào:**
- Điểm kiểm tra (30%)
- Tỷ lệ hoàn thành bài tập (25%)
- Tần suất truy cập (15%)
- Thời gian học (15%)
- Thời điểm nộp bài (15%)

**3 lớp đầu ra:** Thấp / Trung bình / Cao

---

## Cấu trúc dự án

```
├── app_new.py              # Entry point
├── config.py               # Cấu hình
├── requirements.txt        # Dependencies
├── RUN_APP.bat             # Script chạy Windows
├── RUN_APP_MAC.sh          # Script chạy macOS
├── src/
│   ├── core/               # Logic phân tích và ML
│   ├── models/             # Data models
│   ├── services/           # Data services
│   ├── utils/              # Utilities
│   └── web/                # Flask routes và app
│       └── routes/         # auth, student, teacher, advanced
├── templates/              # HTML templates
├── static/                 # CSS, JS, images
├── data/                   # JSON data storage
├── models/                 # Saved ML models
└── logs/                   # Application logs
```

---

## Yêu cầu hệ thống

- Python 3.11+
- RAM: 4GB+
- Disk: 500MB+

## Dependencies chính

```
flask, flask-wtf, numpy, pandas, scikit-learn, openpyxl, redis
```
"# DoAnTotNghiep" 
"# DoAnTotNghiep" 
