# frontend/app.py
from typing import List, Dict, Optional  
import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import time
from pathlib import Path
import base64
import plotly.express as px
from PIL import Image
import os
import validators
import logging

logger = logging.getLogger(__name__)


# Set page configuration
st.set_page_config(
    page_title="Web Scraper & Q&A Generator 🤖",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for light blue theme and enhanced UI
st.markdown("""
    <style>
        /* Main background */
        .stApp {
            background-color: #f0f8ff;
        }
        
        /* Sidebar */
        .css-1d391kg {
            background-color: #e1f1ff;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: #1e88e5;
        }
        
        /* Cards */
        .stCard {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        /* Buttons */
        .stButton>button {
            background-color: #1e88e5;
            color: white;
            border-radius: 5px;
            border: none;
            padding: 10px 20px;
        }
        
        .stButton>button:hover {
            background-color: #1565c0;
        }
        
        /* Progress bar */
        .stProgress > div > div > div > div {
            background-color: #1e88e5;
        }
    </style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

class APIClient:
    """Client for interacting with the backend API."""
    
    @staticmethod
    def scrape_url(url: str, config: dict) -> dict:
        try:
            response = requests.post(
                f"{API_BASE_URL}/scrape/",
                json={"url": url, "config": config}
            )
            # Add debug prints
            print(f"Status Code: {response.status_code}")
            print(f"Response Text: {response.text}")
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API Error: {response.status_code} - {response.text}")
        except Exception as e:
            raise Exception(f"Error in scrape_url: {str(e)}")
    
    # frontend/app.py
    @staticmethod
    def generate_qa(job_id: int, num_pairs: int, min_confidence: float) -> dict:
        response = requests.post(
            f"{API_BASE_URL}/qa/generate/{job_id}",
            params={
                "num_pairs": num_pairs,
                "min_confidence": min_confidence
            }
        )
        if response.status_code == 200:
            return response.json()
        raise Exception(f"Error generating QA: {response.text}")

    @staticmethod
    def convert_documents(job_id: int, formats: List[str]) -> dict:
        response = requests.post(
            f"{API_BASE_URL}/documents/convert/{job_id}",
            json=formats  # Send the list directly as the request body
        )
        if response.status_code == 200:
            return response.json()
        raise Exception(f"Error converting documents: {response.text}")

    @staticmethod
    def get_job_history() -> list:
        try:
            response = requests.get(f"{API_BASE_URL}/jobs/")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error getting job history: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Exception in get_job_history: {str(e)}")
            return []

def show_header():
    """Display the application header."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🌐 Web Scraper & Q&A Generator")
        st.markdown("#### 🚀 Turn any documentation into a powerful Q&A knowledge base!")
    
    with col2:
        st.image("gemini.jpeg", width=150)  # Add your logo image

def show_url_input():
    """Display URL input section."""
    st.markdown("### 🔗 Enter Website URL")
    with st.container():
        url = st.text_input(
            "Website URL",
            placeholder="https://fastapi.tiangolo.com/",
            key="url_input"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            max_pages = st.slider("📚 Maximum Pages", 1, 100, 10)
            respect_robots = st.checkbox("🤖 Respect robots.txt", value=True)
        
        with col2:
            multi_page = st.checkbox("📑 Scrape Multiple Pages", value=True)
            rate_limit = st.slider("⏱️ Rate Limit (requests/second)", 1, 5, 1)
        
        config = {
            "max_pages": max_pages,
            "rate_limit": rate_limit,
            "respect_robots_txt": respect_robots,
            "scrape_multiple_pages": multi_page
        }
        
        return url, config

def show_conversion_options():
    """Display document conversion options."""
    st.markdown("### 📄 Document Generation")
    col1, col2 = st.columns(2)
    
    with col1:
        generate_markdown = st.checkbox("📝 Generate Markdown", value=True)
        generate_pdf = st.checkbox("📰 Generate PDF", value=True)
    
    with col2:
        num_qa_pairs = st.select_slider(
            "🔢 Number of Q&A Pairs",
            options=[10, 25, 50, 100],
            value=25
        )
        min_confidence = st.slider(
            "🎯 Minimum Confidence Score",
            0.0, 1.0, 0.7,
            step=0.1
        )
    
    return generate_markdown, generate_pdf, num_qa_pairs, min_confidence

def show_progress(job_id: int):
    """Display progress indicators."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    stages = [
        ("Scraping website...", 0.3),
        ("Generating Q&A pairs...", 0.6),
        ("Converting documents...", 0.9),
        ("Finishing up...", 1.0)
    ]
    
    for text, progress in stages:
        status_text.text(text)
        progress_bar.progress(progress)
        time.sleep(1)  # Simulate processing time
    
    status_text.success("✨ Processing completed!")

def show_results(job_id: int, qa_pairs: list):
    """Display processing results."""
    st.markdown("### 📊 Results")
    
    tabs = st.tabs(["Q&A Pairs 💭", "Statistics 📈", "Downloads ⬇️"])
    
    with tabs[0]:
        df = pd.DataFrame(qa_pairs)
        st.dataframe(
            df[["question", "answer", "confidence_score", "category"]],
            hide_index=True,
            use_container_width=True
        )
    
    with tabs[1]:
        col1, col2 = st.columns(2)
        
        with col1:
            # Confidence score distribution
            fig1 = px.histogram(
                df,
                x="confidence_score",
                title="Confidence Score Distribution",
                color_discrete_sequence=['#1e88e5']
            )
            st.plotly_chart(fig1)
        
        with col2:
            # Category distribution
            category_counts = df["category"].value_counts()
            fig2 = px.pie(
                values=category_counts.values,
                names=category_counts.index,
                title="Question Categories"
            )
            st.plotly_chart(fig2)
    
    with tabs[2]:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                "📝 Download Markdown",
                "markdown_content",
                file_name=f"document_{job_id}.md",
                mime="text/markdown"
            )
        
        with col2:
            st.download_button(
                "📰 Download PDF",
                "pdf_content",
                file_name=f"document_{job_id}.pdf",
                mime="application/pdf"
            )
        
        with col3:
            st.download_button(
                "📊 Download Q&A (CSV)",
                df.to_csv(index=False),
                file_name=f"qa_pairs_{job_id}.csv",
                mime="text/csv"
            )

def show_history():
    """Display job history in sidebar."""
    with st.sidebar:
        st.markdown("### 📜 Recent Jobs")
        try:
            jobs = APIClient.get_job_history()
            
            # Add some debug logging
            if jobs:
                for job in jobs:
                    # Check if job is a dictionary and has required keys
                    if isinstance(job, dict) and 'url' in job and 'status' in job and 'timestamp' in job:
                        with st.expander(f"🔍 {job['url'][:30]}..."):
                            st.write(f"Status: {job['status']}")
                            st.write(f"Date: {job['timestamp']}")
                            if st.button("Load Results", key=f"load_{job['id']}"):
                                return job['id']
                    else:
                        st.warning("Invalid job data format")
            else:
                st.info("No jobs found")
                
        except Exception as e:
            st.error(f"Error loading job history: {str(e)}")
            logger.error(f"Error in show_history: {str(e)}")
    
    return None

def main():
    """Main application function."""
    show_header()
    selected_job_id = show_history()
    
    if selected_job_id:
        st.info("Loading existing job results...")
        show_results(selected_job_id, [])
    else:
        url, config = show_url_input()
        generate_markdown, generate_pdf, num_qa_pairs, min_confidence = show_conversion_options()
        
        if st.button("🚀 Start Processing"):
            if not validators.url(url):
                st.error("❌ Please enter a valid URL")
                return
            
            try:
                with st.spinner("📡 Processing website..."):
                    # Add debug output
                    st.info(f"Sending request to API...")
                    response = APIClient.scrape_url(url, config)
                    
                    # Debug: Show raw response
                    st.write("API Response:", response)
                    
                    if isinstance(response, dict):
                        if 'job_id' in response:
                            job_id = response['job_id']
                        else:
                            st.error("Response doesn't contain job_id. Response keys: " + str(response.keys()))
                            return
                    else:
                        st.error(f"Unexpected response type: {type(response)}")
                        return
                    
                    show_progress(job_id)
                    
                    # Generate Q&A pairs
                    qa_response = APIClient.generate_qa(
                        job_id, num_qa_pairs, min_confidence
                    )
                    
                    # Convert documents
                    formats = []
                    if generate_markdown:
                        formats.append("markdown")
                    if generate_pdf:
                        formats.append("pdf")
                    
                    if formats:
                        try:
                            APIClient.convert_documents(job_id, formats)
                        except Exception as e:
                            st.error(f"Error converting documents: {str(e)}")
                    
                    # Show results
                    show_results(job_id, qa_response.get('qa_pairs', []))
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("Please check if the backend server is running at " + API_BASE_URL)
                # Add debug info
                st.write("Config being sent:", config)

if __name__ == "__main__":
    main()
