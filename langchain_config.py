import os
from gnews import GNews
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# -----------------------------
# 🔑 Load API Key from .env
# -----------------------------
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(model="llama-3.1-8b-instant", api_key=groq_api_key)

# -----------------------------
# 📰 News Fetcher
# -----------------------------
def fetch_news(query, num_articles=5, country="IN", language="en"):
    google_news = GNews(language=language, country=country, max_results=num_articles)
    articles = google_news.get_news(query)
    return articles or []

# -----------------------------
# 📌 Summarizer Chain
# -----------------------------
template = """
You are an AI assistant helping an equity research analyst.
Summarize the following news article.

Query: {query}

Article:
{article}

Return summary in max 4 sentences and give a sentiment (Positive, Negative, Neutral).
"""
prompt = PromptTemplate(template=template, input_variables=["query", "article"])
llm_chain = LLMChain(prompt=prompt, llm=llm)

# -----------------------------
# 🔗 Main function used in app.py
# -----------------------------
def get_ai_summary_for_query(query, num_articles=5, country="IN", language="en"):
    # 1️⃣ Fetch articles
    articles = fetch_news(query, num_articles=num_articles, country=country, language=language)
    if not articles:
        return [], [], "No articles found."

    # 2️⃣ Remove duplicate articles by title
    unique_articles = []
    seen_titles = set()
    for a in articles:
        title = a.get("title", "").strip()
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_articles.append(a)

    # 3️⃣ Per-article summaries using LangChain
    per_article_summaries = []
    for a in unique_articles:
        article_text = f"Title: {a.get('title','')}\nDescription: {a.get('description','')}"
        ai_summary = llm_chain.run({"query": query, "article": article_text})

        per_article_summaries.append({
            "title": a.get("title", ""),
            "url": a.get("url", ""),
            "summary": ai_summary,
            "sentiment": (
                "Positive" if "positive" in ai_summary.lower()
                else "Negative" if "negative" in ai_summary.lower()
                else "Neutral"
            )
        })

    # 4️⃣ Overall summary
    all_text = " ".join([s["summary"] for s in per_article_summaries])
    overall_summary = llm_chain.run({"query": query, "article": all_text})

    return unique_articles, per_article_summaries, overall_summary
