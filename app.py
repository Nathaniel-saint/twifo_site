from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message # Import Mail dependencies
import os
import numpy as np

app = Flask(__name__)

# --- System Security & Database Configs ---
app.config['SECRET_KEY'] = 'ths_secret_admin_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- SMTP Outbound Mail Server Configs ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'             # Change to your provider's SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'naddaemarfo18@gmail.com' # Replace with your test email account
app.config['MAIL_PASSWORD'] = 'ecbkbahjnlagimzm' # Replace with your App Password
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

with app.app_context():
    db.create_all()

# --- Semantic AI Setup ---
from sentence_transformers import SentenceTransformer, util
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
    return render_template('index.html')

@app.route('/about')
def about():
    school_faqs = [
        {"question": "What are the school hours?", "answer": "We run from 8:00 AM to 3:30 PM, Monday to Friday."},
        {"question": "Does the school offer boarding?", "answer": "Yes, excellent boarding facilities are available for both boys and girls."},
        {"question": "What extracurriculars are available?", "answer": "We have dynamic Clubs, sports groups, and music departments."}
    ]
    return render_template('about.html', faqs=school_faqs)


# --- Complete Academics Route with Department & Club Arrays ---
@app.route('/academics')
def academics():
    departments = [
        {
            "id": "dept-science",
            "name": "Science & Mathematics",
            "description": "Fostering critical thinking through rigorous experimental learning. Our state-of-the-art laboratory equips students with practical skills in Biology, Chemistry, Physics, and Core/Elective Mathematics."
        },
        {
            "id": "dept-languages",
            "name": "Languages & Humanities",
            "description": "Building powerful global communicators. This department oversees training in English Language, Literature, French, and Social Studies, encouraging deep cultural awareness and narrative excellence."
        },
        {
            "id": "dept-it",
            "name": "Information Technology & Vocational",
            "description": "Preparing students for a digital future. Covering foundational computing, software packages, introductory programming, visual arts, and home economics workflows."
        }
    ]
    
    clubs = [
        {
            "id": "club-it",
            "name": "The Tech & Innovation Club",
            "description": "Where student ideas meet engineering. Members explore software logic, web design layouts, and hardware configurations—frequently hosting school tech exhibitions."
        },
        {
            "id": "club-sports",
            "name": "Athletics & Sports Society",
            "description": "Promoting teamwork, leadership, and physiological wellness. Encompasses our championship football team, basketball squad, and track field training schedules."
        },
        {
            "id": "club-creative",
            "name": "Creative Arts & Debating Club",
            "description": "Nurturing public speech confidence and artistic flair. Students participate in inter-school debate tournaments, poetry events, and musical production showcases."
        }
    ]
    return render_template('academics.html', departments=departments, clubs=clubs)


@app.route('/alumni')
def alumni():
    stories = [
        {
            "name": "Abena Mansa",
            "year": "2018",
            "story": "After graduating from THS, Abena went on to study Medicine at KNUST. She currently works as a resident pediatrician and credits her strong foundation to our science department.",
            "image_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150"
        },
        {
            "name": "Kwame Boateng",
            "year": "2015",
            "story": "Kwame is now a successful software engineer in Accra. He spent his time at THS leading the campus IT club and organizing the school's very first tech exhibition.",
            "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150"
        }
    ]
    return render_template('alumni.html', alumni_stories=stories)


# --- Admissions Form Route (Database Storage Activated) ---
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
    all_applications = Application.query.all()
    return render_template('admin_dashboard.html', applications=all_applications)

@app.route('/admin/update_status/<int:app_id>/<string:new_status>')
def update_application_status(app_id, new_status):
    applicant = Application.query.get_or_404(app_id)
    
    if new_status in ['Approved', 'Declined']:
        # Update database entry state
        applicant.status = new_status
        db.session.commit()
        
        # --- Trigger Automatic Email System ---
        try:
            # Create core Message container (Subject, Recipient)
            msg = Message(
                subject=f"Admission Application Update - #THS{applicant.id}",
                recipients=[applicant.email]
            )
            
            # Tailor the content dynamically based on your choice
            if new_status == 'Approved':
                msg.body = f"Dear {applicant.first_name} {applicant.last_name},\n\n" \
                           f"Congratulations! We are pleased to inform you that your admission application to " \
                           f"Twifo Hemang Shalom School has been APPROVED.\n\n" \
                           f"Our admissions office will reach out to you within 3 business days with your formal admission " \
                           f"letter, uniform measurements information, and fee details.\n\n" \
                           f"Welcome to our vibrant community!\n\n" \
                           f"Warm regards,\n" \
                           f"Admissions Board\n" \
                           f"Twifo Hemang Shalom School"
            else:
                msg.body = f"Dear {applicant.first_name} {applicant.last_name},\n\n" \
                           f"Thank you for your interest in joining Twifo Hemang Shalom School.\n\n" \
                           f"After careful review of our enrollment capacity limitations for the upcoming term, we regret to " \
                           f"inform you that we are unable to offer you a spot at this time.\n\n" \
                           f"We keep all profiles on file for one academic year should any unexpected vacancies arise.\n\n" \
                           f"We wish you the very best in your academic pursuits.\n\n" \
                           f"Sincerely,\n" \
                           f"Admissions Board\n" \
                           f"Twifo Hemang Shalom School"
            
            # Dispatch the email immediately
            mail.send(msg)
            print(f"SUCCESS: Notification email successfully dispatched to {applicant.email}")
            
        except Exception as e:
            # Safe fallback if network/SMTP config fails so your site doesn't crash
            print(f"ERROR: Database updated, but automated mail dispatch failed: {str(e)}")
            
    return redirect(url_for('admin_dashboard'))

# --- AI Chat API Endpoint ---
@app.route('/api/chat', methods=['POST'])
def chat_api():
    user_data = request.json
    user_message = user_data.get('message', '').strip()
    if not user_message:
        return jsonify({"reply": "I didn't catch that."})
    
    greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon']
    if user_message.lower() in greetings:
        return jsonify({"reply": "Hello! I am the THS School AI Assistant. Ask me anything about our admissions, boarding, hours, or location!"})

    query_embedding = model.encode(user_message, convert_to_tensor=True)
    cos_scores = util.cos_sim(query_embedding, knowledge_embeddings)[0]
    best_match_idx = int(np.argmax(cos_scores.cpu().numpy()))
    
    if cos_scores[best_match_idx].item() > 0.35:
        ai_reply = knowledge_base[best_match_idx]
    else:
        ai_reply = "I'm sorry, I couldn't find a direct answer in our database. Please contact our administration via email at info@twifoshalomschool.edu."
        
    return jsonify({"reply": ai_reply})

if __name__ == '__main__':
    app.run(debug=True)