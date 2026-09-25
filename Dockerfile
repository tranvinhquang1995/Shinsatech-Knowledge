# Sử dụng Python image bản nhẹ nhất để tối ưu dung lượng
FROM python:3.11-slim

# Set thư mục làm việc
WORKDIR /app

# Copy file requirements và cài đặt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ Source code vào Container
COPY . .

# Expose port mặc định của Streamlit
EXPOSE 8501

# Lệnh boot hệ thống
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
