# DNU Reminder - Hệ thống nhắc nhở học tập

Hệ thống quản lý và nhắc nhở lịch học, bài tập, thi cử cho sinh viên Đại học Đà Nẵng.

## 🚀 Tính năng chính

- **Quản lý sự kiện**: Tạo, sửa, xóa lịch học, bài tập, thi cử
- **Import từ JSON**: Nhập dữ liệu từ file JSON
- **Lịch sự kiện**: Xem sự kiện theo lịch tháng
- **Dashboard**: Tổng quan sự kiện sắp tới
- **Export dữ liệu**: Xuất dữ liệu ra file JSON
- **Giao diện responsive**: Hỗ trợ mobile và desktop

## 🛠️ Công nghệ sử dụng

- **Backend**: Python Flask
- **Database**: SQLite với SQLAlchemy ORM
- **Frontend**: HTML/CSS/JavaScript, Bootstrap 5
- **Authentication**: Flask-Login với session-based auth

## 📋 Yêu cầu hệ thống

- Python 3.7+
- pip (Python package manager)

## 🚀 Cài đặt và chạy

### 1. Clone repository
```bash
git clone <repository-url>
cd DNU_Reminder
```

### 2. Tạo môi trường ảo (khuyến nghị)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 4. Chạy ứng dụng
```bash
python app.py
```

Ứng dụng sẽ chạy tại: http://localhost:5000

## 📱 Hướng dẫn sử dụng

### Đăng ký và đăng nhập
1. Truy cập http://localhost:5000
2. Click "Đăng ký" để tạo tài khoản mới
3. Đăng nhập với tài khoản vừa tạo

### Tạo sự kiện mới
1. Đăng nhập vào hệ thống
2. Click "Tạo sự kiện mới" từ Dashboard
3. Điền thông tin sự kiện:
   - **Tiêu đề**: Tên sự kiện
   - **Loại**: Lịch học, Bài tập, hoặc Thi cử
   - **Thời gian**: Ngày và giờ diễn ra
   - **Mô tả**: Chi tiết sự kiện (không bắt buộc)

### Import từ JSON
1. Chuẩn bị file JSON với định dạng:
```json
[
  {
    "title": "Tên sự kiện",
    "event_type": "Class|Assignment|Exam",
    "datetime": "2024-01-15T14:30:00",
    "description": "Mô tả sự kiện"
  }
]
```

2. Vào trang Import
3. Chọn file JSON và click "Import sự kiện"

### Xem lịch
1. Vào trang "Lịch" để xem sự kiện theo tháng
2. Click vào các chấm màu để xem chi tiết sự kiện
3. Sử dụng nút mũi tên để chuyển tháng

## 📊 Cấu trúc database

### Bảng Users
- `id`: ID người dùng
- `username`: Tên đăng nhập
- `password`: Mật khẩu (đã hash)
- `created_at`: Ngày tạo tài khoản

### Bảng Events
- `id`: ID sự kiện
- `user_id`: ID người dùng sở hữu
- `title`: Tiêu đề sự kiện
- `event_type`: Loại sự kiện (Class/Assignment/Exam)
- `datetime`: Thời gian diễn ra
- `description`: Mô tả chi tiết
- `source`: Nguồn dữ liệu (Manual/JSON/API)
- `created_at`: Ngày tạo sự kiện

### Bảng Imports
- `id`: ID import
- `user_id`: ID người dùng
- `filename`: Tên file import
- `import_date`: Ngày import
- `status`: Trạng thái import

## 🔧 Cấu hình

### Thay đổi secret key
Trong file `app.py`, thay đổi:
```python
app.config['SECRET_KEY'] = 'your-secret-key-here'
```

### Thay đổi database
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
```

## 📁 Cấu trúc thư mục

```
DNU_Reminder/
├── app.py                 # Ứng dụng chính
├── requirements.txt       # Dependencies
├── README.md             # Hướng dẫn
├── templates/            # HTML templates
│   ├── base.html         # Template cơ sở
│   ├── index.html        # Trang chủ
│   ├── login.html        # Đăng nhập
│   ├── register.html     # Đăng ký
│   ├── dashboard.html    # Dashboard
│   ├── events.html       # Danh sách sự kiện
│   ├── new_event.html    # Tạo sự kiện mới
│   ├── edit_event.html   # Sửa sự kiện
│   ├── import.html       # Import JSON
│   └── calendar.html     # Lịch sự kiện
└── dnu_reminder.db      # Database SQLite (tự tạo)
```

## 🧪 Testing

### Tạo dữ liệu mẫu
1. Đăng nhập vào hệ thống
2. Tạo một vài sự kiện mẫu
3. Test các chức năng CRUD

### Test import JSON
1. Tải file mẫu từ trang Import
2. Sửa đổi file theo ý muốn
3. Upload lại để test

## 🚀 Deployment

### Local development
```bash
python app.py
```

### Production (khuyến nghị)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Tạo Pull Request

## 📝 License

Dự án học tập - Không sử dụng cho mục đích thương mại.

## 📞 Hỗ trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra console logs
2. Xem file database có được tạo không
3. Kiểm tra dependencies đã cài đúng chưa

## 🔮 Roadmap

- [ ] Email notifications
- [ ] API integration
- [ ] Mobile app
- [ ] Advanced filtering
- [ ] Conflict resolution
- [ ] Multi-language support
