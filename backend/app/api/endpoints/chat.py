from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...api.deps import get_current_user
from ...core.ai_service import ai_service
from ...models.user_management import User, StudentProfile, ParentStudentRelation
from ...models.learning_chat import ChatSession, Message
from ...schemas.learning_chat import (
    ChatSessionCreate, ChatSessionResponse, ChatSessionWithMessages,
    MessageCreate, MessageResponse
)

router = APIRouter()


@router.get("/sessions", response_model=List[ChatSessionResponse])
def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List all chat sessions for the user.
    """
    chat_sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).all()
    
    return chat_sessions


@router.post("/sessions", response_model=ChatSessionResponse)
def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create new session (QA, Discussion, Revision).
    """
    # Verify student profile exists and user has access
    student_profile = db.query(StudentProfile).filter(
        StudentProfile.id == session_data.student_profile_id
    ).first()
    
    if not student_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    # Check if user has access to this student profile
    if current_user.user_type == "parent":
        is_linked = db.query(ParentStudentRelation).filter(
            ParentStudentRelation.parent_id == current_user.id,
            ParentStudentRelation.student_profile_id == session_data.student_profile_id
        ).first()
        
        if not is_linked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not linked to this student"
            )
    elif current_user.user_type == "student":
        if student_profile.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create sessions for your own profile"
            )
    
    # Create chat session
    chat_session = ChatSession(
        user_id=current_user.id,
        student_profile_id=session_data.student_profile_id,
        mode=session_data.mode,
        title=session_data.title
    )
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)
    
    return chat_session


@router.get("/sessions/{id}", response_model=ChatSessionWithMessages)
def get_chat_session(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get session details and messages.
    """
    # Get chat session
    chat_session = db.query(ChatSession).filter(
        ChatSession.id == id
    ).first()
    
    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Check if user has access to this session
    if chat_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this session"
        )
    
    return chat_session


@router.get("/sessions/{id}/messages", response_model=List[MessageResponse])
def get_chat_messages(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get message history for a session.
    """
    # Get chat session
    chat_session = db.query(ChatSession).filter(
        ChatSession.id == id
    ).first()
    
    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Check if user has access to this session
    if chat_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this session"
        )
    
    # Get messages
    messages = db.query(Message).filter(
        Message.chat_session_id == id
    ).order_by(Message.timestamp).all()
    
    return messages


@router.post("/sessions/{id}/messages", response_model=MessageResponse)
async def send_message(
    id: str,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Send user message and get AI response.
    """
    # Get chat session
    chat_session = db.query(ChatSession).filter(
        ChatSession.id == id
    ).first()
    
    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Check if user has access to this session
    if chat_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this session"
        )
    
    # Create user message
    user_message = Message(
        chat_session_id=id,
        content=message_data.content,
        sender_type="user"
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # Get chat history for context
    chat_history = db.query(Message).filter(
        Message.chat_session_id == id
    ).order_by(Message.timestamp).limit(10).all()
    
    # Format chat history for AI
    formatted_history = []
    for msg in chat_history:
        role = "user" if msg.sender_type == "user" else "assistant"
        formatted_history.append({"role": role, "content": msg.content})
    
    # Create system prompt based on chat mode
    system_prompt = "You are an AI educational assistant for a school chat application. "
    
    if chat_session.mode == "qa":
        system_prompt += "Provide clear, accurate, and educational answers to questions. "
    elif chat_session.mode == "quiz":
        system_prompt += "Help the student learn by asking questions and providing feedback. "
    elif chat_session.mode == "planner":
        system_prompt += "Help the student plan their study schedule and tasks. "
    elif chat_session.mode == "discussion":
        system_prompt += "Engage in thoughtful discussion about the topic. "
    
    system_prompt += "Keep your responses educational, age-appropriate, and concise."
    
    # Get AI response
    ai_response = await ai_service.generate_chat_response(
        message=message_data.content,
        chat_history=formatted_history,
        system_prompt=system_prompt
    )
    
    # Check for errors
    if "error" in ai_response:
        # Create a fallback response
        ai_response_content = "I'm sorry, I'm having trouble responding right now. Please try again later."
        suggested_questions = []
    else:
        # Extract AI response content
        try:
            ai_response_content = ai_response["choices"][0]["message"]["content"]
            
            # Generate suggested follow-up questions
            suggested_questions = [
                "Can you explain this in more detail?",
                "How does this relate to other topics we've studied?",
                "Can you provide an example of this concept?"
            ]
        except (KeyError, IndexError):
            ai_response_content = "I'm sorry, I couldn't generate a proper response. Please try again."
            suggested_questions = []
    
    # Create AI message
    ai_message = Message(
        chat_session_id=id,
        content=ai_response_content,
        sender_type="ai",
        suggested_questions=suggested_questions
    )
    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)
    
    # Update chat session timestamp
    from datetime import datetime
    chat_session.updated_at = datetime.utcnow()
    db.commit()
    
    return user_message