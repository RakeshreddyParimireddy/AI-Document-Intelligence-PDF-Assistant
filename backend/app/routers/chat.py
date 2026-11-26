"""Chat routes: create a chat over some documents, ask questions, see history."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Chat, ChatDocument, Document, Message, User
from app.schemas import AskRequest, ChatCreate, ChatOut, Citation, MessageOut
from app.services import llm
from app.services.retriever import search_chunks

router = APIRouter(prefix="/api/chats", tags=["chat"])

DEFAULT_TITLE = "New chat"
SNIPPET_CHARS = 300  # how much of a chunk to show in a citation
TOP_K_SINGLE = 5  # chunks sent to the LLM for a one-document chat
TOP_K_MULTI = 8  # ...and for a multi-document chat


def get_own_chat(chat_id: int, user: User, db: Session) -> Chat:
    chat = db.scalar(select(Chat).where(Chat.id == chat_id, Chat.user_id == user.id))
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


def chat_document_ids(chat: Chat, db: Session) -> list[int]:
    return list(
        db.scalars(select(ChatDocument.document_id).where(ChatDocument.chat_id == chat.id))
    )


def to_chat_out(chat: Chat, db: Session) -> ChatOut:
    return ChatOut(
        id=chat.id,
        title=chat.title,
        created_at=chat.created_at,
        document_ids=chat_document_ids(chat, db),
    )


@router.post("", response_model=ChatOut, status_code=status.HTTP_201_CREATED)
def create_chat(
    body: ChatCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document_ids = list(dict.fromkeys(body.document_ids))  # remove duplicates
    owned = set(
        db.scalars(
            select(Document.id).where(
                Document.id.in_(document_ids), Document.user_id == current_user.id
            )
        )
    )
    if owned != set(document_ids):
        raise HTTPException(status_code=404, detail="Document not found")

    chat = Chat(user_id=current_user.id, title=body.title or DEFAULT_TITLE)
    db.add(chat)
    db.flush()  # gives chat an id before we link documents
    db.add_all(ChatDocument(chat_id=chat.id, document_id=doc_id) for doc_id in document_ids)
    db.commit()
    db.refresh(chat)
    return to_chat_out(chat, db)


@router.get("", response_model=list[ChatOut])
def list_chats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chats = db.scalars(
        select(Chat).where(Chat.user_id == current_user.id).order_by(Chat.created_at.desc())
    ).all()
    return [to_chat_out(chat, db) for chat in chats]


@router.get("/{chat_id}/messages", response_model=list[MessageOut])
def list_messages(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = get_own_chat(chat_id, current_user, db)
    return db.scalars(
        select(Message).where(Message.chat_id == chat.id).order_by(Message.id)
    ).all()


@router.post("/{chat_id}/ask", response_model=MessageOut)
def ask(
    chat_id: int,
    body: AskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """RAG: find relevant chunks, ask the LLM to answer from them, return answer + citations."""
    chat = get_own_chat(chat_id, current_user, db)
    question = body.question.strip()

    # 1. Retrieve: the chunks closest in meaning to the question.
    #    Across several documents we take a few more, so one document can't fill every slot.
    document_ids = chat_document_ids(chat, db)
    top_k = TOP_K_SINGLE if len(document_ids) <= 1 else TOP_K_MULTI
    chunks = (
        search_chunks(db, current_user.id, question, document_ids, top_k) if document_ids else []
    )

    # 2. Generate: let the LLM answer using only those chunks
    if not chunks:
        # Nothing to search (e.g. documents deleted or still processing)
        answer, citations = llm.NOT_FOUND_ANSWER, []
    else:
        try:
            result = llm.answer_question(question, chunks)
        except llm.LLMNotConfiguredError:
            raise HTTPException(
                status_code=503, detail="The AI is not configured: set LLM_API_KEY in .env"
            )
        except llm.LLMServiceError:
            raise HTTPException(
                status_code=502, detail="The AI service failed. Please try again."
            )
        answer = result.answer
        citations = [
            Citation(
                document_id=chunks[n - 1].document_id,
                document=chunks[n - 1].filename,
                page=chunks[n - 1].page_number,
                snippet=chunks[n - 1].content[:SNIPPET_CHARS],
            ).model_dump()
            for n in result.source_numbers
        ]

    # 3. Save both messages so the chat history can be shown later
    if chat.title == DEFAULT_TITLE:
        chat.title = question[:60]
    db.add(Message(chat_id=chat.id, role="user", content=question, citations=[]))
    assistant_message = Message(
        chat_id=chat.id, role="assistant", content=answer, citations=citations
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    return assistant_message
