# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
from langchain_config import get_ai_summary_for_query
from fpdf import FPDF

# --------------------------
# 🌐 Page Config
# --------------------------
st.set_page_config(page_title="AI News Research Tool", page_icon="📰", layout="wide")

# --------------------------
# 🎨 Custom Styling
# --------------------------
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); font-family: 'Segoe UI', sans-serif; color: #f5f5f5; }
section[data-testid="stSidebar"] { background: linear-gradient(135deg, #1a1a2e, #16213e); color: #f5f5f5 !important; }
h1 { color: #00e5ff !important; text-align: center; font-weight: bold; }
h2, h3 { color: #90caf9 !important; }
div.stButton > button { background: linear-gradient(90deg, #ff6f61, #ffcc70); color: black; border-radius: 12px; padding: 0.6em 1.2em; font-weight: bold; border: none; box-shadow: 0px 4px 8px rgba(0,0,0,0.3); transition: all 0.3s ease-in-out; }
div.stButton > button:hover { background: linear-gradient(90deg, #ffcc70, #ff6f61); transform: scale(1.05); }
div[data-baseweb="tab-list"] { background: #1e1e2f; border-radius: 8px; padding: 4px; }
button[data-baseweb="tab"] { font-weight: bold; color: #f5f5f5 !important; }
.streamlit-expanderHeader { font-weight: bold; background: #2e2e48; border-radius: 8px; padding: 6px; color: #f5f5f5 !important; }
.stMarkdown, .stCode { background: #121212; padding: 15px; border-radius: 10px; box-shadow: 0px 4px 8px rgba(255,255,255,0.1); margin-bottom: 10px; color: #f5f5f5; }
</style>
""", unsafe_allow_html=True)

# --------------------------
# 🏷️ Header
# --------------------------
st.markdown("<h1>📰 AI News Research Tool</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:18px;'>✨ Fetch and analyze the latest news with AI ✨</p>", unsafe_allow_html=True)
st.divider()

# --------------------------
# ⚙️ Sidebar Controls
# --------------------------
st.sidebar.header("⚙️ General Options")
num_articles = st.sidebar.slider("📑 Number of Articles", 3, 20, 5)
country = st.sidebar.selectbox("🌍 Country", ["US", "IN", "UK", "SG", "JP"], index=1)
language = st.sidebar.selectbox("🗣️ Language", ["en", "hi", "fr", "de"], index=0)

# --------------------------
# 🔍 Query Input
# --------------------------
query = st.text_input("🔍 What news are you looking for? (e.g., 'Tech company quarterly results')")

# --------------------------
# 📄 PDF Generator
# --------------------------
def generate_pdf(title, content, filename="output.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 8, f"{title}\n\n{content}")
    pdf.output(filename)
    return filename

# --------------------------
# 🔹 Fetch News & Summaries
# --------------------------
if st.button("🚀 Get News"):
    if not query:
        st.warning("⚠️ Please enter a query.")
    else:
        with st.spinner("⏳ Fetching articles and generating summaries..."):
            try:
                articles, per_article_summaries, overall_summary = get_ai_summary_for_query(
                    query=query,
                    num_articles=num_articles,
                    country=country,
                    language=language
                )

                if not articles:
                    st.error("❌ No articles found for that query.")
                else:
                    tab1, tab2, tab3 = st.tabs(["📰 Articles", "📝 Per-Article Summary", "📌 Overall AI Summary"])

                    # --- Articles ---
                    with tab1:
                        st.subheader("📰 Latest Articles")
                        for i, a in enumerate(articles, start=1):
                            with st.expander(f"{i}. {a.get('title', 'No title')}"):
                                st.write(a.get("description", ""))
                                if a.get("url"):
                                    st.markdown(f"[🔗 Read more]({a['url']})")

                    # --- Per-Article Summaries ---
                    with tab2:
                        st.subheader("📝 AI Summaries for Each Article")
                        if per_article_summaries:
                            for row in per_article_summaries:
                                sentiment = row.get("sentiment", "Neutral").lower()
                                if "positive" in sentiment:
                                    st.success(f"📈 {row['title']}\n\n{row['summary']}")
                                elif "negative" in sentiment:
                                    st.error(f"📉 {row['title']}\n\n{row['summary']}")
                                else:
                                    st.info(f"⚖️ {row['title']}\n\n{row['summary']}")

                            # Download as PDF
                            pdf_text = ""
                            for row in per_article_summaries:
                                pdf_text += f"{row['title']}\n{row['summary']}\nSentiment: {row['sentiment']}\n\n"
                            generate_pdf("Per-Article Summaries", pdf_text, "per_article_summaries.pdf")
                            st.download_button("⬇️ Download Per-Article Summaries (PDF)", "per_article_summaries.pdf")

                        else:
                            st.warning("⚠️ Per-article summaries not available.")

                    # --- Overall Summary ---
                    with tab3:
                        st.subheader("📌 AI Overall Research Summary")
                        if overall_summary:
                            if "positive" in overall_summary.lower():
                                st.success("📈 Positive Outlook\n\n" + overall_summary)
                            elif "negative" in overall_summary.lower():
                                st.error("📉 Negative Outlook\n\n" + overall_summary)
                            else:
                                st.info("⚖️ Neutral Analysis\n\n" + overall_summary)

                            generate_pdf("Overall Summary", overall_summary, "overall_summary.pdf")
                            st.download_button("⬇️ Download Overall Summary (PDF)", "overall_summary.pdf")
                        else:
                            st.warning("⚠️ No overall summary generated.")

                    # 💾 Save Query History
                    log = {"query": query, "summary": str(overall_summary), "time": datetime.now()}
                    pd.DataFrame([log]).to_csv("query_history.csv", mode="a", header=False, index=False)

            except Exception as e:
                st.error(f"⚠️ Error: {e}")

# --------------------------
# 📊 Query History Section
# --------------------------
st.sidebar.header("📂 Search History")
try:
    history = pd.read_csv("query_history.csv", names=["query", "summary", "time"], encoding="utf-8")
    st.sidebar.write(f"📌 Total Queries Logged: {len(history)}")

    if st.sidebar.checkbox("📜 Show Recent Queries"):
        st.sidebar.dataframe(history.tail(10))

    keyword = st.sidebar.text_input("🔎 Filter by keyword")
    if keyword:
        filtered = history[history["query"].str.contains(keyword, case=False, na=False)]
        st.sidebar.write(f"✅ Found {len(filtered)} matching queries")
        st.sidebar.dataframe(filtered.tail(10))

    if st.sidebar.button("🧹 Clear History"):
        open("query_history.csv", "w", encoding="utf-8").close()
        st.sidebar.success("✅ History cleared!")

    if st.sidebar.button("⬇️ Export History as PDF"):
        pdf_text = ""
        for _, row in history.iterrows():
            pdf_text += f"{row['time']} - {row['query']}\nSummary: {row['summary']}\n\n"
        generate_pdf("Query History", pdf_text, "query_history.pdf")
        st.download_button("⬇️ Download Query History (PDF)", "query_history.pdf")

except FileNotFoundError:
    st.sidebar.write("No history yet. Run some queries!")
