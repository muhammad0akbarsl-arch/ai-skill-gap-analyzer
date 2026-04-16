import streamlit as st
import PyPDF2
from openai import OpenAI
import os

# Load API key from Streamlit secrets
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.title("AI Skill Gap Analyzer")

# Upload CV
uploaded_file = st.file_uploader("Upload your CV (PDF)", type="pdf")

# Job Description
job_desc = st.text_area("Paste Job Description")

# Function to extract PDF text
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Analyze Button
if st.button("Analyze"):
    if uploaded_file and job_desc:
        cv_text = extract_text_from_pdf(uploaded_file)

        prompt = f"""
        You are a career coach and HR expert.

        Compare CV and job description.

        Return in this format:

        Match Score: XX%

        Matching Skills:
        - skill 1
        - skill 2

        Missing Skills:
        - skill 1
        - skill 2

        Action Plan:
        - step 1
        - step 2

        CV:
        {cv_text}

        JOB DESCRIPTION:
        {job_desc}
        """

        response = client.chat.completions.create(
            model="gpt-5",
            messages=[{"role": "user", "content": prompt}]
        )

        result = response.choices[0].message.content

        st.subheader("Result")
        st.markdown(result)

    else:
        st.warning("Please upload CV and paste job description")
