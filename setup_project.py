import os
import subprocess
from pathlib import Path

def create_directory_structure():
    """Create the project directory structure."""
    # Define the directory structure
    directories = [
        "backend/app",
        "backend/app/services",
        "backend/app/models",
        "backend/app/database",
        "backend/tests",
        "frontend",
        "frontend/components",
    ]

    # Create directories
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def create_files():
    """Create initial files with basic content."""
    files = {
        "backend/requirements.txt": """fastapi==0.104.1
uvicorn==0.24.0
beautifulsoup4==4.12.2
requests==2.31.0
sqlalchemy==2.0.23
markdown2==2.4.10
weasyprint==60.1
openai==1.3.5
python-dotenv==1.0.0
validators==0.22.0
ratelimit==2.2.1
""",
        "frontend/requirements.txt": """streamlit==1.28.2
requests==2.31.0
pandas==2.1.3
python-dotenv==1.0.0
""",
        "environment.yml": """name: web-scraper-qa
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.10
  - pip
  - pip:
    - -r backend/requirements.txt
    - -r frontend/requirements.txt
""",
        ".env.example": """OPENAI_API_KEY=your-api-key-here
""",
        "README.md": """# Web Scraper and Q&A Generator

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
""",
        "backend/app/__init__.py": "",
        "backend/app/main.py": """from fastapi import FastAPI

app = FastAPI(title="Web Scraper and Q&A Generator API")

@app.get("/")
async def root():
    return {"message": "Web Scraper and Q&A Generator API"}
""",
        "frontend/app.py": """import streamlit as st

st.title("Web Scraper and Q&A Generator")
st.write("Welcome to the Web Scraper and Q&A Generator!")
"""
    }

    for file_path, content in files.items():
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

def main():
    """Main function to set up the project."""
    print("Creating project structure...")
    create_directory_structure()
    
    print("Creating initial files...")
    create_files()
    
    print("\nProject structure created successfully!")
    print("\nNext steps:")
    print("1. Create conda environment: conda env create -f environment.yml")
    print("2. Activate environment: conda activate web-scraper-qa")
    print("3. Copy .env.example to .env and add your OpenAI API key")
    print("4. Start backend: cd backend && uvicorn app.main:app --reload")
    print("5. Start frontend: cd frontend && streamlit run app.py")

if __name__ == "__main__":
    main()
