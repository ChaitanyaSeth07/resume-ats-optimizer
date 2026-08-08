"""
Resume ATS Optimizer - Main Streamlit App
Current version: PDF → Structure → AI Optimization → Scoring
"""

import streamlit as st
from core.pdf_parser import extract_text_from_pdf, get_pdf_info
from core.structure_extractor import extract_structure
from core.llm_optimizer import optimize_resume
from core.scoring_engine import calculate_overall_score

# Page configuration
st.set_page_config(
    page_title="Resume ATS Optimizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("📄 Resume ATS Optimizer")
st.markdown("""
Upload your resume (PDF) and paste a job description.  
The tool will optimize your resume for ATS systems and the specific role.
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
    st.markdown("---")
    st.markdown("**Status:** Scoring Engine added")
    st.caption("v0.2 - Optimization + Scoring")

# Main inputs
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

if st.button("🚀 Start Optimization", type="primary", use_container_width=True):

    if uploaded_file is None:
        st.error("Please upload a PDF resume first.")
    elif not job_description.strip():
        st.warning("Please paste a job description.")
    else:
        # Step 1: Extract text
        with st.spinner("Step 1/4 — Extracting text from PDF..."):
            resume_text = extract_text_from_pdf(uploaded_file)
            pdf_info = get_pdf_info(uploaded_file)

        if resume_text is None:
            st.error("Could not extract text from the PDF.")
        else:
            st.success(f"Text extracted from {pdf_info['page_count']} page(s).")

            # Step 2: Structure
            with st.spinner("Step 2/4 — Organizing into sections..."):
                structured = extract_structure(resume_text)
            st.success("Structure extraction completed.")

            # Step 3: AI Optimization
            with st.spinner("Step 3/4 — AI is optimizing your resume..."):
                optimized_resume = optimize_resume(structured, job_description)

            if optimized_resume is None:
                st.error("AI optimization failed. Check your API key in .env")
            else:
                st.success("AI optimization completed!")

                # Step 4: Scoring
                with st.spinner("Step 4/4 — Scoring the optimized resume..."):
                    score_report = calculate_overall_score(optimized_resume, job_description)

                # === RESULTS ===
                st.subheader("Results")

                # Score cards
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Overall Score", f"{score_report['overall_score']}/100")
                c2.metric("Rating", score_report['rating'])
                c3.metric("Keyword Match", f"{score_report['keyword_score']}%")
                c4.metric("Structure Score", f"{score_report['structural_score']}%")

                # Missing keywords
                if score_report["missing_keywords"]:
                    with st.expander("Keywords missing from resume (consider adding)"):
                        st.write(", ".join(score_report["missing_keywords"]))

                # Optimized resume
                st.subheader("Optimized Resume")
                st.text_area("Improved Resume", value=optimized_resume, height=450)

                st.download_button(
                    label="Download Optimized Resume (TXT)",
                    data=optimized_resume,
                    file_name="optimized_resume.txt",
                    mime="text/plain"
                )

                st.info("Next: Feedback Loop + DOCX generation")

                # Save to session
                st.session_state["optimized_resume"] = optimized_resume
                st.session_state["score_report"] = score_report
                st.session_state["job_description"] = job_description
                st.session_state["output_format"] = output_format

st.markdown("---")
st.caption("Resume ATS Optimizer • v0.2 • Streamlit + Groq")