# LinkedIn launch post

I’m excited to share a new portfolio project I built: **AI Finance Operations Agent** 🚀

The project explores how AI and data automation can be combined to streamline invoice operations.

**What it does:**
- Extracts structured fields from invoice PDFs
- Uses Gemini for AI-assisted extraction
- Falls back to deterministic parsing when AI is unavailable or quota-limited
- Validates invoice totals
- Detects potential duplicate invoices
- Flags unusual vendor spending
- Assigns invoice risk levels
- Stores processed results for analysis
- Presents finance KPIs and trends through a Streamlit dashboard

**Tech stack:** Python, Streamlit, Pandas, Pydantic, PyPDF and Google Gemini.

One of the main design goals was not to rely blindly on an LLM: the extracted data is independently validated and checked against business rules and historical vendor data.

GitHub: https://github.com/akkisakpal/AkshaySakpal/tree/main/projects/AI-Finance-Operations-Agent

#Python #AI #DataAnalytics #MachineLearning #GenAI #Streamlit #DataEngineering #FinanceAutomation #GitHub
