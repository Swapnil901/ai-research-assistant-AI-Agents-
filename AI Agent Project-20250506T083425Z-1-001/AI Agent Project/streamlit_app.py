import streamlit as st
import os
import sys
import tempfile
from textwrap import wrap
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Set project path
project_path = "/content/drive/MyDrive/AI Agent Project"
sys.path.append(project_path)

# Load modules
from summarizer_tool import SummarizerTool
from github_repo_tool import GitHubRepoTool
from memory_store import get_chroma_memory
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SerpAPIWrapper

# Load secrets
secrets_path = os.path.join(project_path, "secrets.txt")
with open(secrets_path, "r") as f:
    for line in f:
        if line.strip():
            key, value = line.strip().split("=", 1)
            os.environ[key.strip()] = value.strip()

# Initialize tools
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.7,
    api_key=os.environ["OPENAI_API_KEY"]
)

memory_db = get_chroma_memory()
search_tool = SerpAPIWrapper(serpapi_api_key=os.environ["SERPAPI_API_KEY"])
summarizer_tool = SummarizerTool()
github_tool = GitHubRepoTool()

# Streamlit UI Branding
st.set_page_config(page_title="AI Research Assistant", layout="centered")
st.markdown("<h1 style='text-align: center;'>🤖 AI Research Assistant</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: gray;'>A GPT-4 powered research agent using LangChain, SerpAPI & GitHub APIs</h4>", unsafe_allow_html=True)
st.markdown("---")

# Input field
user_input = st.text_input("🔍 Enter your research topic:")

if st.button("Run AI Agent") and user_input.strip():
    # 1. Recall memory
    with st.spinner("🔁 Searching memory..."):
        mem_results = memory_db.similarity_search(user_input, k=3)
        memory_result = "\n".join([f"- {r.page_content}" for r in mem_results]) or "No relevant memory found."
    st.markdown("### 🧠 Recalled Memory (for context only)")
    st.markdown(memory_result)

    # 2. Web search
    with st.spinner("🌐 Searching the web..."):
        web_search_raw = search_tool.run(user_input)

    # 3. Generate detailed explanation
    with st.spinner("📚 Generating detailed explanation..."):
        prompt = f"Explain this research topic in simple terms like you're teaching a beginner:\n\n{user_input}"
        detailed_explanation = llm.invoke(prompt).content
    st.markdown("### 📚 Detailed Explanation")
    st.markdown(detailed_explanation)

    # 4. Summarize
    with st.spinner("🧠 Summarizing web content..."):
        summary_result = summarizer_tool._run(web_search_raw)
    st.markdown("### 🔍 Key Summary Points")
    st.markdown(summary_result)

    # 5. GitHub Repos
    with st.spinner("💻 Fetching GitHub repositories..."):
        github_result = github_tool._run(user_input)
    st.markdown("### 💻 GitHub Projects")
    st.markdown(github_result)

    # 6. Build final report (exclude memory!)
    final_report = f"""
📌 **Research Topic**
{user_input}

📚 **Detailed Explanation**
{detailed_explanation}

🔍 **Key Summary Points**
{summary_result}

💻 **GitHub Projects**
{github_result}
"""

    st.markdown("### 📄 Final Report")
    st.markdown(final_report)
    st.session_state["final_report"] = final_report

    # 7. PDF Export with branding
    def save_text_to_pdf(text, filename):
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        y = height - 40

        # Header
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, y, "🤖 AI Research Report")
        y -= 30

        # Topic (if found)
        c.setFont("Helvetica", 12)
        topic_line = next((line for line in text.split("\n") if line.startswith("📌")), "")
        if topic_line:
            c.drawString(40, y, topic_line.replace("📌", "Topic:"))
            y -= 30

        # Main content
        c.setFont("Helvetica", 10)
        for line in text.split('\n'):
            wrapped_lines = wrap(line, width=110)
            for wrap_line in wrapped_lines:
                c.drawString(40, y, wrap_line)
                y -= 15
                if y < 40:
                    c.showPage()
                    y = height - 40

        # Footer
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(40, 20, "Generated by AI Research Assistant · Powered by GPT-4 + LangChain")
        c.save()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        save_text_to_pdf(final_report, tmp.name)
        with open(tmp.name, "rb") as pdf_file:
            st.download_button("📥 Download PDF", data=pdf_file, file_name="AI_Research_Report.pdf", mime="application/pdf")

# Footer
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 12px; color: gray;'>© 2025 AI Research Assistant · Built with ❤️ using OpenAI & LangChain</p>", unsafe_allow_html=True)
