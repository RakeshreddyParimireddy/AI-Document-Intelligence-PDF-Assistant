"""Gemini provider tests, with a fake Gemini client - no API key, no cost."""
import json
from types import SimpleNamespace

import pytest
from google.genai import errors as genai_errors
from google.genai import types as genai_types

from app.config import get_settings
from app.services import llm
from tests.conftest import HANDBOOK_PAGES, INVOICE_PAGES


class FakeGemini:
    """Stands in for google.genai.Client. `reply(prompt)` returns a dict, or a special string."""

    def __init__(self, reply):
        self.reply = reply
        self.requests = []  # every request sent, so tests can inspect them
        self.models = SimpleNamespace(generate_content=self._generate_content)

    def _generate_content(self, *, model, contents, config):
        self.requests.append({"model": model, "contents": contents, "config": config})
        data = self.reply(contents)
        if data == "rate-limited":
            raise genai_errors.ClientError(
                429, {"error": {"message": "quota exceeded", "status": "RESOURCE_EXHAUSTED"}}
            )
        if data == "server-error":
            raise genai_errors.ServerError(500, {"error": {"message": "boom", "status": "INTERNAL"}})
        if data == "blocked":
            return SimpleNamespace(
                prompt_feedback=None,
                candidates=[SimpleNamespace(finish_reason=genai_types.FinishReason.SAFETY)],
                text=None,
            )
        return SimpleNamespace(
            prompt_feedback=None,
            candidates=[SimpleNamespace(finish_reason=genai_types.FinishReason.STOP)],
            text=json.dumps(data),
        )


@pytest.fixture
def fake_gemini(monkeypatch):
    """Use like: fake = fake_gemini(lambda prompt: {...})."""

    def _install(reply):
        fake = FakeGemini(reply)
        monkeypatch.setattr(get_settings(), "llm_provider", "gemini")
        monkeypatch.setattr(get_settings(), "llm_model", "")
        monkeypatch.setattr(llm, "get_gemini_client", lambda: fake)
        return fake

    return _install


def new_chat_with(client, headers, upload, pages, name="doc.pdf"):
    doc_id = upload(headers, pages, name).json()["id"]
    response = client.post("/api/chats", headers=headers, json={"document_ids": [doc_id]})
    return response.json()["id"], doc_id


def ask(client, headers, chat_id, question):
    return client.post(f"/api/chats/{chat_id}/ask", headers=headers, json={"question": question})


def test_answer_with_citations(client, make_user, upload, fake_gemini):
    fake = fake_gemini(lambda prompt: {"found": True, "answer": "25 days.", "sources": [1, 1, 42]})
    headers = make_user()
    chat_id, _ = new_chat_with(client, headers, upload, HANDBOOK_PAGES, "handbook.pdf")

    answer = ask(client, headers, chat_id, "How many vacation days do I get?").json()
    assert answer["content"] == "25 days."
    # Duplicate and invalid (42) excerpt numbers are dropped; excerpt 1 = handbook page 2
    assert [(c["document"], c["page"]) for c in answer["citations"]] == [("handbook.pdf", 2)]

    request = fake.requests[0]
    assert request["model"] == llm.DEFAULT_MODELS["gemini"]
    assert "How many vacation days" in request["contents"]
    assert request["config"].response_mime_type == "application/json"
    assert request["config"].response_json_schema == llm.ANSWER_SCHEMA
    assert request["config"].system_instruction == llm.ANSWER_SYSTEM_PROMPT
    assert request["config"].http_options.timeout == 120_000  # milliseconds


def test_not_found(client, make_user, upload, fake_gemini):
    fake_gemini(lambda prompt: {"found": False, "answer": "", "sources": []})
    headers = make_user()
    chat_id, _ = new_chat_with(client, headers, upload, INVOICE_PAGES)
    answer = ask(client, headers, chat_id, "Who won the World Cup?").json()
    assert answer["content"] == llm.NOT_FOUND_ANSWER
    assert answer["citations"] == []


def test_blocked_reply_gives_a_polite_answer(client, make_user, upload, fake_gemini):
    fake_gemini(lambda prompt: "blocked")
    headers = make_user()
    chat_id, _ = new_chat_with(client, headers, upload, INVOICE_PAGES)
    assert ask(client, headers, chat_id, "something").json()["content"] == llm.REFUSAL_ANSWER


def test_rate_limit_gives_429_with_a_friendly_message(client, make_user, upload, fake_gemini):
    fake_gemini(lambda prompt: "rate-limited")
    headers = make_user()
    chat_id, doc_id = new_chat_with(client, headers, upload, INVOICE_PAGES)

    response = ask(client, headers, chat_id, "What is the total?")
    assert response.status_code == 429
    assert "try again in a minute" in response.json()["detail"]
    # The whole-document tasks get the same treatment
    assert client.post(f"/api/documents/{doc_id}/summarize", headers=headers).status_code == 429
    # Nothing was saved for the failed question
    assert client.get(f"/api/chats/{chat_id}/messages", headers=headers).json() == []


def test_server_error_gives_502(client, make_user, upload, fake_gemini):
    fake_gemini(lambda prompt: "server-error")
    headers = make_user()
    chat_id, _ = new_chat_with(client, headers, upload, INVOICE_PAGES)
    assert ask(client, headers, chat_id, "What is the total?").status_code == 502


def test_summary_and_extract(client, make_user, upload, fake_gemini):
    def reply(prompt):
        if "Fields to extract" in prompt:
            return {"results": [
                {"field": "Total amount", "found": True, "value": "$14,850.00", "page": 1},
                {"field": "Ship date", "found": False, "value": "", "page": 0},
            ]}
        return {"summary": "An invoice from ACME.", "key_points": ["Total $14,850.00"]}

    fake = fake_gemini(reply)
    headers = make_user()
    _, doc_id = new_chat_with(client, headers, upload, INVOICE_PAGES, "invoice.pdf")

    summary = client.post(f"/api/documents/{doc_id}/summarize", headers=headers).json()
    assert summary["summary"] == "An invoice from ACME."
    assert fake.requests[0]["config"].http_options.timeout == llm.LONG_TASK_TIMEOUT * 1000

    rows = client.post(
        f"/api/documents/{doc_id}/extract",
        headers=headers,
        json={"fields": ["Total amount", "Ship date"]},
    ).json()["results"]
    assert rows == [
        {"field": "Total amount", "value": "$14,850.00", "page": 1},
        {"field": "Ship date", "value": None, "page": None},
    ]


def test_custom_model_is_used(client, make_user, upload, fake_gemini, monkeypatch):
    fake = fake_gemini(lambda prompt: {"found": False, "answer": "", "sources": []})
    monkeypatch.setattr(get_settings(), "llm_model", "gemini-3.8-flash")
    headers = make_user()
    chat_id, _ = new_chat_with(client, headers, upload, INVOICE_PAGES)
    ask(client, headers, chat_id, "anything")
    assert fake.requests[0]["model"] == "gemini-3.8-flash"
