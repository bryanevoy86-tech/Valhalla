import pytest

def test_research_models_importable():
    # Ensure DB models exist for research persistence
    from app.models.research import ResearchSource, ResearchPlaybook
    assert getattr(ResearchSource, "__tablename__", None) == "research_sources"
    assert getattr(ResearchPlaybook, "__tablename__", None) == "research_playbooks"
