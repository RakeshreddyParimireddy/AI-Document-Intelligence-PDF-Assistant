"""Turn LLM errors into clear HTTP errors (shared by the chat and insights routes)."""
from fastapi import HTTPException

from app.services import llm


def run_llm(task):
    """Run an LLM task, e.g. run_llm(lambda: llm.answer_question(...))."""
    try:
        return task()
    except llm.LLMNotConfiguredError:
        raise HTTPException(
            status_code=503, detail="The AI isn't set up on this server yet (LLM_API_KEY is missing)."
        )
    except llm.LLMRateLimitError:
        raise HTTPException(
            status_code=429,
            detail="The AI is busy right now (free plan limit). Please try again in a minute.",
        )
    except llm.LLMServiceError:
        raise HTTPException(status_code=502, detail="The AI service failed. Please try again.")
