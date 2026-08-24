import uuid
import time
import json
import re

def generate_certificate_code():
    """Generates a unique hackathon-style verification code for certificates."""
    unique_suffix = str(uuid.uuid4())[:8].upper()
    return f"CV-CERT-2026-{unique_suffix}"

def extract_coding_fingerprint(code):
    """
    BONUS FEATURE 2: Coding Style Fingerprint.
    Tracks student's coding behavior, variable naming convention, comment ratio, and indentation preference.
    """
    lines = code.splitlines()
    total_lines = len(lines)
    if total_lines == 0:
        return {}

    comment_lines = sum(1 for l in lines if l.strip().startswith('#') or l.strip().startswith('//'))
    camel_case_vars = len(re.findall(r'\b[a-z]+[A-Z][a-zA-Z0-9]*\b', code))
    snake_case_vars = len(re.findall(r'\b[a-z]+_[a-z0-9_]+\b', code))
    
    naming_style = "SnakeCase" if snake_case_vars > camel_case_vars else "CamelCase" if camel_case_vars > 0 else "Standard"

    indent_spaces = 4
    for l in lines:
        if l.startswith('  ') and not l.startswith('    '):
            indent_spaces = 2
            break

    return {
        "naming_style": naming_style,
        "comment_density_pct": round((comment_lines / total_lines) * 100, 1),
        "indentation": f"{indent_spaces} Spaces",
        "avg_line_length": round(sum(len(l) for l in lines) / total_lines, 1)
    }

def format_api_response(success=True, data=None, message=""):
    """Uniform REST API JSON response structure."""
    return {
        "success": success,
        "message": message,
        "data": data or {}
    }
