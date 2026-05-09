import os, sys, subprocess

# Change to the project directory using Python (handles Unicode paths)
project_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "Nguyễn Minh Phúc - Xây dựng mô hình dự đoán mức độ hoàn thành của sinh viên"
)

python = r"C:\student_venv\Scripts\python.exe"

print(f"Starting app from: {project_dir}")
print("Access at: http://localhost:5000")

subprocess.run([python, "app_new.py"], cwd=project_dir)
