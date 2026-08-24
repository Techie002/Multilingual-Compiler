import ast
import re
import io
import tokenize
import sqlite3

class CompilerAnalyzer:
    def __init__(self, code, language="python"):
        self.code = code
        self.language = language.lower().strip()

    def analyze_all(self):
        """Runs lexical analysis, syntax parsing, AST construction, semantic checks, and optimization analysis."""
        tokens = self.get_tokens()
        syntax_res = self.check_syntax()
        parse_tree = self.get_parse_tree()
        ast_tree = self.get_ast()
        semantic_res = self.check_semantics()
        optimization_res = self.analyze_optimization()

        return {
            "tokens": tokens,
            "syntax_errors": syntax_res["errors"],
            "parse_tree": parse_tree,
            "ast": ast_tree,
            "semantic_issues": semantic_res["issues"],
            "optimization": optimization_res
        }

    def get_tokens(self):
        """Lexical Analysis: Converts code into token stream."""
        tokens = []
        if self.language in ['python', 'py', 'python3']:
            try:
                reader = io.StringIO(self.code).readline
                for tok in tokenize.generate_tokens(reader):
                    token_name = tokenize.tok_name[tok.type]
                    if token_name in ['ENCODING', 'ENDMARKER', 'NL', 'COMMENT']:
                        continue
                    tokens.append({
                        "type": token_name,
                        "value": tok.string,
                        "line": tok.start[0],
                        "column": tok.start[1]
                    })
            except Exception as e:
                tokens.append({"type": "LEXICAL_ERROR", "value": str(e), "line": 1, "column": 0})
        elif self.language in ['sql', 'sqlite', 'mysql', 'postgresql']:
            # SQL Tokenizer
            token_specification = [
                ('SQL_KEYWORD', r'\b(SELECT|FROM|WHERE|JOIN|INNER|LEFT|RIGHT|FULL|OUTER|ON|GROUP\s+BY|ORDER\s+BY|HAVING|INSERT\s+INTO|INSERT|VALUES|UPDATE|SET|DELETE|CREATE\s+TABLE|CREATE|TABLE|PRIMARY\s+KEY|FOREIGN\s+KEY|DROP|ALTER|WITH|AS|AND|OR|NOT|IN|LIKE|IS|NULL|COUNT|SUM|AVG|MIN|MAX|DISTINCT|LIMIT|OFFSET|UNION|ASC|DESC)\b'),
                ('NUMBER',      r'\b\d+(\.\d+)?\b'),
                ('STRING',      r"'[^']*'|\"[^\"]*\""),
                ('IDENTIFIER',  r'\b[A-Za-z_][A-Za-z0-9_]*\b'),
                ('OPERATOR',    r'[+\-*/%=<>!&|]+'),
                ('PUNCTUATION', r'[;,\.\(\)]'),
                ('NEWLINE',     r'\n'),
                ('SKIP',        r'[ \t]+'),
                ('COMMENT',     r'--.*'),
                ('MISMATCH',    r'.'),
            ]
            tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
            line_num = 1
            for mo in re.finditer(tok_regex, self.code, re.IGNORECASE):
                kind = mo.lastgroup
                value = mo.group()
                if kind == 'NEWLINE':
                    line_num += 1
                elif kind in ['SKIP', 'COMMENT']:
                    continue
                elif kind == 'MISMATCH':
                    tokens.append({"type": "UNRECOGNIZED", "value": value, "line": line_num, "column": mo.start()})
                else:
                    tokens.append({"type": kind, "value": value, "line": line_num, "column": mo.start()})
        else:
            # Multi-language Regex Lexer for C, C++, Java, JS, PHP, Go, Rust, Bash, RAG
            token_specification = [
                ('KEYWORD', r'\b(if|else|while|for|return|int|float|double|char|void|class|public|static|function|const|let|var|def|import|sys|include|echo|print|package|func|struct|fn|mut|impl|trait|match|DOCUMENTS|QUERY|TOP_K|SELECT|FROM)\b'),
                ('NUMBER',   r'\b\d+(\.\d+)?\b'),
                ('STRING',   r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\''),
                ('VARIABLE', r'\$[A-Za-z_][A-Za-z0-9_]*'), # PHP/Bash variables
                ('IDENT',    r'\b[A-Za-z_][A-Za-z0-9_]*\b'),
                ('OP',       r'[+\-*/%=<>!&|]+'),
                ('PUNCT',    r'[;,\.\(\)\{\}\[\]]'),
                ('NEWLINE',  r'\n'),
                ('SKIP',     r'[ \t]+'),
                ('MISMATCH', r'.'),
            ]
            tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
            line_num = 1
            for mo in re.finditer(tok_regex, self.code):
                kind = mo.lastgroup
                value = mo.group()
                if kind == 'NEWLINE':
                    line_num += 1
                elif kind == 'SKIP':
                    continue
                elif kind == 'MISMATCH':
                    tokens.append({"type": "UNRECOGNIZED", "value": value, "line": line_num, "column": mo.start()})
                else:
                    tokens.append({"type": kind, "value": value, "line": line_num, "column": mo.start()})

        return tokens[:200]

    def check_syntax(self):
        """Syntax Analysis: Validates syntax and returns list of syntax errors."""
        errors = []
        if self.language in ['python', 'py', 'python3']:
            try:
                ast.parse(self.code)
            except SyntaxError as se:
                errors.append({
                    "line": se.lineno or 1,
                    "column": se.offset or 0,
                    "message": f"SyntaxError: {se.msg}"
                })
        elif self.language in ['sql', 'sqlite', 'mysql', 'postgresql']:
            # Validate SQL syntax against in-memory SQLite parser
            try:
                conn = sqlite3.connect(":memory:")
                cursor = conn.cursor()
                statements = [s.strip() for s in self.code.split(';') if s.strip()]
                for stmt in statements:
                    cursor.execute(stmt)
                conn.close()
            except sqlite3.Error as e:
                errors.append({
                    "line": 1,
                    "column": 0,
                    "message": f"SQLSyntaxError: {str(e)}"
                })
        else:
            # Bracket & Semicolon balance checker for C/C++/Java/JS/PHP/Go/Rust
            stack = []
            matching = {')': '(', '}': '{', ']': '['}
            lines = self.code.splitlines()
            for line_idx, line in enumerate(lines, 1):
                clean_line = line.split('//')[0].split('#')[0].split('--')[0]
                for char in clean_line:
                    if char in '({[':
                        stack.append((char, line_idx))
                    elif char in ')}]':
                        if not stack or stack[-1][0] != matching[char]:
                            errors.append({
                                "line": line_idx,
                                "column": 0,
                                "message": f"SyntaxError: Mismatched closing character '{char}'"
                            })
                        else:
                            stack.pop()

            if stack:
                err_char, err_line = stack.pop()
                errors.append({
                    "line": err_line,
                    "column": 0,
                    "message": f"SyntaxError: Unclosed bracket/parenthesis '{err_char}'"
                })

        return {"valid": len(errors) == 0, "errors": errors}

    def get_parse_tree(self):
        """Builds a Parse Tree visualization object."""
        lines = self.code.splitlines()
        root = {
            "name": f"Program ({self.language.upper()})",
            "children": []
        }

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith(('#', '//', '--', '/*')):
                continue

            node_type = "Statement"
            if stripped.upper().startswith(('SELECT', 'CREATE', 'INSERT', 'UPDATE', 'DELETE', 'WITH')):
                node_type = f"SQL_{stripped.split()[0].upper()}"
            elif stripped.startswith(('def ', 'function ', 'class ', 'int ', 'void ', 'public ', 'package ', 'func ', 'fn ')):
                node_type = "Declaration"
            elif stripped.startswith(('if ', 'else', 'for ', 'while ', 'match ', 'switch ')):
                node_type = "ControlFlow"
            elif stripped.startswith(('return ', 'return;')):
                node_type = "ReturnStatement"
            elif stripped.startswith(('echo ', 'print', 'fmt.Println', 'println!')):
                node_type = "OutputOperation"

            root["children"].append({
                "name": f"Line {idx}: {node_type}",
                "value": stripped[:40] + ("..." if len(stripped) > 40 else "")
            })

        return root

    def get_ast(self):
        """Constructs Abstract Syntax Tree representation."""
        if self.language in ['python', 'py', 'python3']:
            try:
                tree = ast.parse(self.code)
                return self._ast_to_dict(tree)
            except Exception as e:
                return {"name": "ParseError", "children": [{"name": str(e)}]}
        elif self.language in ['sql', 'sqlite', 'mysql', 'postgresql']:
            return self._sql_ast_generator()
        elif self.language in ['rag', 'rag_pipeline', 'retrieval']:
            return self._rag_ast_generator()
        else:
            return self._generic_ast_generator()

    def _ast_to_dict(self, node):
        node_name = node.__class__.__name__
        children = []

        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        children.append(self._ast_to_dict(item))
            elif isinstance(value, ast.AST):
                children.append(self._ast_to_dict(value))

        res = {"name": node_name}
        if children:
            res["children"] = children[:15]
        return res

    def _sql_ast_generator(self):
        """Builds AST representation for SQL queries."""
        root = {"name": "SQLQueryPlan", "children": []}
        statements = [s.strip() for s in self.code.split(';') if s.strip()]
        
        for idx, stmt in enumerate(statements, 1):
            upper = stmt.upper()
            if upper.startswith("SELECT"):
                stmt_node = {"name": f"SelectQuery #{idx}", "children": []}
                # Extract Columns
                if "FROM" in upper:
                    cols_part = stmt[6:upper.index("FROM")].strip()
                    stmt_node["children"].append({"name": "Projection (SELECT)", "details": cols_part[:40]})
                    
                    # Extract Table
                    rest = stmt[upper.index("FROM") + 4:]
                    table_name = rest.split()[0] if rest.split() else "Unknown"
                    stmt_node["children"].append({"name": "ScanRelation (FROM)", "details": table_name})
                    
                    if "WHERE" in upper:
                        where_part = upper.split("WHERE")[1].split("GROUP")[0].split("ORDER")[0].strip()
                        stmt_node["children"].append({"name": "FilterPredicate (WHERE)", "details": where_part[:35]})
                    if "JOIN" in upper:
                        stmt_node["children"].append({"name": "JoinOperation", "details": "Relational Join"})
                    if "GROUP BY" in upper:
                        stmt_node["children"].append({"name": "Aggregation (GROUP BY)", "details": "Group Keys"})
                    if "ORDER BY" in upper:
                        stmt_node["children"].append({"name": "SortOrder (ORDER BY)", "details": "Ordering"})
                else:
                    stmt_node["children"].append({"name": "ScalarExpression", "details": stmt[6:30]})
                root["children"].append(stmt_node)
            elif upper.startswith("CREATE TABLE"):
                table_name = upper.split("CREATE TABLE")[1].split("(")[0].strip()
                root["children"].append({"name": f"CreateTable #{idx}", "details": table_name})
            elif upper.startswith("INSERT INTO"):
                table_name = upper.split("INSERT INTO")[1].split()[0].strip()
                root["children"].append({"name": f"InsertRecord #{idx}", "details": f"Target: {table_name}"})
            elif upper.startswith("UPDATE"):
                root["children"].append({"name": f"UpdateRecord #{idx}", "details": "Mutation"})
            elif upper.startswith("DELETE"):
                root["children"].append({"name": f"DeleteRecord #{idx}", "details": "Deletion"})
            else:
                root["children"].append({"name": f"DDLStatement #{idx}", "details": stmt[:30]})

        return root

    def _rag_ast_generator(self):
        """Builds AST representation for RAG pipeline execution."""
        root = {
            "name": "RAGPipelineExecutionGraph",
            "children": [
                {
                    "name": "KnowledgeCorpusIngestion",
                    "children": [
                        {"name": "TextChunkingStrategy", "details": "Sentence / Semantic Chunks"},
                        {"name": "VectorEmbeddingIndexer", "details": "TF-IDF / Dense Vectors"}
                    ]
                },
                {
                    "name": "QuerySemanticRetrieval",
                    "children": [
                        {"name": "QueryVectorEncoder", "details": "Cosine Similarity Metric"},
                        {"name": "TopKSimilarityFilter", "details": "Top-K Nearest Chunks"}
                    ]
                },
                {
                    "name": "AugmentedPromptSynthesis",
                    "children": [
                        {"name": "GroundingContextInjection", "details": "System Grounding Guard"},
                        {"name": "GenerativeOutput", "details": "LLM Inference"}
                    ]
                }
            ]
        }
        return root

    def _generic_ast_generator(self):
        """Constructs AST for C, C++, Java, JS, PHP, Go, Rust, Bash."""
        root = {"name": f"TranslationUnit ({self.language.upper()})", "children": []}
        lines = self.code.splitlines()
        for idx, line in enumerate(lines, 1):
            s = line.strip()
            if not s or s.startswith(('//', '#', '/*')):
                continue
            if s.startswith(('def ', 'function ', 'class ', 'int ', 'void ', 'package ', 'func ', 'fn ')):
                root["children"].append({"name": "FunctionDefinition", "details": s[:30]})
            elif s.startswith(('for', 'while', 'loop')):
                root["children"].append({"name": "LoopConstruct", "details": s[:30]})
            elif s.startswith(('if', 'else', 'match', 'switch')):
                root["children"].append({"name": "ConditionalBranch", "details": s[:30]})
            elif s.startswith(('echo ', 'print', 'fmt.Println', 'println!')):
                root["children"].append({"name": "OutputStatement", "details": s[:30]})
            elif '=' in s:
                root["children"].append({"name": "AssignmentExpression", "details": s[:30]})

        return root

    def check_semantics(self):
        """Semantic Analysis: Checks undefined variables, SQL pitfalls, RAG configurations."""
        issues = []
        
        if self.language in ['python', 'py', 'python3']:
            try:
                tree = ast.parse(self.code)
                defined_vars = set()
                used_vars = set()

                for node in ast.walk(tree):
                    if isinstance(node, ast.Name):
                        if isinstance(node.ctx, ast.Store):
                            defined_vars.add((node.id, node.lineno))
                        elif isinstance(node.ctx, ast.Load):
                            used_vars.add(node.id)

                builtins = {'print', 'len', 'range', 'int', 'str', 'float', 'list', 'dict', 'set', 'sum', 'min', 'max', 'abs', 'open', 'input', 'enumerate', 'zip', 'sys'}
                for var, line in defined_vars:
                    if var not in used_vars and not var.startswith('_') and var not in builtins:
                        issues.append({
                            "type": "UnusedVariable",
                            "line": line,
                            "message": f"Variable '{var}' is declared but never read."
                        })
            except Exception:
                pass
        elif self.language in ['sql', 'sqlite', 'mysql', 'postgresql']:
            statements = [s.strip() for s in self.code.split(';') if s.strip()]
            for stmt_idx, stmt in enumerate(statements, 1):
                upper_stmt = stmt.upper()
                if "DELETE FROM" in upper_stmt or upper_stmt.startswith("DELETE"):
                    if "WHERE" not in upper_stmt:
                        issues.append({
                            "type": "DestructiveQuery",
                            "line": stmt_idx,
                            "message": f"Statement #{stmt_idx}: DELETE statement without WHERE clause will delete ALL rows in the table."
                        })
                if "UPDATE " in upper_stmt or upper_stmt.startswith("UPDATE"):
                    if "WHERE" not in upper_stmt:
                        issues.append({
                            "type": "DestructiveQuery",
                            "line": stmt_idx,
                            "message": f"Statement #{stmt_idx}: UPDATE statement without WHERE clause will modify ALL rows in the table."
                        })
                if "JOIN " in upper_stmt and "ON " not in upper_stmt and "USING" not in upper_stmt:
                    issues.append({
                        "type": "CartesianProduct",
                        "line": stmt_idx,
                        "message": f"Statement #{stmt_idx}: JOIN without ON condition produces an expensive Cartesian Product (cross join)."
                    })
        elif self.language in ['php']:
            lines = self.code.splitlines()
            for idx, line in enumerate(lines, 1):
                if re.search(r'\b[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*', line) and not line.strip().startswith(('$', 'const ', 'class ', '//', '#')):
                    if not line.strip().startswith(('if', 'for', 'while', 'return', 'echo')):
                        issues.append({
                            "type": "MissingDollarSign",
                            "line": idx,
                            "message": "PHP variable assignment requires leading '$' (e.g. '$var = value;')."
                        })
        elif self.language in ['go', 'golang']:
            if "package main" not in self.code:
                issues.append({
                    "type": "MissingPackage",
                    "line": 1,
                    "message": "Go executable programs must declare 'package main'."
                })
            if "func main()" not in self.code:
                issues.append({
                    "type": "MissingMain",
                    "line": 1,
                    "message": "Go executable programs must define an entrypoint 'func main()'."
                })
        elif self.language in ['rust', 'rs']:
            if "fn main()" not in self.code:
                issues.append({
                    "type": "MissingMain",
                    "line": 1,
                    "message": "Rust binaries require an entrypoint function 'fn main()'."
                })

        return {"issues": issues}

    def analyze_optimization(self):
        """Code Optimization Analyzer: Detects dead code, inefficient loops, SQL indexing hints."""
        suggestions = []
        score = 100

        if self.language in ['sql', 'sqlite', 'mysql', 'postgresql']:
            upper = self.code.upper()
            if "SELECT *" in upper:
                suggestions.append("Avoid `SELECT *` in production queries: Explicitly specify column names to reduce I/O overhead.")
                score -= 10
            if "JOIN" in upper:
                suggestions.append("Ensure indexed foreign key columns are used in `JOIN ... ON` predicates for $O(1)$ index seeks.")
            if "WHERE" in upper and "LIKE '%" in upper:
                suggestions.append("Leading wildcard `LIKE '%term'` prevents B-Tree index utilization and causes full table scans.")
                score -= 15
            if not suggestions:
                suggestions.append("SQL query statements are structured cleanly.")
            return {
                "performance_score": max(50, score),
                "suggestions": suggestions
            }

        lines = self.code.splitlines()
        has_nested_loops = False
        loop_depth = 0

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if re.search(r'\b(for|while)\b', stripped):
                loop_depth += 1
                if loop_depth > 1:
                    has_nested_loops = True
            elif stripped.startswith(('}', 'end')) or (stripped and not line.startswith(' ' * (loop_depth * 4))):
                if loop_depth > 0:
                    loop_depth -= 1

            if stripped.startswith(('return', 'return;')):
                if idx < len(lines) and lines[idx].strip() and not lines[idx].strip().startswith(('}', 'def', 'function', 'else', 'elif')):
                    suggestions.append(f"Line {idx+1}: Dead code detected after return statement.")
                    score -= 10

        if has_nested_loops:
            suggestions.append("Nested loops detected: High time complexity O(N^2) or worse. Consider using hash maps or optimized lookup structures.")
            score -= 15

        if "range(len(" in self.code:
            suggestions.append("Anti-pattern detected: `range(len(...))` used. Use `enumerate(...)` for better readability and performance.")
            score -= 5

        if not suggestions:
            suggestions.append("Code structure is clean with good algorithmic patterns.")

        return {
            "performance_score": max(20, score),
            "suggestions": suggestions
        }
