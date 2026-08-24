import os
import json
import sqlite3
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, make_response, send_file
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import init_db, get_db_connection
from compiler.runner import execute_code
from compiler.lexer_parser import CompilerAnalyzer
from compiler.hint_engine import HintEngine
from ai.ai_engine import AIEngine
from ai.comparison import compare_student_vs_ai
from plagiarism.detector import PlagiarismDetector
from evaluation.evaluator import evaluate_submission
from reports.generator import generate_pdf_report, generate_csv_export
from utils.auth import login_user_session, logout_user_session, get_current_user, login_required, role_required
from utils.helpers import generate_certificate_code, extract_coding_fingerprint, format_api_response

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "codevision_ai_hackathon_secret_key_2026")

# Initialize SQLite database schema and seed data
init_db()

@app.context_processor
def inject_user():
    """Injects current_user context into HTML templates."""
    return dict(current_user=get_current_user())

# ====================================================
# PAGE ROUTES & AUTHENTICATION
# ====================================================

@app.route('/')
def index_page():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username_or_email = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        user = conn.execute("""
            SELECT * FROM users WHERE username = ? OR email = ?
        """, (username_or_email, username_or_email)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            login_user_session(user)
            flash("Welcome back to CodeVision AI!", "success")
            return redirect(url_for('dashboard_router'))
        else:
            flash("Invalid username/email or password.", "danger")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'student')

        if not username or not email or not password:
            flash("Please fill in all required fields.", "warning")
            return render_template('register.html')

        conn = get_db_connection()
        existing = conn.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email)).fetchone()
        if existing:
            conn.close()
            flash("Username or Email already registered.", "danger")
            return render_template('register.html')

        pw_hash = generate_password_hash(password)
        conn.execute("""
            INSERT INTO users (username, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, (username, email, pw_hash, role))
        conn.commit()

        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        login_user_session(user)
        flash("Registration successful!", "success")
        return redirect(url_for('dashboard_router'))

    return render_template('register.html')

@app.route('/logout')
def logout_action():
    logout_user_session()
    flash("Successfully logged out.", "info")
    return redirect(url_for('index_page'))

@app.route('/dashboard')
@login_required
def dashboard_router():
    role = session.get('role', 'student')
    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'faculty':
        return redirect(url_for('faculty_dashboard'))
    else:
        return redirect(url_for('student_dashboard'))

@app.route('/student/dashboard')
@role_required(['student', 'admin'])
def student_dashboard():
    user = get_current_user()
    conn = get_db_connection()
    assignments = conn.execute("SELECT * FROM assignments ORDER BY id ASC").fetchall()
    submissions = conn.execute("""
        SELECT s.*, a.title as assignment_title
        FROM submissions s
        LEFT JOIN assignments a ON s.assignment_id = a.id
        WHERE s.user_id = ?
        ORDER BY s.created_at DESC
    """, (user['id'],)).fetchall()
    certificates = conn.execute("""
        SELECT c.*, a.title as assignment_title
        FROM certificates c
        JOIN assignments a ON c.assignment_id = a.id
        WHERE c.user_id = ?
    """, (user['id'],)).fetchall()
    conn.close()

    parsed_assignments = []
    for a in assignments:
        d = dict(a)
        try:
            d['public_test_cases_list'] = json.loads(d.get('public_test_cases') or '[]')
        except Exception:
            d['public_test_cases_list'] = []
        try:
            d['common_errors_list'] = json.loads(d.get('common_errors') or '[]')
        except Exception:
            d['common_errors_list'] = []
        parsed_assignments.append(d)

    return render_template('student_dashboard.html', assignments=parsed_assignments, submissions=submissions, certificates=certificates)

@app.route('/faculty/dashboard')
@role_required(['faculty', 'admin'])
def faculty_dashboard():
    conn = get_db_connection()
    assignments = conn.execute("SELECT * FROM assignments ORDER BY created_at DESC").fetchall()
    submissions = conn.execute("""
        SELECT s.*, u.username, a.title as assignment_title
        FROM submissions s
        JOIN users u ON s.user_id = u.id
        LEFT JOIN assignments a ON s.assignment_id = a.id
        ORDER BY s.created_at DESC
    """).fetchall()
    students_count = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'student'").fetchone()['cnt']
    conn.close()

    return render_template('faculty_dashboard.html', assignments=assignments, submissions=submissions, students_count=students_count)

@app.route('/admin/dashboard')
@role_required(['admin'])
def admin_dashboard():
    conn = get_db_connection()
    users = conn.execute("SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC").fetchall()
    stats = {
        "total_users": conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()['cnt'],
        "total_assignments": conn.execute("SELECT COUNT(*) as cnt FROM assignments").fetchone()['cnt'],
        "total_submissions": conn.execute("SELECT COUNT(*) as cnt FROM submissions").fetchone()['cnt'],
    }
    conn.close()
    return render_template('admin_dashboard.html', users=users, stats=stats)

@app.route('/editor')
def editor_page():
    assignment_id = request.args.get('assignment_id', type=int)
    assignment = None
    if assignment_id:
        conn = get_db_connection()
        assign_row = conn.execute("SELECT * FROM assignments WHERE id = ?", (assignment_id,)).fetchone()
        conn.close()
        if assign_row:
            assignment = dict(assign_row)
            try:
                assignment['public_test_cases_list'] = json.loads(assignment.get('public_test_cases') or '[]')
            except Exception:
                assignment['public_test_cases_list'] = []
            try:
                assignment['common_errors_list'] = json.loads(assignment.get('common_errors') or '[]')
            except Exception:
                assignment['common_errors_list'] = []
    return render_template('editor.html', assignment=assignment)

@app.route('/assignment/<int:assignment_id>')
@login_required
def assignment_details(assignment_id):
    conn = get_db_connection()
    assignment = conn.execute("SELECT * FROM assignments WHERE id = ?", (assignment_id,)).fetchone()
    conn.close()
    if not assignment:
        flash("Assignment not found.", "warning")
        return redirect(url_for('dashboard_router'))
    return render_template('assignment_details.html', assignment=assignment)

@app.route('/leaderboard')
def leaderboard_page():
    return render_template('leaderboard.html')

@app.route('/certificate/<int:submission_id>')
@login_required
def certificate_page(submission_id):
    conn = get_db_connection()
    cert = conn.execute("""
        SELECT c.*, u.username, a.title as assignment_title, s.score
        FROM certificates c
        JOIN users u ON c.user_id = u.id
        JOIN assignments a ON c.assignment_id = a.id
        JOIN submissions s ON c.submission_id = s.id
        WHERE c.submission_id = ?
    """, (submission_id,)).fetchone()
    conn.close()

    if not cert:
        flash("Certificate not found or not eligible yet (Requires passing 100% of test cases on a Question Bank problem).", "warning")
        return redirect(url_for('dashboard_router'))

    return render_template('certificate.html', cert=cert)


# ====================================================
# REST API ENDPOINTS
# ====================================================

@app.route('/api/compile', methods=['POST'])
def api_compile():
    """POST /compile - Executes source code in isolated compiler sandbox."""
    data = request.get_json() or {}
    code = data.get('code', '')
    language = data.get('language', 'python')
    custom_input = data.get('custom_input', '')

    if not code.strip():
        return jsonify(format_api_response(False, message="Source code cannot be empty.")), 400

    result = execute_code(code, language, custom_input)
    return jsonify(format_api_response(True, data=result.to_dict(), message="Code executed successfully."))

@app.route('/api/analyze-code', methods=['POST'])
def api_analyze_code():
    """POST /analyze-code - Performs Lexical, Syntax, AST, Semantic, and Optimization Analysis."""
    data = request.get_json() or {}
    code = data.get('code', '')
    language = data.get('language', 'python')

    analyzer = CompilerAnalyzer(code, language)
    analysis_results = analyzer.analyze_all()

    return jsonify(format_api_response(True, data=analysis_results, message="Compiler analysis completed."))

@app.route('/api/generate-code', methods=['POST'])
def api_generate_code():
    """POST /generate-code - AI Code Generator."""
    data = request.get_json() or {}
    problem = data.get('problem_statement', '')
    constraints = data.get('constraints', '')
    difficulty = data.get('difficulty', 'Medium')
    language = data.get('language', 'python')

    if not problem.strip():
        return jsonify(format_api_response(False, message="Problem statement required.")), 400

    ai_engine = AIEngine()
    gen_result = ai_engine.generate_code(problem, constraints, difficulty, language)

    user_id = session.get('user_id', 1)
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO ai_generations (user_id, problem_statement, constraints, difficulty, generated_code, time_complexity, space_complexity, explanation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, problem, constraints, difficulty, gen_result['generated_code'], gen_result['time_complexity'], gen_result['space_complexity'], gen_result['explanation']))
    conn.commit()
    conn.close()

    return jsonify(format_api_response(True, data=gen_result, message="AI solution generated."))

@app.route('/api/submit', methods=['POST'])
@login_required
def api_submit():
    """POST /submit - Submits student code for automated evaluation and scoring."""
    data = request.get_json() or {}
    raw_assign_id = data.get('assignment_id')
    assignment_id = int(raw_assign_id) if (raw_assign_id and str(raw_assign_id).isdigit()) else None
    code = data.get('code', '')
    language = data.get('language', 'python')
    user_id = session['user_id']

    if not code.strip():
        return jsonify(format_api_response(False, message="Cannot submit empty code.")), 400

    conn = get_db_connection()
    assignment = conn.execute("SELECT * FROM assignments WHERE id = ?", (assignment_id,)).fetchone() if assignment_id else None
    
    if not assignment:
        # Generic submission if no specific assignment
        public_tc = [{"input": "", "expected_output": ""}]
        hidden_tc = []
        assign_title = "Sandbox Submission"
    else:
        public_tc = assignment['public_test_cases']
        hidden_tc = assignment['hidden_test_cases']
        assign_title = assignment['title']

    # Execute Automated Evaluation
    eval_res = evaluate_submission(code, language, public_tc, hidden_tc)

    # Insert submission record
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO submissions (assignment_id, user_id, code, language, status, execution_time, memory_usage, output, score, correctness_score, style_score, ai_probability_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        assignment_id,
        user_id,
        code,
        language,
        "Evaluated",
        eval_res['execution_time'],
        eval_res['memory_usage_mb'],
        f"Passed {eval_res['test_cases_passed']}/{eval_res['total_test_cases']} tests.",
        eval_res['final_score'],
        eval_res['correctness_score'],
        eval_res['style_score'],
        eval_res['ai_probability_score']
    ))
    submission_id = cursor.lastrowid

    # Insert detailed evaluations
    cursor.execute("""
        INSERT INTO evaluations (submission_id, test_cases_passed, total_test_cases, detailed_results, feedback)
        VALUES (?, ?, ?, ?, ?)
    """, (
        submission_id,
        eval_res['test_cases_passed'],
        eval_res['total_test_cases'],
        json.dumps(eval_res['detailed_results']),
        eval_res['feedback']
    ))

    # Certificate Generation ONLY when solving a Question Bank mock question AND 100% test cases passed
    total_tc = eval_res.get('total_test_cases', 0)
    passed_tc = eval_res.get('test_cases_passed', 0)
    is_cert_eligible = bool(assignment_id and assignment and total_tc > 0 and passed_tc == total_tc)

    cert_id = None
    if is_cert_eligible:
        cert_code = generate_certificate_code()
        cursor.execute("""
            INSERT INTO certificates (user_id, assignment_id, submission_id, certificate_code)
            VALUES (?, ?, ?, ?)
        """, (user_id, assignment_id, submission_id, cert_code))
        cert_id = cursor.lastrowid

    # Update coding style fingerprint
    fingerprint = extract_coding_fingerprint(code)
    cursor.execute("UPDATE users SET style_fingerprint = ? WHERE id = ?", (json.dumps(fingerprint), user_id))

    conn.commit()
    conn.close()

    eval_res['submission_id'] = submission_id
    eval_res['certificate_eligible'] = is_cert_eligible

    return jsonify(format_api_response(True, data=eval_res, message="Submission evaluated successfully."))

@app.route('/api/compare', methods=['POST'])
def api_compare():
    """POST /compare - Student Code VS AI Generated Code comparison."""
    data = request.get_json() or {}
    student_code = data.get('student_code', '')
    ai_code = data.get('ai_code', '')
    language = data.get('language', 'python')

    comparison_results = compare_student_vs_ai(student_code, ai_code, language)
    return jsonify(format_api_response(True, data=comparison_results, message="Comparison completed."))

@app.route('/api/plagiarism', methods=['POST'])
def api_plagiarism():
    """POST /plagiarism - Plagiarism scan across existing student submissions."""
    data = request.get_json() or {}
    source_code = data.get('code', '')
    submission_id = data.get('submission_id')

    detector = PlagiarismDetector()

    conn = get_db_connection()
    other_submissions = conn.execute("""
        SELECT s.id, s.code, u.username
        FROM submissions s
        JOIN users u ON s.user_id = u.id
        WHERE s.id != ?
        ORDER BY s.created_at DESC LIMIT 50
    """, (submission_id or 0,)).fetchall()

    highest_match = None
    max_sim = 0.0

    for sub in other_submissions:
        res = detector.check_plagiarism(source_code, sub['code'])
        if res['overall_similarity'] > max_sim:
            max_sim = res['overall_similarity']
            highest_match = {
                "matched_submission_id": sub['id'],
                "matched_user": sub['username'],
                "details": res
            }

    conn.close()

    if not highest_match:
        highest_match = {
            "matched_user": "None",
            "details": detector.check_plagiarism(source_code, source_code)
        }

    return jsonify(format_api_response(True, data=highest_match, message="Plagiarism detection scan finished."))

@app.route('/api/analytics', methods=['GET'])
@role_required(['faculty', 'admin'])
def api_analytics():
    """GET /analytics - Faculty Dashboard Analytics for Chart.js."""
    conn = get_db_connection()
    
    total_students = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'student'").fetchone()['cnt']
    total_submissions = conn.execute("SELECT COUNT(*) as cnt FROM submissions").fetchone()['cnt']
    avg_score = conn.execute("SELECT AVG(score) as avg FROM submissions").fetchone()['avg'] or 0.0

    # Top performers
    top_performers = conn.execute("""
        SELECT u.username, MAX(s.score) as top_score, COUNT(s.id) as sub_count
        FROM submissions s
        JOIN users u ON s.user_id = u.id
        GROUP BY u.id
        ORDER BY top_score DESC LIMIT 5
    """).fetchall()

    # Language usage distribution
    lang_dist = conn.execute("""
        SELECT language, COUNT(*) as count
        FROM submissions
        GROUP BY language
    """).fetchall()

    # Score distribution brackets
    score_brackets = conn.execute("""
        SELECT 
            SUM(CASE WHEN score >= 80 THEN 1 ELSE 0 END) as excellent,
            SUM(CASE WHEN score >= 50 AND score < 80 THEN 1 ELSE 0 END) as good,
            SUM(CASE WHEN score < 50 THEN 1 ELSE 0 END) as needs_improvement
        FROM submissions
    """).fetchone()

    conn.close()

    analytics_data = {
        "total_students": total_students,
        "total_submissions": total_submissions,
        "avg_score": round(avg_score, 1),
        "top_performers": [dict(tp) for tp in top_performers],
        "language_usage": {row['language']: row['count'] for row in lang_dist},
        "score_distribution": {
            "Excellent (80-100)": score_brackets['excellent'] or 0,
            "Good (50-79)": score_brackets['good'] or 0,
            "Needs Improvement (<50)": score_brackets['needs_improvement'] or 0
        }
    }

    return jsonify(format_api_response(True, data=analytics_data))

@app.route('/api/leaderboard', methods=['GET'])
def api_leaderboard():
    """GET /leaderboard - Real-time student leaderboard with individual current standing."""
    current_u = get_current_user()
    current_user_id = current_u['id'] if current_u else None

    conn = get_db_connection()
    rankings = conn.execute("""
        SELECT u.id as user_id, u.username, u.email,
               MAX(s.score) as highest_score,
               (SELECT s2.score FROM submissions s2 WHERE s2.user_id = u.id ORDER BY s2.created_at DESC, s2.id DESC LIMIT 1) as latest_score,
               AVG(s.score) as avg_score,
               COUNT(s.id) as submissions_count,
               MAX(s.created_at) as last_active
        FROM submissions s
        JOIN users u ON s.user_id = u.id
        WHERE u.role = 'student'
        GROUP BY u.id
        ORDER BY highest_score DESC, latest_score DESC, avg_score DESC
        LIMIT 50
    """).fetchall()

    user_standing = None
    if current_u:
        # Check if user is in rankings
        for idx, r in enumerate(rankings):
            if r['user_id'] == current_user_id:
                user_standing = {
                    "rank": idx + 1,
                    "username": r['username'],
                    "highest_score": r['highest_score'],
                    "latest_score": r['latest_score'],
                    "avg_score": round(r['avg_score'], 1) if r['avg_score'] is not None else 0.0,
                    "submissions_count": r['submissions_count'],
                    "last_active": r['last_active']
                }
                break
        
        # If user has submissions but not in top 50, calculate personal rank
        if not user_standing:
            user_subs = conn.execute("SELECT COUNT(*) as cnt, MAX(score) as max_s, AVG(score) as avg_s FROM submissions WHERE user_id = ?", (current_user_id,)).fetchone()
            if user_subs and user_subs['cnt'] > 0:
                latest_s = conn.execute("SELECT score, created_at FROM submissions WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT 1", (current_user_id,)).fetchone()
                user_standing = {
                    "rank": "50+",
                    "username": current_u['username'],
                    "highest_score": user_subs['max_s'],
                    "latest_score": latest_s['score'] if latest_s else user_subs['max_s'],
                    "avg_score": round(user_subs['avg_s'], 1) if user_subs['avg_s'] is not None else 0.0,
                    "submissions_count": user_subs['cnt'],
                    "last_active": latest_s['created_at'] if latest_s else "N/A"
                }
            else:
                user_standing = {
                    "rank": "Unranked",
                    "username": current_u['username'],
                    "highest_score": 0,
                    "latest_score": 0,
                    "avg_score": 0,
                    "submissions_count": 0,
                    "last_active": "No submissions yet"
                }

    conn.close()

    rank_list = []
    for r in rankings:
        d = dict(r)
        d['is_current_user'] = (current_user_id is not None and d['user_id'] == current_user_id)
        d['avg_score'] = round(d['avg_score'], 1) if d['avg_score'] is not None else 0.0
        rank_list.append(d)

    return jsonify(format_api_response(True, data={
        "rankings": rank_list,
        "current_user_standing": user_standing,
        "current_user_id": current_user_id
    }))

@app.route('/api/hints', methods=['POST'])
def api_hints():
    """POST /hints - Deterministic, non-AI rule-based and AST-driven problem hints and code diagnostics."""
    data = request.get_json() or {}
    code = data.get('code', '')
    language = data.get('language', 'python')
    compiler_output = data.get('output', '') or data.get('compiler_output', '')
    assignment_id = data.get('assignment_id')
    problem_statement = data.get('problem_statement', '')

    problem_title = ""
    problem_desc = problem_statement

    if assignment_id:
        try:
            conn = get_db_connection()
            assignment = conn.execute("SELECT title, description FROM assignments WHERE id = ?", (assignment_id,)).fetchone()
            conn.close()
            if assignment:
                problem_title = assignment['title']
                problem_desc = assignment['description']
        except Exception:
            pass

    hints_data = HintEngine.get_hints(
        code=code,
        language=language,
        compiler_output=compiler_output,
        problem_title=problem_title,
        problem_desc=problem_desc
    )
    return jsonify(format_api_response(True, data=hints_data, message="Hints generated successfully."))

@app.route('/api/ai/interview-questions', methods=['POST'])
def api_ai_interview():
    """POST /ai/interview-questions - Generates AI interview questions."""
    ai = AIEngine()
    questions = ai.generate_interview_questions()
    return jsonify(format_api_response(True, data=questions))

@app.route('/api/assignments/create', methods=['POST'])
@role_required(['faculty', 'admin'])
def api_create_assignment():
    """POST /assignments/create - Faculty assignment creation endpoint."""
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    constraints = data.get('constraints', '')
    difficulty = data.get('difficulty', 'Medium')
    language = data.get('language', 'python')
    template_code = data.get('template_code', '')
    public_tc = data.get('public_test_cases', [])
    hidden_tc = data.get('hidden_test_cases', [])

    if not title or not description:
        return jsonify(format_api_response(False, message="Title and description are required.")), 400

    user_id = session['user_id']
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO assignments (title, description, constraints, difficulty, language, template_code, public_test_cases, hidden_test_cases, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title, description, constraints, difficulty, language, template_code,
        json.dumps(public_tc), json.dumps(hidden_tc), user_id
    ))
    conn.commit()
    conn.close()

    return jsonify(format_api_response(True, message="Assignment created successfully."))

@app.route('/api/reports/pdf/<int:submission_id>')
@login_required
def api_report_pdf(submission_id):
    """GET /reports/pdf/<id> - Download downloadable PDF evaluation report."""
    current_u = get_current_user()
    conn = get_db_connection()
    sub = conn.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,)).fetchone()
    if not sub:
        conn.close()
        return jsonify({"error": "Submission not found"}), 404

    # Check permission: students can only access their own submissions, faculty/admins can view any
    if current_u['role'] == 'student' and sub['user_id'] != current_u['id']:
        conn.close()
        return jsonify({"error": "Unauthorized access to submission report."}), 403

    user = conn.execute("SELECT * FROM users WHERE id = ?", (sub['user_id'],)).fetchone()
    assignment = conn.execute("SELECT * FROM assignments WHERE id = ?", (sub['assignment_id'],)).fetchone() if sub['assignment_id'] else None
    evaluation = conn.execute("SELECT * FROM evaluations WHERE submission_id = ?", (submission_id,)).fetchone()
    conn.close()

    filepath = generate_pdf_report(
        dict(sub),
        dict(user) if user else {},
        dict(assignment) if assignment else {},
        dict(evaluation) if evaluation else None
    )

    return send_file(
        filepath,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f"CodeVision_Report_Sub_{submission_id}.pdf"
    )

@app.route('/api/reports/csv')
@role_required(['faculty', 'admin'])
def api_report_csv():
    """GET /reports/csv - Export CSV gradebook of all student submissions."""
    conn = get_db_connection()
    submissions = conn.execute("""
        SELECT s.*, u.username, a.title as assignment_title
        FROM submissions s
        JOIN users u ON s.user_id = u.id
        LEFT JOIN assignments a ON s.assignment_id = a.id
        ORDER BY s.created_at DESC
    """).fetchall()
    conn.close()

    csv_data = generate_csv_export([dict(s) for s in submissions])
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = "attachment; filename=codevision_gradebook.csv"
    response.headers["Content-type"] = "text/csv"
    return response

if __name__ == '__main__':
    print("Starting CodeVision AI Platform on http://127.0.0.1:5000 ...")
    app.run(debug=True, host='127.0.0.1', port=5000)
