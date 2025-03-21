import pdfplumber
import docx
import pandas as pd
import os
import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.neighbors import NearestNeighbors

# Function to extract text from PDF
def extract_text_from_pdf(file_path):
    text = ""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    return text.strip() if text.strip() else None  # Return None if empty

# Function to extract text from DOCX
def extract_text_from_docx(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    doc = docx.Document(file_path)
    text = "\n".join([para.text.strip() for para in doc.paragraphs if para.text.strip()])
    
    return text if text else None  # Return None if empty

# Function to read resume text
def read_resume_text(file_path):
    if file_path.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.lower().endswith('.docx'):
        return extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload a PDF or DOCX file.")

# Function to extract the "Skills" section
def extract_skills_section(text):
    if not text:
        return None  # Handle empty text

    skills_section_keywords = [
        r'\bskills\b', r'\btechnical skills\b', r'\bprofessional skills\b', 
        r'\bcore competencies\b', r'\bexpertise\b'
    ]
    
    stop_sections = [
        r'\bexperience\b', r'\bprojects\b', r'\bcertifications\b', 
        r'\beducation\b', r'\bwork history\b', r'\bachievements\b'
    ]

    text_lower = text.lower()

    for keyword in skills_section_keywords:
        pattern = rf"{keyword}.*?\n(.*?)(?:{'|'.join(stop_sections)}|$)"
        match = re.search(pattern, text_lower, re.DOTALL)
        if match and match.group(1).strip():
            return match.group(1).strip()

    return None  # Return None if no skills section found

# Load the dataset
df_path = "synthetic_jobs_large.csv"
if not os.path.exists(df_path):
    raise FileNotFoundError(f"Job dataset not found: {df_path}")

df = pd.read_csv(df_path)

# Ensure required columns exist
required_columns = {"Job Title", "Company Name", "Skills Required"}
if not required_columns.issubset(df.columns):
    raise ValueError(f"Dataset is missing required columns: {required_columns - set(df.columns)}")

# Vectorizing the skills column
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(df["Skills Required"].fillna(""))

# Function to recommend careers based on skills
def recommend_careers(input_skills, df, vectorizer, top_k=5):
    if not input_skills:
        return None  # Return None if input skills are empty

    input_vector = vectorizer.transform([input_skills])

    knn = NearestNeighbors(n_neighbors=min(top_k, len(df)), metric='cosine')
    knn.fit(X)

    distances, indices = knn.kneighbors(input_vector)

    recommendations = df.iloc[indices[0]][["Job Title", "Company Name"]]
    return recommendations if not recommendations.empty else None
