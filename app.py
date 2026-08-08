"""
Resume ATS Optimizer - Main Streamlit App
Current version: Full Feedback Loop (Generate → Score → Improve)
"""

import streamlit as st
from core.pdf_parser import extract_text_from_pdf, get_pdf_info
from core.structure_extractor import extract_structure
from core.feedback_loop import run_feedback_loop

# Page configuration
st.set_page_config(
    page_title="Resume ATS Optimizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📄 Resume ATS Optimizer")
st.markdown("""
Upload your resume (PDF) and paste a job description.  
The tool will optimize your resume using a practical feedback loop for better ATS performance.
""")

st.divider()

# Sidebar
with st.sidebar:
    st.header("Settings")
    output_format = st.selectbox(
        "Output Format",
        options=["DOCX", "PDF", "Both"],
        index=0
    )
    target_score = st.slider("Target Score", min_value=60, max_value=90, value=75)
    max_attempts = st.slider("Max Improvement Attempts", min_value=1, max_value=3, value=3)

    st.markdown("---")
    st.markdown("**Status:** Feedback Loop Active")
    st.caption("v0.3 - Generate → Score → Improve")

# Inputs
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Upload Resume (PDF)")
    uploaded_file = st.file_uploader("Choose a PDF resume", type=["pdf"])

with col2:
    st.subheader("2. Job Description")
    job_description = st.text_area(
        "Paste the job description here",
        height=200,
        placeholder="Paste the full job description..."
    )

st.divider()

if st.button("🚀 Start Optimization with Feedback Loop", type="primary", use_container_width=True):

    if uploaded_file is None:
        st.error("Please upload a PDF resume first.")
    elif not job_description.strip():
        st.warning("Please paste a job description.")
    else:
        # Step 1: Extract text
        with st.spinner("Step 1/3 — Extracting text from PDF..."):
            resume_text = extract_text_from_pdf(uploaded_file)
            pdf_info = get_pdf_info(uploaded_file)

        if resume_text is None:
            st.error("Could not extract text from the PDF.")
        else:
            st.success(f"Text extracted from {pdf_info['page_count']} page(s).")

            # Step 2: Structure
            with st.spinner("Step 2/3 — Organizing into sections..."):
                structured = extract_structure(resume_text)
            st.success("Structure extraction completed.")

            # Step 3: Feedback Loop
            with st.spinner("Step 3/3 — Running AI Feedback Loop (this may take 20–60 seconds)..."):
                final_resume, score_report, attempts = run_feedback_loop(
                    structured_resume=structured,
                    job_description=job_description,
                    max_attempts=max_attempts,
                    target_score=float(target_score)
                )

            if final_resume is None:
                st.error("Optimization failed. Please check your API key.")
            else:
                st.success(f"Feedback loop completed after {attempts} attempt(s)!")

                # === RESULTS ===
                st.subheader("Final Results")

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Overall Score", f"{score_report['overall_score']}/100")
                c2.metric("Rating", score_report['rating'])
                c3.metric("Keyword Match", f"{score_report['keyword_score']}%")
                c4.metric("Attempts Used", attempts)

                if score_report.get("missing_keywords"):
                    with st.expander("Still missing some keywords"):
                        st.write(", ".join(score_report["missing_keywords"]))

                st.subheader("Final Optimized Resume")
                st.text_area("Improved Resume", value=final_resume, height=450)

                st.download_button(
                    label="Download Optimized Resume (TXT)",
                    data=final_resume,
                    file_name="optimized_resume.txt",
                    mime="text/plain"
                )

                st.info("Next major step: Generate clean ATS-friendly DOCX file")

                # Save to session
                st.session_state["final_resume"] = final_resume
                st.session_state["score_report"] = score_report
                st.session_state["output_format"] = output_format

st.markdown("---")
st.caption("Resume ATS Optimizer • v0.3 • Feedback Loop Active • Streamlit + Groq")