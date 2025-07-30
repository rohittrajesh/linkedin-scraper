import os
from typing import List

import openai
from src.config import logger
from src.db import SessionLocal
from src.models import Profile

# ─── Configure OpenAI API Key ────────────────────────────────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY")


def summarize_posts(post_texts: List[str], max_sentences: int = 5) -> str:
    """
    Generate a concise summary (3-5 sentences) of the provided post texts using OpenAI.
    """
    # Combine posts with a clear delimiter
    combined = "\n---\n".join(post_texts)
    # Truncate if overly long
    if len(combined) > 15000:
        combined = combined[:15000] + "..."

    messages = [
        {"role": "system", "content": "You are an assistant that summarizes collections of LinkedIn posts into brief summaries."},
        {"role": "user", "content": (
            "Here are some LinkedIn post contents separated by '---'. "
            f"Please provide a concise summary (3-5 sentences) of the major themes and topics covered.\n\n{combined}"
        )}
    ]
    logger.info("Sending summarization request to OpenAI for %d posts", len(post_texts))
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
        max_tokens=512,
    )
    summary = response.choices[0].message.content.strip()
    logger.info("Received summary from OpenAI")
    return summary


def summarize_profile(profile_url: str) -> str:
    db = SessionLocal()
    profile = db.query(Profile).filter_by(url=profile_url).first()
    if not profile:
        db.close()
        raise ValueError(f"No data found for profile URL: {profile_url}")

    # Load posts while session is open
    post_texts = [p.content for p in profile.posts]
    db.close()

    if not post_texts:
        return "No posts found to summarize."
    return summarize_posts(post_texts)
