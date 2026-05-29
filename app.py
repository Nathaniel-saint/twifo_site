from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session 
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from werkzeug.utils import secure_filename 
from threading import Thread 
from dotenv import load_dotenv

# Production Clients
from google import genai
from google.genai import types
import resend  

# Load local environment configuration properties if testing locally
load_dotenv()

app = Flask(__name__)

# --- Production Environment Keys & Integrity Validations ---
SECRET_KEY = os.environ.get('SECRET_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')  

# Hard fail immediately if the cloud cluster fails to inject infrastructure secrets
if not SECRET_KEY or not GEMINI_API_KEY or not RESEND_API_KEY:
    raise RuntimeError("PRODUCTION SYSTEM CRITICAL ERROR: Essential infrastructure keys are missing!")

app.config['SECRET_KEY'] = SECRET_KEY

# Persistent Directory Setup 
if os.path.exists('/app/static/uploads'):
    # Production on Railway: Store sqlite data safely inside the persistent volume mount point
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////app/static/uploads/school.db'
    app.config['UPLOAD_FOLDER'] = '/app/static/uploads'
else:
    # Local System Testing Fallback
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'
    app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

# --- Security & Traffic Limitations Configs ---
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Max size cap: 5MB to block payload attacks
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Initialize Database & Core API clients
db = SQLAlchemy(app)
resend.api_key = RESEND_API_KEY  

# --- Production Asynchronous HTTP Email Engine ---
def send_async_email(to_email, subject, body_text):
    """Dispatches transactional communications asynchronously over HTTPS Port 443."""
    try:
        # Wrap message body safely into clean HTML structures with structural typography rules
        html_content = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 580px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
            <h2 style="color: #1e3a8a; margin-top: 0;">Twifo Hemang Shalom School</h2>
            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
            <p style="white-space: pre-line; color: #334155; font-size: 16px; line-height: 1.6;">{body_text}</p>
            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
            <small style="color: #64748b; font-size: 12px; display: block; text-align: center;">This is an automated operational transmission from the administrative system dashboard.</small>
        </div>
        """
        
        # Dispatch request via Resend infrastructure
        resend.Emails.send({
            "from": "Twifo Hemang Shalom School <onboarding@resend.dev>", 
            "to": [to_email],
            "subject": subject,
            "html": html_content
        })
        print(f"Production Service Monitor: Email thread successfully processed delivery payload for: {to_email}")
    except Exception as e:
        print(f"Background Email Engine Exception Log: {str(e)}")

# --- Schema Architecture ---
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    document_file = db.Column(db.String(200), nullable=True)  
    status = db.Column(db.String(20), default='Pending')

class SupportRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    student_email = db.Column(db.String(100), nullable=False)
    service_type = db.Column(db.String(50), nullable=False) 
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending')

class NewsPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.String(20), nullable=False)

with app.app_context():
    db.create_all()

# --- Google Gemini Engine Client ---
client = genai.Client(api_key=GEMINI_API_KEY)

def load_school_knowledge_context():
    if not os.path.exists('school_data.txt'):
        return (
            "Twifo Hemang Shalom School was founded in 2004. It is dedicated to academic excellence, "
            "holistic growth, and deep moral uprightness. Founders and proprietors are Rev. Dr. Robert Yaw Owusu (PhD) "
            "and Mrs. Christiana Owusu. The school is located in the Central Region of Ghana."
        )
    with open('school_data.txt', 'r', encoding='utf-8') as f:
        return f.read().strip()

school_context = load_school_knowledge_context()

# --- Navigation Architecture Routes ---
@app.route('/')
def home():
    all_posts = NewsPost.query.order_by(NewsPost.id.desc()).all()
    return render_template('index.html', posts=all_posts)

@app.route('/about')
def about():
    school_faqs = [
        {"question": "What are the school hours?", "answer": "We run from 8:00 AM to 3:30 PM, Monday to Friday."},
        {"question": "Does the school offer boarding?", "answer": "Yes, excellent boarding facilities are available for both boys and girls."},
        {"question": "What extracurriculars are available?", "answer": "We have dynamic Clubs, sports groups, and music departments."}
    ]
    return render_template('about.html', faqs=school_faqs)

@app.route('/academics')
def academics():
    departments = [
        {"id": "dept-science", "name": "Science & Mathematics", "description": "Fostering critical thinking through rigorous experimental learning."},
        {"id": "dept-languages", "name": "Languages & Humanities", "description": "Building powerful global communicators."},
        {"id": "dept-it", "name": "Information Technology & Vocational", "description": "Preparing students for a digital future."}
    ]
    clubs = [
        {"id": "club-it", "name": "The Tech & Innovation Club", "description": "Where student ideas meet engineering."},
        {"id": "club-sports", "name": "Athletics & Sports Society", "description": "Promoting teamwork and leadership."},
        {"id": "club-creative", "name": "Creative Arts & Debating Club", "description": "Nurturing public speech confidence."}
    ]
    return render_template('academics.html', departments=departments, clubs=clubs)

@app.route('/alumni')
def alumni():
    stories = [
        {"name": "Abena Mansa", "year": "2018", "story": "Studied Medicine at KNUST.", "image_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150"},
        {"name": "Kwame Boateng", "year": "2015", "story": "Software Engineer in Accra.", "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150"}
    ]
    return render_template('alumni.html', alumni_stories=stories)

@app.route('/admissions', methods=['GET', 'POST'])
def admissions():
    if request.method == 'POST':
        fname = request.form.get('firstname')
        lname = request.form.get('lastname')
        u_email = request.form.get('email')
        uploaded_file = request.files.get('document')
        filename_to_save = None
        
        if uploaded_file and uploaded_file.filename != '':
            if allowed_file(uploaded_file.filename):
                safe_filename = secure_filename(uploaded_file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename_to_save = f"{timestamp}_{os.urandom(4).hex()}_{safe_filename}"
                uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_to_save))
            else:
                flash("Invalid file attachment format! Only PDF, PNG, and JPG documents are accepted.", "error")
                return render_template('admissions.html', success=False)

        new_app = Application(first_name=fname, last_name=lname, email=u_email, document_file=filename_to_save)
        db.session.add(new_app)
        db.session.commit()
        return render_template('admissions.html', success=True)
    return render_template('admissions.html', success=False)

# --- Admin Panel Core Operations ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_pass = request.form.get('password')
        secure_admin_password = os.environ.get('ADMIN_DASHBOARD_PASSWORD', 'Robert_Chritiana@THS')
        if admin_pass == secure_admin_password:
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        flash("Invalid administrator access credentials entered.", "error")
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    all_applications = Application.query.all()
    all_support_requests = SupportRequest.query.all()
    all_posts = NewsPost.query.order_by(NewsPost.id.desc()).all()
    return render_template('admin_dashboard.html', applications=all_applications, support_requests=all_support_requests, posts=all_posts)

@app.route('/admin/add_news', methods=['POST'])
def add_news():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized Access Denied"}), 403
    p_title = request.form.get('title')
    p_content = request.form.get('content')
    if p_title and p_content:
        formatted_date = datetime.now().strftime("%B %d, %Y")
        new_post = NewsPost(title=p_title, content=p_content, date_posted=formatted_date)
        db.session.add(new_post)
        db.session.commit()
        flash("News announcement successfully published to the live public noticeboard!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_news/<int:post_id>')
def delete_news(post_id):
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized Access Denied"}), 403
    post = NewsPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Announcement removed from the noticeboard.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_status/<int:app_id>/<string:new_status>')
def update_application_status(app_id, new_status):
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized Access Denied"}), 403
        
    applicant = Application.query.get_or_404(app_id)
    
    if new_status in ['Approved', 'Declined']:
        applicant.status = new_status
        db.session.commit()
        
        full_name = f"{applicant.first_name} {applicant.last_name}"
        
        if new_status == 'Approved':
            email_body = (
                f"Dear {full_name},\n\n"
                f"Congratulations! We are pleased to inform you that your admission application to "
                f"Twifo Hemang Shalom School has been APPROVED.\n\n"
                f"Our admissions office will reach out to you within 3 business days with your "
                f"formal admission letter, uniform measurements information, and fee details.\n\n"
                f"Welcome to our vibrant community!\n\n"
                f"Warm regards,\n"
                f"Admissions Board\n"
                f"Twifo Hemang Shalom School"
            )
        else:
            email_body = (
                f"Dear {full_name},\n\n"
                f"Thank you for your interest in joining Twifo Hemang Shalom School.\n\n"
                f"After careful review of our enrollment capacity limitations for the upcoming term, "
                f"we regret to inform you that we are unable to offer you a spot at this time.\n\n"
                f"We keep all profiles on file for one academic year should any unexpected vacancies arise.\n\n"
                f"We wish you the very best in your academic pursuits.\n\n"
                f"Sincerely,\n"
                f"Admissions Board\n"
                f"Twifo Hemang Shalom School"
            )
            
        email_subject = f"Admission Application Update - #THS{applicant.id}"
        Thread(target=send_async_email, args=(applicant.email, email_subject, email_body)).start()
        flash(f"Success! Applicant #{applicant.id} status updated to {new_status}. Processing notification email.", "success")
            
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reply_support/<int:request_id>', methods=['POST'])
def reply_support(request_id):
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized Access Denied"}), 403
        
    support_req = SupportRequest.query.get_or_404(request_id)
    admin_reply = request.form.get('admin_reply')
    
    if admin_reply:
        email_body = (
            f"Dear {support_req.student_name},\n\n"
            f"This is an official response from the Student Support Services Department "
            f"regarding your recent request for {support_req.service_type}.\n\n"
            f"Message from Administration:\n"
            f"{admin_reply}\n\n"
            f"If you have further questions, please feel free to reply to this email "
            f"or visit our office.\n\n"
            f"Warm regards,\n"
            f"Support Team\n"
            f"Twifo Hemang Shalom School"
        )
        
        email_subject = f"Update regarding your {support_req.service_type} Request"
        Thread(target=send_async_email, args=(support_req.student_email, email_subject, email_body)).start()
        
        support_req.status = 'Resolved'
        db.session.commit()
        flash(f"Reply successfully processing! Notification email dispatched to {support_req.student_name}.", "success")
            
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('home'))

@app.route('/support', methods=['GET', 'POST'])
def support():
    services = [
        {"name": "Academic Tutoring & Peer Mentorship", "description": "One-on-one help with core subjects like Mathematics, Integrated Science, and English Language."},
        {"name": "Guidance & Psychological Counseling", "description": "Confidential personal counseling, emotional check-ins, and stress management workshops."},
        {"name": "University & Career Placement Support", "description": "Assistance with university applications, scholarship essays, and career pathway advice."},
        {"name": "Campus Health & Medical Services", "description": "24/7 care provided by our campus infirmary staff for student physical wellness."}
    ]
    
    if request.method == 'POST':
        s_name = request.form.get('student_name')
        s_email = request.form.get('student_email')
        s_type = request.form.get('service_type')
        s_msg = request.form.get('message')
        new_request = SupportRequest(student_name=s_name, student_email=s_email, service_type=s_type, message=s_msg)
        db.session.add(new_request)
        db.session.commit()
        flash("Your support request has been submitted successfully!", "success")
        return redirect(url_for('support'))
        
    return render_template('support.html', services=services)

# --- Smart Chat API Route Using Gemini 2.5 Flash ---
@app.route('/api/chat', methods=['POST'])
def chat_api():
    user_data = request.json or {}
    user_message = user_data.get('message', '').strip()

    if not user_message:
        return jsonify({"reply": "I didn't catch that."})
    elif "<script>" in user_message.lower():
        return jsonify({"reply": "I am unable to execute or parse code scripts. How can I help you today?"})
    
    try:
        system_instruction = (
            "You are the polite, welcoming, and official AI Assistant for Twifo Hemang Shalom School.\n"
            "Your main objective is to answer user queries accurately using the verified school context provided below.\n"
            "Always give a direct, natural text answer based on this context.\n\n"
            f"OFFICIAL SCHOOL CONTEXT:\n{school_context}"
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3, 
            ),
        )
        ai_reply = response.text.strip()
    except Exception as e:
        print(f"Gemini Engine Infrastructure Failure Trace: {str(e)}")
        ai_reply = "I ran into a small configuration issue while processing that request. Please try again later."

    return jsonify({"reply": ai_reply})

if __name__ == '__main__':
    app.run(debug=True)