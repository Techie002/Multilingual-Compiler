import json
from compiler.runner import execute_code
from compiler.lexer_parser import CompilerAnalyzer
from ai.ai_engine import AIEngine

def normalize_output(s):
    """Normalizes output strings, CRLF/LF line breaks, trailing whitespace, and JSON structures."""
    if s is None:
        return ""
    text = str(s).replace("\r\n", "\n").replace("\r", "\n").strip()
    # If JSON formatted array or object, normalize representation
    if (text.startswith("[") and text.endswith("]")) or (text.startswith("{") and text.endswith("}")):
        try:
            parsed = json.loads(text)
            return json.dumps(parsed, sort_keys=True, separators=(',', ':'))
        except Exception:
            pass
    lines = [l.rstrip() for l in text.splitlines()]
    return "\n".join(lines)

def evaluate_submission(source_code, language, public_test_cases, hidden_test_cases):
    """
    Evaluates student submission against public and hidden test cases.
    Returns comprehensive scoring metrics out of 100 points.
    """
    if isinstance(public_test_cases, str):
        public_test_cases = json.loads(public_test_cases or "[]")
    if isinstance(hidden_test_cases, str):
        hidden_test_cases = json.loads(hidden_test_cases or "[]")

    all_test_cases = []
    for tc in public_test_cases:
        tc['is_hidden'] = False
        all_test_cases.append(tc)
    for tc in hidden_test_cases:
        tc['is_hidden'] = True
        all_test_cases.append(tc)

    total_test_cases = len(all_test_cases)
    passed_count = 0
    detailed_results = []
    total_exec_time = 0.0
    total_memory_mb = 0.0

    for idx, tc in enumerate(all_test_cases, 1):
        inp = str(tc.get("input", "")).strip()
        expected = str(tc.get("expected_output", "")).strip()

        exec_res = execute_code(source_code, language, custom_input=inp, timeout=5)
        actual_output = exec_res.stdout.strip()
        
        total_exec_time += exec_res.execution_time
        total_memory_mb = max(total_memory_mb, exec_res.memory_usage_mb)

        norm_actual = normalize_output(actual_output)
        norm_expected = normalize_output(expected)
        passed = (norm_actual == norm_expected) and (exec_res.exit_code == 0)
        if passed:
            passed_count += 1

        detailed_results.append({
            "test_case_num": idx,
            "is_hidden": tc['is_hidden'],
            "input": "***** (Hidden)" if tc['is_hidden'] else inp,
            "expected_output": "***** (Hidden)" if tc['is_hidden'] else expected,
            "actual_output": "***** (Hidden)" if tc['is_hidden'] and not passed else actual_output,
            "passed": passed,
            "error": exec_res.stderr if exec_res.stderr else None,
            "execution_time": exec_res.execution_time
        })

    # Correctness Score (0 to 50 pts)
    correctness_score = (passed_count / total_test_cases * 50.0) if total_test_cases > 0 else 0.0

    # Execution Time Efficiency (0 to 20 pts)
    avg_exec_time = (total_exec_time / total_test_cases) if total_test_cases > 0 else 0.0
    if avg_exec_time <= 0.1:
        time_score = 20.0
    elif avg_exec_time <= 0.5:
        time_score = 15.0
    elif avg_exec_time <= 1.0:
        time_score = 10.0
    else:
        time_score = 5.0

    # Memory Efficiency (0 to 10 pts)
    if total_memory_mb <= 20.0:
        memory_score = 10.0
    elif total_memory_mb <= 50.0:
        memory_score = 7.0
    else:
        memory_score = 4.0

    # Code Quality & Style Score (0 to 20 pts)
    analyzer = CompilerAnalyzer(source_code, language)
    opt_res = analyzer.analyze_optimization()
    syntax_res = analyzer.check_syntax()

    style_score = (opt_res["performance_score"] / 100.0) * 20.0
    if not syntax_res["valid"]:
        style_score = max(0.0, style_score - 10.0)

    final_score = round(correctness_score + time_score + memory_score + style_score, 1)

    # AI Probability Predictor
    ai_engine = AIEngine()
    ai_prob_score = ai_engine.predict_ai_probability(source_code)

    feedback = f"Passed {passed_count}/{total_test_cases} test cases. Overall Code Efficiency & Correctness Rating: {final_score}/100."
    if passed_count == total_test_cases:
        feedback += " Outstanding submission!"

    return {
        "final_score": final_score,
        "correctness_score": round(correctness_score * 2, 1), # Out of 100 scale for UI
        "style_score": round(style_score * 5, 1),
        "test_cases_passed": passed_count,
        "total_test_cases": total_test_cases,
        "execution_time": round(total_exec_time, 4),
        "memory_usage_mb": round(total_memory_mb, 2),
        "ai_probability_score": ai_prob_score,
        "detailed_results": detailed_results,
        "feedback": feedback
    }
