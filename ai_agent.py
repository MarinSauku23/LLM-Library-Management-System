import os
from dotenv import load_dotenv
from openai import OpenAI
from prompt import SQL_PROMPT, ANSWER_PROMPT, RECOMMEND_PROMPT, ANSWER_OUTSIDE_SQL_PROMPT, INSIGHTS_PROMPT, READING_HABITS_PROMPT
import json
import requests

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



def _clean_sql(raw: str) -> str:
    sql = (raw or "").strip()


    if sql.startswith("```"):
        parts = sql.split("```")

        if len(parts) >= 2:
            sql = parts[1]
        sql = sql.replace("sql", "", 1).strip()

    # normalizes common wrong capitalizations
    sql = sql.replace("FROM User", "FROM users")
    sql = sql.replace("JOIN User", "JOIN users")
    sql = sql.replace("FROM Books", "FROM books")
    sql = sql.replace("JOIN Books", "JOIN books")

    # makes sure it handles case-sensitivity when questions are asked regarding the reading_status
    sql = sql.replace("reading_status = 'reading'", "LOWER(reading_status) = 'reading'")
    sql = sql.replace('reading_status = "reading"', "LOWER(reading_status) = 'reading'")
    sql = sql.replace("reading_status = 'completed'", "LOWER(reading_status) = 'completed'")
    sql = sql.replace('reading_status = "completed"', "LOWER(reading_status) = 'completed'")

    return sql.strip()


def ai_to_sql(user_question: str, current_user_id: int, is_admin: bool) -> str:
    user_content = (
        f"CURRENT_USER_ID = {current_user_id}\n"
        f"IS_ADMIN = {1 if is_admin else 0}\n"
        f"QUESTION: {user_question}"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SQL_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0,
    )


    raw_sql = response.choices[0].message.content or ""
    sql = _clean_sql(raw_sql)
    return sql


def generate_natural_answer(user_question: str, sql_query: str, rows: list[dict], user_name: str, is_admin: bool) -> str:
    rows_json = json.dumps(rows, ensure_ascii=False)

    meta_info = (
        f"User name: {user_name}\n"
        f"Is admin: {is_admin}\n"
        f"Question: {user_question}\n"
        f"Executed SQL: {sql_query}\n"
        f"SQL result rows (JSON):\n{rows_json}"
    )

    response = client.chat.completions.create(
        model = "gpt-4o",
        messages=[
            {"role": "system", "content": ANSWER_PROMPT},
            {"role": "user", "content": meta_info},
        ],
        temperature=0.4,
    )

    content = response.choices[0].message.content or ""
    return content.strip()


# generates book recommendations given the user's reading history
def recommend_books(requester_name: str, target_user_name: str, user_books: list[dict]
                    , is_admin: bool = False) -> str:
    books_json = json.dumps(user_books, ensure_ascii=False)

    user_content = (
        f"Requester name: {requester_name}\n"
        f"Target user name: {target_user_name}\n"
        f"Is requester admin: {is_admin}\n"
        f"Target user's existing books (JSON):\n{books_json}"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": RECOMMEND_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.7,
    )

    content = response.choices[0].message.content or ""
    return content.strip()


# calls DuckDuckGo API
def duckduckgo_search(query: str) -> str:
    try:
        response = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_html": 1,
                "no_redirect": 1,
            },
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return f"(Web search failed: {e})"

    snippets: list[str] = []

    abstract = data.get("AbstractText")
    if abstract:
        snippets.append(abstract)

    related = data.get("RelatedTopics") or []
    for topic in related[:5]:
        if isinstance(topic,dict) and topic.get("Text"):
            snippets.append(topic["Text"])

    if not snippets:
        return "No matching results from web search."

    return "\n".join(snippets)


# DuckDuckGo and LLM are used to answer questions that are not related with the DB
def answers_from_web(user_question: str, user_books: list[dict], is_admin: bool = False) -> str:
    titles = ", ".join({book["title"] for book in user_books if book.get("title")})

    if titles:
        search_query = f"{user_question} Among these books: {titles}"
    else:
        search_query = user_question

    search_snippets = duckduckgo_search(search_query)
    books_json = json.dumps(user_books, ensure_ascii=False)

    user_content = (
        f"User question: {user_question}\n\n"
        f"User's books (JSON):\n{books_json}\n\n"
        f"Is admin: {is_admin}\n\n"
        f"DuckDuckGo snippets:\n{search_snippets}"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": ANSWER_OUTSIDE_SQL_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.5,
    )

    content = response.choices[0].message.content or ""
    return content.strip()



def insights_summary(metrics: dict) -> str:
    payload = json.dumps(metrics, ensure_ascii=False)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": INSIGHTS_PROMPT},
            {"role": "user", "content": f"METRICS_JSON:\n{payload}"},
        ],
        temperature=0.4,
    )

    return (response.choices[0].message.content or "").strip()


# deep analysis of a user's reading habits through a summary
def analyze_reading_habits(requester_name: str, target_user_name: str, user_books: list[dict]) -> str:
    books_json = json.dumps(user_books, ensure_ascii=False)
    user_content = (
        f"User name: {requester_name}\n"
        f"Target user name: {target_user_name}\n"
        f"Their book collection (JSON):\n{books_json}"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": READING_HABITS_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.6,
    )

    return (response.choices[0].message.content or "").strip()