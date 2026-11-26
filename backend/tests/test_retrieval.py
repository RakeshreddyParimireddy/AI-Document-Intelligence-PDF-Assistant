"""Retrieval tests: vector search finds the right chunks, and only the user's own."""
from tests.conftest import HANDBOOK_PAGES, INVOICE_PAGES


def search(client, headers, question, **extra):
    return client.post(
        "/api/documents/search", headers=headers, json={"question": question, **extra}
    )


def setup_two_documents(make_user, upload):
    headers = make_user()
    invoice_id = upload(headers, INVOICE_PAGES, "invoice.pdf").json()["id"]
    handbook_id = upload(headers, HANDBOOK_PAGES, "handbook.pdf").json()["id"]
    return headers, invoice_id, handbook_id


def test_finds_the_chunk_with_the_same_meaning(client, make_user, upload):
    headers, _, _ = setup_two_documents(make_user, upload)
    # "vacation" never appears in the documents; "annual leave" does
    results = search(client, headers, "How many vacation days do I get?").json()
    assert results[0]["document"] == "handbook.pdf"
    assert results[0]["page"] == 2
    assert "25 days" in results[0]["content"]


def test_finds_answers_in_the_right_document(client, make_user, upload):
    headers, _, _ = setup_two_documents(make_user, upload)
    top = search(client, headers, "What is the late payment fee?").json()[0]
    assert (top["document"], top["page"]) == ("invoice.pdf", 2)
    top = search(client, headers, "How do I report a lost laptop?").json()[0]
    assert (top["document"], top["page"]) == ("handbook.pdf", 4)


def test_results_are_sorted_by_score_and_limited(client, make_user, upload):
    headers, _, _ = setup_two_documents(make_user, upload)
    results = search(client, headers, "payment").json()
    assert len(results) == 5  # default top 5
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)
    assert len(search(client, headers, "payment", top_k=2).json()) == 2


def test_can_limit_search_to_some_documents(client, make_user, upload):
    headers, invoice_id, _ = setup_two_documents(make_user, upload)
    results = search(client, headers, "vacation days", document_ids=[invoice_id]).json()
    assert results and all(r["document"] == "invoice.pdf" for r in results)


def test_other_users_documents_are_never_searched(client, make_user, upload):
    _, _, handbook_id = setup_two_documents(make_user, upload)
    bob = make_user("bob@example.com")
    assert search(client, bob, "vacation days").json() == []
    response = search(client, bob, "vacation days", document_ids=[handbook_id])
    assert response.status_code == 404


def test_failed_documents_are_not_searched(client, make_user, upload):
    headers = make_user()
    upload(headers, [""], "scanned.pdf")
    assert search(client, headers, "anything").json() == []


def test_search_validates_input(client, make_user):
    headers = make_user()
    assert search(client, headers, "").status_code == 422
    assert search(client, headers, "x", top_k=50).status_code == 422
    assert client.post("/api/documents/search", json={"question": "x"}).status_code == 401
