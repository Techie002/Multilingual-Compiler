import ast
import re
import sys

class HintEngine:
    """
    Deterministic, Rule-Based & AST-Driven Code and Problem Hint Engine.
    Provides algorithmic hints, progressive problem guidance, code anti-pattern diagnostics,
    and runtime/compiler error explanations for Python, C, C++, Java, JS, SQL, RAG, PHP, Go, Rust, and Bash.
    """

    # Predefined Knowledge Base for Common Algorithmic Concepts & Problems
    PROBLEM_KNOWLEDGE_BASE = {
        "factorial": {
            "title": "Factorial Calculation",
            "hints": [
                {
                    "level": 1,
                    "title": "Core Concept & Strategy",
                    "content": "Factorial of N ($N!$) is the product of all positive integers less than or equal to N ($N! = N \\times (N-1)!$). By definition, $0! = 1$ and $1! = 1$."
                },
                {
                    "level": 2,
                    "title": "Edge Cases & Boundaries",
                    "content": "Ensure you handle $N = 0$ and $N = 1$ base cases correctly (they should return 1). If using recursion, verify that you stop at $N \\le 1$ to avoid infinite recursion."
                },
                {
                    "level": 3,
                    "title": "Implementation & Efficiency",
                    "content": "An iterative loop ($O(N)$ time, $O(1)$ space) avoids the stack overhead of recursion. If using recursion, verify your base case: `if n <= 1: return 1`."
                }
            ]
        },
        "two sum": {
            "title": "Two Sum Problem",
            "hints": [
                {
                    "level": 1,
                    "title": "Core Concept & Strategy",
                    "content": "You need to find two numbers that sum to a target. For any element `x`, the complement you are looking for is `target - x`."
                },
                {
                    "level": 2,
                    "title": "Edge Cases & Boundaries",
                    "content": "You cannot use the same element twice (i.e. check different indices). Ensure your solution handles negative numbers and duplicate values."
                },
                {
                    "level": 3,
                    "title": "Optimization Strategy",
                    "content": "A brute-force double loop takes $O(N^2)$ time. Instead, use a Hash Map (dictionary) storing `{value: index}` to achieve $O(N)$ time complexity in a single pass."
                }
            ]
        },
        "fibonacci": {
            "title": "Fibonacci Sequence",
            "hints": [
                {
                    "level": 1,
                    "title": "Core Concept & Strategy",
                    "content": "The Fibonacci sequence starts with $F(0)=0, F(1)=1$, and each subsequent term is $F(n) = F(n-1) + F(n-2)$."
                },
                {
                    "level": 2,
                    "title": "Edge Cases & Boundaries",
                    "content": "Check boundary conditions for $n = 0$ and $n = 1$. Naive recursive implementation has exponential $O(2^N)$ complexity and will time out on inputs greater than 30."
                },
                {
                    "level": 3,
                    "title": "Space & Time Optimization",
                    "content": "You only need to remember the last two values ($a$ and $b$). An iterative loop updates `a, b = b, a + b` in $O(N)$ time and $O(1)$ space."
                }
            ]
        },
        "palindrome": {
            "title": "Palindrome Verification",
            "hints": [
                {
                    "level": 1,
                    "title": "Core Concept & Strategy",
                    "content": "A palindrome reads the same forwards and backwards (e.g. 'racecar' or '121')."
                },
                {
                    "level": 2,
                    "title": "Edge Cases & Boundaries",
                    "content": "Consider case-sensitivity, non-alphanumeric characters (spaces, punctuation), single-character strings, and empty strings."
                },
                {
                    "level": 3,
                    "title": "Implementation Tip",
                    "content": "Use a two-pointer approach comparing characters from left and right inward in $O(N)$ time, or string slicing `s == s[::-1]` in Python."
                }
            ]
        },
        "binary search": {
            "title": "Binary Search",
            "hints": [
                {
                    "level": 1,
                    "title": "Core Concept & Strategy",
                    "content": "Binary search requires a sorted array. In each step, compare the target with the middle element and discard half the search space."
                },
                {
                    "level": 2,
                    "title": "Edge Cases & Boundaries",
                    "content": "Prevent index overflow when calculating mid (use `left + (right - left) // 2`). Check loop termination condition `while left <= right:`."
                },
                {
                    "level": 3,
                    "title": "Complexity Analysis",
                    "content": "Binary search runs in $O(\\log N)$ time and $O(1)$ auxiliary space. Ensure pointers are updated correctly: `left = mid + 1` or `right = mid - 1`."
                }
            ]
        },
        "reverse": {
            "title": "Reversal Algorithm",
            "hints": [
                {
                    "level": 1,
                    "title": "Core Concept & Strategy",
                    "content": "To reverse an array or string in-place, swap elements at symmetric positions: element at index `i` swaps with element at index `N - 1 - i`."
                },
                {
                    "level": 2,
                    "title": "Edge Cases & Boundaries",
                    "content": "Handle empty inputs and single-element inputs where no swaps are necessary. Ensure you stop at `N // 2` to avoid swapping elements back."
                },
                {
                    "level": 3,
                    "title": "In-Place Optimization",
                    "content": "Use two pointers (`start` and `end`) moving towards each other to achieve $O(N)$ time and $O(1)$ memory without creating a new copy."
                }
            ]
        },
        "sort": {
            "title": "Sorting Algorithm",
            "hints": [
                {
                    "level": 1,
                    "title": "Core Concept & Strategy",
                    "content": "Determine whether comparison-based sorting ($O(N \\log N)$ like MergeSort / QuickSort) or linear-time sorting (Counting Sort for small ranges) is appropriate."
                },
                {
                    "level": 2,
                    "title": "Edge Cases & Boundaries",
                    "content": "Test with already sorted arrays, reverse sorted arrays, arrays with all identical elements, and empty arrays."
                },
                {
                    "level": 3,
                    "title": "Stability & Memory",
                    "content": "In-place QuickSort uses $O(\\log N)$ recursion stack space. MergeSort is stable but uses $O(N)$ auxiliary space."
                }
            ]
        },
        "prime": {
            "title": "Prime Number / Math",
            "hints": [
                {
                    "level": 1,
                    "title": "Core Concept & Strategy",
                    "content": "A prime number is greater than 1 with no divisors other than 1 and itself. 0 and 1 are NOT prime numbers. 2 is the only even prime."
                },
                {
                    "level": 2,
                    "title": "Boundary & Math Optimization",
                    "content": "You only need to check potential divisors up to $\\sqrt{N}$. If $N$ has a factor larger than $\\sqrt{N}$, its corresponding factor must be less than $\\sqrt{N}$."
                },
                {
                    "level": 3,
                    "title": "Efficiency",
                    "content": "For checking multiple primes, consider the Sieve of Eratosthenes ($O(N \\log \\log N)$). For single checks, iterate `i` from 2 up to `int(n**0.5) + 1`."
                }
            ]
        },
        "sql": {
            "title": "SQL Query & Relational Design",
            "hints": [
                {
                    "level": 1,
                    "title": "Query Clause Order & Filtering",
                    "content": "Standard SQL execution order: `FROM` $\\rightarrow$ `WHERE` $\\rightarrow$ `GROUP BY` $\\rightarrow$ `HAVING` $\\rightarrow$ `SELECT` $\\rightarrow$ `ORDER BY` $\\rightarrow$ `LIMIT`. Apply row filters in `WHERE` and aggregate group filters in `HAVING`."
                },
                {
                    "level": 2,
                    "title": "Joins, Aggregations & NULLs",
                    "content": "Always specify explicit `JOIN ... ON tableA.id = tableB.id` conditions. In SQL, `NULL = NULL` yields Unknown (use `IS NULL` or `COALESCE`)."
                },
                {
                    "level": 3,
                    "title": "Performance & B-Tree Indexing",
                    "content": "Avoid `SELECT *` in production to reduce disk I/O. Use indexes on foreign keys and columns frequently used in `WHERE` filters and `JOIN` predicates."
                }
            ]
        },
        "rag": {
            "title": "RAG (Retrieval-Augmented Generation) Pipeline",
            "hints": [
                {
                    "level": 1,
                    "title": "Architecture & Semantic Vectors",
                    "content": "RAG indexes unstructured knowledge documents into chunks, generates vector embeddings, and performs top-K cosine similarity search to retrieve relevant context."
                },
                {
                    "level": 2,
                    "title": "Chunking Strategy & Overlap",
                    "content": "Overly small chunks lose sentence context; overly large chunks dilute cosine similarity. Optimal chunk sizes are 200-500 tokens with 10-20% boundary overlap."
                },
                {
                    "level": 3,
                    "title": "Grounding & Hallucination Prevention",
                    "content": "Inject retrieved top-K context into the system prompt with strict grounding instructions: 'Answer strictly using the provided context' to prevent LLM hallucinations."
                }
            ]
        }
    }

    @classmethod
    def get_hints(cls, code="", language="python", compiler_output="", problem_title="", problem_desc=""):
        """
        Main entrypoint: Generates all deterministic hints:
        1. Problem-Aware Progressive Hints (Levels 1, 2, 3)
        2. Code & AST-based Diagnostics (anti-patterns, structural gotchas)
        3. Error Resolution Diagnostics (if compiler/runtime error occurred)
        """
        problem_hints = cls._generate_problem_hints(problem_title, problem_desc, code, language)
        code_diagnostics = cls._analyze_code_diagnostics(code, language)
        error_guidance = cls._diagnose_compiler_error(compiler_output, language)

        return {
            "problem_hints": problem_hints,
            "code_diagnostics": code_diagnostics,
            "error_guidance": error_guidance
        }

    @classmethod
    def _generate_problem_hints(cls, title="", description="", code="", language="python"):
        """Extracts progressive problem hints based on keyword semantics and topic detection."""
        lang = language.lower()
        search_corpus = f"{title} {description} {code} {lang}".lower()

        # Check knowledge base matches
        for key, entry in cls.PROBLEM_KNOWLEDGE_BASE.items():
            if key in search_corpus:
                return {
                    "matched_topic": entry["title"],
                    "hints": entry["hints"]
                }

        # Dynamic Generic Algorithmic Hints when no direct match is found
        return {
            "matched_topic": f"{language.upper()} Programming Guidance",
            "hints": [
                {
                    "level": 1,
                    "title": "Understanding Constraints & Approach",
                    "content": "Analyze problem constraints carefully. For $N \\le 10^5$, an $O(N)$ or $O(N \\log N)$ solution is required. For $N \\le 1000$, an $O(N^2)$ algorithm will pass."
                },
                {
                    "level": 2,
                    "title": "Edge Cases & Input Pitfalls",
                    "content": "Always test edge cases: empty input `[]` or `\"\"`, single elements, 0, negative values, and maximum constraint bounds."
                },
                {
                    "level": 3,
                    "title": "Data Structure Selection",
                    "content": "Use Hash Sets / Hash Maps for $O(1)$ lookups, Deque for $O(1)$ push/pop at both ends, or Two Pointers to optimize space."
                }
            ]
        }

    @classmethod
    def _analyze_code_diagnostics(cls, code, language="python"):
        """Deterministic static analysis & pattern diagnostics using AST and heuristics."""
        diagnostics = []
        lang = language.lower().strip()

        if not code or not code.strip():
            diagnostics.append({
                "type": "info",
                "badge": "Empty Code",
                "title": "No Code Written Yet",
                "message": f"Start typing your {language.upper()} solution in the editor on the left to receive live static diagnostics and hints."
            })
            return diagnostics

        # Language-specific diagnostics
        if lang in ['python', 'py', 'python3']:
            diagnostics.extend(cls._analyze_python_ast(code))
        elif lang in ['sql', 'sqlite', 'mysql', 'postgresql']:
            diagnostics.extend(cls._analyze_sql_code(code))
        elif lang in ['rag', 'rag_pipeline', 'retrieval']:
            diagnostics.extend(cls._analyze_rag_code(code))
        elif lang in ['php']:
            diagnostics.extend(cls._analyze_php_code(code))
        elif lang in ['go', 'golang']:
            diagnostics.extend(cls._analyze_go_code(code))
        elif lang in ['rust', 'rs']:
            diagnostics.extend(cls._analyze_rust_code(code))
        elif lang in ['bash', 'sh', 'shell']:
            diagnostics.extend(cls._analyze_bash_code(code))
        else:
            diagnostics.extend(cls._analyze_generic_code(code, lang))

        # Check competitive programming I/O patterns
        diagnostics.extend(cls._check_io_patterns(code, lang))

        # Check loop and complexity heuristics
        if lang not in ['sql', 'rag']:
            diagnostics.extend(cls._check_complexity_heuristics(code))

        if not diagnostics:
            diagnostics.append({
                "type": "success",
                "badge": "Clean Code",
                "title": "Code Structure Looks Great",
                "message": "No obvious anti-patterns, infinite loop risks, or missing return branches detected. Ready to run and test!"
            })

        return diagnostics

    @classmethod
    def _analyze_python_ast(cls, code):
        """Deep AST analysis for Python programs."""
        diagnostics = []
        try:
            tree = ast.parse(code)
        except SyntaxError as se:
            diagnostics.append({
                "type": "error",
                "badge": "Syntax Error",
                "title": f"Syntax Error on Line {se.lineno or 1}",
                "message": f"Python parser encountered an error: `{se.msg}`. Verify colons `:`, indentation, brackets, and quotes around line {se.lineno}."
            })
            return diagnostics

        functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        for fn in functions:
            returns = [n for n in ast.walk(fn) if isinstance(n, ast.Return)]
            has_explicit_return = any(r.value is not None for r in returns)
            
            if fn.name not in ['main', '__init__', 'setup'] and not has_explicit_return:
                diagnostics.append({
                    "type": "warning",
                    "badge": "Missing Return",
                    "title": f"Function `{fn.name}()` may not return a value",
                    "message": f"Function `{fn.name}` on line {fn.lineno} does not have an explicit `return <value>` statement. Ensure it returns the computed output."
                })

            recursive_calls = [
                n for n in ast.walk(fn) 
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == fn.name
            ]
            if recursive_calls:
                if_nodes = [n for n in ast.walk(fn) if isinstance(n, ast.If)]
                if not if_nodes:
                    diagnostics.append({
                        "type": "error",
                        "badge": "Recursion Trap",
                        "title": f"Unconditional Recursion in `{fn.name}()`",
                        "message": f"Function `{fn.name}` calls itself recursively on line {fn.lineno} without an `if` base case check, which will cause a `RecursionError`."
                    })

        while_loops = [node for node in ast.walk(tree) if isinstance(node, ast.While)]
        for wl in while_loops:
            if isinstance(wl.test, ast.Constant) and wl.test.value is True:
                has_break = any(isinstance(n, ast.Break) for n in ast.walk(wl))
                if not has_break:
                    diagnostics.append({
                        "type": "warning",
                        "badge": "Infinite Loop Risk",
                        "title": f"Potential Infinite Loop on Line {wl.lineno}",
                        "message": "`while True` loop detected without an explicit `break` condition in its body. Ensure there is a termination condition."
                    })

        for call in [node for node in ast.walk(tree) if isinstance(node, ast.Call)]:
            if isinstance(call.func, ast.Name) and call.func.id == 'range':
                if call.args and isinstance(call.args[0], ast.Call):
                    inner = call.args[0]
                    if isinstance(inner.func, ast.Name) and inner.func.id == 'len':
                        diagnostics.append({
                            "type": "tip",
                            "badge": "Pythonic Idiom",
                            "title": "Use `enumerate()` Instead of `range(len())`",
                            "message": "Iterating with `range(len(items))` is an anti-pattern. Use `for idx, item in enumerate(items):` for cleaner, faster code."
                        })
                        break

        return diagnostics

    @classmethod
    def _analyze_sql_code(cls, code):
        """Static diagnostics for SQL queries."""
        diagnostics = []
        statements = [s.strip() for s in code.split(';') if s.strip()]
        
        for idx, stmt in enumerate(statements, 1):
            upper = stmt.upper()
            if "DELETE FROM" in upper and "WHERE" not in upper:
                diagnostics.append({
                    "type": "error",
                    "badge": "Unsafe Mutation",
                    "title": f"Unconstrained DELETE on Statement #{idx}",
                    "message": "DELETE query without a `WHERE` clause will purge ALL rows in the table."
                })
            if "UPDATE " in upper and "WHERE" not in upper:
                diagnostics.append({
                    "type": "error",
                    "badge": "Unsafe Mutation",
                    "title": f"Unconstrained UPDATE on Statement #{idx}",
                    "message": "UPDATE statement without a `WHERE` filter will overwrite values across all rows."
                })
            if "JOIN " in upper and "ON " not in upper and "USING" not in upper:
                diagnostics.append({
                    "type": "warning",
                    "badge": "Cartesian Product",
                    "title": f"Missing `ON` Clause in JOIN on Statement #{idx}",
                    "message": "JOIN without `ON` condition creates an $O(M \\times N)$ Cartesian Product. Specify `ON tableA.col = tableB.col`."
                })
            if "SELECT *" in upper:
                diagnostics.append({
                    "type": "tip",
                    "badge": "Query Optimization",
                    "title": "Specify Explicit Columns Instead of `SELECT *`",
                    "message": "Explicitly listing required column names saves network bandwidth, disk I/O, and prevents schema change breakages."
                })
            if "WHERE" in upper and "LIKE '%" in upper:
                diagnostics.append({
                    "type": "tip",
                    "badge": "Index Optimization",
                    "title": "Leading Wildcard `LIKE '%term'` Causes Full Table Scan",
                    "message": "Leading wildcards prevent B-Tree index lookups. Use exact prefix matching `LIKE 'term%'` or full-text indexing."
                })

        return diagnostics

    @classmethod
    def _analyze_rag_code(cls, code):
        """Static diagnostics for RAG pipelines."""
        diagnostics = []
        if "DOCUMENTS" not in code and "corpus" not in code and "DOC:" not in code:
            diagnostics.append({
                "type": "warning",
                "badge": "Empty Knowledge Base",
                "title": "No Knowledge Corpus Defined",
                "message": "Define a knowledge base list (e.g. `DOCUMENTS = ['chunk 1', 'chunk 2']`) to provide context for semantic retrieval."
            })
        if "QUERY" not in code and "query" not in code and "QUESTION:" not in code:
            diagnostics.append({
                "type": "info",
                "badge": "Input Query",
                "title": "Define an Input Query",
                "message": "Specify `QUERY = 'your question here'` or provide custom stdin to test cosine similarity matching."
            })
        return diagnostics

    @classmethod
    def _analyze_php_code(cls, code):
        """Static diagnostics for PHP scripts."""
        diagnostics = []
        lines = code.splitlines()
        for idx, line in enumerate(lines, 1):
            if re.search(r'\b[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*', line) and not line.strip().startswith(('$', 'const ', 'class ', '//', '#')):
                if not line.strip().startswith(('if', 'for', 'while', 'return', 'echo', 'public', 'private', 'protected')):
                    diagnostics.append({
                        "type": "warning",
                        "badge": "PHP Syntax",
                        "title": f"Missing `$` on Variable on Line {idx}",
                        "message": "PHP variables must begin with a dollar sign `$`, e.g. `$variable_name = 10;`."
                    })
        return diagnostics

    @classmethod
    def _analyze_go_code(cls, code):
        """Static diagnostics for Go programs."""
        diagnostics = []
        if "package main" not in code:
            diagnostics.append({
                "type": "error",
                "badge": "Missing Package",
                "title": "Missing `package main` Declaration",
                "message": "Every executable Go binary requires `package main` at the top of the file."
            })
        if "func main()" not in code:
            diagnostics.append({
                "type": "error",
                "badge": "Missing Entrypoint",
                "title": "Missing `func main()` Entrypoint",
                "message": "Go executable programs require a `func main() { ... }` entrypoint."
            })
        return diagnostics

    @classmethod
    def _analyze_rust_code(cls, code):
        """Static diagnostics for Rust programs."""
        diagnostics = []
        if "fn main()" not in code:
            diagnostics.append({
                "type": "error",
                "badge": "Missing Main",
                "title": "Missing `fn main()` Entrypoint",
                "message": "Rust binaries require an entrypoint function `fn main() { ... }`."
            })
        return diagnostics

    @classmethod
    def _analyze_bash_code(cls, code):
        """Static diagnostics for Bash scripts."""
        diagnostics = []
        if not code.startswith("#!/bin/bash") and not code.startswith("#!/bin/sh"):
            diagnostics.append({
                "type": "tip",
                "badge": "Shebang Header",
                "title": "Add `#!/bin/bash` Shebang",
                "message": "Including a shebang `#!/bin/bash` on the first line ensures cross-platform shell interpreter consistency."
            })
        return diagnostics

    @classmethod
    def _analyze_generic_code(cls, code, language):
        """Heuristic checks for C, C++, Java, JavaScript."""
        diagnostics = []
        lines = code.splitlines()

        for idx, line in enumerate(lines, 1):
            if re.search(r'\bif\s*\([^=!<>\n]*=[^=!<>\n]*\)', line):
                diagnostics.append({
                    "type": "warning",
                    "badge": "Logic Bug",
                    "title": f"Assignment in `if` condition on Line {idx}",
                    "message": f"Line {idx} appears to use assignment `=` instead of equality comparison `==` inside an `if` condition."
                })

        if language in ['c', 'cpp', 'java']:
            if re.search(r'\b(int|float|double|String|bool)\s+[a-zA-Z0-9_]+\s*\([^)]*\)\s*\{', code):
                if 'return ' not in code:
                    diagnostics.append({
                        "type": "warning",
                        "badge": "Missing Return",
                        "title": "Non-void Function Missing `return`",
                        "message": "You declared a function with a return type, but no `return` statement was found."
                    })

        return diagnostics

    @classmethod
    def _check_io_patterns(cls, code, language):
        """Checks for competitive programming I/O issues."""
        diagnostics = []
        if 'input("' in code or "input('" in code:
            diagnostics.append({
                "type": "tip",
                "badge": "I/O Formatting",
                "title": "Avoid Interactive Prompts in `input()`",
                "message": "When submitting code to automated evaluators, use `input()` or `sys.stdin.read()` without prompt strings to match expected benchmark test case outputs."
            })
        return diagnostics

    @classmethod
    def _check_complexity_heuristics(cls, code):
        """Checks for nested loops and efficiency bottlenecks."""
        diagnostics = []
        lines = code.splitlines()
        nested_loop_depth = 0
        max_depth = 0

        for line in lines:
            stripped = line.strip()
            if re.search(r'\b(for|while|loop)\b', stripped):
                nested_loop_depth += 1
                max_depth = max(max_depth, nested_loop_depth)
            elif stripped.startswith(('}', 'end')) or (stripped and not line.startswith(' ' * (nested_loop_depth * 4))):
                if nested_loop_depth > 0:
                    nested_loop_depth -= 1

        if max_depth >= 2:
            diagnostics.append({
                "type": "tip",
                "badge": "Time Complexity",
                "title": f"Nested Loops Detected ($O(N^{max_depth})$)",
                "message": "Your code contains nested loops. If input sizes are large ($N > 10^4$), this may cause Time Limit Exceeded (TLE). Consider whether a Hash Map, Two Pointers, or Precomputation can reduce complexity to $O(N)$."
            })

        return diagnostics

    @classmethod
    def _diagnose_compiler_error(cls, compiler_output, language="python"):
        """Diagnoses compiler / runtime errors and provides clear explanations."""
        if not compiler_output or not compiler_output.strip():
            return None

        out = compiler_output.strip()

        if "ZeroDivisionError" in out:
            return {
                "error_type": "ZeroDivisionError",
                "explanation": "Your code attempted to divide a number by zero or perform modulo `% 0`.",
                "remedy": "Add a guard check `if divisor != 0:` before performing division or modulo operations."
            }
        elif "IndexError" in out:
            return {
                "error_type": "IndexError (List Index Out of Range)",
                "explanation": "Your code attempted to access an array/list index that does not exist.",
                "remedy": "Check loop boundary limits. Remember that in 0-indexed languages, valid indices range from `0` to `len(arr) - 1`."
            }
        elif "KeyError" in out:
            return {
                "error_type": "KeyError",
                "explanation": "Your code attempted to access a dictionary/map with a key that is not present.",
                "remedy": "Use `dict.get(key, default_value)` or check `if key in dict:` before accessing the key."
            }
        elif "RecursionError" in out:
            return {
                "error_type": "RecursionError (Maximum Depth Exceeded)",
                "explanation": "Your recursive function ran too deep without hitting a valid stopping base case.",
                "remedy": "Check that: 1) Your base case is reachable; 2) Recursive arguments decrease towards the base case."
            }
        elif "SQLError" in out or "sqlite3.Error" in out or "OperationalError" in out:
            return {
                "error_type": "SQL Execution Error",
                "explanation": f"The SQL engine encountered an execution error: {out[:120]}...",
                "remedy": "Check table and column names, correct JOIN clauses, and ensure proper SQL statement syntax with semicolons."
            }
        elif "TypeError" in out:
            return {
                "error_type": "TypeError",
                "explanation": "An operation was performed on incompatible data types.",
                "remedy": "Convert input types explicitly (e.g. `int(input())`) before arithmetic or indexing."
            }
        elif "NameError" in out:
            match = re.search(r"name '(\w+)' is not defined", out)
            var_name = match.group(1) if match else "variable"
            return {
                "error_type": f"NameError ('{var_name}' is not defined)",
                "explanation": f"The variable or function `{var_name}` is used before being declared.",
                "remedy": f"Check the spelling of `{var_name}` and ensure it is defined before use."
            }
        elif "SyntaxError" in out:
            return {
                "error_type": "SyntaxError",
                "explanation": "The code contains invalid language syntax that the parser cannot compile.",
                "remedy": "Check for missing colons, brackets, or quotes in your code."
            }

        return {
            "error_type": "Compilation / Runtime Notice",
            "explanation": f"The engine produced message: {out[:120]}...",
            "remedy": "Review the compiler diagnostic trace above and check corresponding line numbers."
        }
