from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import json
import os
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pickle
import os
from dotenv import load_dotenv
from os.path import join, dirname

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Google Calendar API configuration
GOOGLE_CLIENT_SECRETS_FILE = os.environ.get("GOOGLE_CLIENT_SECRETS_FILE")
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Cho phép OAuth2 HTTP trong development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dnu_reminder.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    notification_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    events = db.relationship('Event', backref='user', lazy=True)
    imports = db.relationship('Import', backref='user', lazy=True)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # Class, Assignment, Exam
    datetime = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text)
    source = db.Column(db.String(50), default='Manual')  # JSON, API, Manual
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Import(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    import_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(50), default='Success')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('register.html')
            
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return render_template('register.html')
        
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            notification_enabled=True
        )
        db.session.add(user)
        db.session.commit()
        
        # Send welcome email
        welcome_subject = "Welcome to DNU Reminder!"
        welcome_content = f"""
        <html>
            <body>
                <h2>Chào mừng đến với DNU Reminder!</h2>
                <p>Xin chào {username},</p>
                <p>Cảm ơn bạn đã đăng ký sử dụng DNU Reminder. 
                Từ giờ bạn sẽ nhận được các thông báo về:</p>
                <ul>
                    <li>Lịch học sắp diễn ra</li>
                    <li>Lịch thi sắp đến</li>
                    <li>Các sự kiện quan trọng khác</li>
                </ul>
                <p>Chúc bạn học tập tốt!</p>
            </body>
        </html>
        """
        send_email_notification(email, welcome_subject, welcome_content)
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        session_token = request.form.get('session_token', '').strip()
        # Normalize token: accept either raw value or full "ASP.NET_SessionId=..."
        if session_token.lower().startswith('asp.net_sessionid='):
            session_token = session_token.split('=', 1)[-1].strip()
        else:
            session_token = "3jjabcxyzeitppf52s0jne1d"

        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            # Local login success
            login_user(user)

            # Optional DNU token verification and storage
            if session_token:
                try:
                    resp = requests.post(
                        'https://ttsinhvien.dainam.edu.vn/DangNhap/SaveToken',
                        headers={'Cookie': f'ASP.NET_SessionId={session_token}'},
                        data={
                            'ASP.NET_SessionId': session_token,
                            'Role': '0',
                            'UserName': username,
                            'Password': password
                        },
                        allow_redirects=False,
                        timeout=10
                    )
                    location = resp.headers.get('Location', '')
                    if '/DangNhap/Login?message=' in location:
                        flash('Đăng nhập DNU thất bại. Vui lòng kiểm tra lại thông tin hoặc token.')
                    else:
                        session['dnu_session_cookie'] = session_token
                        session['dnu_session_verified_at'] = datetime.now(timezone.utc).isoformat()
                        flash('Kết nối hệ thống DNU thành công. Token đã được lưu trong phiên.')
                except requests.RequestException as e:
                    flash(f'Lỗi kết nối tới hệ thống DNU: {str(e)}')

            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    # Attempt to sign out from DNU if session token exists
    token = session.get('dnu_session_cookie')
    if token:
        try:
            resp = requests.get(
                'https://ttsinhvien.dainam.edu.vn/DangNhap/Signout',
                headers={'Cookie': f'ASP.NET_SessionId={token}'},
                allow_redirects=False,
                timeout=10
            )
            location = resp.headers.get('Location', '')
            if '/DangNhap/Login' in location:
                flash('Đã đăng xuất tài khoản. Phiên DNU cũng đã được đăng xuất.')
        except requests.RequestException:
            pass
        finally:
            session.pop('dnu_session_cookie', None)
            session.pop('dnu_session_verified_at', None)
    else:
        flash('Đã đăng xuất tài khoản. Phiên DNU đăng xuất thất bại.')
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    events = Event.query.filter_by(user_id=current_user.id).order_by(Event.datetime).all()
    # Convert events to serializable format for consistency
    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'event_type': event.event_type,
            'datetime': event.datetime,
            'description': event.description,
            'source': event.source
        })
    return render_template('dashboard.html', events=events_data)

@app.route('/events')
@login_required
def events():
    events = Event.query.filter_by(user_id=current_user.id).order_by(Event.datetime).all()
    # Convert events to serializable format for consistency
    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'event_type': event.event_type,
            'datetime': event.datetime,
            'description': event.description,
            'source': event.source
        })
    return render_template('events.html', events=events_data)

@app.route('/events/new', methods=['GET', 'POST'])
@login_required
def new_event():
    if request.method == 'POST':
        title = request.form['title']
        event_type = request.form['event_type']
        datetime_str = request.form['datetime']
        description = request.form['description']
        
        event_datetime = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
        
        event = Event(
            user_id=current_user.id,
            title=title,
            event_type=event_type,
            datetime=event_datetime,
            description=description,
            source='Manual'
        )
        
        db.session.add(event)
        db.session.commit()
        
        flash('Event created successfully!')
        return redirect(url_for('events'))
    
    return render_template('new_event.html')

@app.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.user_id != current_user.id:
        flash('Access denied')
        return redirect(url_for('events'))
    
    if request.method == 'POST':
        event.title = request.form['title']
        event.event_type = request.form['event_type']
        event.datetime = datetime.strptime(request.form['datetime'], '%Y-%m-%dT%H:%M')
        event.description = request.form['description']
        
        db.session.commit()
        flash('Event updated successfully!')
        return redirect(url_for('events'))
    
    # Convert event to serializable format for consistency
    event_data = {
        'id': event.id,
        'title': event.title,
        'event_type': event.event_type,
        'datetime': event.datetime,
        'description': event.description,
        'source': event.source,
        'created_at': event.created_at
    }
    
    return render_template('edit_event.html', event=event_data)

@app.route('/events/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.user_id != current_user.id:
        flash('Access denied')
        return redirect(url_for('events'))
    
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully!')
    return redirect(url_for('events'))

@app.route('/import', methods=['GET', 'POST'])
@login_required
def import_events():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        if file and file.filename.endswith('.json'):
            try:
                data = json.load(file)
                imported_count = 0
                
                # Create import record
                import_record = Import(
                    user_id=current_user.id,
                    filename=file.filename
                )
                db.session.add(import_record)
                
                # Process events from JSON
                if isinstance(data, list):
                    for event_data in data:
                        if all(key in event_data for key in ['title', 'event_type', 'datetime']):
                            try:
                                event_datetime = datetime.fromisoformat(event_data['datetime'])
                                event = Event(
                                    user_id=current_user.id,
                                    title=event_data['title'],
                                    event_type=event_data['event_type'],
                                    datetime=event_datetime,
                                    description=event_data.get('description', ''),
                                    source='JSON'
                                )
                                db.session.add(event)
                                imported_count += 1
                            except ValueError:
                                continue
                
                db.session.commit()
                flash(f'Successfully imported {imported_count} events from {file.filename}')
                
            except json.JSONDecodeError:
                flash('Invalid JSON file')
            except Exception as e:
                flash(f'Error importing file: {str(e)}')
        else:
            flash('Please select a valid JSON file')
        
        return redirect(url_for('import_events'))
    
    imports = Import.query.filter_by(user_id=current_user.id).order_by(Import.import_date.desc()).all()
    # Convert imports to serializable format for consistency
    imports_data = []
    for import_record in imports:
        imports_data.append({
            'id': import_record.id,
            'filename': import_record.filename,
            'import_date': import_record.import_date,
            'status': import_record.status
        })
    return render_template('import.html', imports=imports_data)

@app.route('/calendar')
@login_required
def calendar():
    events = Event.query.filter_by(user_id=current_user.id).all()
    # Convert events to serializable format
    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'event_type': event.event_type,
            'datetime': event.datetime.isoformat(),
            'description': event.description,
            'source': event.source,
            'created_at': event.created_at.isoformat() if event.created_at else None
        })
    return render_template('calendar.html', events=events_data)

@app.route('/api/events')
@login_required
def api_events():
    events = Event.query.filter_by(user_id=current_user.id).all()
    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'event_type': event.event_type,
            'datetime': event.datetime.isoformat(),
            'description': event.description,
            'source': event.source
        })
    return jsonify(events_data)

@app.route('/debug/events')
@login_required
def debug_events():
    """Debug route to check events in database"""
    events = Event.query.filter_by(user_id=current_user.id).all()
    events_info = []
    for event in events:
        events_info.append({
            'id': event.id,
            'title': event.title,
            'event_type': event.event_type,
            'datetime': event.datetime.isoformat(),
            'datetime_obj': str(event.datetime),
            'day': event.datetime.day,
            'month': event.datetime.month,
            'year': event.datetime.year,
            'description': event.description,
            'source': event.source
        })
    return jsonify({
        'total_events': len(events),
        'events': events_info
    })

@app.route('/export')
@login_required
def export_events():
    events = Event.query.filter_by(user_id=current_user.id).all()
    events_data = []
    for event in events:
        events_data.append({
            'title': event.title,
            'event_type': event.event_type,
            'datetime': event.datetime.isoformat(),
            'description': event.description,
            'source': event.source
        })
    
    response = jsonify(events_data)
    response.headers['Content-Disposition'] = f'attachment; filename=events_{current_user.username}_{datetime.now().strftime("%Y%m%d")}.json'
    return response

@app.route('/reminders')
@login_required
def reminders():
    """Check for upcoming events and show reminders"""
    now = datetime.now()
    upcoming_events = []
    
    # Get events in next 24 hours
    tomorrow = now + timedelta(days=1)
    events = Event.query.filter_by(user_id=current_user.id).filter(
        Event.datetime >= now,
        Event.datetime <= tomorrow
    ).order_by(Event.datetime).all()
    
    for event in events:
        time_diff = event.datetime - now
        if time_diff.total_seconds() > 0:
            # Add to upcoming events list for display
            upcoming_events.append({
                'event': {
                    'id': event.id,
                    'title': event.title,
                    'event_type': event.event_type,
                    'datetime': event.datetime,
                    'description': event.description,
                    'source': event.source
                },
                'time_until': {
                    'days': time_diff.days,
                    'seconds': time_diff.seconds
                }
            })
            
            # Send email reminders based on time thresholds
            hours_until = time_diff.total_seconds() / 3600
            
            # Only send reminders if user has notifications enabled
            if current_user.notification_enabled and current_user.email:
                # Send reminder 24 hours before
                if 23.5 <= hours_until <= 24.5:
                    send_event_reminder(event, current_user)
                    flash('Đã gửi email nhắc nhở cho sự kiện sắp diễn ra trong 24 giờ tới')
                
                # Send reminder 2 hours before
                elif 1.5 <= hours_until <= 2.5:
                    send_event_reminder(event, current_user)
                    flash('Đã gửi email nhắc nhở cho sự kiện sắp diễn ra trong 2 giờ tới')
                
                # Send reminder 30 minutes before
                elif 0.45 <= hours_until <= 0.75:
                    send_event_reminder(event, current_user)
                    flash('Đã gửi email nhắc nhở cho sự kiện sắp diễn ra trong 30 phút tới')
    
    return render_template('reminders.html', upcoming_events=upcoming_events)

@app.route('/dnu-sync', methods=['GET', 'POST'])
@login_required
def dnu_sync():
    """Sync with DNU system to get class schedule and exam schedule"""
    if request.method == 'POST':
        # Check if user has DNU session token
        dnu_token = session.get('dnu_session_cookie')
        if not dnu_token:
            flash('Vui lòng đăng nhập với DNU trước khi đồng bộ!', 'error')
            return redirect(url_for('dashboard'))
        
        try:
            events_created = 0
            headers = {
                'Cookie': f'ASP.NET_SessionId={dnu_token}',
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            # 1. Sync class schedule
            week = request.form.get('week', '5')
            class_payload = {
                'HocKy': '1',
                'NamHoc': '2025',
                'ChuyenNganh': '0',
                'Dothoc': '0',
                'Tuan': week
            }
            
            class_response = requests.post(
                'https://ttsinhvien.dainam.edu.vn/TraCuuLichHoc/ThongTinLichHocTuan',
                data=class_payload,
                headers=headers,
                timeout=30
            )
            
            class_events = 0
            if class_response.status_code == 200:
                soup = BeautifulSoup(class_response.text, 'html.parser')
                schedule_table = soup.find('table', class_='table table-bordered table-condensed')
                
                if schedule_table:
                    class_events = parse_dnu_schedule(schedule_table, current_user.id, week)
                    events_created += class_events
            
            # 2. Sync exam schedule
            exam_payload = {
                'HocKy': '1',
                'NamHoc': '2025',
                'ChuyenNganh': '0',
                'Dothoc': '0',
                'LoaiThi': '-1'
            }
            
            exam_response = requests.post(
                'https://ttsinhvien.dainam.edu.vn/TraCuuLichThi/ThongTinLichThi',
                data=exam_payload,
                headers=headers,
                timeout=30
            )
            
            exam_events = 0
            if exam_response.status_code == 200:
                soup = BeautifulSoup(exam_response.text, 'html.parser')
                exam_table = soup.find('table', {'id': 'ctl00_ContentCP_ctl00_gvDiem'})
                
                if exam_table:
                    exam_events = parse_dnu_exam_schedule(exam_table, current_user.id)
                    events_created += exam_events
            
            # Show success message with both types of events
            if events_created > 0:
                flash(f'Đồng bộ thành công! Đã tạo {class_events} sự kiện lớp học và {exam_events} lịch thi.', 'success')
            else:
                flash('Không tìm thấy sự kiện nào để đồng bộ.', 'warning')
                
        except requests.RequestException as e:
            flash(f'Lỗi kết nối: {str(e)}', 'error')
        except Exception as e:
            flash(f'Lỗi xử lý: {str(e)}', 'error')
    
    return render_template('dnu_sync.html')

def parse_dnu_exam_schedule(table, user_id):
    """Parse DNU exam schedule table and create exam events"""
    events_created = 0
    try:
        # Find all rows in tbody
        rows = table.find_all('tr')
        
        # Lấy header để xác định vị trí các cột
        header_row = rows[0]
        headers = header_row.find_all('th')
        
        # Tạo mapping giữa tên cột và index
        column_indices = {}
        for i, header in enumerate(headers):
            header_text = header.get_text(strip=True).lower()
            if 'tên học phần' in header_text:
                column_indices['subject'] = i
            elif 'ngày thi' in header_text:
                column_indices['date'] = i
            elif 'giờ thi' in header_text:
                column_indices['time'] = i
            elif 'phòng thi' in header_text:
                column_indices['room'] = i
            elif 'hình thức' in header_text:
                column_indices['type'] = i
            elif 'lần thi' in header_text:
                column_indices['attempt'] = i
            elif 'đợt thi' in header_text:
                column_indices['period'] = i
            elif 'ca thi' in header_text:
                column_indices['shift'] = i
            elif 'ghi chú' in header_text:
                column_indices['note'] = i

        # Xử lý từng dòng dữ liệu (bỏ qua dòng header)
        for row in rows[1:]:
            columns = row.find_all('td')
            if len(columns) >= len(column_indices):
                try:
                    # Extract exam information using column mapping
                    subject = columns[column_indices['subject']].get_text(strip=True)
                    exam_date_str = columns[column_indices['date']].get_text(strip=True)
                    exam_time = columns[column_indices['time']].get_text(strip=True)
                    exam_room = columns[column_indices['room']].get_text(strip=True)
                    exam_type = columns[column_indices['type']].get_text(strip=True)
                    exam_attempt = columns[column_indices['attempt']].get_text(strip=True)
                    exam_period = columns[column_indices['period']].get_text(strip=True)
                    exam_note = columns[column_indices['note']].get_text(strip=True) if 'note' in column_indices else ""
                    exam_shift = columns[column_indices['shift']].get_text(strip=True) if 'shift' in column_indices else ""

                    # Bỏ qua nếu không có thông tin môn thi hoặc ngày thi
                    if not subject or not exam_date_str:
                        continue

                    # Parse date and time
                    exam_date = datetime.strptime(exam_date_str, '%d/%m/%Y')
                    
                    # Parse time from "7 giờ 00" or "14 giờ 00" format
                    hour = int(exam_time.split()[0])
                    exam_datetime = exam_date.replace(hour=hour, minute=0)

                    # Create event title
                    event_title = f"Thi {subject}"

                    # Create event description
                    description_parts = [
                        f"Môn thi: {subject}",
                        f"Lần thi: {exam_attempt}",
                        f"Đợt thi: {exam_period}"
                    ]
                    
                    if exam_room.strip():
                        description_parts.append(f"Phòng thi: {exam_room}")
                    if exam_type.strip():
                        description_parts.append(f"Hình thức: {exam_type}")
                    if exam_shift.strip():
                        description_parts.append(f"Ca thi: {exam_shift}")
                    if exam_note.strip():
                        description_parts.append(f"Ghi chú: {exam_note}")

                    description = " | ".join(description_parts)

                    # Create event
                    event = Event(
                        user_id=user_id,
                        title=event_title,
                        event_type='Exam',
                        datetime=exam_datetime,
                        description=description,
                        source='DNU API'
                    )

                    db.session.add(event)
                    events_created += 1

                except (ValueError, IndexError) as e:
                    print(f"Error parsing exam row: {e}")
                    continue

        db.session.commit()

    except Exception as e:
        print(f"Error parsing exam schedule: {e}")
        db.session.rollback()

    return events_created

def send_email_notification(user_email, subject, content):
    """Send email notification to user"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = user_email
        msg['Subject'] = subject

        # Add body
        msg.attach(MIMEText(content, 'html'))

        # Create server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        
        # Login
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        # Send email
        server.send_message(msg)
        
        # Close connection
        server.quit()
        
        print(f"Email sent successfully to {user_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def send_event_reminder(event, user):
    """Send reminder email for an event"""
    if not user.notification_enabled or not user.email:
        return False
    
    # Format event time
    event_time = event.datetime.strftime('%H:%M')
    event_date = event.datetime.strftime('%d/%m/%Y')
    
    # Create email subject based on event type
    if event.event_type == 'Exam':
        subject = f"Nhắc nhở: Lịch thi {event.title} - {event_date}"
    else:
        subject = f"Nhắc nhở: {event.title} - {event_date}"
    
    # Create email content
    content = f"""
    <html>
        <body>
            <h2>{event.title}</h2>
            <p><strong>Thời gian:</strong> {event_time} ngày {event_date}</p>
            <p><strong>Loại sự kiện:</strong> {event.event_type}</p>
            <p><strong>Chi tiết:</strong></p>
            <p>{event.description.replace('|', '<br>')}</p>
            <hr>
            <p><small>Email này được gửi tự động từ hệ thống DNU Reminder. 
            Vui lòng không trả lời email này.</small></p>
        </body>
    </html>
    """
    
    return send_email_notification(user.email, subject, content)

def check_and_send_reminders():
    """Check for upcoming events and send reminders"""
    now = datetime.now()
    reminder_window = now + timedelta(hours=24)  # Nhắc trước 24 giờ
    
    # Lấy các sự kiện sắp diễn ra trong 24 giờ tới
    upcoming_events = Event.query.filter(
        Event.datetime > now,
        Event.datetime <= reminder_window
    ).all()
    
    for event in upcoming_events:
        user = User.query.get(event.user_id)
        if user and user.notification_enabled:
            # Tính thời gian còn lại đến sự kiện
            time_until = event.datetime - now
            
            # Gửi nhắc nhở cho các mốc thời gian khác nhau
            if timedelta(hours=23) <= time_until <= timedelta(hours=24):  # Nhắc trước 24h
                send_event_reminder(event, user)
            elif timedelta(hours=1) <= time_until <= timedelta(hours=2):   # Nhắc trước 2h
                send_event_reminder(event, user)
            elif timedelta(minutes=30) <= time_until <= timedelta(minutes=31): # Nhắc trước 30p
                send_event_reminder(event, user)

def parse_dnu_schedule(table, user_id, week):
    """Parse DNU schedule table and create events using regex"""
    import re
    events_created = 0
    
    try:
        # Find all rows in tbody
        rows = table.find('tbody').find_all('tr')
        
        # Tính toán ngày cho tuần học dựa vào tuần 5 là mốc (18/8/2025)
        base_week = 5  # Tuần 5 là tuần tham chiếu
        base_date = datetime(2025, 8, 18)  # Tuần 5 bắt đầu từ 18/8/2025
        
        # Tính số tuần chênh lệch so với tuần 5
        week_diff = int(week) - base_week
        
        # Tính ngày bắt đầu của tuần cần tìm
        week_start = base_date + timedelta(weeks=week_diff)
        
        # Debug log
        print(f"Tuần {week} bắt đầu từ: {week_start.strftime('%d/%m/%Y')}")
        
        for row in rows:
            # Get session type (SÁNG/CHIỀU)
            session_cell = row.find('td')
            if not session_cell:
                continue
                
            session_text = session_cell.get_text(strip=True)
            if 'SÁNG' in session_text:
                session = 'SÁNG'
            elif 'CHIỀU' in session_text:
                session = 'CHIỀU'
            else:
                continue
            
            # Check each day column (Monday to Sunday)
            day_cells = row.find_all('td')[1:8]  # Skip first column (session)
            
            for day_idx, cell in enumerate(day_cells):
                # Use regex to find all spans with meaningful content
                cell_html = str(cell)
                
                # Pattern to match course information spans
                # Look for spans that contain course details
                course_pattern = r'<span[^>]*>([^<]+)</span>'
                course_matches = re.findall(course_pattern, cell_html)
                
                # Filter out empty or meaningless content
                meaningful_content = [match.strip() for match in course_matches if match.strip() and len(match.strip()) > 2]
                
                if meaningful_content and len(meaningful_content) >= 3:
                    # Check if this contains lesson information (look for "Tiết:" pattern)
                    lesson_pattern = r'Tiết:\s*(\d+)\s*-\s*(\d+)'
                    lesson_match = re.search(lesson_pattern, cell_html)
                    
                    if lesson_match:
                        # This is a valid course cell
                        start_period = int(lesson_match.group(1))
                        end_period = int(lesson_match.group(2))
                        
                        # Calculate time based on periods
                        # Each period is 60 minutes (1 hour)
                        # Tiết 1-5: 7:00 - 11:00 (sáng)
                        # Tiết 6-10: 13:00 - 17:00 (chiều)
                        if start_period <= 5:
                            # Morning session (7:00 - 11:00)
                            period_start_hour = 7 + (start_period - 1)
                        else:
                            # Afternoon session (13:00 - 17:00)
                            period_start_hour = 13 + (start_period - 6)
                        
                        period_start_minute = 0
                        
                        if end_period <= 5:
                            period_end_hour = 7 + (end_period - 1)
                        else:
                            period_end_hour = 13 + (end_period - 6)
                        
                        period_end_minute = 0
                        
                        # Calculate date for this day
                        day_date = week_start + timedelta(days=day_idx)
                        
                        # Extract course information
                        course_name = ""
                        room = ""
                        teacher = ""
                        date_range = ""
                        
                        for content in meaningful_content:
                            if "Tiết:" in content:
                                continue
                            elif "P." in content or "Phòng" in content:
                                room = content
                            elif "GV:" in content:
                                teacher = content
                            elif "(" in content and ")" in content and "-" in content:
                                date_range = content
                            elif not course_name and len(content) > 10:  # First long content is likely course name
                                course_name = content
                        
                        # Create event title
                        event_title = course_name if course_name else f"Lịch học tuần {week} - {session}"
                        
                        # Create event description
                        description_parts = []
                        if course_name:
                            description_parts.append(f"Học phần: {course_name}")
                        if room:
                            description_parts.append(f"Phòng: {room}")
                        if teacher:
                            description_parts.append(f"Giảng viên: {teacher}")
                        if date_range:
                            description_parts.append(f"Thời gian: {date_range}")
                        description_parts.append(f"Tuần: {week}, Buổi: {session}")
                        
                        description = " | ".join(description_parts)
                        
                        # Create event
                        event = Event(
                            user_id=user_id,
                            title=event_title,
                            event_type='Class',
                            datetime=datetime.combine(day_date, datetime.strptime(f"{period_start_hour:02d}:{period_start_minute:02d}", '%H:%M').time()),
                            description=description,
                            source='DNU API'
                        )
                        
                        db.session.add(event)
                        events_created += 1
        
        db.session.commit()
        
    except Exception as e:
        print(f"Error parsing schedule: {e}")
        db.session.rollback()
    
    return events_created

def start_reminder_scheduler():
    """Start the reminder scheduler"""
    from apscheduler.schedulers.background import BackgroundScheduler
    
    scheduler = BackgroundScheduler()
    
    # Chạy hàm check_and_send_reminders mỗi 30 phút
    scheduler.add_job(
        func=check_and_send_reminders,
        trigger="interval",
        minutes=30
    )
    
    scheduler.start()

def get_google_calendar_service():
    """Get Google Calendar service instance"""
    creds = None
    
    # Try to load credentials from token file
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # Check if credentials are invalid or don't exist
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            return None
            
    # Build and return the service
    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error building service: {e}")
        return None

@app.route('/calendar/authorize')
@login_required
def authorize_google_calendar():
    """Start the Google Calendar OAuth2 flow"""
    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    session['state'] = state
    return redirect(authorization_url)

@app.route('/calendar/oauth2callback')
def oauth2callback():
    """Handle the OAuth2 callback from Google"""
    try:
        state = session['state']
        
        flow = Flow.from_client_secrets_file(
            GOOGLE_CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            state=state,
            redirect_uri=url_for('oauth2callback', _external=True)
        )
        
        # Lấy full URL từ request, đảm bảo có scheme
        authorization_response = request.url
        if not authorization_response.startswith(('http:', 'https:')):
            authorization_response = 'http://' + request.host + request.full_path
        
        flow.fetch_token(authorization_response=authorization_response)
        credentials = flow.credentials
        
        # Save credentials for future use
        token_path = os.path.join(os.path.dirname(GOOGLE_CLIENT_SECRETS_FILE), 'token.pickle')
        with open(token_path, 'wb') as token:
            pickle.dump(credentials, token)
        
        flash('Google Calendar đã được kết nối thành công!')
        return redirect(url_for('dashboard'))
    
    except Exception as e:
        flash(f'Lỗi kết nối Google Calendar: {str(e)}')
        return redirect(url_for('calendar'))

@app.route('/calendar/sync')
@login_required
def sync_to_google_calendar():
    """Sync events to Google Calendar"""
    service = get_google_calendar_service()
    
    if not service:
        flash('Vui lòng kết nối với Google Calendar trước!')
        return redirect(url_for('authorize_google_calendar'))
    
    # Get all events for current user
    events = Event.query.filter_by(user_id=current_user.id).all()
    synced_count = 0
    
    for event in events:
        # Create Google Calendar event
        gcal_event = {
            'summary': event.title,
            'location': '',
            'description': event.description,
            'start': {
                'dateTime': event.datetime.isoformat(),
                'timeZone': 'Asia/Ho_Chi_Minh',
            },
            'end': {
                'dateTime': (event.datetime + timedelta(hours=1)).isoformat(),
                'timeZone': 'Asia/Ho_Chi_Minh',
            },
            'reminders': {
                'useDefault': True
            }
        }
        
        try:
            service.events().insert(calendarId='primary', body=gcal_event).execute()
            synced_count += 1
        except Exception as e:
            print(f"Error syncing event {event.id}: {e}")
            continue
    
    flash(f'Đã đồng bộ {synced_count} sự kiện lên Google Calendar!')
    return redirect(url_for('calendar'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Start the reminder scheduler
    start_reminder_scheduler()
    
    app.run(debug=True)
