"""
Resume ATS Optimizer - Security Hardened Version
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from core.pdf_parser import extract_text_from_pdf, get_pdf_info
from core.structure_extractor import extract_structure
from core.feedback_loop import run_feedback_loop
from core.docx_builder import create_ats_docx
from core.converter import convert_docx_to_pdf
from core.evaluation_logger import log_evaluation, get_all_logs
from core.security import (
    validate_uploaded_file,
    basic_output_validation,
    clear_sensitive_session_keys
)

# Page configuration
st.set_page_config(
    page_title="Resume ATS Optimizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; margin-bottom: 0.3rem; }
    .sub-header { color: #666; margin-bottom: 1.5rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">📄 Resume ATS Optimizer</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Optimize your resume for ATS systems using AI + Feedback Loop</p>', unsafe_allow_html=True)

st.divider()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("⚙️ Settings")
    output_format = st.selectbox("Preferred Output", ["DOCX", "PDF", "Both"], index=2)
    target_score = st.slider("Target Score", 60, 90, 75)
    max_attempts = st.slider("Max Attempts", 1, 3, 3)

    st.markdown("---")
    st.markdown("**Version:** `v1.0-secure`")
    st.caption("Security measures active")

    st.markdown("---")
    st.subheader("Creator Access")
    creator_password = st.text_input("Enter creator password", type="password")
    show_dashboard = creator_password == "ats2026"

# ==================== CREATOR DASHBOARD ====================
if show_dashboard:
    st.header("Creator Evaluation Dashboard")
    st.caption("Only metrics are shown. No resume content is stored.")

    logs = get_all_logs()

    if not logs:
        st.warning("No evaluation data found yet.")
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
            sns.histplot(df["overall_score"].dropna(), bins=10, kde=True, ax=ax1)
            st.pyplot(fig1)

        with col_b:
            st.markdown("**Keyword vs Structure**")
            fig2, ax2 = plt.subplots(figsize=(6, 4))
            sns.scatterplot(data=df, x="keyword_score", y="structural_score", hue="rating", ax=ax2)
            st.pyplot(fig2)

        st.markdown("**Attempts Used**")
        fig3, ax3 = plt.subplots(figsize=(8, 3.5))
        sns.countplot(data=df, x="attempts_used", ax=ax3)
        st.pyplot(fig3)

        st.dataframe(df, use_container_width=True)

        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Metrics CSV", csv_data, "evaluation_metrics.csv", "text/csv")

    st.divider()
    st.info("Creator mode active.")

# ==================== NORMAL USER INTERFACE ====================
else:
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

    if st.button("🚀 Start Optimization", type="primary", use_container_width=True):

        # ---- Security: Validate file ----
        is_valid, error_msg = validate_uploaded_file(uploaded_file)
        if not is_valid:
            st.error(error_msg)
            st.stop()

        if not job_description.strip():
            st.warning("Please paste a job description.")
            st.stop()

        with st.status("Processing your resume...", expanded=True) as status:
            st.write("Extracting text from PDF...")
            resume_text = extract_text_from_pdf(uploaded_file)

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

            # ---- Security: Validate LLM output ----
            is_output_valid, output_error = basic_output_validation(final_resume)
            if not is_output_valid:
                st.error(f"Output validation failed: {output_error}")
                st.stop()

            st.write("Creating clean ATS-friendly DOCX...")
            docx_buffer = create_ats_docx(final_resume)

            pdf_buffer = None
            if output_format in ["PDF", "Both"]:
                st.write("Converting to PDF...")
                pdf_buffer = convert_docx_to_pdf(docx_buffer)

            # Log only metrics (no resume content)
            log_evaluation(
                score_report=score_report,
                attempts_used=attempts,
                target_score=float(target_score),
                original_text_length=len(resume_text),
                job_description_length=len(job_description)
            )

            status.update(label="Optimization Complete!", state="complete", expanded=False)

        st.success(f"Optimization finished after **{attempts}** attempt(s)")

        st.subheader("Score Overview")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Overall Score", f"{score_report['overall_score']}/100")
        m2.metric("Rating", score_report['rating'])
        m3.metric("Keyword Match", f"{score_report['keyword_score']}%")
        m4.metric("Structure Score", f"{score_report['structural_score']}%")

        if score_report.get("missing_keywords"):
            with st.expander("Keywords still missing"):
                st.write(", ".join(score_report["missing_keywords"]))

        st.divider()
        st.subheader("Original vs Optimized")
        left, right = st.columns(2)

        with left:
            st.markdown("#### Original Resume")
            st.text_area("Original", value=resume_text, height=420, disabled=True, label_visibility="collapsed")

        with right:
            st.markdown("#### Optimized Resume")
            st.text_area("Optimized", value=final_resume, height=420, label_visibility="collapsed")

        st.divider()
        st.subheader("Download Optimized Resume")

        dl1, dl2, dl3 = st.columns(3)

        with dl1:
            st.download_button(
                "Download DOCX",
                data=docx_buffer,
                file_name="optimized_resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

        with dl2:
            if pdf_buffer:
                st.download_button(
                    "Download PDF",
                    data=pdf_buffer,
                    file_name="optimized_resume.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.button("PDF not available", disabled=True, use_container_width=True)

        with dl3:
            st.download_button(
                "Download TXT",
                data=final_resume,
                file_name="optimized_resume.txt",
                mime="text/plain",
                use_container_width=True
            )

        # ---- Security: Clear sensitive data from session ----
        clear_sensitive_session_keys(st.session_state)

st.markdown("---")
st.caption("Resume ATS Optimizer • v1.0-secure • Security measures active")