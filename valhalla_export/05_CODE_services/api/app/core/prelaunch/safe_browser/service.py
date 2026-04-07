"""Safe Browser Service"""
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from . import models, schemas


def record_history(
    db: Session,
    child_id: UUID,
    query: str | None,
    url: str | None,
    title: str | None,
    result_type: str | None,
) -> models.KidBrowserHistory:
    """Record a browser history entry."""
    entry = models.KidBrowserHistory(
        child_id=child_id,
        query=query,
        url=url,
        title=title,
        result_type=result_type,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_history_for_child(db: Session, child_id: UUID) -> List[models.KidBrowserHistory]:
    """Get browser history for a specific child."""
    return (
        db.query(models.KidBrowserHistory)
        .filter(models.KidBrowserHistory.child_id == child_id)
        .order_by(models.KidBrowserHistory.created_at.desc())
        .all()
    )


def run_kid_safe_search(
    db: Session, payload: schemas.KidSearchRequest
) -> schemas.KidSearchResponse:
    """Run a safe search for a child.
    
    TODO: wire in a real safe-search / curated source logic.
    For now, just return placeholder results and log the query.
    """

    dummy_results = [
        schemas.KidSearchResult(
            title="What is a BRRRR house? (Kid-Safe)",
            url="https://safe.valhalla/kids/brrrr",
            snippet="A simple explanation of how buying, fixing, renting, and refinancing a house works.",
            result_type="learning",
        ),
        schemas.KidSearchResult(
            title="Fun money lesson adventure",
            url="https://safe.valhalla/kids/money-adventure",
            snippet="A story about saving, sharing, and spending wisely.",
            result_type="story",
        ),
    ]

    # Record the search itself as a history entry (no specific URL)
    record_history(
        db=db,
        child_id=payload.child_id,
        query=payload.query,
        url=None,
        title=None,
        result_type="search",
    )

    return schemas.KidSearchResponse(results=dummy_results)


def navigate_to_page(
    db: Session, payload: schemas.KidNavigateRequest
) -> schemas.PageContent:
    """Navigate to a kid-safe page.
    
    TODO: in future, fetch and filter actual content from the web.
    """

    title = "Kid-Safe Page"
    text_blocks = [
        "This is a kid-safe explanation page.",
        "Later this will be real content filtered through your values.",
    ]

    # Log visit in history
    record_history(
        db=db,
        child_id=payload.child_id,
        query=None,
        url=payload.url,
        title=title,
        result_type="article",
    )

    return schemas.PageContent(title=title, text_blocks=text_blocks, media=[])
