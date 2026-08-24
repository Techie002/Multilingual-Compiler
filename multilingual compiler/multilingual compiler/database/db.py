import sqlite3
import os
import json
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database.db')
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')

def get_db_connection():
    """Establishes and returns a sqlite3 connection with dictionary row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema and seeds initial sample data if empty."""
    conn = get_db_connection()
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()

    # Always ensure template_code is empty for clean IDE experience
    cursor = conn.cursor()
    cursor.execute("UPDATE assignments SET template_code = '' WHERE template_code IS NOT NULL AND template_code != ''")
    conn.commit()

    # Seed default data if users table is empty
    cursor.execute("SELECT COUNT(*) as count FROM users")
    if cursor.fetchone()['count'] == 0:
        seed_database(conn)

    conn.close()

def seed_database(conn):
    """Seeds initial users, assignments, and sample submissions for testing."""
    cursor = conn.cursor()

    # Create default users if not existing
    admin_pw = generate_password_hash("admin123")
    faculty_pw = generate_password_hash("faculty123")
    student_pw = generate_password_hash("student123")
    student2_pw = generate_password_hash("student123")

    users_to_add = [
        ("admin", "admin@codevision.ai", admin_pw, "admin"),
        ("prof_smith", "smith@codevision.ai", faculty_pw, "faculty"),
        ("alex_dev", "alex@student.edu", student_pw, "student"),
        ("maria_code", "maria@student.edu", student2_pw, "student")
    ]

    for u_name, u_email, u_hash, u_role in users_to_add:
        exists = cursor.execute("SELECT id FROM users WHERE email = ? OR username = ?", (u_email, u_name)).fetchone()
        if not exists:
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            """, (u_name, u_email, u_hash, u_role))

    conn.commit()

    fac = cursor.execute("SELECT id FROM users WHERE role='faculty'").fetchone()
    faculty_id = fac['id'] if fac else 1

    seed_assignments_list(conn, faculty_id)

def seed_assignments_list(conn, faculty_id=1):
    cursor = conn.cursor()

    # ==========================================================
    # MULTI-LANGUAGE CODING QUESTIONS SEED DATA (All Difficulties: Easy, Medium, Hard, Expert)
    # Empty template_code by default so user fills from scratch in the IDE
    # ==========================================================
    sample_assignments = [
        # 1. PYTHON: Factorial Calculation (Easy)
        {
            "title": "Factorial Calculation",
            "description": "Write a program that takes an integer N from standard input and outputs the factorial of N (N!). Special case: 0! = 1.",
            "constraints": "0 <= N <= 15. Time Limit: 2.0s. Memory Limit: 32MB.",
            "difficulty": "Easy",
            "language": "python",
            "template_code": "",
            "public_test_cases": [
                {"input": "5", "expected_output": "120", "explanation": "5! = 5 * 4 * 3 * 2 * 1 = 120"},
                {"input": "0", "expected_output": "1", "explanation": "0! is mathematically defined as 1"}
            ],
            "hidden_test_cases": [
                {"input": "1", "expected_output": "1"},
                {"input": "7", "expected_output": "5040"},
                {"input": "10", "expected_output": "3628800"}
            ],
            "common_errors": [
                "Returning 0 instead of 1 for 0! (base case error)",
                "Maximum recursion depth exceeded on recursive calls without base case",
                "Forgetting to parse sys.stdin.read() with int() causing TypeError",
                "Formatting output with extra text/prompt strings instead of pure number"
            ]
        },
        # 2. PYTHON: Valid Palindrome String (Easy)
        {
            "title": "Valid Palindrome String",
            "description": "Given a string from standard input, determine if it is a palindrome, considering only alphanumeric characters and ignoring cases. Output 'True' or 'False'.",
            "constraints": "1 <= s.length <= 2 * 10^5. String consists only of printable ASCII characters.",
            "difficulty": "Easy",
            "language": "python",
            "template_code": "",
            "public_test_cases": [
                {"input": "A man, a plan, a canal: Panama", "expected_output": "True", "explanation": "'amanaplanacanalpanama' is a palindrome"},
                {"input": "race a car", "expected_output": "False", "explanation": "'raceacar' is not a palindrome"}
            ],
            "hidden_test_cases": [
                {"input": " ", "expected_output": "True"},
                {"input": "0P", "expected_output": "False"},
                {"input": "Madam, I'm Adam", "expected_output": "True"}
            ],
            "common_errors": [
                "Failing to strip non-alphanumeric characters like commas, colons, and spaces",
                "Case sensitivity mismatch (e.g., 'A' != 'a')",
                "Index out of bounds on empty input string",
                "Outputting 1/0 or true/false (lowercase) instead of exact True/False"
            ]
        },
        # 3. PYTHON: Two Sum Problem (Medium)
        {
            "title": "Two Sum Problem",
            "description": "Given an array of integers and an integer target on separate input lines, output the 0-based indices of the two numbers such that they add up to target formatted as [i, j].",
            "constraints": "2 <= nums.length <= 10^4, -10^9 <= nums[i] <= 10^9. Exactly one valid answer exists.",
            "difficulty": "Medium",
            "language": "python",
            "template_code": "",
            "public_test_cases": [
                {"input": "[2, 7, 11, 15]\n9", "expected_output": "[0, 1]", "explanation": "nums[0] + nums[1] == 2 + 7 == 9"},
                {"input": "[3, 2, 4]\n6", "expected_output": "[1, 2]", "explanation": "nums[1] + nums[2] == 2 + 4 == 6"}
            ],
            "hidden_test_cases": [
                {"input": "[3, 3]\n6", "expected_output": "[0, 1]"},
                {"input": "[1, 5, 8, 12, 19]\n20", "expected_output": "[0, 4]"}
            ],
            "common_errors": [
                "Reusing the same element twice (e.g. index [0, 0] when target is 2*nums[0])",
                "O(N^2) nested loops exceeding execution time limit on 10,000 element arrays",
                "Formatting output with spaces like '[0, 1]' vs '[0, 1]' (use json.dumps)"
            ]
        },
        # 4. PYTHON: Longest Increasing Subsequence (Hard)
        {
            "title": "Longest Increasing Subsequence (LIS)",
            "description": "Given an integer array on standard input (JSON format or space-separated), return the length of the longest strictly increasing subsequence in O(N log N) or O(N^2) time.",
            "constraints": "1 <= nums.length <= 2500, -10^4 <= nums[i] <= 10^4.",
            "difficulty": "Hard",
            "language": "python",
            "template_code": "",
            "public_test_cases": [
                {"input": "[10, 9, 2, 5, 3, 7, 101, 18]", "expected_output": "4", "explanation": "The longest increasing subsequence is [2, 3, 7, 101], therefore the length is 4."},
                {"input": "[0, 1, 0, 3, 2, 3]", "expected_output": "4", "explanation": "The longest increasing subsequence is [0, 1, 2, 3], length 4."}
            ],
            "hidden_test_cases": [
                {"input": "[7, 7, 7, 7, 7, 7, 7]", "expected_output": "1"},
                {"input": "[1, 3, 6, 7, 9, 4, 10, 5, 6]", "expected_output": "6"},
                {"input": "[4, 10, 4, 3, 8, 9]", "expected_output": "3"}
            ],
            "common_errors": [
                "Confusing contiguous subarray with non-contiguous subsequence",
                "Non-strictly increasing (allowing equal adjacent elements)",
                "Time limit exceeded on large arrays with exponential recursion without memoization"
            ]
        },
        # 5. PYTHON: Word Search II & Trie Backtracking (Expert)
        {
            "title": "Word Search & Grid Path Traversal",
            "description": "Given an M x N grid of characters as JSON and a target word string, return 'True' if the word exists in the grid constructed from sequentially adjacent cells (horizontally or vertically neighboring), where the same letter cell may not be used more than once. Otherwise print 'False'.",
            "constraints": "1 <= m, n <= 10, 1 <= word.length <= 15.",
            "difficulty": "Expert",
            "language": "python",
            "template_code": "",
            "public_test_cases": [
                {"input": "[[\"A\",\"B\",\"C\",\"E\"],[\"S\",\"F\",\"C\",\"S\"],[\"A\",\"D\",\"E\",\"E\"]]\nABCCED", "expected_output": "True", "explanation": "Path A -> B -> C -> C -> E -> D exists"},
                {"input": "[[\"A\",\"B\",\"C\",\"E\"],[\"S\",\"F\",\"C\",\"S\"],[\"A\",\"D\",\"E\",\"E\"]]\nABCB", "expected_output": "False", "explanation": "Cannot reuse cell 'B'"}
            ],
            "hidden_test_cases": [
                {"input": "[[\"A\",\"B\",\"C\",\"E\"],[\"S\",\"F\",\"E\",\"S\"],[\"A\",\"D\",\"E\",\"E\"]]\nABCESEEEFS", "expected_output": "True"},
                {"input": "[[\"a\"]]\na", "expected_output": "True"}
            ],
            "common_errors": [
                "Revisiting visited cells without marking/backtracking state",
                "Index out of bounds on grid boundary checks",
                "Failing to clean up visited matrix on backtracking"
            ]
        },
        # 6. C: Reverse an Array in Place (Easy)
        {
            "title": "Reverse an Array in Place",
            "description": "Given integer N followed by N space-separated integers on standard input, reverse the array in place and print the reversed elements separated by single spaces.",
            "constraints": "1 <= N <= 1000. Each element fits in standard 32-bit signed integer.",
            "difficulty": "Easy",
            "language": "c",
            "template_code": "",
            "public_test_cases": [
                {"input": "5\n1 2 3 4 5", "expected_output": "5 4 3 2 1", "explanation": "Reversing [1, 2, 3, 4, 5] yields [5, 4, 3, 2, 1]"},
                {"input": "1\n42", "expected_output": "42", "explanation": "Single element array remains unchanged"}
            ],
            "hidden_test_cases": [
                {"input": "4\n10 20 30 40", "expected_output": "40 30 20 10"},
                {"input": "6\n-1 -2 -3 -4 -5 -6", "expected_output": "-6 -5 -4 -3 -2 -1"}
            ],
            "common_errors": [
                "Buffer overflow by accessing arr[n] (out of bounds index)",
                "Double-swapping elements by iterating all the way to N instead of N/2",
                "Trailing whitespace formatting issues at the end of output line",
                "Failing to handle negative integer elements correctly"
            ]
        },
        # 7. C: Matrix Transpose (Medium)
        {
            "title": "Matrix Transpose",
            "description": "Given row count R and column count C followed by an R x C matrix, output its transposed C x R matrix where rows and columns are flipped.",
            "constraints": "1 <= R, C <= 50. All matrix values are integers.",
            "difficulty": "Medium",
            "language": "c",
            "template_code": "",
            "public_test_cases": [
                {"input": "2 3\n1 2 3\n4 5 6", "expected_output": "1 4\n2 5\n3 6", "explanation": "2x3 matrix transposed into 3x2 matrix"},
                {"input": "2 2\n1 0\n0 1", "expected_output": "1 0\n0 1", "explanation": "Identity matrix transpose equals itself"}
            ],
            "hidden_test_cases": [
                {"input": "3 1\n10\n20\n30", "expected_output": "10 20 30"},
                {"input": "1 3\n5 10 15", "expected_output": "5\n10\n15"}
            ],
            "common_errors": [
                "Swapping loop variable bounds (e.g. iterating i < r in column outer loop)",
                "Segment violation when dimensions R != C if allocating square matrix without bounds check",
                "Printing extra empty lines at end of output"
            ]
        },
        # 8. C++: Binary Search Algorithm (Easy)
        {
            "title": "Binary Search Algorithm",
            "description": "Given N sorted integers and a target key K on standard input, perform logarithmic O(log N) binary search and print the 0-based index of K. If K is not present, print -1.",
            "constraints": "1 <= N <= 10^5. Input array is strictly sorted in ascending order.",
            "difficulty": "Easy",
            "language": "cpp",
            "template_code": "",
            "public_test_cases": [
                {"input": "5\n1 3 5 7 9\n7", "expected_output": "3", "explanation": "7 is found at index 3"},
                {"input": "5\n1 3 5 7 9\n2", "expected_output": "-1", "explanation": "2 is not present in the array"}
            ],
            "hidden_test_cases": [
                {"input": "1\n100\n100", "expected_output": "0"},
                {"input": "6\n-10 -5 0 5 10 15\n-10", "expected_output": "0"},
                {"input": "6\n-10 -5 0 5 10 15\n20", "expected_output": "-1"}
            ],
            "common_errors": [
                "Integer overflow bug in `(low + high) / 2` with large indices; always use `low + (high - low) / 2`",
                "Infinite while loop if failing to adjust `low = mid + 1` or `high = mid - 1`",
                "Off-by-one errors with loop condition `low < high` instead of `low <= high`"
            ]
        },
        # 9. C++: Valid Parentheses Stack (Medium)
        {
            "title": "Valid Parentheses Stack",
            "description": "Given a string containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string has valid matching brackets. Print 'Valid' or 'Invalid'.",
            "constraints": "1 <= s.length <= 10^4. String consists of parentheses only.",
            "difficulty": "Medium",
            "language": "cpp",
            "template_code": "",
            "public_test_cases": [
                {"input": "()[]{}", "expected_output": "Valid", "explanation": "Every bracket is closed in correct order"},
                {"input": "(]", "expected_output": "Invalid", "explanation": "Mismatched bracket types"}
            ],
            "hidden_test_cases": [
                {"input": "([{}])", "expected_output": "Valid"},
                {"input": ")(", "expected_output": "Invalid"},
                {"input": "(((((", "expected_output": "Invalid"}
            ],
            "common_errors": [
                "Segmentation fault when accessing `st.top()` on an empty stack",
                "Returning true when opening brackets remain unclosed in the stack at the end",
                "Printing 'true/false' instead of exact 'Valid' or 'Invalid'"
            ]
        },
        # 10. C++: Trapping Rain Water (Hard)
        {
            "title": "Trapping Rain Water",
            "description": "Given N non-negative integers representing an elevation map where the width of each bar is 1, compute how much water it can trap after raining.",
            "constraints": "1 <= N <= 2 * 10^4, 0 <= height[i] <= 10^5.",
            "difficulty": "Hard",
            "language": "cpp",
            "template_code": "",
            "public_test_cases": [
                {"input": "12\n0 1 0 2 1 0 1 3 2 1 2 1", "expected_output": "6", "explanation": "The elevation map traps 6 units of rain water."},
                {"input": "6\n4 2 0 3 2 5", "expected_output": "9", "explanation": "Traps 9 units of rain water."}
            ],
            "hidden_test_cases": [
                {"input": "3\n2 0 2", "expected_output": "2"},
                {"input": "1\n5", "expected_output": "0"},
                {"input": "4\n3 0 0 3", "expected_output": "6"}
            ],
            "common_errors": [
                "O(N^2) brute force exceeding runtime limit (use two-pointer or monotonic stack approach in O(N))",
                "Boundary bars incorrectly accumulating water without an outer wall"
            ]
        },
        # 11. C++: Matrix Chain Multiplication (Expert)
        {
            "title": "Matrix Chain Multiplication DP",
            "description": "Given an array `p[]` of dimensions of size N representing matrices A1, A2, ..., AN-1 where matrix Ai has dimension p[i-1] x p[i], find the minimum number of scalar multiplications needed to multiply the chain.",
            "constraints": "2 <= N <= 100, 1 <= p[i] <= 500.",
            "difficulty": "Expert",
            "language": "cpp",
            "template_code": "",
            "public_test_cases": [
                {"input": "5\n40 20 30 10 30", "expected_output": "26000", "explanation": "Optimal parenthesization requires 26,000 multiplications"},
                {"input": "5\n10 20 30 40 30", "expected_output": "30000", "explanation": "Minimum scalar multiplications is 30,000"}
            ],
            "hidden_test_cases": [
                {"input": "4\n10 30 5 60", "expected_output": "4500"},
                {"input": "3\n10 20 30", "expected_output": "6000"}
            ],
            "common_errors": [
                "Incorrect diagonal DP traversal order",
                "Off-by-one matrix indexing causing segment violation",
                "Integer overflow on large multiplication counts (use long long)"
            ]
        },
        # 12. JAVA: Fibonacci Number DP (Easy)
        {
            "title": "Fibonacci Number DP",
            "description": "Calculate the N-th Fibonacci number where F(0)=0, F(1)=1, and F(N)=F(N-1)+F(N-2). Read N from standard input and print F(N).",
            "constraints": "0 <= N <= 30. Time Limit: 2.0s. Memory Limit: 64MB.",
            "difficulty": "Easy",
            "language": "java",
            "template_code": "",
            "public_test_cases": [
                {"input": "0", "expected_output": "0", "explanation": "F(0) = 0"},
                {"input": "6", "expected_output": "8", "explanation": "F(6) = 0, 1, 1, 2, 3, 5, 8"}
            ],
            "hidden_test_cases": [
                {"input": "1", "expected_output": "1"},
                {"input": "10", "expected_output": "55"},
                {"input": "15", "expected_output": "610"}
            ],
            "common_errors": [
                "Exponential O(2^N) time limit exceeded using naive recursion without memoization",
                "Incorrect handling of base case N=0 returning 1 instead of 0",
                "ClassName mismatch (must use `public class Solution` or standard entry point)"
            ]
        },
        # 13. JAVA: Reverse Words in a String (Medium)
        {
            "title": "Reverse Words in a String",
            "description": "Given an input string s from standard input, reverse the order of the words. Words should be separated by a single space with leading and trailing spaces removed.",
            "constraints": "1 <= s.length <= 10^4. Contains English letters, digits, and spaces.",
            "difficulty": "Medium",
            "language": "java",
            "template_code": "",
            "public_test_cases": [
                {"input": "the sky is blue", "expected_output": "blue is sky the", "explanation": "Words reversed in place"},
                {"input": "  hello world  ", "expected_output": "world hello", "explanation": "Leading/trailing spaces trimmed"}
            ],
            "hidden_test_cases": [
                {"input": "a good   example", "expected_output": "example good a"},
                {"input": "single", "expected_output": "single"}
            ],
            "common_errors": [
                "Leaving multiple consecutive spaces between words in output",
                "Failing to trim leading or trailing spaces from input",
                "Empty string array elements produced when splitting with single space instead of `\\s+`"
            ]
        },
        # 14. JAVASCRIPT: Flatten Nested Array (Medium)
        {
            "title": "Flatten Nested Array",
            "description": "Given a JSON array of arbitrarily nested arrays on standard input, flatten it into a single-dimensional array and print the resulting JSON string.",
            "constraints": "Array depth up to 10. Contains integer elements.",
            "difficulty": "Medium",
            "language": "javascript",
            "template_code": "",
            "public_test_cases": [
                {"input": "[1, [2, [3, 4], 5]]", "expected_output": "[1,2,3,4,5]", "explanation": "Nested arrays flattened into single dimensional array"},
                {"input": "[[1, 2], [3, 4]]", "expected_output": "[1,2,3,4]", "explanation": "2D array flattened"}
            ],
            "hidden_test_cases": [
                {"input": "[1, 2, 3]", "expected_output": "[1,2,3]"},
                {"input": "[[[[[42]]]]]", "expected_output": "[42]"},
                {"input": "[]", "expected_output": "[]"}
            ],
            "common_errors": [
                "Using array.flat() with default depth 1 which fails on 3+ level nested structures",
                "Outputting with spaces like '[1, 2, 3]' vs compact '[1,2,3]' (use JSON.stringify)",
                "Stack overflow on deep recursion without base check"
            ]
        },
        # 15. SQL: Second Highest Salary (Medium)
        {
            "title": "Second Highest Salary",
            "description": "Write a SQL query to find the second highest distinct salary from the Employee table. If there is no second highest salary, return NULL.",
            "constraints": "Employee table has columns: id (INT), salary (INT).",
            "difficulty": "Medium",
            "language": "sql",
            "template_code": "",
            "public_test_cases": [
                {"input": "CREATE TABLE Employee (id INT, salary INT);\nINSERT INTO Employee VALUES (1, 100), (2, 200), (3, 300);\nSELECT (SELECT DISTINCT salary FROM Employee ORDER BY salary DESC LIMIT 1 OFFSET 1) AS SecondHighestSalary;", "expected_output": "200", "explanation": "200 is the second highest salary"},
                {"input": "CREATE TABLE Employee (id INT, salary INT);\nINSERT INTO Employee VALUES (1, 100);\nSELECT (SELECT DISTINCT salary FROM Employee ORDER BY salary DESC LIMIT 1 OFFSET 1) AS SecondHighestSalary;", "expected_output": "None", "explanation": "Only 1 salary exists so output is NULL / None"}
            ],
            "hidden_test_cases": [
                {"input": "CREATE TABLE Employee (id INT, salary INT);\nINSERT INTO Employee VALUES (1, 300), (2, 300), (3, 200);\nSELECT (SELECT DISTINCT salary FROM Employee ORDER BY salary DESC LIMIT 1 OFFSET 1) AS SecondHighestSalary;", "expected_output": "200"}
            ],
            "common_errors": [
                "Forgetting DISTINCT keyword causing duplicate top salaries to be returned as second highest",
                "Not wrapping in subquery causing empty result set instead of NULL when no 2nd record exists"
            ]
        },
        # 16. SQL: Department Top 3 Salaries (Hard)
        {
            "title": "Department Top Earners (Window Functions)",
            "description": "Given Employee (id, name, salary, departmentId) and Department (id, name) tables, write a SQL query to find employees who earn top salaries in each department using DENSE_RANK or subqueries.",
            "constraints": "Standard ANSI SQL with SQLite Window Functions / Subqueries.",
            "difficulty": "Hard",
            "language": "sql",
            "template_code": "",
            "public_test_cases": [
                {"input": "CREATE TABLE Department (id INT, name TEXT);\nCREATE TABLE Employee (id INT, name TEXT, salary INT, departmentId INT);\nINSERT INTO Department VALUES (1, 'IT'), (2, 'Sales');\nINSERT INTO Employee VALUES (1, 'Joe', 85000, 1), (2, 'Henry', 80000, 2), (3, 'Sam', 60000, 2), (4, 'Max', 90000, 1);\nSELECT d.name AS Department, e.name AS Employee, e.salary AS Salary FROM Employee e JOIN Department d ON e.departmentId = d.id WHERE (SELECT COUNT(DISTINCT e2.salary) FROM Employee e2 WHERE e2.departmentId = e.departmentId AND e2.salary > e.salary) < 1 ORDER BY Department, Salary DESC;", "expected_output": "IT | Max | 90000\nSales | Henry | 80000", "explanation": "Top earner for IT is Max, Sales is Henry"}
            ],
            "hidden_test_cases": [
                {"input": "CREATE TABLE Department (id INT, name TEXT);\nCREATE TABLE Employee (id INT, name TEXT, salary INT, departmentId INT);\nINSERT INTO Department VALUES (1, 'Eng');\nINSERT INTO Employee VALUES (1, 'Alice', 100000, 1);\nSELECT d.name AS Department, e.name AS Employee, e.salary AS Salary FROM Employee e JOIN Department d ON e.departmentId = d.id ORDER BY Salary DESC;", "expected_output": "Eng | Alice | 100000"}
            ],
            "common_errors": [
                "Using simple LIMIT 3 which applies to the whole table instead of partitioned per department",
                "Handling duplicate ties in salary incorrectly without DENSE_RANK"
            ]
        },
        # 17. GO: Slice Deduplication (Easy)
        {
            "title": "Slice Deduplication",
            "description": "Given space-separated integers on standard input, print the elements with duplicates removed while strictly preserving their original first-occurrence order.",
            "constraints": "1 <= N <= 10^4. Integer elements fit in standard 32-bit int.",
            "difficulty": "Easy",
            "language": "go",
            "template_code": "",
            "public_test_cases": [
                {"input": "1 2 2 3 4 4 5", "expected_output": "1 2 3 4 5", "explanation": "Duplicates 2 and 4 removed"},
                {"input": "10 10 10", "expected_output": "10", "explanation": "Only single 10 preserved"}
            ],
            "hidden_test_cases": [
                {"input": "5 4 3 2 1", "expected_output": "5 4 3 2 1"},
                {"input": "-1 2 -1 3 2", "expected_output": "-1 2 3"}
            ],
            "common_errors": [
                "Sorting the slice which breaks the original order requirement",
                "Not handling negative integer values in string parsing"
            ]
        },
        # 18. RUST: Vector Partition Even and Odd (Easy)
        {
            "title": "Vector Partition Even and Odd",
            "description": "Given space-separated integers on standard input, output two lines: the first line containing all even integers, and the second line containing all odd integers in their original order.",
            "constraints": "1 <= N <= 1000. Elements are integers.",
            "difficulty": "Easy",
            "language": "rust",
            "template_code": "",
            "public_test_cases": [
                {"input": "1 2 3 4 5 6", "expected_output": "2 4 6\n1 3 5", "explanation": "Evens on line 1, odds on line 2"},
                {"input": "2 4 6", "expected_output": "2 4 6\n", "explanation": "All even numbers"}
            ],
            "hidden_test_cases": [
                {"input": "1 3 5", "expected_output": "\n1 3 5"},
                {"input": "-2 -1 0 1 2", "expected_output": "-2 0 2\n-1 1"}
            ],
            "common_errors": [
                "Negative odd numbers modulo check (in Rust `-1 % 2 == -1`, so check `x % 2 != 0` for odd instead of `x % 2 == 1`)",
                "Ownership and borrowing conflicts when attempting to mutate vector in place"
            ]
        }
    ]

    for item in sample_assignments:
        cursor.execute("""
            INSERT INTO assignments (title, description, constraints, difficulty, language, template_code, public_test_cases, hidden_test_cases, common_errors, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["title"],
            item["description"],
            item["constraints"],
            item["difficulty"],
            item["language"],
            item["template_code"],
            json.dumps(item["public_test_cases"]),
            json.dumps(item["hidden_test_cases"]),
            json.dumps(item["common_errors"]),
            faculty_id
        ))

    conn.commit()

def reseed_assignments():
    """Wipes and reseeds assignments with the updated clean problem set (empty template_code and all difficulties)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS assignments")
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    
    # Get faculty id
    fac = cursor.execute("SELECT id FROM users WHERE role='faculty'").fetchone()
    faculty_id = fac['id'] if fac else 1
    
    seed_assignments_list(conn, faculty_id)
    conn.close()

if __name__ == '__main__':
    init_db()
    reseed_assignments()
    print("Database initialized & assignments reseeded successfully.")

