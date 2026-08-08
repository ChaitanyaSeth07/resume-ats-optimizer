"""
Resume ATS Optimizer - Main Streamlit App
Current version: Improved UI + DOCX + PDF download
"""

import streamlit as st
from core.pdf_parser import extract_text_from_pdf, get_pdf_info
from core.structure_extractor import extract_structure
from core.feedback_loop import run_feedback_loop
from core.docx_builder import create_ats_docx
from core.converter import convert_docx_to_pdf

# Page configuration
st.set_page_config(
    page_title="Resume ATS Optimizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        index=2
    )
    target_score = st.slider("Target Score", min_value=60, max_value=90, value=75)
    max_attempts = st.slider("Max Attempts", min_value=1, max_value=3, value=3)

    st.markdown("---")
    st.markdown("**Current Version:** `v0.6`")
    st.caption("UI + DOCX + PDF support")

# ==================== INPUT SECTION ====================
st.subheader("1. Upload & Job Description")

col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("Upload your current resume (PDF)", type=["pdf"])

with col2:
    job_description = st.text_area(
        "Paste the Job Description",
        height=180,
        placeholder="Paste the full job description here..."
    )

st.divider()

# ==================== PROCESS ====================
if st.button("🚀 Start Optimization", type="primary", use_container_width=True):

    if uploaded_file is None:
        st.error("Please upload a PDF resume first.")
    elif not job_description.strip():
        st.warning("Please paste a job description.")
    else:
        with st.status("Processing your resume...", expanded=True) as status:
            st.write("Extracting text from PDF...")
            resume_text = extract_text_from_pdf(uploaded_file)
            pdf_info = get_pdf_info(uploaded_file)

            if resume_text is None:
                st.error("Could not extract text from the PDF.")
                st.stop()

            st.write("Organizing content into sections...")
            structured = extract_structure(resume_text)

            st.write("Running AI Feedback Loop...")
            final_resume, score_report, attempts = run_feedback_loop(
                structured_resume=structured,
                job_description=job_description,
                max_attempts=max_attempts,
                target_score=float(target_score)
            )

            if final_resume is None:
                st.error("Optimization failed. Check your API key.")
                st.stop()

            st.write("Creating clean ATS-friendly DOCX...")
            docx_buffer = create_ats_docx(final_resume)

            pdf_buffer = None
            if output_format in ["PDF", "Both"]:
                st.write("Converting to PDF...")
                pdf_buffer = convert_docx_to_pdf(docx_buffer)

            status.update(label="Optimization Complete!", state="complete", expanded=False)

        # ==================== RESULTS ====================
        st.success(f"Optimization finished after **{attempts}** attempt(s)")

        st.subheader("Score Overview")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Overall Score", f"{score_report['overall_score']}/100")
        m2.metric("Rating", score_report['rating'])
        m3.metric("Keyword Match", f"{score_report['keyword_score']}%")
        m4.metric("Structure Score", f"{score_report['structural_score']}%")

        if score_report.get("missing_keywords"):
            with st.expander("Keywords still missing (optional)"):
                st.write(", ".join(score_report["missing_keywords"]))

        st.divider()

        # Side-by-side
        st.subheader("Original vs Optimized")
        left, right = st.columns(2)

        with left:
            st.markdown("#### Original Resume")
            st.text_area("Original", value=resume_text, height=420, disabled=True, label_visibility="collapsed")

        with right:
            st.markdown("#### Optimized Resume")
            st.text_area("Optimized", value=final_resume, height=420, label_visibility="collapsed")

        st.divider()

        # Downloads
        st.subheader("Download Optimized Resume")

        dl1, dl2, dl3 = st.columns(3)

        with dl1:
            st.download_button(
                label="Download DOCX",
                data=docx_buffer,
                file_name="optimized_resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

        with dl2:
            if pdf_buffer:
                st.download_button(
                    label="Download PDF",
                    data=pdf_buffer,
                    file_name="optimized_resume.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.button("PDF not available", disabled=True, use_container_width=True)
                st.caption("PDF conversion requires Microsoft Word or LibreOffice")

        with dl3:
            st.download_button(
                label="Download TXT",
                data=final_resume,
                file_name="optimized_resume.txt",
                mime="text/plain",
                use_container_width=True
            )

        st.session_state["final_resume"] = final_resume
        st.session_state["score_report"] = score_report

st.markdown("---")
st.caption("Resume ATS Optimizer • v0.6 • DOCX + PDF • Streamlit + Groq")