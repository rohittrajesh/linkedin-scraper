# src/cli.py

from datetime import datetime
import typer

# ensure tables exist
from src.db import init_db, SessionLocal
init_db()

from src.linkedin_scraper import ensure_logged_in, fetch_profile_info, fetch_all_posts
from src.models import Profile, Post

app = typer.Typer()

@app.command()
def login():
    """Log in to LinkedIn and save your session (no credentials in code)."""
    ensure_logged_in()
    typer.echo("✅ Session saved! You can now scrape profiles.")

@app.command()
def scrape(profile_url: str):
    """
    Scrape LinkedIn profile + all posts for PROFILE_URL, and persist to SQLite.
    """
    # 1) ensure we’re logged in
    ctx = ensure_logged_in()

    # 2) scrape profile info & posts
    info  = fetch_profile_info(ctx, profile_url)
    posts = fetch_all_posts(ctx, profile_url)

    # 3) persist to DB
    db = SessionLocal()
    # — upsert Profile —
    profile = db.query(Profile).filter_by(url=profile_url).first()
    if not profile:
        profile = Profile(url=profile_url)
    profile.name       = info["name"]
    profile.headline   = info["headline"]
    profile.location   = info["location"]
    profile.email      = info["email"]
    profile.phone      = info["phone"]
    profile.scraped_at = datetime.utcnow()
    db.add(profile)
    db.commit()
    db.refresh(profile)

    # — replace old posts —
    db.query(Post).filter(Post.profile_id == profile.id).delete()
    db.commit()
    for p in posts:
        db.add(Post(
            profile_id=profile.id,
            post_url=p["post_url"],
            content=p["content"],
            posted_at=p["posted_at"],
        ))
    db.commit()

    typer.echo(f"✅ Saved profile '{profile.name}' plus {len(posts)} posts.")
