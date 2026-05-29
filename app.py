from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session 
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import os
import numpy as np
from datetime import datetime
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)

# --- System Security & Database Configs ---
app.config['SECRET_KEY'] = 'ths_secret_admin_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- SMTP Outbound Mail Server Configs ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'            
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'naddaemarfo18@gmail.com' 
app.config['MAIL_PASSWORD'] = 'ecbkbahjnlagimzm' 
app.config['MAIL_DEFAULT_SENDER'] = ('Twifo Hemang Shalom School', 'naddaemarfo18@gmail.com')

# Initialize extensions
db = SQLAlchemy(app)
mail = Mail(app)

# --- Database Models ---
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
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

# --- Semantic AI Setup ---
model = SentenceTransformer('all-MiniLM-L6-v2')

def load_knowledge_base():
    if not os.path.exists('school_data.txt'):
        return ["Welcome to Twifo Hemang Shalom School! How can we assist you today?"]
    with open('school_data.txt', 'r', encoding='utf-8') as f:
        return [line.strip() for line in f.readlines() if line.strip()]

knowledge_base = load_knowledge_base()
knowledge_embeddings = model.encode(knowledge_base, convert_to_tensor=True)


# --- Core Web Page Routes ---

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
        new_app = Application(first_name=fname, last_name=lname, email=u_email)
        db.session.add(new_app)
        db.session.commit()
        return render_template('admissions.html', success=True)
    return render_template('admissions.html', success=False)


# --- Secure Admin Panel Dashboard Routes ---
@app.route('/admin/dashboard')
def admin_dashboard():
    url_key = request.args.get('key')
    if url_key == 'shalom2026':
        session['is_admin'] = True

    if not session.get('is_admin'):
        return redirect(url_for('home'))
        
    all_applications = Application.query.all()
    all_support_requests = SupportRequest.query.all()
    all_posts = NewsPost.query.order_by(NewsPost.id.desc()).all()
    
    return render_template('admin_dashboard.html', applications=all_applications, support_requests=all_support_requests, posts=all_posts)

@app.route('/admin/add_news', methods=['POST'])
def add_news():
    if not session.get('is_admin'):
        return "Unauthorized Access Denied", 403
    p_title = request.form.get('title')
    p_content = request.form.get('content')
    if p_title and p_content:
        formatted_date = datetime.now().strftime("%B %d, %Y")
        new_post = NewsPost(title=p_title, content=p_content, date_posted=formatted_date)
        db.session.add(new_post)
        db.session.commit()
        flash("News announcement successfully published to the live public noticeboard!", "success")
    return redirect(url_for('admin_dashboard', key='shalom2026'))

@app.route('/admin/delete_news/<int:post_id>')
def delete_news(post_id):
    if not session.get('is_admin'):
        return "Unauthorized Access Denied", 403
    post = NewsPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Announcement removed from the noticeboard.", "success")
    return redirect(url_for('admin_dashboard', key='shalom2026'))

@app.route('/admin/update_status/<int:app_id>/<string:new_status>')
def update_application_status(app_id, new_status):
    if not session.get('is_admin'):
        return "Unauthorized Access Denied", 403
    applicant = Application.query.get_or_404(app_id)
    if new_status in ['Approved', 'Declined']:
        applicant.status = new_status
        db.session.commit()
        try:
            msg = Message(subject=f"Admission Application Update - #THS{applicant.id}", recipients=[applicant.email])
            if new_status == 'Approved':
                msg.body = f"Dear {applicant.first_name},\n\nYour application has been APPROVED."
            else:
                msg.body = f"Dear {applicant.first_name},\n\nWe regret to inform you we cannot offer you a spot."
            mail.send(msg)
            flash(f"Success! Applicant #{applicant.id} status set to {new_status} and email sent.", "success")
        except Exception:
            flash(f"Database updated to {new_status}, but email delivery failed.", "error")
    return redirect(url_for('admin_dashboard', key='shalom2026'))

@app.route('/admin/reply_support/<int:request_id>', methods=['POST'])
def reply_support(request_id):
    if not session.get('is_admin'):
        return "Unauthorized Access Denied", 403
    support_req = SupportRequest.query.get_or_404(request_id)
    admin_reply = request.form.get('admin_reply')
    if admin_reply:
        try:
            msg = Message(subject=f"Update regarding your {support_req.service_type} Request", recipients=[support_req.student_email])
            msg.body = f"Dear {support_req.student_name},\n\n{admin_reply}"
            mail.send(msg)
            support_req.status = 'Resolved'
            db.session.commit()
            flash(f"Reply successfully emailed to {support_req.student_name}!", "success")
        except Exception as e:
            flash(f"Failed to send email: {str(e)}", "error")
    return redirect(url_for('admin_dashboard', key='shalom2026'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('home'))

@app.route('/support', methods=['GET', 'POST'])
def support():
    services = [{"name": "Academic Tutoring & Peer Mentorship", "description": "One-on-one help with core subjects."}]
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

@app.route('/api/chat', methods=['POST'])
def chat_api():
    user_data = request.json
    user_message = user_data.get('message', '').strip()
    if not user_message:
        return jsonify({"reply": "I didn't catch that."})
    if user_message.lower() in ['hello', 'hi']:
        return jsonify({"reply": "Hello! I am the THS School AI Assistant."})
    query_embedding = model.encode(user_message, convert_to_tensor=True)
    cos_scores = util.cos_sim(query_embedding, knowledge_embeddings)[0]
    best_match_idx = int(np.argmax(cos_scores.cpu().numpy()))
    ai_reply = knowledge_base[best_match_idx] if cos_scores[best_match_idx].item() > 0.35 else "Please email admin."
    return jsonify({"reply": ai_reply})

if __name__ == '__main__':
    app.run(debug=True)