# AI Finance Operations Agent

AI-assisted invoice processing and finance analytics portfolio project.

Workflow: Invoice PDF -> text extraction -> Gemini AI or fallback extraction -> validation -> duplicate detection -> vendor anomaly detection -> risk classification -> persistent CSV -> Streamlit dashboard.

Features:
- PDF invoice extraction
- Gemini 3.6 Flash extraction
- Automatic fallback when Gemini is unavailable or quota-limited
- Invoice validation
- Duplicate detection
- Vendor spending anomaly detection
- Risk classification
- Streamlit dashboard and filters
- Upload and process new invoices

Tech stack: Python, Streamlit, Pandas, Pydantic, PyPDF and Google Gemini.

Run locally:

    pip install -r requirements.txt
    streamlit run dashboard/app.py

Set GEMINI_API_KEY as an environment variable. Never commit API keys.

Author: Akshay Sakpal
