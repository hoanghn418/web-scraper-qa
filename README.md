# Web Scraper and Q&A Generator

This project scrapes documentation websites and generates Q&A pairs for RAG applications.

## Setup

1. Clone the repository
2. Create conda environment:
   ```bash
   conda env create -f environment.yml
   ```
3. Activate environment:
   ```bash
   conda activate web-scraper-qa
   ```
4. Copy .env.example to .env and update with your OpenAI API key
5. Start backend:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```
6. Start frontend:
   ```bash
   cd frontend
   streamlit run app.py
   ```
