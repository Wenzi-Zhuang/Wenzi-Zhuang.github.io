"""Per-student conversation history kept inside each NAS course folder."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .auth import CourseSession, current_session
from .auth_routes import allowed
from .services.student_files import list_threads, read_thread, save_thread

router = APIRouter()


class SavedMessage(BaseModel):
    role: str = Field(pattern=r"^(user|assistant)$")
    content: str = Field(min_length=1, max_length=16000)


class ThreadBody(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    messages: list[SavedMessage] = Field(max_length=80)


@router.get("/api/assistants/{assistant_id}/threads")
async def threads(assistant_id: str, session: CourseSession = Depends(current_session)):
    student = session.student_for(assistant_id)
    allowed(assistant_id, student.student_no)
    return {"threads": list_threads(assistant_id, student.student_no)}


@router.get("/api/assistants/{assistant_id}/threads/{thread_id}")
async def thread(assistant_id: str, thread_id: str, session: CourseSession = Depends(current_session)):
    student = session.student_for(assistant_id)
    allowed(assistant_id, student.student_no)
    try:
        data = read_thread(assistant_id, student.student_no, thread_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if not data:
        raise HTTPException(404, "对话不存在")
    return data


@router.put("/api/assistants/{assistant_id}/threads/{thread_id}")
async def put_thread(assistant_id: str, thread_id: str, body: ThreadBody,
                     session: CourseSession = Depends(current_session)):
    student = session.student_for(assistant_id)
    allowed(assistant_id, student.student_no)
    try:
        if not read_thread(assistant_id, student.student_no, thread_id) and len(list_threads(assistant_id, student.student_no)) >= 50:
            raise HTTPException(429, "对话记录已满，请联系教师清理旧对话")
        return save_thread(assistant_id, student.student_no, thread_id, body.title,
                           [item.model_dump() for item in body.messages])
    except ValueError as exc:
        raise HTTPException(413, str(exc)) from exc
