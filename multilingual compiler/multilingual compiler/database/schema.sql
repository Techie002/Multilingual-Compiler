-- CodeVision AI Database Schema (SQLite)

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student', 'faculty', 'admin')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    style_fingerprint TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    constraints TEXT,
    difficulty TEXT CHECK(difficulty IN ('Easy', 'Medium', 'Hard', 'Expert')),
    language TEXT DEFAULT 'python',
    template_code TEXT,
    public_test_cases TEXT NOT NULL, -- JSON string array of {input, expected_output}
    hidden_test_cases TEXT NOT NULL, -- JSON string array of {input, expected_output}
    common_errors TEXT, -- JSON array of common errors / edge cases
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deadline TIMESTAMP,
    FOREIGN KEY(created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER,
    user_id INTEGER NOT NULL,
    code TEXT NOT NULL,
    language TEXT NOT NULL,
    status TEXT DEFAULT 'Submitted', -- 'Submitted', 'Evaluated', 'Error'
    execution_time REAL DEFAULT 0.0,
    memory_usage REAL DEFAULT 0.0,
    output TEXT,
    score REAL DEFAULT 0.0,
    correctness_score REAL DEFAULT 0.0,
    style_score REAL DEFAULT 0.0,
    ai_probability_score REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(assignment_id) REFERENCES assignments(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL,
    test_cases_passed INTEGER DEFAULT 0,
    total_test_cases INTEGER DEFAULT 0,
    detailed_results TEXT, -- JSON string of individual test case results
    feedback TEXT,
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(submission_id) REFERENCES submissions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    submission_id INTEGER,
    report_type TEXT NOT NULL, -- 'PDF', 'CSV'
    file_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(submission_id) REFERENCES submissions(id)
);

CREATE TABLE IF NOT EXISTS ai_generations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    problem_statement TEXT NOT NULL,
    constraints TEXT,
    difficulty TEXT,
    generated_code TEXT NOT NULL,
    time_complexity TEXT,
    space_complexity TEXT,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS plagiarism_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL,
    compare_submission_id INTEGER NOT NULL,
    overall_similarity REAL NOT NULL,
    token_similarity REAL NOT NULL,
    ast_similarity REAL NOT NULL,
    cosine_similarity REAL NOT NULL,
    match_details TEXT, -- JSON breakdown of matching regions
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(submission_id) REFERENCES submissions(id),
    FOREIGN KEY(compare_submission_id) REFERENCES submissions(id)
);

CREATE TABLE IF NOT EXISTS certificates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    assignment_id INTEGER NOT NULL,
    submission_id INTEGER NOT NULL,
    certificate_code TEXT UNIQUE NOT NULL,
    issue_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pdf_path TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(assignment_id) REFERENCES assignments(id),
    FOREIGN KEY(submission_id) REFERENCES submissions(id)
);
