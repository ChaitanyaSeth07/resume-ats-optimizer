# Research Paper Outline

**Working Title:**  
An AI-Powered Feedback-Loop System for ATS-Optimized Resume Generation with Privacy-Aware Design

---

## 1. Abstract
- Problem: Many resumes fail Applicant Tracking Systems (ATS) due to poor structure, weak keyword alignment, and non-parseable formatting.
- Solution: A practical automated system that combines PDF parsing, structure extraction, LLM-based optimization, a scoring engine, and an iterative feedback loop.
- Additional focus: Privacy-aware design that avoids storing resume content and implements multiple security controls.
- Contribution: An end-to-end open system with measurable improvement metrics and a creator evaluation dashboard.
- Results: (To be filled after data collection)

---

## 2. Introduction
- Growing reliance on ATS in recruitment
- Common failure points of resumes in ATS
- Limitations of existing tools (manual ChatGPT usage, commercial scanners, lack of iterative refinement)
- Research goal: Design, implement, and evaluate a feedback-driven resume optimization system that is both effective and privacy-conscious

---

## 3. Related Work
- How modern ATS systems parse and rank resumes
- Commercial tools (Jobscan, Resume Worded, etc.)
- LLM applications in career documents
- Iterative refinement / feedback-loop methods in NLP
- Privacy concerns when sending personal documents to external AI APIs
- Research gap addressed by this work

---

## 4. System Architecture

### 4.1 Pipeline Overview
1. Secure PDF Upload & Validation
2. Text Extraction
3. Structure Extraction (sections + contact)
4. LLM Optimization (truthfulness-constrained)
5. Scoring Engine (keyword + structural)
6. Feedback Loop (generate → score → improve)
7. Clean ATS-friendly DOCX / PDF Generation
8. Metrics Logging (results only, no resume content)

### 4.2 Design Principles
- Based on real ATS behavior (standard headings, clean linear structure, keyword relevance)
- Truthfulness constraint (no invented experience or metrics)
- Privacy-by-design (no permanent storage of resume or job description content)
- Practical feedback loop instead of closed commercial ATS APIs

### 4.3 Technology Stack
- Frontend/Backend: Streamlit
- PDF Parsing: pdfplumber
- Document Generation: python-docx
- LLM: Groq (Llama 3.3 70B) via OpenAI-compatible API
- Scoring & Analysis: Custom engine + pandas + seaborn
- Security utilities: Custom validation and cleanup modules

---

## 5. Methodology

### 5.1 Resume Parsing and Structuring
### 5.2 Prompt Engineering for Optimization
- Strong instructions against hallucination
- Structured output format
- Job-description targeting

### 5.3 Scoring Metrics
- Keyword Match Score
- Structural Compliance Score
- Weighted Overall Score
- Rating categories

### 5.4 Feedback Loop
- Threshold-based regeneration
- Maximum attempt limit
- Injection of specific weaknesses into subsequent prompts

### 5.5 Privacy and Security Measures
- API key management via environment variables and Streamlit secrets
- File type and size validation
- Temporary file cleanup
- No storage of full resume or job description text
- Basic LLM output validation
- Session state cleanup of sensitive data
- Creator-only evaluation dashboard (password protected)

---

## 6. Experimental Setup
- Number of resume–job description pairs tested
- Hardware / software environment
- Evaluation metrics collected automatically:
  - Overall Score
  - Keyword Score
  - Structural Score
  - Attempts used
  - Target reached (Yes/No)
- Analysis tools: pandas, seaborn, matplotlib, Tableau (optional)

---

## 7. Results
(To be completed after systematic evaluation)

- Descriptive statistics of score improvements
- Distribution of overall scores
- Relationship between keyword match and structural score
- Number of feedback iterations required
- Qualitative examples (original vs optimized)
- Visualizations

---

## 8. Discussion
- Effectiveness of the feedback loop compared to single-pass optimization
- Strengths of the privacy-aware design
- Remaining limitations (dependence on external LLM, PDF conversion constraints, evaluation scale)
- Practical usefulness for job seekers

---

## 9. Limitations and Future Work
- External LLM dependency and potential hallucination residual risk
- Limited dataset size in current evaluation
- PDF conversion reliability across platforms
- Possible future integration with stronger ATS simulators
- Potential for local / on-device models for higher privacy
- Larger-scale user study

---

## 10. Conclusion
- Summary of the system and its contributions
- Demonstration that a practical feedback-loop approach can improve ATS-oriented resume quality
- Importance of combining performance with privacy-aware engineering
- Directions for future research

---

## References
(To be added)

---

## Appendix
- Full prompt templates
- Scoring algorithm details
- Security control summary
- Sample (anonymized) metric logs
- System architecture diagram