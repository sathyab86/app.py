import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, List, Optional
# Add these imports at the top of app.py
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin

class WebScraper:
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
    
    def scrape_website(self, url: str) -> dict:
        """Scrape quality-related information from website"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get text content
            text_content = soup.get_text().lower()
            
            # Initialize results
            results = {
                'certifications_found': [],
                'quality_mentions': 0,
                'process_mentions': 0,
                'tools_mentions': 0,
                'quality_pages': [],
                'suggested_scores': {}
            }
            
            # Find certifications
            for cert in self.quality_indicators['certifications']:
                if cert.lower() in text_content:
                    results['certifications_found'].append(cert)
            
            # Count quality-related terms
            for term in self.quality_indicators['quality_terms']:
                results['quality_mentions'] += len(re.findall(r'\b' + re.escape(term.lower()) + r'\b', text_content))
            
            # Count process-related terms
            for term in self.quality_indicators['process_terms']:
                results['process_mentions'] += len(re.findall(r'\b' + re.escape(term.lower()) + r'\b', text_content))
            
            # Count quality tools mentions
            for term in self.quality_indicators['tools_terms']:
                results['tools_mentions'] += len(re.findall(r'\b' + re.escape(term.lower()) + r'\b', text_content))
            
            # Find quality-related pages
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and any(term in href.lower() for term in ['quality', 'certification', 'compliance']):
                    full_url = urljoin(url, href)
                    results['quality_pages'].append(full_url)
            
            # Calculate suggested scores
            results['suggested_scores'] = self._calculate_suggested_scores(results)
            
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
    
    def _calculate_suggested_scores(self, results: dict) -> dict:
        """Calculate suggested scores based on scraped data"""
        scores = {}
        
        # QMS Score
        qms_score = min(
            (len(results['certifications_found']) * 2) +  # 2 points per certification
            (results['quality_mentions'] // 5),           # 1 point per 5 quality mentions
            10  # Max score of 10
        )
        scores['QMS'] = max(1, qms_score)  # Minimum score of 1
        
        # Process Control Score
        process_score = min(
            (results['process_mentions'] // 3) +          # 1 point per 3 process mentions
            (len(results['quality_pages']) // 2),         # 1 point per 2 quality pages
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

# Add to the Data Collection UI function:
def create_data_collection_ui(capability_manager):
    st.header("Quality Data Collection")
    
    # Create tabs for different collection methods
    manual_tab, web_tab = st.tabs(["Manual Entry", "Website Analysis"])
    
    # Web Scraping Tab
    with web_tab:
        st.subheader("Website Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("Company Name", key="web_company_name")
            company_url = st.text_input("Company Website URL")
        with col2:
            industry = st.selectbox("Industry", ["Manufacturing", "Technology", "Healthcare", "Automotive", "Other"], key="web_industry")
            assessment_date = st.date_input("Assessment Date", key="web_date")

        if st.button("Analyze Website"):
            if company_url:
                with st.spinner("Analyzing website..."):
                    try:
                        scraper = WebScraper()
                        results = scraper.scrape_website(company_url)
                        
                        # Display results in organized sections
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
                                if capability in capability_manager.capabilities:
                                    st.metric(
                                        capability_manager.capabilities[capability].name,
                                        f"{score}/10"
                                    )
                        
                        st.write("### Quality-Related Pages Found")
                        if results['quality_pages']:
                            for page in results['quality_pages'][:5]:
                                st.write(f"- {page}")
                        
                        # Option to use suggested scores
                        if st.button("Use These Scores for Assessment"):
                            if 'assessments' not in st.session_state:
                                st.session_state.assessments = []
                            
                            assessment = {
                                "company_name": company_name,
                                "industry": industry,
                                "assessment_date": assessment_date.strftime("%Y-%m-%d"),
                                "source": "web_analysis",
                                "url": company_url,
                                "scores": results['suggested_scores'],
                                "evidence": {
                                    "certifications": results['certifications_found'],
                                    "quality_pages": results['quality_pages'],
                                    "metrics": metrics
                                }
                            }
                            
                            st.session_state.assessments.append(assessment)
                            st.success("Assessment saved! View it in the Analysis tab.")
                    
                    except Exception as e:
                        st.error(f"Error analyzing website: {str(e)}")
            else:
                st.warning("Please enter a website URL")
    
    # Manual Entry Tab
    with manual_tab:
        st.subheader("Manual Assessment")
        
        # Company Information
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("Company Name", key="manual_company_name")
            industry = st.selectbox("Industry", ["Manufacturing", "Technology", "Healthcare", "Automotive", "Other"], key="manual_industry")
        with col2:
            assessment_date = st.date_input("Assessment Date", key="manual_date")
            assessor = st.text_input("Assessor Name")
        
        # Capability Scoring
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
                    
                    # Show scoring criteria
                    with st.expander("View Scoring Criteria"):
                        for level, desc in cap.scoring_criteria.items():
                            if int(level) == scores[cap_id]:
                                st.markdown(f"**Level {level}:** {desc} 👈")
                            else:
                                st.write(f"Level {level}: {desc}")
        
        # Save Assessment
        if st.button("Save Manual Assessment"):
            if company_name:
                if 'assessments' not in st.session_state:
                    st.session_state.assessments = []
                
                assessment = {
                    "company_name": company_name,
                    "industry": industry,
                    "assessment_date": assessment_date.strftime("%Y-%m-%d"),
                    "assessor": assessor,
                    "source": "manual",
                    "scores": scores,
                    "evidence": evidence
                }
                
                st.session_state.assessments.append(assessment)
                st.success("Assessment saved successfully!")
            else:
                st.error("Please enter company name")
# Analysis UI
def create_analysis_ui(capability_manager):
    st.header("Quality Analysis Dashboard")
    
    if 'assessments' not in st.session_state or not st.session_state.assessments:
        st.info("No assessments available for analysis. Please collect some data first.")
        return
    
    # Convert assessments to DataFrame
    assessment_data = []
    for assessment in st.session_state.assessments:
        row = {
            "company_name": assessment["company_name"],
            "industry": assessment["industry"],
            "assessment_date": assessment["assessment_date"],
            "assessor": assessment["assessor"]
        }
        row.update(assessment["scores"])
        assessment_data.append(row)
    
    df = pd.DataFrame(assessment_data)
    
    # Analysis Options
    analysis_type = st.selectbox(
        "Select Analysis Type",
        ["Industry Benchmark", "Capability Comparison", "Trend Analysis"]
    )
    
    if analysis_type == "Industry Benchmark":
        st.subheader("Industry Benchmark Analysis")
        
        # Calculate industry averages
        industry_avg = df.groupby('industry')[list(capability_manager.capabilities.keys())].mean()
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=industry_avg.values,
            x=list(capability_manager.capabilities.keys()),
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
        
        selected_companies = st.multiselect(
            "Select Companies to Compare",
            df['company_name'].unique()
        )
        
        if selected_companies:
            company_data = df[df['company_name'].isin(selected_companies)]
            
            fig = go.Figure()
            
            for company in selected_companies:
                company_scores = company_data[company_data['company_name'] == company]
                capabilities = list(capability_manager.capabilities.keys())
                scores = [company_scores[cap].iloc[0] for cap in capabilities]
                
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
        st.subheader("Trend Analysis")
        st.write("Trend analysis will be implemented in future updates")

# Capability Management UI
def create_capability_management_ui(capability_manager):
    st.header("Quality Capability Management")
    
    action = st.sidebar.radio(
        "Select Action",
        ["View Capabilities", "Add Capability", "Edit Capability", "Remove Capability"]
    )
    
    if action == "View Capabilities":
        st.subheader("Current Capabilities")
        
        for category in capability_manager.get_all_categories():
            st.write(f"\n### {category}")
            capabilities = capability_manager.get_capabilities_by_category(category)
            
            for cap_id, cap in capabilities.items():
                with st.expander(f"{cap.name} ({cap_id})"):
                    st.write("**Scoring Criteria:**")
                    for score, description in cap.scoring_criteria.items():
                        st.write(f"Level {score}: {description}")
    
    elif action == "Add Capability":
        st.subheader("Add New Capability")
        
        cap_id = st.text_input("Capability ID (no spaces)")
        cap_name = st.text_input("Capability Name")
        
        existing_categories = capability_manager.get_all_categories()
        use_existing = st.checkbox("Use existing category", value=True)
        
        if use_existing:
            cap_category = st.selectbox("Category", existing_categories)
        else:
            cap_category = st.text_input("New Category")
        
        st.subheader("Scoring Criteria")
        scoring_criteria = {}
        
        for score in ["1", "3", "5", "7", "10"]:
            description = st.text_area(f"Level {score} Description")
            if description:
                scoring_criteria[score] = description
        
        if st.button("Add Capability"):
            if cap_id and cap_name and cap_category and scoring_criteria:
                capability_manager.add_capability(
                    cap_id,
                    cap_name,
                    cap_category,
                    scoring_criteria
                )
                st.success(f"Added capability: {cap_name}")
            else:
                st.error("Please fill in all fields")
    
    elif action == "Edit Capability":
        st.subheader("Edit Capability")
        
        cap_id = st.selectbox(
            "Select Capability",
            list(capability_manager.capabilities.keys())
        )
        
        if cap_id:
            cap = capability_manager.capabilities[cap_id]
            
            new_name = st.text_input("Name", value=cap.name)
            new_category = st.selectbox(
                "Category",
                capability_manager.get_all_categories(),
                index=capability_manager.get_all_categories().index(cap.category)
            )
            
            st.subheader("Scoring Criteria")
            new_criteria = {}
            
            for score in ["1", "3", "5", "7", "10"]:
                description = st.text_area(
                    f"Level {score}",
                    value=cap.scoring_criteria.get(score, "")
                )
                if description:
                    new_criteria[score] = description
            
            if st.button("Save Changes"):
                capability_manager.edit_capability(
                    cap_id,
                    name=new_name,
                    category=new_category,
                    scoring_criteria=new_criteria
                )
                st.success("Changes saved")
    
    elif action == "Remove Capability":
        st.subheader("Remove Capability")
        
        cap_id = st.selectbox(
            "Select Capability to Remove",
            list(capability_manager.capabilities.keys())
        )
        
        if cap_id and st.button("Remove Capability"):
            capability_manager.remove_capability(cap_id)
            st.success(f"Removed capability: {cap_id}")

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
