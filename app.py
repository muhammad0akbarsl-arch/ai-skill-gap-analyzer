import streamlit as st
import PyPDF2
from openai import OpenAI
import matplotlib.pyplot as plt

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="AI Skill Gap Analyzer", layout="wide")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("📄 AI Skill Gap Analyzer (ATS Style)")

# =========================
# INPUT
# =========================
uploaded_file = st.file_uploader("Upload your CV (PDF)", type="pdf")
job_desc = st.text_area("Paste Job Description")

# =========================
# PDF TEXT EXTRACTION
# =========================
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text

# =========================
# PARSE AI RESPONSE
# =========================
def parse_response(text):
    lines = text.split("\n")

    score = 0
    matching = []
    missing = []
    experience_gap = ""
    education_match = ""
    keyword_match = ""

    section = None

    for line in lines:
        line = line.strip()

        if line.startswith("MATCH_SCORE"):
            try:
                score = int(line.split(":")[1].strip())
            except:
                score = 0

        elif "MATCHING_SKILLS" in line:
            section = "match"

        elif "MISSING_SKILLS" in line:
            section = "missing"

        elif "EXPERIENCE_GAP" in line:
            section = "exp"

        elif "EDUCATION_MATCH" in line:
            section = "edu"

        elif "KEYWORD_MATCH" in line:
            section = "key"

        elif "ACTION_PLAN" in line:
            section = None

        elif line.startswith("-"):
            if section == "match":
                matching.append(line[1:].strip())
            elif section == "missing":
                missing.append(line[1:].strip())

        else:
            if section == "exp":
                experience_gap += line + " "
            elif section == "edu":
                education_match += line + " "
            elif section == "key":
                keyword_match += line + " "

    return score, matching, missing, experience_gap, education_match, keyword_match

# =========================
# MAIN BUTTON
# =========================
if st.button("🔍 Analyze"):
    if uploaded_file and job_desc:

        with st.spinner("Analyzing your CV like an ATS system..."):
            try:
                cv_text = extract_text_from_pdf(uploaded_file)

                # Limit size (important)
                cv_text = cv_text[:4000]
                job_desc = job_desc[:2000]

                # =========================
                # PROMPT
                # =========================
                prompt = f"""
You are a senior HR recruiter and ATS (Applicant Tracking System).

Your task is to evaluate how well a candidate's CV matches a job description.

SCORING RULES:
- 0–100 scale
- Consider:
  1. Skills match (technical & soft skills)
  2. Relevant experience
  3. Tools/software mentioned
  4. Keywords alignment
  5. Education relevance
- Be strict and realistic (like a real ATS system)

OUTPUT FORMAT (STRICT — FOLLOW EXACTLY):

MATCH_SCORE: <number only>

MATCHING_SKILLS:
- <skill>
- <skill>

MISSING_SKILLS:
- <skill>
- <skill>

EXPERIENCE_GAP:
- <short explanation>

EDUCATION_MATCH:
- <short explanation>

KEYWORD_MATCH:
- <short explanation>

ACTION_PLAN:
- <specific step to improve>
- <specific step to improve>
- <specific step to improve>

IMPORTANT:
- Do NOT add explanations outside this format
- Keep skills concise (1–3 words)
- Maximum 6 skills per section

CV:
{cv_text}

JOB DESCRIPTION:
{job_desc}
"""

                # =========================
                # API CALL
                # =========================
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert ATS recruiter."},
                        {"role": "user", "content": prompt}
                    ]
                )

                result = response.choices[0].message.content

                # =========================
                # PARSE
                # =========================
                score, matching, missing, exp_gap, edu_match, key_match = parse_response(result)

                # =========================
                # ATS SCORE
                # =========================
                st.subheader("📊 ATS Match Score")

                st.progress(score / 100)
                st.metric("Match Score", f"{score}%")

                if score >= 80:
                    st.success("Strong match 🚀")
                elif score >= 60:
                    st.warning("Moderate match ⚠️")
                else:
                    st.error("Low match ❌")

                # =========================
                # CHART
                # =========================
                st.subheader("📈 Skill Gap Analysis")

                labels = ["Matching Skills", "Missing Skills"]
                values = [len(matching), len(missing)]

                fig, ax = plt.subplots()
                ax.bar(labels, values)

                st.pyplot(fig)

                # =========================
                # SKILLS
                # =========================
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("✅ Matching Skills")
                    if matching:
                        for skill in matching:
                            st.write(f"- {skill}")
                    else:
                        st.write("No matching skills found")

                with col2:
                    st.subheader("❌ Missing Skills")
                    if missing:
                        for skill in missing:
                            st.write(f"- {skill}")
                    else:
                        st.write("No missing skills detected")

                # =========================
                # EXTRA INSIGHTS
                # =========================
                st.subheader("🧠 Additional Insights")

                st.write("**📉 Experience Gap:**")
                st.write(exp_gap if exp_gap else "-")

                st.write("**🎓 Education Match:**")
                st.write(edu_match if edu_match else "-")

                st.write("**🔍 Keyword Match:**")
                st.write(key_match if key_match else "-")

                # =========================
                # RAW OUTPUT
                # =========================
                with st.expander("🔍 See Full AI Response"):
                    st.markdown(result)

            except Exception as e:
                st.error(f"Error: {str(e)}")

    else:
        st.warning("⚠️ Please upload CV and paste job description")
