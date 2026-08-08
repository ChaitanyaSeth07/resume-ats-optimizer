"""
Resume ATS Optimizer - Main Streamlit App
Current version: Improved UI (Side-by-side + Better Score Display)
"""

import streamlit as st
from core.pdf_parser import extract_text_from_pdf, get_pdf_info
from core.structure_extractor import extract_structure
from core.feedback_loop import run_feedback_loop
from core.docx_builder import create_ats_docx

# Page configuration
st.set_page_config(
    page_title="Resume ATS Optimizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better look
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }
    .sub-header {
        color: #666;
        margin-bottom: 1.5rem;
    }
    .score-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">📄 Resume ATS Optimizer</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Optimize your resume for ATS systems using AI + Feedback Loop</p>', unsafe_allow_html=True)

st.divider()

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    output_format = st.selectbox(
        "Preferred Output",
        options=["DOCX", "PDF", "Both"],
        index=0
    )
    target_score = st.slider("Target Score", min_value=60, max_value=90, value=75, help="The feedback loop will try to reach this score")
    max_attempts = st.slider("Max Attempts", min_value=1, max_value=3, value=3)

    st.markdown("---")
    st.markdown("**Current Version:** `v0.5`")
    st.caption("Improved UI + Side-by-side view")

# ==================== INPUT SECTION ====================
st.subheader("1. Upload & Job Description")

col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("Upload your current resume (PDF)", type=["pdf"])

with col2:
    job_description = st.text_area(
        "Paste the Job Description",
        height=180,
        placeholder="Paste the full job description here for targeted optimization..."
    )

st.divider()

# ==================== PROCESS BUTTON ====================
if st.button("🚀 Start Optimization", type="primary", use_container_width=True):

    if uploaded_file is None:
        st.error("Please upload a PDF resume first.")
    elif not job_description.strip():
        st.warning("Please paste a job description for better results.")
    else:
        # ---------- Step 1: Extract ----------
        with st.status("Processing your resume...", expanded=True) as status:
            st.write("Extracting text from PDF...")
            resume_text = extract_text_from_pdf(uploaded_file)
            pdf_info = get_pdf_info(uploaded_file)

            if resume_text is None:
                st.error("Could not extract text from the PDF.")
                st.stop()

            st.write("Organizing content into sections...")
            structured = extract_structure(resume_text)

            st.write("Running AI Feedback Loop (this may take 20–60 seconds)...")
            final_resume, score_report, attempts = run_feedback_loop(
                structured_resume=structured,
                job_description=job_description,
                max_attempts=max_attempts,
                target_score=float(target_score)
            )

            if final_resume is None:
                st.error("Optimization failed. Please check your API key in the .env file.")
                st.stop()

            st.write("Creating clean ATS-friendly DOCX...")
            docx_file = create_ats_docx(final_resume)

            status.update(label="Optimization Complete!", state="complete", expanded=False)

        # ==================== RESULTS ====================
        st.success(f"Optimization finished after **{attempts}** attempt(s)")

        # Score Overview
        st.subheader("Score Overview")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Overall Score", f"{score_report['overall_score']}/100", delta=None)
        m2.metric("Rating", score_report['rating'])
        m3.metric("Keyword Match", f"{score_report['keyword_score']}%")
        m4.metric("Structure Score", f"{score_report['structural_score']}%")

        # Missing keywords
        if score_report.get("missing_keywords"):
            with st.expander("Keywords that are still missing (optional to add)"):
                st.write(", ".join(score_report["missing_keywords"]))

        st.divider()

        # Side-by-side comparison
        st.subheader("Original vs Optimized")

        left, right = st.columns(2)

        with left:
            st.markdown("#### Original Resume (Extracted)")
            st.text_area(
                "Original",
                value=resume_text,
                height=450,
                disabled=True,
                label_visibility="collapsed"
            )

        with right:
            st.markdown("#### Optimized Resume")
            st.text_area(
                "Optimized",
                value=final_resume,
                height=450,
                label_visibility="collapsed"
            )

        st.divider()

        # Download section
        st.subheader("Download Your Optimized Resume")

        dl1, dl2, dl3 = st.columns([1, 1, 2])

        with dl1:
            st.download_button(
                label="Download DOCX",
                data=docx_file,
                file_name="optimized_resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

        with dl2:
            st.download_button(
                label="Download TXT",
                data=final_resume,
                file_name="optimized_resume.txt",
                mime="text/plain",
                use_container_width=True
            )

        # Store in session
        st.session_state["final_resume"] = final_resume
        st.session_state["score_report"] = score_report
        st.session_state["original_text"] = resume_text

st.markdown("---")
st.caption("Resume ATS Optimizer • v0.5 • Improved UI • Streamlit + Groq")