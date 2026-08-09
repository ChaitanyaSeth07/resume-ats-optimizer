# Research Paper Outline  
**Title (Working):**  
An AI-Powered Feedback-Loop Approach for ATS-Optimized Resume Generation

---

## 1. Abstract
- Brief summary of the problem (resumes failing ATS)
- Proposed solution (automated system with LLM + feedback loop)
- Key results (to be filled later with real metrics)
- Main contribution

---

## 2. Introduction
- Importance of ATS in modern recruitment
- Common problems with existing resumes (poor parsing, keyword mismatch, weak structure)
- Limitations of current tools (Jobscan, Resume Worded, manual ChatGPT use)
- Goal of this research: Build and evaluate a practical, automated, feedback-driven resume optimization system

---

## 3. Related Work
- Traditional ATS systems and how they parse resumes
- Existing resume optimization tools
- Use of Large Language Models for resume writing
- Feedback-loop / iterative refinement approaches in NLP
- Gap that this work addresses

---

## 4. System Architecture
### 4.1 Overall Pipeline
1. PDF Text Extraction
2. Structure Extraction
3. LLM-based Optimization
4. Scoring Engine
5. Feedback Loop (iterative improvement)
6. Clean DOCX / PDF Generation

### 4.2 Design Principles
- Based on real ATS behavior (clean structure, standard headings, keyword alignment)
- Truthfulness constraint (no hallucinated experience)
- Practical feedback loop instead of real commercial ATS APIs

### 4.3 Tech Stack
- Streamlit
- pdfplumber
- python-docx
- Groq (Llama 3.3 70B)
- Custom scoring engine

---

## 5. Methodology
### 5.1 Resume Parsing & Structuring
### 5.2 Prompt Design for Optimization
### 5.3 Scoring Metrics
- Keyword Match Score
- Structural Compliance Score
- Overall Weighted Score
### 5.4 Feedback Loop Mechanism
- Threshold-based regeneration
- Maximum attempts
- Feedback injected into the next prompt

---

## 6. Experimental Setup
- Dataset: Number of resumes + job descriptions tested
- Evaluation metrics:
  - Before vs After Overall Score
  - Keyword Match improvement
  - Structural Score improvement
  - Number of feedback iterations needed
- Tools used for analysis: Python, pandas, Seaborn, Matplotlib, Tableau

---

## 7. Results
(To be filled with real data later)

- Score improvement statistics
- Distribution of improvements
- Example qualitative comparisons
- Visualizations (Seaborn + Tableau)

---

## 8. Discussion
- What worked well
- Limitations of the current system
- Comparison with purely manual or single-pass LLM optimization
- Practical usefulness

---

## 9. Limitations & Future Work
- Dependence on external LLM quality
- PDF conversion limitations on some systems
- Need for larger-scale evaluation
- Possible integration with real ATS simulators
- Fine-tuning possibilities

---

## 10. Conclusion
- Summary of contributions
- Practical impact
- Future direction

---

## References
(To be added later)

---

## Appendix
- Example original vs optimized resumes
- Full prompt templates
- Scoring algorithm details 