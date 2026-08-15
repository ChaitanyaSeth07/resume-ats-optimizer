"""
Resume ATS Optimizer
v1.5 — Graph pipeline + Clean Professional UI
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

from core.pdf_parser import extract_text_from_pdf, get_pdf_info
from core.structure_extractor import extract_structure
from core.feedback_loop import run_feedback_loop
from core.langgraph_pipeline import run_graph_optimization
from core.docx_builder import create_ats_docx
from core.converter import convert_docx_to_pdf
from core.evaluation_logger import log_evaluation, get_all_logs
from core.security import validate_uploaded_file, basic_output_validation, clear_sensitive_session_keys
from core.report_builder import build_analysis_report
from core.memory_graph_viz import build_error_mind_figure

# -------------------- Page Config --------------------
st.set_page_config(
    page_title="Resume ATS Optimizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- Professional CSS --------------------
st.markdown("""
<style>
    .stApp { background-color: #F8FAFC; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    h1, h2, h3, h4 {
        color: #0F172A !important;
        font-weight: 650 !important;
    }
    p, label, span, div { color: #334155; }

    .hero-title {
        font-size: 2.1rem; font-weight: 700; color: #0F172A; margin-bottom: 0.35rem;
    }
    .hero-subtitle {
        font-size: 1.05rem; color: #334155; margin-bottom: 0.75rem;
    }
    .hero-desc {
        font-size: 0.95rem; color: #64748B; max-width: 720px; margin-bottom: 0.9rem;
    }
    .badge {
        display: inline-block; background: #EFF6FF; color: #2563EB;
        border: 1px solid #BFDBFE; font-size: 0.78rem; font-weight: 600;
        padding: 0.25rem 0.65rem; border-radius: 999px; margin-bottom: 1.25rem;
    }

    .card-title {
        font-size: 0.8rem; font-weight: 700; letter-spacing: 0.04em;
        color: #0F172A; margin-bottom: 0.35rem;
    }
    .card-desc {
        font-size: 0.9rem; color: #64748B; margin-bottom: 0.9rem;
    }

    .section-title {
        font-size: 1.25rem; font-weight: 650; color: #0F172A; margin-bottom: 0.25rem;
    }
    .section-subtitle {
        font-size: 0.92rem; color: #64748B; margin-bottom: 1.1rem;
    }

    .score-main {
        font-size: 2.6rem; font-weight: 700; color: #2563EB; line-height: 1.1;
    }
    .score-label {
        font-size: 0.85rem; color: #64748B; font-weight: 600; letter-spacing: 0.03em;
    }
    .score-rating {
        font-size: 1.05rem; font-weight: 600; color: #0F172A; margin-top: 0.25rem;
    }

    .metric-card {
        background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px;
        padding: 1rem 1.1rem; text-align: center;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
    }
    .metric-value {
        font-size: 1.45rem; font-weight: 700; color: #0F172A;
    }
    .metric-label {
        font-size: 0.78rem; color: #64748B; font-weight: 600; margin-top: 0.2rem;
    }

    .status-good { color: #16A34A !important; }
    .status-warn { color: #D97706 !important; }
    .status-bad  { color: #DC2626 !important; }

    .journey {
        background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px;
        padding: 1rem 1.25rem; font-size: 0.92rem; color: #334155; line-height: 1.7;
    }

    .empty-state {
        text-align: center; padding: 2.5rem 1rem; color: #334155;
        background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px;
    }
    .empty-title {
        font-size: 1.25rem; font-weight: 650; color: #0F172A; margin-bottom: 0.5rem;
    }
    .empty-flow {
        margin-top: 1.25rem; font-size: 0.92rem; color: #64748B; line-height: 1.8;
    }

    .footer {
        text-align: center; color: #64748B; font-size: 0.82rem;
        margin-top: 2.5rem; padding-top: 1rem; border-top: 1px solid #E2E8F0;
    }

    div.stButton > button[kind="primary"] {
        background-color: #2563EB; border-color: #2563EB; color: #FFFFFF;
        font-weight: 600; padding: 0.6rem 1.2rem; border-radius: 8px;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #1D4ED8; border-color: #1D4ED8; color: #FFFFFF;
    }

    section[data-testid="stSidebar"] {
        background-color: #FFFFFF; border-right: 1px solid #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize variables
uploaded_file = None
job_description = ""

# -------------------- Sidebar --------------------
with st.sidebar:
    st.markdown("### Settings")

    target_score = st.slider(
        "Target Score",
        min_value=60,
        max_value=90,
        value=75,
        help="The feedback loop will attempt to improve the resume until this score is reached."
    )

    max_attempts = st.slider(
        "Maximum Attempts",
        min_value=1,
        max_value=3,
        value=3,
        help="Maximum number of AI improvement cycles."
    )

    output_format = st.selectbox(
        "Output Format",
        options=["DOCX", "PDF", "Both"],
        index=2
    )

    st.markdown("---")
    st.markdown("**Version**")
    st.caption("V2.2")
    st.caption("Graph pipeline + Clean UI")

    st.markdown("---")
    st.markdown("### Creator Access")
    creator_password = st.text_input("Enter creator password", type="password")
    show_dashboard = creator_password == "ats2026"

    st.markdown("---")
    st.markdown("### Resume Design")

    design_theme = st.selectbox(
        "Color Theme",
        ["Blue", "Charcoal", "Teal", "Green", "Burgundy"],
        index=0
    )
    design_font = st.selectbox(
        "Typography",
        ["Calibri", "Arial", "Georgia", "Garamond"],
        index=0
    )
    design_header = st.selectbox(
        "Header Style",
        ["Centered", "Left-aligned", "Minimal"],
        index=0
    )
    design_section = st.selectbox(
        "Section Style",
        ["Underline", "Caps + line", "Simple bold"],
        index=0
    )
    design_spacing = st.selectbox(
        "Spacing",
        ["Compact", "Normal", "Comfortable"],
        index=1
    )
    design_accent = st.selectbox(
        "Accent Strength",
        ["Low", "Medium"],
        index=1
    )
    st.caption("Design stays ATS-safe: no icons, tables, or multi-column layouts.")
    
# -------------------- Creator Dashboard --------------------
if show_dashboard:
    st.markdown("## Creator Evaluation Dashboard")
    st.caption("Metrics only. No resume content is stored or shown.")

    logs = get_all_logs()

    if not logs:
        st.warning("No evaluation data found yet. Run a few optimizations first.")
    else:
        df = pd.DataFrame(logs)

        for col in ["overall_score", "keyword_score", "structural_score", "attempts_used", "target_score"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Evaluations", len(df))
        c2.metric("Avg Overall Score", f"{df['overall_score'].mean():.1f}")
        c3.metric("Avg Keyword Match", f"{df['keyword_score'].mean():.1f}%")
        c4.metric("Avg Attempts", f"{df['attempts_used'].mean():.1f}")

        st.divider()

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**Overall Score Distribution**")
            fig1, ax1 = plt.subplots(figsize=(6, 4))
            sns.histplot(df["overall_score"].dropna(), bins=10, kde=True, ax=ax1, color="#2563EB")
            ax1.set_xlabel("Overall Score")
            ax1.set_ylabel("Count")
            st.pyplot(fig1)

        with col_b:
            st.markdown("**Keyword vs Structure Score**")
            fig2, ax2 = plt.subplots(figsize=(6, 4))
            sns.scatterplot(
                data=df,
                x="keyword_score",
                y="structural_score",
                hue="rating",
                ax=ax2,
                s=80
            )
            ax2.set_xlabel("Keyword Match %")
            ax2.set_ylabel("Structure Score")
            st.pyplot(fig2)

        st.markdown("**Attempts Used per Run**")
        fig3, ax3 = plt.subplots(figsize=(8, 3.5))
        sns.countplot(data=df, x="attempts_used", ax=ax3, color="#2563EB")
        ax3.set_xlabel("Number of Attempts")
        ax3.set_ylabel("Count")
        st.pyplot(fig3)

        st.divider()
        st.markdown("**Raw Metrics Log**")
        st.dataframe(df, use_container_width=True)

        st.divider()
        st.markdown("### 3-D Error Memory Brain")
        st.caption(
            "Hybrid view of anonymized error memory: K-means communities, "
            "Mexican-hat relational field, tanh-normalized links, and regression-based gain prediction. "
            "No resume content is shown."
        )

        fig_mind, mind_summary = build_error_mind_figure()
        if fig_mind is None:
            st.warning("Could not build the 3-D Error Brain. Install plotly + scikit-learn.")
        else:
            st.plotly_chart(fig_mind, use_container_width=True)

            if mind_summary:
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Nodes", mind_summary.get("nodes", 0))
                m2.metric("Relations", mind_summary.get("edges", 0))
                m3.metric("Communities", mind_summary.get("clusters", 0))
                m4.metric(
                    "Gain model",
                    "Ready" if mind_summary.get("regression_ready") else "Need more data"
                )

            st.markdown("""
**How to read this**
- **Dot color** = K-means error community
- **Dot size** = success / frequency
- **Blue links** = positive Mexican-hat relations
- **Red links** = inhibitory / distant relations
- **Hover** = success rate, avg gain, predicted gain
""")

        st.divider()
        st.markdown("### Download Analysis")

        report_buffer = build_analysis_report(logs)
        d1, d2 = st.columns(2)

        with d1:
            st.download_button(
                label="Download Full Analysis Report (DOCX)",
                data=report_buffer,
                file_name="resume_ats_analysis_report.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

        with d2:
            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Raw Metrics (CSV)",
                data=csv_data,
                file_name="evaluation_metrics.csv",
                mime="text/csv",
                use_container_width=True
            )

    st.divider()
    st.info("Creator mode is active. Regular users do not see this dashboard.")
    st.stop()

# -------------------- Hero --------------------
st.markdown('<div class="hero-title">Resume ATS Optimizer</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">AI-powered resume optimization for modern recruitment.</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="hero-desc">Upload your resume and provide a job description. '
    'The system analyzes, improves, scores, and generates an ATS-friendly version.</div>',
    unsafe_allow_html=True
)
st.markdown('<div class="badge">AI + ATS Feedback Loop</div>', unsafe_allow_html=True)

st.divider()

# -------------------- Input Section --------------------
st.markdown('<div class="section-title">Optimize Your Resume</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-subtitle">Provide your resume and the job description to begin.</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="card-title">YOUR RESUME</div>', unsafe_allow_html=True)
    st.markdown('<div class="card-desc">Upload your current resume as a PDF.</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        label_visibility="collapsed"
    )
    if uploaded_file:
        st.success(f"✓ {uploaded_file.name} uploaded")
    else:
        st.caption("Supported format: PDF")

with col2:
    st.markdown('<div class="card-title">JOB DESCRIPTION</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="card-desc">Paste the job description for the position you\'re targeting.</div>',
        unsafe_allow_html=True
    )
    job_description = st.text_area(
        "Job Description",
        height=160,
        placeholder="Paste the full job description here...",
        label_visibility="collapsed"
    )
    st.caption("Tip: Include the complete job description for better keyword matching.")

st.write("")

# -------------------- CTA --------------------
optimize_clicked = st.button("🚀 Optimize My Resume", type="primary", use_container_width=True)

# -------------------- Empty State --------------------
if (not optimize_clicked) and (uploaded_file is None) and (not job_description.strip()):
    st.markdown("""
    <div class="empty-state">
        <div class="empty-title">Ready to optimize your resume?</div>
        <div>Upload your resume and paste a job description to get started.</div>
        <div class="empty-flow">
            PDF Resume + Job Description<br>
            ↓<br>
            AI Optimization<br>
            ↓<br>
            ATS Scoring<br>
            ↓<br>
            Error Diagnosis + Targeted Fix<br>
            ↓<br>
            Optimized Resume
        </div>
    </div>
    """, unsafe_allow_html=True)

# -------------------- Processing & Results --------------------
if optimize_clicked:
    is_valid, error_msg = validate_uploaded_file(uploaded_file)
    if not is_valid:
        st.error(error_msg)
        st.stop()

    if not job_description.strip():
        st.error("Please paste a job description to continue.")
        st.stop()

    with st.status("Optimization in progress", expanded=True) as status:
        st.write("✓ Extracting resume text")
        resume_text = extract_text_from_pdf(uploaded_file)

        if resume_text is None:
            st.error(
                "We couldn't complete the optimization.\n\n"
                "Please check:\n"
                "• The uploaded PDF contains selectable text\n"
                "• The file is not image-only or scanned without OCR"
            )
            st.stop()

        st.write("✓ Analyzing resume structure")
        structured = extract_structure(resume_text)

        st.write("✓ Running AI optimization")
        st.write("✓ Diagnosing errors and applying targeted fixes")

        design_options = {
            "theme": design_theme,
            "font": design_font,
            "header_style": design_header,
            "section_style": design_section,
            "spacing": design_spacing,
            "accent_strength": design_accent,
        }

        try:
            final_resume, score_report, attempts, graph_state = run_graph_optimization(
                structured_resume=structured,
                job_description=job_description,
                original_text=resume_text,
                target_score=float(target_score),
                max_attempts=int(max_attempts),
                design_options=design_options,
                job_family="general",
            )
        except Exception as e:
            print(f"Graph pipeline failed, falling back: {e}")
            final_resume, score_report, attempts = run_feedback_loop(
                structured_resume=structured,
                job_description=job_description,
                max_attempts=max_attempts,
                target_score=float(target_score),
            )
            graph_state = {}

        if final_resume is None:
            st.error(
                "We couldn't complete the optimization.\n\n"
                "Please check:\n"
                "• Your API configuration\n"
                "• The uploaded PDF contains selectable text\n"
                "• The job description is not empty"
            )
            st.stop()

        is_output_valid, output_error = basic_output_validation(final_resume)
        if not is_output_valid:
            st.error("We couldn't complete the optimization due to an unexpected AI response.")
            st.stop()

        st.write(f"AI improvement attempt {attempts} of {max_attempts}")
        st.write("○ Generating final documents")

        docx_buffer = create_ats_docx(final_resume, design=design_options)

        pdf_buffer = None
        if output_format in ["PDF", "Both"]:
            pdf_buffer = convert_docx_to_pdf(docx_buffer)

        log_evaluation(
            score_report=score_report,
            attempts_used=attempts,
            target_score=float(target_score),
            original_text_length=len(resume_text),
            job_description_length=len(job_description)
        )

        status.update(label="✓ Optimization Complete", state="complete", expanded=False)

    # -------------------- Results --------------------
    st.markdown('<div class="section-title">Optimization Results</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Here\'s how your optimized resume performed.</div>',
        unsafe_allow_html=True
    )

    score = score_report.get("overall_score", 0)
    rating = score_report.get("rating", "—")

    mcol1, mcol2, mcol3, mcol4 = st.columns(4)

    with mcol1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="score-label">ATS SCORE</div>
            <div class="score-main">{score}/100</div>
            <div class="score-rating {'status-good' if rating == 'Excellent' else 'status-warn' if rating in ['Good', 'Average'] else 'status-bad'}">{rating}</div>
        </div>
        """, unsafe_allow_html=True)

    with mcol2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{score_report.get('keyword_score', 0)}%</div>
            <div class="metric-label">KEYWORD MATCH</div>
        </div>
        """, unsafe_allow_html=True)

    with mcol3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{score_report.get('structural_score', 0)}%</div>
            <div class="metric-label">STRUCTURE</div>
        </div>
        """, unsafe_allow_html=True)

    with mcol4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{attempts}</div>
            <div class="metric-label">AI ATTEMPTS</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    st.markdown("#### Optimization Journey")
    st.markdown(f"""
    <div class="journey">
        Initial optimization<br>
        ↓<br>
        Score evaluation<br>
        ↓<br>
        Error diagnosis<br>
        ↓<br>
        Targeted AI fix<br>
        ↓<br>
        Final evaluation<br><br>
        <strong>Attempts used:</strong> {attempts} / {max_attempts}<br>
        <strong>Target score:</strong> {target_score}<br>
        <strong>Final score:</strong> {score}
    </div>
    """, unsafe_allow_html=True)

    if graph_state and graph_state.get("fix_history"):
        with st.expander("Repair path (graph pipeline)"):
            for item in graph_state["fix_history"]:
                st.write(
                    f"Attempt {item.get('attempt')}: "
                    f"{item.get('error_code')} → "
                    f"{'improved' if item.get('improved') else 'no gain'} "
                    f"({item.get('score_before')} → {item.get('score_after')})"
                )

    missing = score_report.get("missing_keywords") or []
    with st.expander("Keyword Analysis"):
        if missing:
            st.markdown("**Keywords that may be missing**")
            st.write(", ".join(missing))
            st.caption("Only add a missing keyword if it accurately reflects your experience.")
        else:
            st.write("No major missing keywords detected.")

    st.divider()

    st.markdown("#### Original vs Optimized")
    left, right = st.columns(2)

    with left:
        st.markdown("**ORIGINAL RESUME**")
        st.caption("Extracted from uploaded PDF")
        st.text_area(
            "original",
            value=resume_text,
            height=420,
            disabled=True,
            label_visibility="collapsed"
        )

    with right:
        st.markdown("**OPTIMIZED RESUME**")
        st.caption("AI-optimized version")
        st.text_area(
            "optimized",
            value=final_resume,
            height=420,
            label_visibility="collapsed"
        )

    st.divider()

    st.markdown("#### What Was Improved")
    st.markdown("""
- ✓ Resume structure analyzed  
- ✓ Job-description keywords evaluated  
- ✓ ATS compatibility checked  
- ✓ Specific errors diagnosed and fixed iteratively  
- ✓ Final resume formatted for ATS-friendly output  
""")

    st.divider()

    st.markdown('<div class="section-title">Download Your Optimized Resume</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Choose the format you want to use.</div>',
        unsafe_allow_html=True
    )

    d1, d2, d3 = st.columns(3)

    with d1:
        st.markdown("**Word Document**")
        st.caption("ATS-friendly DOCX")
        st.download_button(
            "Download DOCX",
            data=docx_buffer,
            file_name="optimized_resume.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

    with d2:
        st.markdown("**PDF**")
        st.caption("Portable version")
        if pdf_buffer:
            st.download_button(
                "Download PDF",
                data=pdf_buffer,
                file_name="optimized_resume.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.button("PDF (requires Word/LibreOffice)", disabled=True, use_container_width=True)
            st.caption("Install Microsoft Word or LibreOffice to enable PDF export. DOCX is still available.")

    with d3:
        st.markdown("**Plain Text**")
        st.caption("ATS-friendly text")
        st.download_button(
            "Download TXT",
            data=final_resume,
            file_name="optimized_resume.txt",
            mime="text/plain",
            use_container_width=True
        )

    clear_sensitive_session_keys(st.session_state)

# -------------------- Footer --------------------
st.markdown("""
<div class="footer">
    Resume ATS Optimizer<br>
    AI-powered resume optimization using LLM + error-aware feedback loop<br>
    V2.2
</div>
""", unsafe_allow_html=True)