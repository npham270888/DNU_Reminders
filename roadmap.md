# Development Roadmap - Hệ thống nhắc nhở học tập
*Dự án học tập/demo - Đơn giản, nhẹ, không production-ready*

## 🗓️ Development Timeline (6-8 tuần)

### **Week 1-2: Foundation Setup**
**Mục tiêu:** Cơ sở hạ tầng cơ bản
- 📁 Setup project structure
- 🔐 Simple login/register (không cần email verification)  
- 🗄️ Database design cơ bản (SQLite)
- 🎨 Basic HTML template với Bootstrap
- ✅ **Deliverable:** Login được, tạo user, connect database

### **Week 3-4: Core Functionality**  
**Mục tiêu:** CRUD cơ bản
- ➕ Add/Edit/Delete events manually
- 📅 Simple calendar view (table hoặc basic grid)
- 📋 List view các events
- 🏷️ Basic event types (Class/Assignment/Exam)
- ✅ **Deliverable:** Có thể quản lý events cơ bản

### **Week 5-6: Data Import**
**Mục tiêu:** Import từ file
- 📄 JSON file upload
- 🔧 Simple JSON parser 
- 📊 Import validation cơ bản
- 🗂️ View imported data
- ✅ **Deliverable:** Upload JSON và hiển thị được data

### **Week 7-8: Notification & Polish**
**Mục tiêu:** Hoàn thiện
- 🔔 Basic web notifications (browser alert)
- ⏰ Simple reminder logic
- 🎨 UI cleanup và responsive
- 🐛 Bug fixes
- ✅ **Deliverable:** Demo được full flow

## 🎯 Simplified Features (Chỉ làm cần thiết)

### **✅ Will Implement**
- User login (session-based, không JWT)
- Manual event CRUD  
- JSON file import
- Basic calendar display
- Simple reminder (popup alert)
- SQLite database
- Responsive design cơ bản

### **❌ Won't Implement** 
- API integration (quá phức tạp)
- Email notifications (cần SMTP setup)
- Real-time sync
- Advanced conflict resolution  
- User management system
- Production deployment
- Security hardening
- Performance optimization

## 🛠️ Tech Stack (Giữ tối giản)

**Frontend:**
- HTML/CSS/JavaScript vanilla
- Bootstrap 5 (CDN)
- Không framework JS phức tạp

**Backend:**  
- Python Flask (lightweight)
- SQLAlchemy ORM
- Session-based auth

**Database:**
- SQLite (file-based, dễ setup)
- Không cần migration tools

**Deployment:**
- Local development only
- Hoặc Heroku free tier (simple)

## 📋 Database Schema (Tối thiểu)

```sql
-- 3 tables chính
users: id, username, password, created_at
events: id, user_id, title, event_type, datetime, description, source
imports: id, user_id, filename, import_date, status
```

## 🔧 Development Approach

### **Keep It Simple:**
- Một file Python chính (app.py)  
- Templates trong thư mục /templates
- Static files trong /static
- Không microservices, không API complex

### **Quick & Dirty:**
- Hardcode một số config
- Basic error handling
- Minimal input validation
- Console logging thay vì proper logging

### **Demo Focus:**
- Làm để demo được core flow
- UI đẹp đủ dùng, không cần pixel perfect
- Data sample để demo
- Screenshots cho documentation

## 📚 Learning Outcomes

**Technical Skills:**
- Web development basics
- File upload handling  
- JSON processing
- Database operations
- Session management

**Project Skills:**
- Requirements analysis
- Simple project planning
- Basic testing
- Documentation

## 🚀 Success Criteria

**Minimum Success:**
- ✅ Login works
- ✅ Can add events manually  
- ✅ Can upload JSON file
- ✅ Calendar shows events
- ✅ Basic reminder works

**Bonus Success:**
- ✅ Mobile responsive
- ✅ Nice UI/UX
- ✅ Export data back to JSON
- ✅ Filter/search events

*Note: Đây là dự án học tập, focus vào việc hiểu concept và implement basic functionality rather than production quality.*

### 1. **Multi-Source Data Import**
- 📄 Import từ file JSON (lịch học, bài tập)
- 🔗 Kết nối API bên ngoài (Google Calendar, hệ thống trường)
- 📊 Sync tự động theo schedule
- ⚡ Manual sync khi cần thiết

### 2. **Event Management**
- ➕ CRUD operations cho sự kiện (Tạo/Đọc/Cập nhật/Xóa)
- 📚 Phân loại: Lịch học, Bài tập, Thi cử
- 🏷️ Gắn nhãn nguồn dữ liệu (JSON/API/Manual)
- 🔄 Conflict resolution khi trùng lặp

### 3. **Smart Reminder System**
- ⏰ Nhắc nhở đa mức độ (1 ngày, 1 giờ, 30 phút trước)
- 🔔 Thông báo trên web (popup/notification)
- 📧 Email reminder (optional)
- ⚙️ Cấu hình cá nhân hóa

### 4. **Calendar View**
- 📅 Hiển thị theo tuần/tháng
- 🎯 Highlight sự kiện quan trọng
- 🔍 Filter theo loại sự kiện
- 📱 Responsive design

## 📊 Data Management Features

### 5. **Data Source Control**
- 🎛️ Bật/tắt từng nguồn dữ liệu
- 🏆 Thiết lập độ ưu tiên nguồn
- 📈 Lịch sử sync và status
- ❌ Error logging và notification

### 6. **Export/Backup**
- 💾 Export dữ liệu ra JSON
- 🔄 Backup tự động
- 📤 Chia sẻ lịch (public link)

## 👤 User Management Features

### 7. **Authentication & Profile**
- 🔐 Đăng ký/đăng nhập đơn giản
- 👤 Profile management
- 🎓 Student code integration
- ⚙️ Settings và preferences

### 8. **Personalization**
- 🎨 Cấu hình giao diện
- 🔔 Tùy chỉnh thông báo
- 📲 Channel preferences (web/email)
- ⏰ Custom reminder timing

## 🛠️ Technical Features

### 9. **API Integration**
- 🔌 RESTful API endpoints
- 🔑 Authentication token system
- 📝 API documentation
- ⚡ Rate limiting

### 10. **Data Processing**
- 🧹 Data validation và sanitization
- 📋 Batch import processing
- 🔄 Real-time sync status
- 📊 Import success/failure tracking

## 🎯 MVP Features (Minimum Viable Product)

**Phase 1 - Essential:**
1. User registration/login
2. JSON file import
3. Basic event CRUD
4. Simple calendar view
5. Web notification

**Phase 2 - Enhanced:**
6. API integration
7. Email reminders
8. Advanced filtering
9. Export functionality

**Phase 3 - Advanced:**
10. Multi-source sync
11. Conflict resolution
12. Analytics dashboard

## 📋 Technical Stack Requirements

- **Frontend:** HTML/CSS/JavaScript (vanilla hoặc framework nhẹ)
- **Backend:** Python Flask hoặc Node.js Express
- **Database:** SQLite/PostgreSQL với JSON support
- **Import:** JSON parser, API client libraries
- **Notification:** Web notifications, email service

## 🎨 UX/UI Focus

- **Simplicity:** Interface sạch, dễ hiểu
- **Speed:** Load nhanh, sync nhanh
- **Reliability:** Ít bug, data consistent
- **Accessibility:** Responsive, keyboard navigation
- **Feedback:** Clear status messages và progress indicators