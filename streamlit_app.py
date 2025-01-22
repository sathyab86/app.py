# app.py

import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin
import pdfplumber
import io
from typing import Dict, List, Optional

class DocumentAnalyzer:
    def __init__(self):
        self.quality_indicators = {
            'certifications': [
                'ISO 9001', 'ISO 13485', 'AS9100', 'IATF 16949', 'API Q1',
                'ISO 17025', 'GMP', 'HACCP', 'Six Sigma'
            ],
            'quality_terms': [
                'quality management', 'quality control', 'quality assurance',
                'QMS', 'quality policy', 'continuous improvement'
            ],
            'process_terms': [
                'SPC', 'statistical process control', 'FMEA', 'process control',
                'quality metrics', 'process validation'
            ],
            'tools_terms': [
                'quality tools', 'measurement system', 'calibration', 
                'inspection', 'testing equipment'
            ],
            'management_terms': [
                'management review', 'quality objectives', 'quality manual',
                'quality records', 'document control'
            ]
        }

    def analyze_pdf(self, pdf_file) -> dict:
        """Analyze PDF content for quality-related information"""
        try:
            text_content = ""
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    text_content += page.extract_text().lower()

            return self._analyze_text_content(text_content)

        except Exception as e:
            return {
                'error': str(e),
                'certifications_found': [],
                'quality_mentions': 0,
                'process_mentions': 0,
                'tools_mentions': 0,
                'suggested_scores': {}
            }

    def analyze_website(self, url: str) -> dict:
        """Analyze website content for quality-related information"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            text_content = soup.get_text().lower()
            results = self._analyze_text_content(text_content)
            
            # Additional web-specific analysis
            results['quality_pages'] = []
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and any(term in href.lower() for term in ['quality', 'certification', 'compliance']):
                    full_url = urljoin(url, href)
                    results['quality_pages'].append(full_url)
            
            return results

        except Exception as e:
            return {
                'error': str(e),
                'certifications_found': [],
                'quality_mentions': 0,
                'process_mentions': 0,
                'tools_mentions': 0,
                'quality_pages': [],
                'suggested_scores': {}
            }

    def _analyze_text_content(self, text_content: str) -> dict:
        """Analyze text content for quality-related information"""
        results = {
            'certifications_found': [],
            'quality_mentions': 0,
            'process_mentions': 0,
            'tools_mentions': 0,
            'management_mentions': 0,
            'suggested_scores': {}
        }

        # Find certifications
        for cert in self.quality_indicators['certifications']:
            if cert.lower() in text_content:
                results['certifications_found'].append(cert)

        # Count various mentions
        for term in self.quality_indicators['quality_terms']:
            results['quality_mentions'] += len(re.findall(r'\b' + re.escape(term.lower()) + r'\b', text_content))
        
        for term in self.quality_indicators['process_terms']:
            results['process_mentions'] += len(re.findall(r'\b' + re.escape(term.lower()) + r'\b', text_content))
        
        for term in self.quality_indicators['tools_terms']:
            results['tools_mentions'] += len(re.findall(r'\b' + re.escape(term.lower()) + r'\b', text_content))
        
        for term in self.quality_indicators['management_terms']:
            results['management_mentions'] += len(re.findall(r'\b' + re.escape(term.lower()) + r'\b', text_content))

        # Calculate suggested scores
        results['suggested_scores'] = self._calculate_suggested_scores(results)
        
        return results

    def _calculate_suggested_scores(self, results: dict) -> dict:
        """Calculate suggested scores based on analyzed data"""
        scores = {}
        
        # QMS Score
        qms_score = min(
            (len(results['certifications_found']) * 2) +  # 2 points per certification
            (results['quality_mentions'] // 5) +          # 1 point per 5 quality mentions
            (results['management_mentions'] // 3),        # 1 point per 3 management mentions
            10  # Max score of 10
        )
        scores['QMS'] = max(1, qms_score)  # Minimum score of 1
        
        # Process Control Score
        process_score = min(
            (results['process_mentions'] // 3) +          # 1 point per 3 process mentions
            (results.get('quality_pages', []).__len__() // 2),  # 1 point per 2 quality pages
            10
        )
        scores['ProcessControl'] = max(1, process_score)
        
        # Tools Score
        tools_score = min(
            (results['tools_mentions'] // 2) +            # 1 point per 2 tools mentions
            (len(results['certifications_found'])),       # 1 point per certification
            10
        )
        scores['SPC'] = max(1, tools_score)
        
        return scores

class QualityCapability:
    def __init__(self, name: str, category: str, scoring_criteria: dict):
        self.name = name
        self.category = category
        self.scoring_criteria = scoring_criteria

class QualityCapabilityManager:
    def __init__(self):
        self.capabilities = {}
        self._initialize_base_capabilities()
    
    def _initialize_base_capabilities(self):
        # Initialize with basic capabilities...
        base_capabilities = {
            "QMS": {
                "name": "Quality Management System",
                "category": "System",
                "criteria": {
                    "1": "No formal QMS",
                    "3": "Basic quality procedures",
                    "5": "ISO 9001 implementation in progress",
                    "7": "ISO 9001 certified",
                    "10": "Advanced integrated QMS with multiple certifications"
                }
            },
            # Add more capabilities here...
        }
        
        for cap_id, cap_info in base_capabilities.items():
            self.add_capability(
                cap_id,
                cap_info["name"],
                cap_info["category"],
                cap_info["criteria"]
            )

    # ... (rest of QualityCapabilityManager methods)

def create_data_collection_ui(capability_manager):
    st.header("Quality Data Collection")
    
    # Create tabs for different collection methods
    tabs = st.tabs(["Manual Entry", "Website Analysis", "Document Analysis"])
    
    # Document Analysis Tab
    with tabs[2]:
        st.subheader("Document Analysis")
        
        uploaded_file = st.file_uploader("Upload Quality Document", type=['pdf'])
        
        if uploaded_file:
            with st.spinner("Analyzing document..."):
                try:
                    analyzer = DocumentAnalyzer()
                    results = analyzer.analyze_pdf(uploaded_file)
                    
                    if 'error' in results:
                        st.error(f"Error analyzing document: {results['error']}")
                    else:
                        display_analysis_results(results)
                except Exception as e:
                    st.error(f"Error processing document: {str(e)}")
    
    # Website Analysis Tab
    with tabs[1]:
        st.subheader("Website Analysis")
        
        company_url = st.text_input("Company Website URL")
        
        if st.button("Analyze Website"):
            if company_url:
                with st.spinner("Analyzing website..."):
                    analyzer = DocumentAnalyzer()
                    results = analyzer.analyze_website(company_url)
                    
                    if 'error' in results:
                        st.error(f"Error analyzing website: {results['error']}")
                    else:
                        display_analysis_results(results)
            else:
                st.warning("Please enter a website URL")
    
    # Manual Entry Tab
    with tabs[0]:
        st.subheader("Manual Assessment")
        # ... (existing manual entry code)

def display_analysis_results(results: dict):
    """Display analysis results in a structured format"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Found Certifications")
        if results['certifications_found']:
            for cert in results['certifications_found']:
                st.write(f"✓ {cert}")
        else:
            st.write("No certifications found")
        
        st.write("### Quality Metrics")
        metrics = {
            "Quality References": results['quality_mentions'],
            "Process References": results['process_mentions'],
            "Tools References": results['tools_mentions'],
            "Management References": results.get('management_mentions', 0)
        }
        for metric, value in metrics.items():
            st.metric(metric, value)
    
    with col2:
        st.write("### Suggested Capability Scores")
        for capability, score in results['suggested_scores'].items():
            st.metric(capability, f"{score}/10")
        
        if 'quality_pages' in results and results['quality_pages']:
            st.write("### Quality-Related Pages")
            for page in results['quality_pages'][:5]:
                st.write(f"- {page}")
    
    # Option to use suggested scores
    if st.button("Use These Scores for Assessment"):
        st.session_state.update(results['suggested_scores'])
        st.success("Scores updated! Switch to Manual Assessment tab to review and adjust.")

def main():
    st.set_page_config(layout="wide", page_title="Quality Management System")
    
    if 'capability_manager' not in st.session_state:
        st.session_state.capability_manager = QualityCapabilityManager()
    
    st.title("Quality Management System")
    
    tabs = st.tabs([
        "Data Collection",
        "Analysis",
        "Capability Management"
    ])
    
    with tabs[0]:
        create_data_collection_ui(st.session_state.capability_manager)
    
    with tabs[1]:
        create_analysis_ui(st.session_state.capability_manager)
    
    with tabs[2]:
        create_capability_management_ui(st.session_state.capability_manager)

if __name__ == "__main__":
    main()
