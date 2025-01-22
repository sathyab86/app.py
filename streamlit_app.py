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

# Classes first
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
            }
        }
        
        for cap_id, cap_info in base_capabilities.items():
            self.add_capability(
                cap_id,
                cap_info["name"],
                cap_info["category"],
                cap_info["criteria"]
            )

# Helper functions
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

# UI Functions
def create_capability_management_ui(capability_manager):
    st.header("Capability Management")
    
    action = st.selectbox(
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
        cap_category = st.text_input("Category")
        
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

def create_data_collection_ui(capability_manager):
    st.header("Data Collection")
    
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
                    key=f"score_{cap_id}"
                )
            
            with col2:
                evidence[cap_id] = st.text_area(
                    "Evidence/Notes",
                    key=f"evidence_{cap_id}"
                )
    
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
    st.header("Analysis")
    
    if 'assessments' not in st.session_state or not st.session_state.assessments:
        st.info("No assessments available for analysis. Please collect some data first.")
        return
    
    df = pd.DataFrame(st.session_state.assessments)
    st.write("### Assessment Data")
    st.dataframe(df)

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
