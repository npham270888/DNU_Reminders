# Tính năng Đồng bộ với hệ thống DNU

## Tổng quan
Tính năng này cho phép người dùng đồng bộ lịch học từ hệ thống DNU (Đại học Đại Nam) vào ứng dụng DNU Reminder một cách tự động.

## Cách hoạt động

### 1. Đăng nhập với DNU
- Người dùng cần đăng nhập với token session DNU
- Token được lưu trong phiên làm việc
- Hệ thống tự động xác minh kết nối với DNU

### 2. Đồng bộ lịch học
- Chọn tuần học cần đồng bộ (1-55)
- Hệ thống gọi API DNU: `https://ttsinhvien.dainam.edu.vn/TraCuuLichHoc/ThongTinLichHocTuan`
- Payload: `HocKy=1&NamHoc=2025&ChuyenNganh=0&Dothoc=0&Tuan={week}`

### 3. Parse dữ liệu HTML
Hệ thống sử dụng regex để parse bảng lịch học và trích xuất:

- **Tên học phần**: Nội dung trong span đầu tiên có độ dài > 10 ký tự
- **Phòng học**: Nội dung chứa "P." hoặc "Phòng"
- **Tiết học**: Pattern "Tiết: X - Y" để tính thời gian
- **Thời gian**: Nội dung trong dấu ngoặc với dấu gạch ngang
- **Giảng viên**: Nội dung bắt đầu bằng "GV:"

### 4. Tính toán thời gian
- Mỗi tiết = 60 phút (1 giờ)
- **Tiết 1-5 (Sáng)**: 7:00 - 11:00
- **Tiết 6-10 (Chiều)**: 13:00 - 17:00
- Công thức:
  - Tiết 1-5: `7 + (tiết - 1)` giờ
  - Tiết 6-10: `13 + (tiết - 6)` giờ

### 5. Tạo sự kiện
- Event type: "Class"
- Source: "DNU API"
- Title: Tên học phần
- Description: Thông tin chi tiết được nối bằng " | "
- Datetime: Thời gian bắt đầu của tiết học

## Ví dụ dữ liệu

### HTML Input:
```html
<span>C&#244;ng nghệ th&#244;ng tin trong chuyển đổi số</span>
<span>P.602 -GD1</span>
<span>Tiết: 6 - 10</span>
<span>(04/08/2025 - 24/08/2025)</span>
<span>GV: Nguyễn Th&#225;i Kh&#225;nh</span>
```

### Event được tạo:
- **Title**: Công nghệ thông tin trong chuyển đổi số
- **Type**: Class
- **Time**: 13:00 (tiết 6)
- **Description**: Học phần: Công nghệ thông tin trong chuyển đổi số | Phòng: P.602 -GD1 | Giảng viên: GV: Nguyễn Thái Khánh | Thời gian: (04/08/2025 - 24/08/2025) | Tuần: X, Buổi: CHIỀU

## Lưu ý quan trọng

1. **Chỉ tạo sự kiện cho ô có nội dung**: Hệ thống kiểm tra pattern "Tiết:" để xác định ô có lịch học
2. **Tính toán thời gian chính xác**: Dựa trên số tiết học thực tế
3. **Thông tin chi tiết**: Tự động trích xuất và phân loại thông tin
4. **Xử lý lỗi**: Rollback database nếu có lỗi trong quá trình parse

## Cài đặt dependencies

```bash
pip install beautifulsoup4==4.12.2
```

## Sử dụng

1. Đăng nhập với token DNU
2. Vào Dashboard → Click "Đồng bộ với hệ thống DNU"
3. Chọn tuần học
4. Click "Đồng bộ lịch học"
5. Kiểm tra kết quả trong Events

## Troubleshooting

- **Lỗi kết nối**: Kiểm tra token DNU và kết nối mạng
- **Không tìm thấy bảng**: Kiểm tra response HTML từ DNU
- **Lỗi parse**: Kiểm tra format HTML có thay đổi không
- **Thời gian sai**: Kiểm tra logic tính toán tiết học
