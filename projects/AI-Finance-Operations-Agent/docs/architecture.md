# Architecture

## Processing pipeline

1. User uploads an invoice PDF.
2. PyPDF extracts machine-readable text.
3. Gemini extracts structured invoice fields when the API is available.
4. A deterministic parser provides a fallback when Gemini is unavailable or quota-limited.
5. Pydantic validates the extracted schema.
6. Invoice arithmetic is checked.
7. Vendor + invoice number are checked for duplicates.
8. Historical vendor spending is used for a simple anomaly rule.
9. A risk level is assigned.
10. The result is persisted in `output/dashboard_data.csv`.
11. Streamlit presents KPIs, spending trends and risk findings.

## Risk logic

- High: invalid total or duplicate invoice.
- Medium: unusually high invoice compared with historical vendor average.
- Low: no validation, duplicate or anomaly flag.

This is a portfolio prototype; production deployment would normally use a database, stronger document/OCR extraction, authentication, audit logging and more robust statistical anomaly detection.
