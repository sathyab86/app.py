import streamlit as st
import requests
import pdfplumber
import textract
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import CountVectorizer

# Industry and Capability Keyword Mapping
industry_keywords = {
    "Manufacturing": {
        "QMS": ["ISO 9001", "Six Sigma", "Lean Manufacturing", "Kaizen", "Quality Control", "Root Cause Analysis"],
        "Process Improvement": ["Total Quality Management", "5S", "Continuous Improvement", "Kanban", "Poka-Yoke"],
    },
    "Aerospace": {
        "QMS": ["AS9100", "FAA Compliance", "NADCAP", "Aviation Safety Standards", "ISO 9001", "Traceability"],
        "Material Testing": ["Fatigue Testing", "Non-Destructive Testing (NDT)", "Tensile Testing", "Heat Treatment"],
    },
    "Automotive": {
        "QMS": ["IATF 16949", "ISO 26262", "APQP", "PPAP", "FMEA", "Automotive SPICE"],
        "Process Improvement": ["Lean Manufacturing", "Kanban", "Continuous Improvement", "Error Proofing", "Kaizen"],
    },
    "Steel Fabrication": {
        "QMS": ["ISO 9001", "Welding Certifications", "AWS Standards", "Fabrication Tolerances", "Material Traceability"],
        "Safety Standards": ["OSHA Compliance", "ISO 45001", "Risk Assessment", "PPE Requirements"],
    },
    "Semiconductor": {
        "QMS": ["ISO 9001", "ISO 14001", "ISO 45001", "Traceability", "Cleanroom Standards", "Yield Optimization"],
        "Process Control": ["SPC", "Design for Manufacturing (DFM)", "Failure Analysis", "Defect Density Control"],
    },
    "Healthcare": {
        "QMS": ["ISO 13485", "FDA Compliance", "Patient Safety", "Medical Device Standards", "HIPAA"],
        "Data Management": ["Electronic Health Records", "Data Privacy", "Interoperability Standards"],
    },
    "IT": {
        "QMS": ["ISO 20000", "ITIL", "Service Level Agreements", "Incident Management", "Problem Management"],
        "Cybersecurity": ["ISO 27001", "SOC 2", "GDPR Compliance", "Risk Assessment", "Vulnerability Management"],
    },
}

# App title
st.title("Enhanced Quality Benchmark Scraper & Scorer")

# Section 1: Scrape data from URL
st.header("Step 1: Scrape Data from URL")
url = st.text_input("Enter the report URL:")
if st.button("Scrape URL"):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        report_text = soup.get_text()
        st.success("Data successfully scraped from URL!")
        st.text_area("Scraped Content Preview:", value=report_text[:500], height=200)
    except Exception as e:
        st.error(f"Error scraping data from URL: {e}")

# Section 2: Upload files for analysis
st.header("Step 2: Upload Report Files for Processing")
uploaded_file = st.file_uploader("Upload a report (PDF, Word, or Text):", type=["pdf", "docx", "txt"])
uploaded_content = ""
if uploaded_file is not None:
    try:
        file_type = uploaded_file.name.split(".")[-1]
        if file_type == "pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                uploaded_content = "\n".join(page.extract_text() for page in pdf.pages)
        elif file_type in ["docx", "txt"]:
            uploaded_content = textract.process(uploaded_file).decode("utf-8")
        else:
            st.error("Unsupported file type.")
        
        st.success("File successfully processed!")
        st.text_area("Extracted Content Preview:", value=uploaded_content[:500], height=200)
    except Exception as e:
        st.error(f"Error processing file: {e}")

# Section 3: Industry-Specific Keywords
st.header("Step 3: Industry-Specific Keywords")
industry = st.selectbox("Select Industry:", options=list(industry_keywords.keys()))
capability = st.selectbox(
    "Select Capability:", 
    options=list(industry_keywords[industry].keys()) if industry else []
)

if industry and capability:
    st.subheader(f"Relevant Keywords for {capability} in {industry}:")
    keywords = industry_keywords[industry][capability]
    st.write(", ".join(keywords))

# Section 4: Analysis & Visualization
st.header("Step 4: Analyze and Visualize Data")
all_text = ""
if uploaded_content.strip():
    all_text = uploaded_content
elif url.strip():
    all_text = report_text

if all_text:
    # Word frequency analysis
    st.subheader("Word Frequency Analysis")
    vectorizer = CountVectorizer(stop_words='english')
    word_counts = vectorizer.fit_transform([all_text])
    word_freq = pd.DataFrame({'Word': vectorizer.get_feature_names_out(), 'Frequency': word_counts.toarray()[0]})
    word_freq = word_freq.sort_values(by="Frequency", ascending=False).head(10)
    st.dataframe(word_freq)

    # Plotting word frequencies
    st.subheader("Word Frequency Visualization")
    fig, ax = plt.subplots()
    ax.barh(word_freq["Word"], word_freq["Frequency"], color='skyblue')
    ax.set_xlabel("Frequency")
    ax.set_ylabel("Words")
    ax.set_title("Top 10 Words by Frequency")
    st.pyplot(fig)

# Section 5: Custom Scoring
st.header("Step 5: Generate Custom Scores")
criteria_tags = st.text_area("Enter additional capability tags/criteria for scoring (comma-separated):")
if st.button("Generate Scores"):
    if criteria_tags or (industry and capability):
        # Combine industry-specific keywords and user-defined tags
        tags = [tag.strip().lower() for tag in criteria_tags.split(",")]
        if industry and capability:
            tags += [keyword.lower() for keyword in industry_keywords[industry][capability]]

        # Scoring
        tag_scores = {tag: all_text.lower().count(tag) for tag in tags}
        score_df = pd.DataFrame(list(tag_scores.items()), columns=["Criterion", "Score"])
        st.dataframe(score_df)

        # Display average score
        avg_score = score_df["Score"].mean()
        st.subheader(f"Average Score: {avg_score:.2f}")

        # Visualize scores
        fig, ax = plt.subplots()
        ax.bar(score_df["Criterion"], score_df["Score"], color='orange')
        ax.set_ylabel("Score")
        ax.set_title("Scores by Criterion")
        st.pyplot(fig)
    else:
        st.error("Please enter at least one capability tag or select industry keywords.")

# Footer
st.markdown("---")
st.markdown("Developed for benchmarking quality reports using scraping, analysis, and scoring.")

