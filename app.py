"""
Resume ATS Optimizer - Main Streamlit App
Current version: PDF Upload → Text Extraction → Structure Extraction → AI Optimization
"""

import streamlit as st
from core.pdf_parser import extract_text_from_pdf, get_pdf_info
from core.structure_extractor import extract_structure
from core.llm_optimizer import optimize_resume

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

# Sidebar for settings
with st.sidebar:
    st.header("Settings")
    output_format = st.selectbox(
        "Output Format",
        options=["DOCX", "PDF", "Both"],
        index=0,
        help="Choose the format for the optimized resume"
    )
    
    st.markdown("---")
    st.markdown("**Status:** AI Optimization ready")
    st.caption("PDF → Structure → LLM Optimization")

# Main content - two columns
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Upload Resume (PDF)")
    uploaded_file = st.file_uploader(
        "Choose a PDF resume",
        type=["pdf"],
        help="Upload your current resume in PDF format"
    )

with col2:
    st.subheader("2. Job Description")
    job_description = st.text_area(
        "Paste the job description here",
        height=200,
        placeholder="Paste the full job description for targeted optimization..."
    )

st.divider()

# Process button
if st.button("🚀 Start Optimization", type="primary", use_container_width=True):
    
    if uploaded_file is None:
        st.error("Please upload a PDF resume first.")
    elif not job_description.strip():
        st.warning("Please paste a job description for better results.")
    else:
        # Step 1: Extract text from PDF
        with st.spinner("Step 1/3 — Extracting text from PDF..."):
            resume_text = extract_text_from_pdf(uploaded_file)
            pdf_info = get_pdf_info(uploaded_file)
        
        if resume_text is None:
            st.error("Could not extract text from the PDF. Please try another file.")
        else:
            st.success(f"Text extracted successfully from {pdf_info['page_count']} page(s).")
            
            # Step 2: Extract structure
            with st.spinner("Step 2/3 — Organizing into sections..."):
                structured = extract_structure(resume_text)
            
            st.success("Structure extraction completed.")
            
            # Step 3: AI Optimization
            with st.spinner("Step 3/3 — AI is optimizing your resume (this may take 10–20 seconds)..."):
                optimized_resume = optimize_resume(structured, job_description)
            
            if optimized_resume is None:
                st.error("AI optimization failed. Please check your API key in the .env file.")
            else:
                st.success("AI optimization completed!")
                
                # Show results
                st.subheader("Optimized Resume")
                st.text_area(
                    "Improved Resume",
                    value=optimized_resume,
                    height=500
                )
                
                st.download_button(
                    label="Download Optimized Resume (TXT)",
                    data=optimized_resume,
                    file_name="optimized_resume.txt",
                    mime="text/plain"
                )
                
                st.info("Next steps coming soon: Scoring → Feedback Loop → Generate clean DOCX/PDF")
                
                # Store in session state
                st.session_state["resume_text"] = resume_text
                st.session_state["structured_resume"] = structured
                st.session_state["optimized_resume"] = optimized_resume
                st.session_state["job_description"] = job_description
                st.session_state["output_format"] = output_format

# Footer
st.markdown("---")
st.caption("Resume ATS Optimizer • Built with Streamlit + Groq • Practical Feedback-Loop Approach")