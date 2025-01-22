# streamlit_app.py

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

# Set page config at the very top
st.set_page_config(layout="wide", page_title="Quality Management System")

# Base Classes
class QualityCapability:
    def __init__(self, name: str, category: str, scoring_criteria: dict):
        self.name = name
        self.category = category
        self.scoring_criteria = scoring_criteria

class QualityCapabilityManager:
    def __init__(self):
        self.capabilities = {}
        self._initialize_base_capabilities()
    
    def add_capability(self, id: str, name: str, category: str, scoring_criteria: dict):
        self.capabilities[id] = QualityCapability(name, category, scoring_criteria)
    
    def remove_capability(self, id: str):
        if id in self.capabilities:
            del self.capabilities[id]
    
    def edit_capability(self, id: str, name: str = None, category: str = None, scoring_criteria: dict = None):
        if id in self.capabilities:
            cap = self.capabilities[id]
            if name:
                cap.name = name
            if category:
                cap.category = category
            if scoring_criteria:
                cap.scoring_criteria = scoring_criteria
    
    def get_capabilities_by_category(self, category: str) -> dict:
        return {id: cap for id, cap in self.capabilities.items() if cap.category == category}
    
    def get_all_categories(self) -> list:
        return list(set(cap.category for cap in self.capabilities.values()))
    
    def _initialize_base_capabilities(self):
        base_capabilities = {
            "QMS": {
                "name": "Quality Management System",
                "category": "System",
                "criteria": {
                    "1": "No formal QMS",
                    "3": "Basic quality procedures",
                    "5": "ISO 9001 implementation in progress",
                    "7": "ISO 9001 certified",
                    "10": "Advanced integrated QMS"
                }
            },
            "SPC": {
                "name": "Statistical Process Control",
                "category": "Tools",
                "criteria": {
                    "1": "No SPC implementation",
                    "3": "Basic data collection",
                    "5": "Regular SPC charts",
                    "7": "Advanced SPC with process capability",
                    "10": "Real-time SPC"
                }
            },
            "ProcessControl": {
                "name": "Process Control",
                "category": "Process",
                "criteria": {
                    "1": "No process control",
                    "3": "Basic process documentation",
                    "5": "Standard work instructions",
                    "7": "Process control plans",
                    "10": "Advanced process control system"
                }
            }
        }
        
        for cap_id, cap_info in base_capabilities.items():
            self.add_capability(
                cap_id,
                cap_info["name"],
                cap_info["category"],
                cap_info["criteria"]
            )

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
            ]
        }

    def analyze_pdf(self, pdf_file) -> dict:
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
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            text_content = soup.get_text().lower()
            results = self._analyze_text_content(text_content)
            
            # Find quality-related pages
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
        results = {
            'certifications_found': [],
            'quality_mentions': 0,
            'process_mentions': 0,
            'tools_mentions': 0,
            'suggested_scores': {}
        }
        
        # Find certifications
        for cert in self.quality_indicators['certifications']:
            if cert.lower() in text_content:
                results['certifications_found'].append(cert)
        
        # Count mentions
        for term in self.quality_indicators['quality_terms']:
            results['quality_mentions'] += len(re.findall(r'\b' + re.escape(term.lower()) + r'\b', text_content))
        
        for term in self.quality_indicators['process_terms']:
            results['process_mentions'] += len(re.findall(r'\b' + re.escape(term.lower()) + r'\b', text_content))
        
        for term in self.quality_indicators['tools_terms']:
            results['tools_mentions'] += len(re.findall(r'\b' + re.escape(term.lower()) + r'\b', text_content))
        
        results['suggested_scores'] = self._calculate_suggested_scores(results)
        return results

    def _calculate_suggested_scores(self, results: dict) -> dict:
        scores = {}
        
        # QMS Score
        qms_score = min(
            (len(results['certifications_found']) * 2) +
            (results['quality_mentions'] // 5),
            10
        )
        scores['QMS'] = max(1, qms_score)
        
        # Process Control Score
        process_score = min(
            (results['process_mentions'] // 3) +
            (len(results.get('quality_pages', [])) // 2),
            10
        )
        scores['ProcessControl'] = max(1, process_score)
        
        # SPC Score
        tools_score = min(
            (results['tools_mentions'] // 2) +
            len(results['certifications_found']),
            10
        )
        scores['SPC'] = max(1, tools_score)
        
        return scores

def display_analysis_results(results: dict):
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
            "Tools References": results['tools_mentions']
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
        
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("Company Name")
            industry = st.selectbox("Industry", ["Manufacturing", "Technology", "Healthcare", "Automotive", "Other"])
        
        with col2:
            assessment_date = st.date_input("Assessment Date")
            assessor = st.text_input("Assessor Name")
        
        st.write("### Capability Assessment")
        scores = {}
        evidence = {}
        
        for category in capability_manager.get_all_categories():
            st.write(f"\n#### {category}")
            capabilities = capability_manager.get_capabilities_by_category(category)
            
            for cap_id, cap in capabilities.items():
                col1, col2 = st.columns([2, 3])
                
                with col1:
                    scores[cap_id] = st.slider(
                        f"{cap.name}",
                        min_value=1,
                        max_value=10,
                        step=2,
                        value=5,
                        key=f"manual_score_{cap_id}"
                    )
                
                with col2:
                    evidence[cap_id] = st.text_area(
                        "Evidence/Notes",
                        key=f"manual_evidence_{cap_id}",
                        height=100
                    )
                    
                    with st.expander("View Scoring Criteria"):
                        for level, desc in cap.scoring_criteria.items():
                            if int(level) == scores[cap_id]:
                                st.markdown(f"**Level {level}:** {desc} 👈")
                            else:
                                st.write(f"Level {level}: {desc}")
        
        if st.button("Save Assessment"):
            if company_name:
                if 'assessments' not in st.session_state:
                    st.session_state.assessments = []
                
                assessment = {
                    "company_name": company_name,
                    "industry": industry,
                    "assessment_date": assessment_date.strftime("%Y-%m-%d"),
                    "assessor": assessor,
                    "scores": scores,
                    "evidence": evidence
                }
                
                st.session_state.assessments.append(assessment)
                st.success("Assessment saved successfully!")
            else:
                st.error("Please enter company name")

def create_analysis_ui(capability_manager):
    st.header("Quality Analysis Dashboard")
    
    if 'assessments' not in st.session_state or not st.session_state.assessments:
        st.info("No assessments available for analysis. Please collect some data first.")
        return
    
    analysis_type = st.selectbox(
        "Select Analysis Type",
        ["Industry Benchmark", "Capability Comparison", "Trend Analysis"]
    )
    
    if analysis_type == "Industry Benchmark":
        st.subheader("Industry Benchmark Analysis")
        
        df = pd.DataFrame(st.session_state.assessments)
        capability_cols = list(capability_manager.capabilities.keys())
        industry_avg = df.groupby('industry')[capability_cols].mean()
        
        fig = go.Figure(data=go.Heatmap(
            z=industry_avg.values,
            x=capability_cols,
            y=industry_avg.index,
            colorscale='Blues',
            text=np.round(industry_avg.values, 1),
            texttemplate='%{text}',
            textfont={"size": 10},
            colorbar=dict(title='Score')
        ))
        
        fig.update_layout(
            title='Industry Average Scores by Capability',
            xaxis_title='Capabilities',
            yaxis_title='Industry'
        )
        
        st.plotly_chart(fig)
    
    elif analysis_type == "Capability Comparison":
        st.subheader("Capability Comparison")
        
        companies = pd.DataFrame(st.session_state.assessments)['company_name'].unique()
        selected_companies = st.multiselect(
            "Select Companies to Compare",
            companies
        )
        
        if selected_companies:
            df = pd.DataFrame(st.session_state.assessments)
            company_data = df[df['company_name'].isin(selected_companies)]
            
            fig = go.Figure()
            
            for company in selected_companies:
                company_scores = company_data[company_data['company_name'] == company].iloc[0]
                capabilities = list(capability_manager.capabilities.keys())
                scores = [company_scores.get(cap, 0) for cap in capabilities]
                
                fig.add_trace(go.Scatterpolar(
                    r=scores,
                    theta=capabilities,
                    fill='toself',
                    name=company
                ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 10]
                    )
                ),
                showlegend=True
            )
            
            st.plotly_chart(fig)
    
    elif analysis_type == "Trend Analysis":
        st.info("Trend analysis feature coming soon!")

# Main execution
if __name__ == "__main__":
    st.title("Quality Management System")
    
    # Initialize session state for capability manager
    if 'capability_manager' not in st.session_state:
        st.session_state.capability_manager = QualityCapabilityManager()
    
    # Create tabs
    tabs = st.tabs([
        "Data Collection",
        "Analysis",
        "Capability Management"
    ])
    
    # Populate tabs
    with tabs[0]:
        create_data_collection_ui(st.session_state.capability_manager)
    
    with tabs[1]:
        create_analysis_ui(st.session_state.capability_manager)
    
    with tabs[2]:
        create_capability_management_ui(st.session_state.capability_manager)
