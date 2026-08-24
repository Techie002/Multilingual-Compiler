import difflib
import re

def compare_student_vs_ai(student_code, ai_code, language="python"):
    """
    Compares Student Code against AI-Generated Code.
    Returns dictionary with Similarity %, Logic Similarity, Structural Similarity, Complexity Comparison, and diff details.
    """
    # 1. Direct text diff similarity
    seq_matcher = difflib.SequenceMatcher(None, student_code, ai_code)
    text_similarity = seq_matcher.ratio() * 100.0

    # 2. Logic Similarity (Normalized control flow & function keywords)
    student_logic = _extract_logic_tokens(student_code)
    ai_logic = _extract_logic_tokens(ai_code)
    logic_matcher = difflib.SequenceMatcher(None, student_logic, ai_logic)
    logic_similarity = logic_matcher.ratio() * 100.0

    # 3. Structural Similarity (Line count, indentation hierarchy, block counts)
    student_struct = _extract_structural_fingerprint(student_code)
    ai_struct = _extract_structural_fingerprint(ai_code)
    struct_matcher = difflib.SequenceMatcher(None, student_struct, ai_struct)
    structural_similarity = struct_matcher.ratio() * 100.0

    overall_similarity = round((text_similarity * 0.3) + (logic_similarity * 0.4) + (structural_similarity * 0.3), 1)

    # 4. Generate line-by-line unified diff snippet
    diff_lines = list(difflib.unified_diff(
        student_code.splitlines(),
        ai_code.splitlines(),
        fromfile='Student Code',
        tofile='AI Generated Code',
        lineterm=''
    ))

    # 5. Complexity Comparison Matrix
    complexity_comp = {
        "student_estimated_time": "O(N)" if "for " in student_code else "O(1)",
        "ai_estimated_time": "O(N)" if "for " in ai_code else "O(1)",
        "student_estimated_space": "O(N)" if "append" in student_code or "[]" in student_code else "O(1)",
        "ai_estimated_space": "O(N)" if "seen = {}" in ai_code or "dict" in ai_code else "O(1)"
    }

    return {
        "overall_similarity": overall_similarity,
        "logic_similarity": round(logic_similarity, 1),
        "structural_similarity": round(structural_similarity, 1),
        "text_similarity": round(text_similarity, 1),
        "complexity_comparison": complexity_comp,
        "unified_diff": diff_lines[:30],
        "analysis_summary": f"Student code matches {overall_similarity}% with AI generated pattern. Logic structural similarity is {round(logic_similarity, 1)}%."
    }

def _extract_logic_tokens(code):
    """Normalizes code to control keywords and operators."""
    tokens = re.findall(r'\b(if|else|elif|for|while|return|def|function|class|import|try|except)\b|[+\-*/%=<>!]', code)
    return " ".join(tokens)

def _extract_structural_fingerprint(code):
    """Extracts structural line lengths and indent depth pattern."""
    lines = code.splitlines()
    fingerprint = []
    for line in lines:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        fingerprint.append(f"indent_{indent}_len_{len(line.strip())}")
    return " ".join(fingerprint)
