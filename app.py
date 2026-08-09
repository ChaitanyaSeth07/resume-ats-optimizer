"""
Resume ATS Optimizer
v0.8 — Clean Professional UI
"""

import streamlit as st
from core.pdf_parser import extract_text_from_pdf, get_pdf_info
from core.structure_extractor import extract_structure
from core.feedback_loop import run_feedback_loop
from core.docx_builder import create_ats_docx
from core.converter import convert_docx_to_pdf
from core.evaluation_logger import log_evaluation
from core.security import validate_uploaded_file, basic_output_validation, clear_sensitive_session_keys

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
    /* Base */
    .stApp {
        background-color: #F8FAFC;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    /* Typography */
    h1, h2, h3, h4 {
        color: #0F172A !important;
        font-weight: 650 !important;
    }
    p, label, span, div {
        color: #334155;
    }

    /* Hero */
    .hero-title {
        font-size: 2.1rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.35rem;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #334155;
        margin-bottom: 0.75rem;
    }
    .hero-desc {
        font-size: 0.95rem;
        color: #64748B;
        max-width: 720px;
        margin-bottom: 0.9rem;
    }
    .badge {
        display: inline-block;
        background: #EFF6FF;
        color: #2563EB;
        border: 1px solid #BFDBFE;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 0.25rem 0.65rem;
        border-radius: 999px;
        margin-bottom: 1.25rem;
    }

    /* Cards */
    .card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.25rem 1.35rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        height: 100%;
    }
    .card-title {
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        color: #0F172A;
        margin-bottom: 0.35rem;
    }
    .card-desc {
        font-size: 0.9rem;
        color: #64748B;
        margin-bottom: 0.9rem;
    }

    /* Section headers */
    .section-title {
        font-size: 1.25rem;
        font-weight: 650;
        color: #0F172A;
        margin-bottom: 0.25rem;
    }
    .section-subtitle {
        font-size: 0.92rem;
        color: #64748B;
        margin-bottom: 1.1rem;
    }

    /* Score highlight */
    .score-main {
        font-size: 2.6rem;
        font-weight: 700;
        color: #2563EB;
        line-height: 1.1;
    }
    .score-label {
        font-size: 0.85rem;
        color: #64748B;
        font-weight: 600;
        letter-spacing: 0.03em;
    }
    .score-rating {
        font-size: 1.05rem;
        font-weight: 600;
        color: #0F172A;
        margin-top: 0.25rem;
    }

    /* Metric cards */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1rem 1.1rem;
        text-align: center;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
    }
    .metric-value {
        font-size: 1.45rem;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-label {
        font-size: 0.78rem;
        color: #64748B;
        font-weight: 600;
        margin-top: 0.2rem;
    }

    /* Semantic colors (scores / status only) */
    .status-good { color: #16A34A !important; }
    .status-warn { color: #D97706 !important; }
    .status-bad  { color: #DC2626 !important; }

    /* Journey */
    .journey {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        font-size: 0.92rem;
        color: #334155;
        line-height: 1.7;
    }

    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 2.5rem 1rem;
        color: #334155;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
    }
    .empty-title {
        font-size: 1.25rem;
        font-weight: 650;
        color: #0F172A;
        margin-bottom: 0.5rem;
    }
    .empty-flow {
        margin-top: 1.25rem;
        font-size: 0.92rem;
        color: #64748B;
        line-height: 1.8;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #64748B;
        font-size: 0.82rem;
        margin-top: 2.5rem;
        padding-top: 1rem;
        border-top: 1px solid #E2E8F0;
    }

    /* Primary button */
    div.stButton > button[kind="primary"] {
        background-color: #2563EB;
        border-color: #2563EB;
        color: #FFFFFF;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        border-radius: 8px;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #1D4ED8;
        border-color: #1D4ED8;
        color: #FFFFFF;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

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
    st.caption("v0.8")
    st.caption("Clean Professional UI")

# -------------------- Hero --------------------
st.markdown('<div class="hero-title">Resume ATS Optimizer</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">AI-powered resume optimization for modern recruitment.</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-desc">Upload your resume and provide a job description. '
    'The system analyzes, improves, scores, and generates an ATS-friendly version.</div>',
    unsafe_allow_html=True
)
st.markdown('<div class="badge">AI + ATS Feedback Loop</div>', unsafe_allow_html=True)

st.divider()

# -------------------- Input Section --------------------
st.markdown('<div class="section-title">Optimize Your Resume</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">Provide your resume and the job description to begin.</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
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
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">JOB DESCRIPTION</div>', unsafe_allow_html=True)
    st.markdown('<div class="card-desc">Paste the job description for the position you\'re targeting.</div>', unsafe_allow_html=True)
    job_description = st.text_area(
        "Job Description",
        height=160,
        placeholder="Paste the full job description here...",
        label_visibility="collapsed"
    )
    st.caption("Tip: Include the complete job description for better keyword matching.")
    st.markdown('</div>', unsafe_allow_html=True)

st.write("")

# -------------------- CTA --------------------
optimize_clicked = st.button("🚀 Optimize My Resume", type="primary", use_container_width=True)

# -------------------- Empty State --------------------
if not optimize_clicked and uploaded_file is None and not job_description:
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
            Feedback Loop<br>
            ↓<br>
            Optimized Resume
        </div>
    </div>
    """, unsafe_allow_html=True)

# -------------------- Processing & Results --------------------
if optimize_clicked:
    # Validation
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
        st.write("✓ Calculating ATS score")
        st.write("⟳ Improving resume")

        final_resume, score_report, attempts = run_feedback_loop(
            structured_resume=structured,
            job_description=job_description,
            max_attempts=max_attempts,
            target_score=float(target_score)
        )

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

        docx_buffer = create_ats_docx(final_resume)

        pdf_buffer = None
        if output_format in ["PDF", "Both"]:
            pdf_buffer = convert_docx_to_pdf(docx_buffer)

        # Log metrics only
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
    st.markdown('<div class="section-subtitle">Here\'s how your optimized resume performed.</div>', unsafe_allow_html=True)

    # Main score
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

    # Optimization Journey
    st.markdown("#### Optimization Journey")
    st.markdown(f"""
    <div class="journey">
        Initial optimization<br>
        ↓<br>
        Score evaluation<br>
        ↓<br>
        AI improvement<br>
        ↓<br>
        Final evaluation<br><br>
        <strong>Attempts used:</strong> {attempts} / {max_attempts}<br>
        <strong>Target score:</strong> {target_score}<br>
        <strong>Final score:</strong> {score}
    </div>
    """, unsafe_allow_html=True)

    # Missing keywords
    missing = score_report.get("missing_keywords") or []
    with st.expander("Keyword Analysis"):
        if missing:
            st.markdown("**Keywords that may be missing**")
            st.write(", ".join(missing))
            st.caption("Only add a missing keyword if it accurately reflects your experience.")
        else:
            st.write("No major missing keywords detected.")

    st.divider()

    # Original vs Optimized
    st.markdown("#### Original vs Optimized")
    left, right = st.columns(2)

    with left:
        st.markdown("**ORIGINAL RESUME**")
        st.caption("Extracted from uploaded PDF")
        st.text_area("original", value=resume_text, height=420, disabled=True, label_visibility="collapsed")

    with right:
        st.markdown("**OPTIMIZED RESUME**")
        st.caption("AI-optimized version")
        st.text_area("optimized", value=final_resume, height=420, label_visibility="collapsed")

    st.divider()

    # What was improved
    st.markdown("#### What Was Improved")
    st.markdown("""
- ✓ Resume structure analyzed  
- ✓ Job-description keywords evaluated  
- ✓ ATS compatibility checked  
- ✓ Resume optimized using iterative AI feedback  
- ✓ Final resume formatted for ATS-friendly output  
""")

    st.divider()

    # Downloads
    st.markdown('<div class="section-title">Download Your Optimized Resume</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Choose the format you want to use.</div>', unsafe_allow_html=True)

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
            st.button("PDF unavailable", disabled=True, use_container_width=True)
            st.caption("PDF conversion is unavailable on this system. DOCX is still available.")

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

    # Clear sensitive session data
    clear_sensitive_session_keys(st.session_state)

# -------------------- Footer --------------------
st.markdown("""
<div class="footer">
    Resume ATS Optimizer<br>
    AI-powered resume optimization using LLM + ATS feedback loop<br>
    v0.8
</div>
""", unsafe_allow_html=True)