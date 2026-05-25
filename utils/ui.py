
import streamlit as st


def score_card(title, value):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="card-title">{title}</div>
            <div class="card-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(title):
    st.markdown(
        f"""
        <div class="section-header">
            <h3 class="section-title">{title}</h3>
            <div class="section-line"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_badges(badges):
    """Render a horizontal list of small badge chips."""
    if not badges:
        return
    html = "<div class='badges-container'>"
    for b in badges:
        html += f"<span class='badge'>{b}</span>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_metrics(metrics: dict):
    """Render small metric rows for LOC, functions, classes."""
    if not metrics:
        return
    cols = st.columns(3)
    with cols[0]:
        st.markdown(
            f"""
            <div class="metric-card small-card">
              <div class="card-title">Lines of Code</div>
              <div class="card-value">{metrics.get('loc', 0)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.markdown(
            f"""
            <div class="metric-card small-card">
              <div class="card-title">Functions</div>
              <div class="card-value">{metrics.get('functions', 0)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cols[2]:
        st.markdown(
            f"""
            <div class="metric-card small-card">
              <div class="card-title">Classes</div>
              <div class="card-value">{metrics.get('classes', 0)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_download_button(report: bytes | str, filename: str = "report.txt"):
    if isinstance(report, str):
        data = report.encode("utf-8")
    else:
        data = report

    st.markdown("<div class='download-btn-container'>", unsafe_allow_html=True)
    st.download_button("📥 Download Actionable Report", data, file_name=filename)
    st.markdown("</div>", unsafe_allow_html=True)
