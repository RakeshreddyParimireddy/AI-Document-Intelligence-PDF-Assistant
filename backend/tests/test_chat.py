"""Chat (RAG answer) tests, with the LLM replaced by a fake - no API key, no cost."""
import json
import re
from types import SimpleNamespace

import anthropic
import httpx
import pytest

from app.config import get_settings
from app.services import llm
from tests.conftest import HANDBOOK_PAGES, INVOICE_PAGES


class FakeClaude:
    """Stands in for the Anthropic client. `reply(prompt)` decides what it answers."""

    def __init__(self, reply):
        self.reply = reply
        self.requests = []  # every request sent, so tests can inspect them
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def with_options(self, **kwargs):
        return self

    def _create(self, **kwargs):
        self.requests.append(kwargs)
        data = self.reply(kwargs["messages"][0]["content"])
        if data == "refusal":
            return SimpleNamespace(stop_reason="refusal", content=[])
        text_block = SimpleNamespace(type="text", text=json.dumps(data))
        return SimpleNamespace(stop_reason="end_turn", content=[text_block])


@pytest.fixture
def fake_claude(monkeypatch):
    """Use like: fake = fake_claude(lambda prompt: {...})."""

    def _install(reply):
        fake = FakeClaude(reply)
        monkeypatch.setattr(get_settings(), "llm_provider", "claude")
        monkeypatch.setattr(llm, "get_claude_client", lambda: fake)
        return fake

    return _install


def cite_first_excerpt(prompt):
    return {"found": True, "answer": "Employees get 25 days.", "sources": [1, 1, 99]}


def new_chat(client, headers, document_ids):
    response = client.post("/api/chats", headers=headers, json={"document_ids": document_ids})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def ask(client, headers, chat_id, question):
    return client.post(f"/api/chats/{chat_id}/ask", headers=headers, json={"question": question})


def test_answer_comes_with_citations(client, make_user, upload, fake_claude):
    fake = fake_claude(cite_first_excerpt)
    headers = make_user()
    doc_id = upload(headers, HANDBOOK_PAGES, "handbook.pdf").json()["id"]
    chat_id = new_chat(client, headers, [doc_id])

    response = ask(client, headers, chat_id, "How many vacation days do I get?")
    assert response.status_code == 200
    answer = response.json()
    assert answer["role"] == "assistant"
    assert answer["content"] == "Employees get 25 days."
    # Excerpt 1 = the best match = handbook page 2. Duplicate and invalid (99) numbers are dropped.
    assert len(answer["citations"]) == 1
    citation = answer["citations"][0]
    assert (citation["document"], citation["page"]) == ("handbook.pdf", 2)
    assert "25 days" in citation["snippet"]

    # The prompt holds the retrieved excerpts and the question, and asks for JSON
    request = fake.requests[0]
    assert "How many vacation days" in request["messages"][0]["content"]
    assert "<excerpt number=\"1\"" in request["messages"][0]["content"]
    assert request["output_config"]["format"]["type"] == "json_schema"


def test_not_found_answer(client, make_user, upload, fake_claude):
    fake_claude(lambda prompt: {"found": False, "answer": "", "sources": []})
    headers = make_user()
    chat_id = new_chat(client, headers, [upload(headers, INVOICE_PAGES).json()["id"]])
    answer = ask(client, headers, chat_id, "Who won the World Cup?").json()
    assert answer["content"] == llm.NOT_FOUND_ANSWER
    assert answer["citations"] == []


def test_refusal_gives_a_polite_answer(client, make_user, upload, fake_claude):
    fake_claude(lambda prompt: "refusal")
    headers = make_user()
    chat_id = new_chat(client, headers, [upload(headers, INVOICE_PAGES).json()["id"]])
    assert ask(client, headers, chat_id, "something").json()["content"] == llm.REFUSAL_ANSWER


def test_history_is_saved_and_title_set(client, make_user, upload, fake_claude):
    fake_claude(cite_first_excerpt)
    headers = make_user()
    chat_id = new_chat(client, headers, [upload(headers, HANDBOOK_PAGES).json()["id"]])
    ask(client, headers, chat_id, "How many vacation days?")

    messages = client.get(f"/api/chats/{chat_id}/messages", headers=headers).json()
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "How many vacation days?"
    chats = client.get("/api/chats", headers=headers).json()
    assert chats[0]["title"] == "How many vacation days?"


def test_multi_document_chat_searches_all_its_documents(client, make_user, upload, fake_claude):
    # Cite every excerpt, so we can see which documents were retrieved
    def cite_all(prompt):
        count = len(re.findall(r"<excerpt number=", prompt))
        return {"found": True, "answer": "ok", "sources": list(range(1, count + 1))}

    fake_claude(cite_all)
    headers = make_user()
    invoice_id = upload(headers, INVOICE_PAGES, "invoice.pdf").json()["id"]
    handbook_id = upload(headers, HANDBOOK_PAGES, "handbook.pdf").json()["id"]
    chat_id = new_chat(client, headers, [invoice_id, handbook_id])

    answer = ask(client, headers, chat_id, "When is payment due and how many vacation days?").json()
    cited_documents = {c["document"] for c in answer["citations"]}
    assert cited_documents == {"invoice.pdf", "handbook.pdf"}


def test_missing_api_key_gives_503_and_saves_nothing(client, make_user, upload):
    # No fake installed: the real client is used, and LLM_API_KEY is empty in tests
    headers = make_user()
    chat_id = new_chat(client, headers, [upload(headers, INVOICE_PAGES).json()["id"]])
    response = ask(client, headers, chat_id, "What is the total?")
    assert response.status_code == 503
    assert client.get(f"/api/chats/{chat_id}/messages", headers=headers).json() == []


def test_llm_failure_gives_502(client, make_user, upload, fake_claude):
    def broken(prompt):
        request = httpx.Request("POST", "https://api.anthropic.com")
        raise anthropic.APIConnectionError(request=request)

    fake_claude(broken)
    headers = make_user()
    chat_id = new_chat(client, headers, [upload(headers, INVOICE_PAGES).json()["id"]])
    assert ask(client, headers, chat_id, "What is the total?").status_code == 502


def test_users_cannot_use_other_users_chats_or_documents(client, make_user, upload, fake_claude):
    fake_claude(cite_first_excerpt)
    alice, bob = make_user("alice@example.com"), make_user("bob@example.com")
    doc_id = upload(alice, INVOICE_PAGES).json()["id"]
    chat_id = new_chat(client, alice, [doc_id])

    assert client.post("/api/chats", headers=bob, json={"document_ids": [doc_id]}).status_code == 404
    assert client.get(f"/api/chats/{chat_id}/messages", headers=bob).status_code == 404
    assert ask(client, bob, chat_id, "What is the total?").status_code == 404
    assert client.get("/api/chats", headers=bob).json() == []
