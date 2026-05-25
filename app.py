import streamlit as st
from utils.reviewer import (
    analyze_code,
    generate_badges,
    sanitize_code,
    check_syntax,
    get_metrics,
    suggest_fixes,
)
from utils.ui import (
    score_card,
    section_title,
    render_badges,
    render_metrics,
    render_download_button,
)

st.set_page_config(
    page_title="CodePulse AI",
    page_icon="⚡",
    layout="wide"
)

# ---------------- HEADER ---------------- #

st.markdown("""
<div class="custom-header">⚡ CodePulse AI</div>
<div class="tagline">
    A focused, minimalist reviewer. Paste code or upload a file; results are concise and actionable.
</div>
""", unsafe_allow_html=True)

# ---------------- COLORS (Dark Theme) ---------------- #

bg_gradient = "linear-gradient(135deg, #050816 0%, #0f172a 100%)"
card_bg = "rgba(17, 24, 39, 0.75)"
border_color = "rgba(255,255,255,0.08)"
text = "#ffffff"
muted_text = "#94a3b8"
accent = "#8b5cf6"
accent2 = "#6366f1"
textarea_bg = "#111827"
code_bg = "#0b1220"

# ---------------- CSS ---------------- #

css = f"""
<style>

@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap');

html, body, [class*="css"] {{
    font-family: 'Outfit', sans-serif !important;
}}

[data-testid="stAppViewContainer"] {{
    background: {bg_gradient};
    color: {text};
}}

[data-testid="stHeader"] {{
    background: transparent;
}}

section.main > div {{
    padding-top: 2rem;
}}

.custom-header {{
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(90deg, {accent2}, {accent});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem;
}}

.tagline {{
    color: {muted_text};
    font-size: 1.05rem;
    margin-bottom: 1.5rem;
}}

label, p, h1, h2, h3, h4, h5, h6, span {{
    color: {text} !important;
}}

.stSelectbox > div > div {{
    background: {textarea_bg} !important;
    border: 1px solid {border_color} !important;
    border-radius: 12px !important;
}}

.stSelectbox div[data-baseweb="select"] > div {{
    background: {textarea_bg} !important;
    color: {text} !important;
}}

.stSelectbox div[data-baseweb="select"] span {{
    color: {text} !important;
}}

div[data-baseweb="popover"] {{
    background: {textarea_bg} !important;
    border-radius: 12px !important;
    border: 1px solid {border_color} !important;
}}

div[role="option"] {{
    background: {textarea_bg} !important;
    color: {text} !important;
}}

div[role="option"]:hover {{
    background: rgba(99,102,241,0.2) !important;
}}

.stTextArea textarea {{
    background: {textarea_bg} !important;
    color: #ffffff !important;
    border-radius: 16px !important;
    border: 1px solid {border_color} !important;
    font-family: 'Fira Code', monospace !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    padding: 18px !important;
}}

.stTextArea textarea::placeholder {{
    color: #94a3b8 !important;
}}

.stTextArea textarea:focus {{
    border: 1px solid {accent} !important;
    box-shadow: 0 0 0 1px {accent} !important;
}}

[data-testid="stFileUploaderDropzone"] {{
    background: rgba(15,23,42,0.45) !important;
    border: 2px dashed {border_color} !important;
    border-radius: 16px !important;
    padding: 30px !important;
}}

[data-testid="stFileUploaderDropzone"] * {{
    color: {text} !important;
}}

[data-testid="stFileUploaderDropzone"] button {{
    background: linear-gradient(90deg, {accent2}, {accent}) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 8px 18px !important;
    font-weight: 600 !important;
}}

.stButton > button {{
    width: 100%;
    background: linear-gradient(90deg, {accent2}, {accent}) !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 12px !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    transition: 0.3s;
}}

.stButton > button:hover {{
    transform: translateY(-2px);
    opacity: 0.95;
}}

pre {{
    background: {code_bg} !important;
    border-radius: 14px !important;
    border: 1px solid {border_color} !important;
    padding: 16px !important;
}}

code {{
    color: #ffffff !important;
    font-family: 'Fira Code', monospace !important;
}}

[data-testid="stCodeBlock"] {{
    background: {code_bg} !important;
    border-radius: 14px !important;
    border: 1px solid {border_color} !important;
}}

[data-testid="stCodeBlock"] * {{
    color: #ffffff !important;
}}

[data-testid="stAlert"] {{
    border-radius: 14px !important;
}}

.stTabs [data-baseweb="tab-list"] {{
    background: rgba(15,23,42,0.35);
    padding: 8px;
    border-radius: 14px;
    gap: 10px;
}}

.stTabs [data-baseweb="tab"] {{
    color: {muted_text} !important;
    border-radius: 10px !important;
    padding: 10px 18px !important;
}}

.stTabs [aria-selected="true"] {{
    background: rgba(99,102,241,0.18) !important;
    color: {text} !important;
}}

.stCheckbox label {{
    color: {text} !important;
}}

.metric-card {{
    background: {card_bg};
    border: 1px solid {border_color};
    border-radius: 18px;
    padding: 22px;
    backdrop-filter: blur(12px);
}}

</style>
"""

st.markdown(css, unsafe_allow_html=True)

# ---------------- INPUTS ---------------- #

language = st.selectbox(
    "Language",
    ["Python", "Java", "C++", "JavaScript"],
    index=0
)

uploaded = st.file_uploader(
    "Upload a code file (optional)",
    type=["py", "java", "cpp", "js"]
)

if "code_input" not in st.session_state:
    st.session_state["code_input"] = ""

if uploaded is not None:
    try:
        raw = uploaded.read().decode("utf-8", errors="ignore")
    except Exception:
        raw = str(uploaded.read())

    st.session_state["code_input"] = raw

code = st.text_area(
    "Paste your code here",
    height=420,
    placeholder="Paste your code...",
    key="code_input"
)

# ---------------- ANALYSIS ---------------- #

cleaned = sanitize_code(code)

syntax_msg = None
suggestion = None

if code and code.strip():

    syntax_msg = check_syntax(cleaned, language)

    if syntax_msg:

        suggestion = suggest_fixes(cleaned, language)

        st.error(syntax_msg)

        st.markdown("### Suggested Quick Fixes")

        for note in suggestion.get("notes", []):
            st.markdown(f"- {note}")

        st.code(
            suggestion.get("suggested", ""),
            language=language.lower()
        )

        def apply_fix(suggested_code):
            st.session_state["code_input"] = suggested_code

        st.button(
            "Apply Suggested Fix",
            on_click=apply_fix,
            args=(suggestion.get("suggested", cleaned),)
        )

    analyze_anyway = st.checkbox(
        "Ignore errors and analyze anyway",
        value=False
    )

else:
    analyze_anyway = False

# ---------------- ANALYZE BUTTON ---------------- #

if st.button("Analyze", use_container_width=True):

    if not code.strip():

        st.warning("Please paste or upload a code file first.")

    else:

        if syntax_msg and not analyze_anyway:

            st.info(
                "Fix syntax issues or enable 'Ignore errors and analyze anyway'."
            )

        else:

            result = analyze_code(cleaned)

            if result:

                section_title("Performance")

                c1, c2, c3 = st.columns(3)

                with c1:
                    score_card("Quality", f"{result['quality']}%")

                with c2:
                    score_card("Readability", f"{result['readability']}%")

                with c3:
                    score_card("Readiness", f"{result['interview']}%")

                metrics = get_metrics(cleaned, language)

                render_metrics(metrics)

                tabs = st.tabs([
                    "Overview",
                    "Heatmap",
                    "Review",
                    "Tips"
                ])

                with tabs[0]:

                    st.markdown("### Badges")
                    render_badges(generate_badges(result))

                    st.markdown("### Summary")
                    st.write(result.get("summary", "No summary available."))

                    st.markdown("### Sanitized Code")

                    st.code(
                        cleaned,
                        language=language.lower()
                    )

                with tabs[1]:

                    st.markdown("### Bug Heatmap")

                    st.code(
                        result.get("heatmap", ""),
                        language="text"
                    )

                with tabs[2]:

                    st.markdown("### Smart Review")

                    for item in result.get("review", []):
                        st.info(item)

                with tabs[3]:

                    st.markdown("### Improvement Suggestions")

                    for tip in result.get("tips", []):
                        st.markdown(f"- {tip}")

                tips_text = "\n- ".join(result.get("tips", []))

                report = f"""
Quality: {result['quality']}%
Readability: {result['readability']}%
Readiness: {result['interview']}%

Tips:
- {tips_text}
"""

                render_download_button(
                    report,
                    filename="codepulse_report.txt"
                )

            else:

                st.markdown("### Analysis skipped")

                st.write(
                    "The code could not be analyzed due to syntax errors."
                )

                st.code(
                    cleaned,
                    language=language.lower()
                )