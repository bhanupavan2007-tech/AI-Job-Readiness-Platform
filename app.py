from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, send_file
)
from pathlib import Path
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape
from functools import wraps
from database import db, Student, Assessment


app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent

app.config["SECRET_KEY"] = "skillready-ai-development-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + (BASE_DIR / "skillready.db").as_posix()
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# Assessment questions
QUESTION_BANK = {
    "Python": [
        {
            "id": 1,
            "question": "What is the correct file extension for Python files?",
            "options": [
                {"value": ".java", "text": ".java"},
                {"value": ".py", "text": ".py"},
                {"value": ".html", "text": ".html"},
                {"value": ".cpp", "text": ".cpp"}
            ],
            "answer": ".py"
        },
        {
            "id": 2,
            "question": "Which keyword is used to define a function in Python?",
            "options": [
                {"value": "function", "text": "function"},
                {"value": "define", "text": "define"},
                {"value": "def", "text": "def"},
                {"value": "fun", "text": "fun"}
            ],
            "answer": "def"
        },
        {
            "id": 3,
            "question": "Which data type stores True or False values?",
            "options": [
                {"value": "int", "text": "int"},
                {"value": "str", "text": "str"},
                {"value": "list", "text": "list"},
                {"value": "bool", "text": "bool"}
            ],
            "answer": "bool"
        },
        {
            "id": 4,
            "question": "Which symbol is used to write a comment in Python?",
            "options": [
                {"value": "//", "text": "//"},
                {"value": "#", "text": "#"},
                {"value": "/* */", "text": "/* */"},
                {"value": "<!-- -->", "text": "<!-- -->"}
            ],
            "answer": "#"
        },
        {
            "id": 5,
            "question": "Which function is used to display output in Python?",
            "options": [
                {"value": "input()", "text": "input()"},
                {"value": "display()", "text": "display()"},
                {"value": "print()", "text": "print()"},
                {"value": "show()", "text": "show()"}
            ],
            "answer": "print()"
        }
    ],

    "Web Development": [
        {
            "id": 1,
            "question": "What does HTML stand for?",
            "options": [
                {"value": "HyperText Markup Language", "text": "HyperText Markup Language"},
                {"value": "HighText Machine Language", "text": "HighText Machine Language"},
                {"value": "HyperTool Multi Language", "text": "HyperTool Multi Language"},
                {"value": "HomeText Markup Language", "text": "HomeText Markup Language"}
            ],
            "answer": "HyperText Markup Language"
        },
        {
            "id": 2,
            "question": "Which HTML tag is used to include JavaScript?",
            "options": [
                {"value": "<css>", "text": "<css>"},
                {"value": "<script>", "text": "<script>"},
                {"value": "<js>", "text": "<js>"},
                {"value": "<code>", "text": "<code>"}
            ],
            "answer": "<script>"
        },
        {
            "id": 3,
            "question": "Which language is used to style web pages?",
            "options": [
                {"value": "Python", "text": "Python"},
                {"value": "SQL", "text": "SQL"},
                {"value": "CSS", "text": "CSS"},
                {"value": "Java", "text": "Java"}
            ],
            "answer": "CSS"
        },
        {
            "id": 4,
            "question": "Which HTML tag creates a hyperlink?",
            "options": [
                {"value": "<p>", "text": "<p>"},
                {"value": "<h1>", "text": "<h1>"},
                {"value": "<a>", "text": "<a>"},
                {"value": "<img>", "text": "<img>"}
            ],
            "answer": "<a>"
        },
        {
            "id": 5,
            "question": "Which CSS property changes text color?",
            "options": [
                {"value": "background", "text": "background"},
                {"value": "font-size", "text": "font-size"},
                {"value": "color", "text": "color"},
                {"value": "margin", "text": "margin"}
            ],
            "answer": "color"
        }
    ],

    "SQL": [
        {
            "id": 1,
            "question": "What does SQL stand for?",
            "options": [
                {"value": "Structured Query Language", "text": "Structured Query Language"},
                {"value": "Simple Question Language", "text": "Simple Question Language"},
                {"value": "System Query Logic", "text": "System Query Logic"},
                {"value": "Standard Quick Language", "text": "Standard Quick Language"}
            ],
            "answer": "Structured Query Language"
        },
        {
            "id": 2,
            "question": "Which SQL command is used to retrieve data?",
            "options": [
                {"value": "INSERT", "text": "INSERT"},
                {"value": "SELECT", "text": "SELECT"},
                {"value": "UPDATE", "text": "UPDATE"},
                {"value": "DELETE", "text": "DELETE"}
            ],
            "answer": "SELECT"
        },
        {
            "id": 3,
            "question": "Which SQL clause filters records?",
            "options": [
                {"value": "ORDER BY", "text": "ORDER BY"},
                {"value": "GROUP BY", "text": "GROUP BY"},
                {"value": "WHERE", "text": "WHERE"},
                {"value": "JOIN", "text": "JOIN"}
            ],
            "answer": "WHERE"
        },
        {
            "id": 4,
            "question": "Which SQL command adds new records?",
            "options": [
                {"value": "INSERT", "text": "INSERT"},
                {"value": "SELECT", "text": "SELECT"},
                {"value": "DROP", "text": "DROP"},
                {"value": "ALTER", "text": "ALTER"}
            ],
            "answer": "INSERT"
        },
        {
            "id": 5,
            "question": "What is the purpose of a primary key?",
            "options": [
                {"value": "To sort records", "text": "To sort records"},
                {"value": "To uniquely identify a record", "text": "To uniquely identify a record"},
                {"value": "To delete records", "text": "To delete records"},
                {"value": "To format a table", "text": "To format a table"}
            ],
            "answer": "To uniquely identify a record"
        }
    ],

    "Communication": [
        {
            "id": 1,
            "question": "What is active listening?",
            "options": [
                {"value": "Interrupting others", "text": "Interrupting others"},
                {"value": "Ignoring the speaker", "text": "Ignoring the speaker"},
                {"value": "Paying attention and understanding the speaker", "text": "Paying attention and understanding the speaker"},
                {"value": "Talking continuously", "text": "Talking continuously"}
            ],
            "answer": "Paying attention and understanding the speaker"
        },
        {
            "id": 2,
            "question": "Which is important for clear communication?",
            "options": [
                {"value": "Using confusing words", "text": "Using confusing words"},
                {"value": "Speaking clearly and concisely", "text": "Speaking clearly and concisely"},
                {"value": "Speaking very quickly", "text": "Speaking very quickly"},
                {"value": "Avoiding eye contact", "text": "Avoiding eye contact"}
            ],
            "answer": "Speaking clearly and concisely"
        },
        {
            "id": 3,
            "question": "Which is an example of non-verbal communication?",
            "options": [
                {"value": "Email writing", "text": "Email writing"},
                {"value": "Text messaging", "text": "Text messaging"},
                {"value": "Body language", "text": "Body language"},
                {"value": "Report writing", "text": "Report writing"}
            ],
            "answer": "Body language"
        },
        {
            "id": 4,
            "question": "What is constructive feedback?",
            "options": [
                {"value": "Feedback that helps someone improve", "text": "Feedback that helps someone improve"},
                {"value": "Insulting someone", "text": "Insulting someone"},
                {"value": "Ignoring mistakes", "text": "Ignoring mistakes"},
                {"value": "Blaming others", "text": "Blaming others"}
            ],
            "answer": "Feedback that helps someone improve"
        },
        {
            "id": 5,
            "question": "How should you communicate in a professional environment?",
            "options": [
                {"value": "Rudely", "text": "Rudely"},
                {"value": "Respectfully and clearly", "text": "Respectfully and clearly"},
                {"value": "Aggressively", "text": "Aggressively"},
                {"value": "Without listening", "text": "Without listening"}
            ],
            "answer": "Respectfully and clearly"
        }
    ]
}


# Login required decorator
def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if "student_id" not in session:
            flash("Please login to access your dashboard.", "error")
            return redirect(url_for("login"))
        return route_function(*args, **kwargs)

    return wrapper


# Homepage
@app.route("/")
def home():
    return render_template("index.html")


# Student registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("register"))

        if len(name) > 100 or len(email) > 120:
            flash("Name or email is too long.", "error")
            return redirect(url_for("register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))

        existing_student = Student.query.filter_by(email=email).first()

        if existing_student:
            flash("This email is already registered.", "error")
            return redirect(url_for("register"))

        new_student = Student(
            name=name,
            email=email,
            password=generate_password_hash(password)
        )

        try:
            db.session.add(new_student)
            db.session.commit()
            flash("Registration successful! Your account has been created.", "success")
            return redirect(url_for("register"))

        except Exception:
            db.session.rollback()
            flash("Something went wrong. Please try again.", "error")
            return redirect(url_for("register"))

    return render_template("register.html")


# Student login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter your email and password.", "error")
            return redirect(url_for("login"))

        student = Student.query.filter_by(email=email).first()

        if student and check_password_hash(student.password, password):
            session.clear()
            session["student_id"] = student.id
            session["student_name"] = student.name

            flash("Login successful! Welcome to SkillReady AI.", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password. Please try again.", "error")
        return redirect(url_for("login"))

    if "student_id" in session:
        return redirect(url_for("dashboard"))

    return render_template("login.html")


# Student dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    student = db.session.get(Student, session["student_id"])

    if student is None:
        session.clear()
        flash("Please login again.", "error")
        return redirect(url_for("login"))

    return render_template("dashboard.html", student_name=student.name)


# Skill assessment
@app.route("/assessment", methods=["GET", "POST"])
@login_required
def assessment():
    student = db.session.get(Student, session["student_id"])

    if student is None:
        session.clear()
        flash("Please login again.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        skill_name = request.form.get("skill_name", "")

        if skill_name not in QUESTION_BANK:
            flash("Please select a valid skill category.", "error")
            return redirect(url_for("assessment"))

        questions = QUESTION_BANK[skill_name]
        correct_answers = 0

        for question in questions:
            submitted_answer = request.form.get(
                f"question_{question['id']}"
            )

            valid_options = [
                option["value"] for option in question["options"]
            ]

            if submitted_answer not in valid_options:
                flash("Please answer all questions.", "error")
                return redirect(url_for("assessment", skill=skill_name))

            if submitted_answer == question["answer"]:
                correct_answers += 1

        total_questions = len(questions)
        score = round((correct_answers / total_questions) * 100, 2)

        if score >= 80:
            readiness_level = "Job Ready"
        elif score >= 60:
            readiness_level = "Nearly Job Ready"
        elif score >= 40:
            readiness_level = "Developing Skills"
        else:
            readiness_level = "Needs Improvement"

        new_assessment = Assessment(
            student_id=student.id,
            skill_name=skill_name,
            total_questions=total_questions,
            correct_answers=correct_answers,
            score=score,
            readiness_level=readiness_level
        )

        try:
            db.session.add(new_assessment)
            db.session.commit()

            return redirect(
                url_for("results", assessment_id=new_assessment.id)
            )

        except Exception:
            db.session.rollback()
            flash("Unable to save your assessment. Please try again.", "error")
            return redirect(url_for("assessment", skill=skill_name))

    skill_name = request.args.get("skill", "Python")

    if skill_name not in QUESTION_BANK:
        skill_name = "Python"

    return render_template(
        "assessment.html",
        skill_name=skill_name,
        questions=QUESTION_BANK[skill_name]
    )


# Individual assessment results
@app.route("/results/<int:assessment_id>")
@login_required
def results(assessment_id):
    assessment_record = Assessment.query.filter_by(
        id=assessment_id,
        student_id=session["student_id"]
    ).first()

    if assessment_record is None:
        flash("Assessment results not found.", "error")
        return redirect(url_for("dashboard"))

    student = db.session.get(Student, session["student_id"])

    return render_template(
        "results.html",
        student_name=student.name,
        skill_name=assessment_record.skill_name,
        score=assessment_record.score,
        correct_answers=assessment_record.correct_answers,
        total_questions=assessment_record.total_questions,
        readiness_level=assessment_record.readiness_level
    )


# My Results History
@app.route("/my-results")
@login_required
def my_results():
    student_id = session["student_id"]

    assessment_records = Assessment.query.filter_by(
        student_id=student_id
    ).order_by(
        Assessment.created_at.desc()
    ).all()

    return render_template(
        "history.html",
        assessments=assessment_records
    )


# Download PDF assessment report
@app.route("/download-report")
@login_required
def download_report():

    student = db.session.get(Student, session["student_id"])

    if student is None:
        session.clear()
        flash("Please login again.", "error")
        return redirect(url_for("login"))

    # Get only this student's assessment records
    assessment_records = Assessment.query.filter_by(
        student_id=student.id
    ).order_by(
        Assessment.created_at.desc()
    ).all()

    # Find the latest score for each skill category
    skill_categories = [
        "Python",
        "Web Development",
        "SQL",
        "Communication"
    ]

    latest_scores = {}

    for skill in skill_categories:
        latest_record = next(
            (
                record for record in assessment_records
                if record.skill_name == skill
            ),
            None
        )

        if latest_record is not None:
            latest_scores[skill] = latest_record.score

    completed_scores = list(latest_scores.values())

    if completed_scores:
        overall_score = round(
            sum(completed_scores) / len(completed_scores), 2
        )
    else:
        overall_score = 0

    if not completed_scores:
        overall_level = "Not Assessed"
    elif overall_score >= 80:
        overall_level = "Job Ready"
    elif overall_score >= 60:
        overall_level = "Nearly Job Ready"
    elif overall_score >= 40:
        overall_level = "Developing Skills"
    else:
        overall_level = "Needs Improvement"

    # Create the PDF in memory
    pdf_buffer = BytesIO()

    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        textColor=colors.HexColor("#172554"),
        spaceAfter=12
    )

    story = []

    story.append(Paragraph("SkillReady AI", title_style))
    story.append(Paragraph("Student Assessment Report", styles["Heading2"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        f"<b>Student Name:</b> {escape(student.name)}",
        styles["Normal"]
    ))
    story.append(Paragraph(
        f"<b>Email:</b> {escape(student.email)}",
        styles["Normal"]
    ))
    story.append(Paragraph(
        f"<b>Report Date:</b> {datetime.now().strftime('%d-%m-%Y')}",
        styles["Normal"]
    ))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Overall Career Readiness", styles["Heading2"]))
    story.append(Paragraph(
        f"<b>Overall Score:</b> {overall_score}%",
        styles["Normal"]
    ))
    story.append(Paragraph(
        f"<b>Readiness Level:</b> {overall_level}",
        styles["Normal"]
    ))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Assessment History", styles["Heading2"]))

    table_data = [[
        "Skill",
        "Score",
        "Correct",
        "Total",
        "Readiness",
        "Date"
    ]]

    for record in assessment_records:
        assessment_date = (
            record.created_at.strftime("%d-%m-%Y")
            if record.created_at else "N/A"
        )

        table_data.append([
            record.skill_name,
            f"{record.score}%",
            str(record.correct_answers),
            str(record.total_questions),
            record.readiness_level,
            assessment_date
        ])

    if not assessment_records:
        table_data.append([
            "No assessments completed", "", "", "", "", ""
        ])

    report_table = Table(
        table_data,
        repeatRows=1,
        colWidths=[
            1.35 * inch,
            0.65 * inch,
            0.65 * inch,
            0.55 * inch,
            1.25 * inch,
            0.85 * inch
        ]
    )

    report_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172554")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    story.append(report_table)
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "This report is generated by SkillReady AI based on the "
        "assessment records saved in your account.",
        styles["Italic"]
    ))

    document.build(story)
    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name="SkillReady_AI_Assessment_Report.pdf",
        mimetype="application/pdf"
    )



# Student logout
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("login"))


# Career Readiness Analysis
@app.route("/career-analysis")
@login_required
def career_analysis():

    student_id = session["student_id"]

    # Get all assessment records of the logged-in student
    assessment_records = Assessment.query.filter_by(
        student_id=student_id
    ).order_by(
        Assessment.created_at.desc()
    ).all()

    # Available skill categories
    skill_categories = [
        "Python",
        "Web Development",
        "SQL",
        "Communication"
    ]

    skill_scores = {}

    # Get the latest score for each skill
    for skill in skill_categories:

        latest_assessment = next(
            (
                record for record in assessment_records
                if record.skill_name == skill
            ),
            None
        )

        if latest_assessment:
            skill_scores[skill] = latest_assessment.score
        else:
            skill_scores[skill] = None

    # Get completed skill scores
    completed_scores = {
        skill: score
        for skill, score in skill_scores.items()
        if score is not None
    }

    # Calculate overall career readiness
    if completed_scores:

        overall_score = round(
            sum(completed_scores.values()) / len(completed_scores),
            2
        )

        strongest_skill = max(
            completed_scores,
            key=completed_scores.get
        )

        weakest_skill = min(
            completed_scores,
            key=completed_scores.get
        )

    else:
        overall_score = 0
        strongest_skill = None
        weakest_skill = None

    # Determine overall readiness level
    if not completed_scores:
        overall_level = "Not Assessed"
    elif overall_score >= 80:
        overall_level = "Job Ready"
    elif overall_score >= 60:
        overall_level = "Nearly Job Ready"
    elif overall_score >= 40:
        overall_level = "Developing Skills"
    else:
        overall_level = "Needs Improvement"

    # Generate improvement suggestions
    suggestions = []

    for skill, score in completed_scores.items():

        if score < 40:
            suggestions.append(
                f"Focus on improving your {skill} fundamentals."
            )

        elif score < 60:
            suggestions.append(
                f"Practice more {skill} questions and exercises."
            )

        elif score < 80:
            suggestions.append(
                f"Improve your {skill} skills through practical projects."
            )

        else:
            suggestions.append(
                f"Excellent work in {skill}! Continue practising."
            )

    # Suggest assessments for incomplete categories
    for skill, score in skill_scores.items():

        if score is None:
            suggestions.append(
                f"Complete your {skill} assessment to improve your career analysis."
            )

    return render_template(
        "career_analysis.html",
        skill_scores=skill_scores,
        overall_score=overall_score,
        overall_level=overall_level,
        strongest_skill=strongest_skill,
        weakest_skill=weakest_skill,
        suggestions=suggestions,
        completed_count=len(completed_scores)
    )


# Initialize database tables
with app.app_context():
    db.create_all()
    print("Database connected successfully!")
    print("Database tables created successfully!")


# Run Flask application
if __name__ == "__main__":
    app.run(debug=True)