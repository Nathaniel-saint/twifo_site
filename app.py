from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    # Dynamic FAQ data sent from python to HTML
    school_faqs = [
        {"question": "What are the school hours?", "answer": "We run from 8:00 AM to 3:30 PM, Monday to Friday."},
        {"question": "Does the school offer boarding?", "answer": "Yes, excellent boarding facilities are available for both boys and girls."},
        {"question": "What extracurriculars are available?", "answer": "We have dynamic Clubs, sports groups, and music departments."}
    ]
    return render_template('about.html', faqs=school_faqs)

@app.route('/admissions')
def admissions():
    return render_template('admissions.html')

@app.route('/alumni')
def alumni():
    # Dynamic alumni data passed from Python to the HTML template
    stories = [
        {
            "name": "Abena Mansa",
            "year": "2018",
            "story": "After graduating from THS, Abena went on to study Medicine at KNUST. She currently works as a resident pediatrician and credits her strong foundation to our science department.",
            "image_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150" # Sample image
        },
        {
            "name": "Kwame Boateng",
            "year": "2015",
            "story": "Kwame is now a successful software engineer in Accra. He spent his time at THS leading the campus IT club and organizing the school's very first tech exhibition.",
            "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150" # Sample image
        }
    ]
    return render_template('alumni.html', alumni_stories=stories)

if __name__ == '__main__':
    app.run(debug=True)