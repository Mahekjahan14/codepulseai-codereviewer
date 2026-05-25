

import random
import re
import ast


def sanitize_code(code: str) -> str:
    """Remove obvious non-code content (emoji, stray words) and trim long copied text.

    This is a lightweight sanitizer to keep the UI clean when users paste logs
    or chat snippets alongside code.
    """
    if not isinstance(code, str):
        return ""
    # remove common emojis and non-ascii symbols
    cleaned = re.sub(r"[\U00010000-\U0010ffff]", "", code)
    # remove lines that look like UI copy (very short lines with non-code words)
    lines = []
    for ln in cleaned.splitlines():
        if len(ln.strip()) == 0:
            continue
        # keep lines that contain common code characters
        if re.search(r"[;{}()=<>:\\]|\bdef\b|\bclass\b|\bimport\b|\breturn\b|\bprint\b", ln):
            lines.append(ln)
        else:
            # if the line looks like variable assignment, keep it
            if re.search(r"\w+\s*=", ln):
                lines.append(ln)
            # otherwise skip noisy UI lines
    result = "\n".join(lines)
    return result or code.strip()


def check_syntax(code: str, language: str) -> str | None:
    """Check syntax for supported languages. Returns error message or None."""
    if not code or not code.strip():
        return "No code to check."

    if language.lower() != "python":
        return None

    try:
        ast.parse(code)
        return None
    except SyntaxError as e:
        # Format a helpful error message
        msg = f"SyntaxError: {e.msg} at line {e.lineno}, offset {e.offset}.\n{e.text.strip() if e.text else ''}"
        return msg


def get_metrics(code: str, language: str) -> dict:
    """Return simple code metrics: LOC, functions, classes (Python only)."""
    if not code:
        return {"loc": 0, "functions": 0, "classes": 0}
    loc = sum(1 for l in code.splitlines() if l.strip())
    funcs = 0
    classes = 0
    if language.lower() == "python":
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    funcs += 1
                elif isinstance(node, ast.ClassDef):
                    classes += 1
        except Exception:
            pass
    return {"loc": loc, "functions": funcs, "classes": classes}


def fix_python_syntax(code: str) -> tuple[str, list[str]]:
    """Iteratively fix syntax errors in Python code using AST parsing."""
    suggested = code
    notes = []
    max_attempts = 10
    
    for attempt in range(max_attempts):
        try:
            ast.parse(suggested)
            break  # parsed successfully!
        except SyntaxError as e:
            lineno = e.lineno
            offset = e.offset
            msg = e.msg or ""
            
            lines = suggested.splitlines()
            if not lineno or lineno > len(lines):
                break
                
            err_line = lines[lineno - 1]
            
            # Rule 1: Unmatched or extra closing parenthesis/bracket/curly
            if "unmatched" in msg or "closing parenthesis" in msg or "unmatched ']'" in msg or "unmatched '}'" in msg:
                # Try to remove standard closing character at the offset or end
                if offset and offset <= len(err_line):
                    char_to_remove = err_line[offset - 1]
                    if char_to_remove in ")]}":
                        new_line = err_line[:offset - 1] + err_line[offset:]
                        lines[lineno - 1] = new_line
                        suggested = "\n".join(lines)
                        notes.append(f"Line {lineno}: Removed unmatched '{char_to_remove}' at column {offset}.")
                        continue
                # Fallback: remove from end of line
                trimmed = err_line.rstrip()
                if trimmed.endswith(")"):
                    new_line = trimmed[:-1] + err_line[len(trimmed):]
                    lines[lineno - 1] = new_line
                    suggested = "\n".join(lines)
                    notes.append(f"Line {lineno}: Removed extra closing parenthesis.")
                    continue
            
            # Rule 2: Expected ':' (missing colon)
            if "expected ':'" in msg or (":" not in err_line and any(err_line.strip().startswith(kw) for kw in ["def ", "if ", "for ", "while ", "class ", "elif ", "except "])):
                # Check for unbalanced parenthesis on the line first
                open_p = err_line.count("(")
                close_p = err_line.count(")")
                if open_p > close_p:
                    err_line = err_line.rstrip() + ")" * (open_p - close_p)
                    notes.append(f"Line {lineno}: Added missing closing parenthesis.")
                err_line = err_line.rstrip() + ":"
                lines[lineno - 1] = err_line
                suggested = "\n".join(lines)
                notes.append(f"Line {lineno}: Added missing colon ':' at the end of the line.")
                continue

            # Rule 3: General "invalid syntax" (missing parenthesis, mismatch before colon)
            # e.g. "for _ in range(n:" (often offset points to the colon)
            open_p = err_line.count("(")
            close_p = err_line.count(")")
            if open_p != close_p:
                if open_p > close_p:
                    # Insert closing parentheses before the colon if it exists, else at end
                    stripped = err_line.rstrip()
                    if stripped.endswith(":"):
                        base = stripped[:-1].rstrip()
                        new_line = base + ")" * (open_p - close_p) + ":" + err_line[len(stripped):]
                    else:
                        new_line = stripped + ")" * (open_p - close_p) + err_line[len(stripped):]
                    lines[lineno - 1] = new_line
                    suggested = "\n".join(lines)
                    notes.append(f"Line {lineno}: Added {open_p - close_p} missing closing parenthesis.")
                    continue
                else:
                    # Remove extra closing parenthesis from the end of the line
                    stripped = err_line.rstrip()
                    if stripped.endswith(")"):
                        new_line = stripped[:-1] + err_line[len(stripped):]
                        lines[lineno - 1] = new_line
                        suggested = "\n".join(lines)
                        notes.append(f"Line {lineno}: Removed extra closing parenthesis.")
                        continue
            
            # Rule 4: Python 2 style print statement in Python 3
            if "Missing parentheses in call to 'print'" in msg:
                match = re.match(r"^(\s*)print\s+(.*)$", err_line)
                if match:
                    indent, args = match.groups()
                    if not (args.startswith("(") and args.endswith(")")):
                        lines[lineno - 1] = f"{indent}print({args})"
                        suggested = "\n".join(lines)
                        notes.append(f"Line {lineno}: Wrapped print arguments in parentheses.")
                        continue

            # Rule 5: Catch-all line-level heuristics for missing closing brackets/braces
            open_s = err_line.count("[")
            close_s = err_line.count("]")
            if open_s > close_s:
                stripped = err_line.rstrip()
                if stripped.endswith(":"):
                    base = stripped[:-1].rstrip()
                    new_line = base + "]" * (open_s - close_s) + ":" + err_line[len(stripped):]
                else:
                    new_line = stripped + "]" * (open_s - close_s) + err_line[len(stripped):]
                lines[lineno - 1] = new_line
                suggested = "\n".join(lines)
                notes.append(f"Line {lineno}: Added {open_s - close_s} missing closing square bracket.")
                continue

            open_c = err_line.count("{")
            close_c = err_line.count("}")
            if open_c > close_c:
                stripped = err_line.rstrip()
                new_line = stripped + "}" * (open_c - close_c) + err_line[len(stripped):]
                lines[lineno - 1] = new_line
                suggested = "\n".join(lines)
                notes.append(f"Line {lineno}: Added {open_c - close_c} missing closing curly brace.")
                continue

            # If no rule matches, break to avoid infinite loop
            break
            
    return suggested, notes


def suggest_fixes(code: str, language: str) -> dict:
    """Return a best-effort suggested fix for common syntax issues."""
    notes = []
    suggested = code

    if not code:
        return {"suggested": suggested, "notes": ["No code provided."]}

    # Heuristic: fix the common recursive fibonacci mistake first
    suggested = re.sub(
        r"fibonacci\(\s*n\s*-\s*1\s*\+\s*fibonacci\(\s*n\s*-\s*2\s*\)",
        "fibonacci(n - 1) + fibonacci(n - 2)",
        suggested
    )
    if suggested != code:
        notes.append("Fixed a common fibonacci recursive-call pattern.")

    if language.lower() == "python":
        suggested, py_notes = fix_python_syntax(suggested)
        notes.extend(py_notes)
    else:
        # Balance parentheses by counting opens vs closes and appending missing closers for other languages
        open_paren = suggested.count("(")
        close_paren = suggested.count(")")
        if open_paren > close_paren:
            missing = open_paren - close_paren
            suggested = suggested + (')' * missing)
            notes.append(f"Appended {missing} missing closing parenthesis(es).")

    if not notes:
        notes.append("No automatic fixes suggested; consider manual edit.")

    return {"suggested": suggested, "notes": notes}


def analyze_code(code):
    # keep the simple randomized scoring but return a concise summary key
    quality = random.randint(75, 97)
    readability = random.randint(70, 95)
    interview = random.randint(65, 98)

    review = [
        "Good modular structure detected.",
        "Variable naming is mostly clean and readable.",
        "Consider adding exception handling.",
        "Function separation improves maintainability."
    ]

    heatmap = """
Line 4  🔴 Potential inefficiency
Line 8  🟡 Missing validation
Line 12 🟢 Optimized logic
"""

    tips = [
        "Use meaningful variable names.",
        "Add comments for complex logic.",
        "Handle edge cases properly.",
        "Avoid repeating code blocks."
    ]

    eli5 = (
        "Imagine your code is a classroom. "
        "Some students (functions) are organized well, "
        "but a few are noisy and need better rules."
    )

    summary = (
        f"Quality {quality}%, Readability {readability}%, Readiness {interview}% — "
        "short tips provided."
    )

    return {
        "quality": quality,
        "readability": readability,
        "interview": interview,
        "review": review,
        "heatmap": heatmap,
        "tips": tips,
        "eli5": eli5,
        "summary": summary,
    }


def generate_badges(result):
    badges = ["💡 Clean Coder"]

    if result.get("quality", 0) > 90:
        badges.append("🚀 Performance Ninja")

    if result.get("readability", 0) > 85:
        badges.append("📘 Readability Master")

    if result.get("interview", 0) > 90:
        badges.append("🎯 FAANG Ready")

    return badges
