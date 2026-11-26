"""Summary tests (fake LLM): the text comes from the saved pages, not the PDF file."""
import json
from types import SimpleNamespace

from app.services import llm
from tests.conftest import INVOICE_PAGES


class FakeClaude:
    def __init__(self):
        self.prompts = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def with_options(self, **kwargs):
        return self

    def _create(self, **kwargs):
        self.prompts.append(kwargs["messages"][0]["content"])
        data = {"summary": "An invoice from ACME.", "key_points": ["Total $14,850.00"]}
        return SimpleNamespace(
            stop_reason="end_turn", content=[SimpleNamespace(type="text", text=json.dumps(data))]
        )


def test_summary_works_after_the_pdf_file_is_gone(client, make_user, upload, monkeypatch):
    fake = FakeClaude()
    monkeypatch.setattr(llm, "get_client", lambda: fake)
    headers = make_user()
    doc_id = upload(headers, INVOICE_PAGES, "invoice.pdf").json()["id"]

    response = client.post(f"/api/documents/{doc_id}/summarize", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["summary"] == "An invoice from ACME."
    # All 3 pages were sent, with their page numbers
    prompt = fake.prompts[0]
    assert '<page number="1">' in prompt and '<page number="3">' in prompt
    assert "$14,850.00" in prompt
