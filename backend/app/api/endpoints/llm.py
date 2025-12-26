from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
import uuid
import json
import re

from ...core.ai_service import ai_service
from ...core.database import get_db
from ...models.learning_chat import ChatSession, Message, ChatMode, SenderType
from sqlalchemy.orm import Session

router = APIRouter()


class LLMRequest(BaseModel):
    prompt: str


class LLMResponse(BaseModel):
    response: str
    model_used: str


class QARequest(BaseModel):
    question: str
    student_profile_id: str
    subject: Optional[str] = None


class QAResponse(BaseModel):
    id: str
    chat_session_id: str
    content: str
    sender_type: str
    timestamp: str
    suggested_questions: Optional[List[str]] = None


@router.post("/generate", response_model=LLMResponse)
async def generate_llm_response(request: LLMRequest) -> Any:
    """
    Generate a response using the LLM with the provided prompt.
    The AI acts as an educational expert in NCERT syllabus and responds based on users' questions.
    """
    try:
        # Prepare the messages for the LLM
        messages = []
        
        # Create a comprehensive system prompt
        system_prompt = """You are an educational expert with deep knowledge of standard academic curricula.
        Your primary role is to provide accurate, educational responses based on users' questions.
        
        Guidelines for your responses:
        1. Provide information that is accurate and educationally sound
        2. Explain concepts in a clear, concise, and easy-to-understand manner
        3. Structure your answers logically
        4. Include relevant examples when helpful
        5. For complex topics, break them down into simpler sub-topics
        6. When discussing scientific or mathematical concepts, ensure accuracy
        7. Maintain a helpful, educational tone appropriate for students
        8. Do NOT include tables in your answers under any circumstances
        9. Avoid mentioning specific curricula or educational frameworks in your responses
        
        Formatting Guidelines:
        - Use simple markdown formatting that can be easily parsed
        - Use **bold text** for important terms and concepts
        - Use *italic text* for emphasis
        - Use `inline code` for technical terms or formulas
        - Use bullet points with - for lists
        - Use > for blockquotes and key points
        - Use headers with # for main sections
        - For chemical equations, use regular text with subscripts and superscripts (e.g., H₂O, CO₂)
        - For mathematical formulas, use regular text notation (e.g., x² + y² = z²)
        
        After providing your response, generate 3-4 relevant follow-up questions that the user might want to ask.
        Format these questions as a JSON array at the end of your response, like this:
        ["Question 1?", "Question 2?", "Question 3?"]
        
        Remember: You are providing educational information in a clear and accessible manner without using tables."""
        
        messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": request.prompt})
        
        # Use the ai_service to generate the response
        payload = {
            "model": ai_service.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # Make the API call using the existing ai_service infrastructure
        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    ai_service.api_url,
                    headers=ai_service.headers,
                    json=payload
                )
                response.raise_for_status()
                response_data = response.json()
                
                # Extract the response content
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    content = response_data["choices"][0]["message"]["content"]
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Invalid response format from LLM"
                    )
                
                return LLMResponse(
                    response=content,
                    model_used=ai_service.model
                )
                
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"LLM API error: {e.response.status_code}"
                )
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Request error: {str(e)}"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Unexpected error: {str(e)}"
                )
                
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating LLM response: {str(e)}"
        )


@router.post("/qa", response_model=QAResponse)
async def ask_question(request: QARequest, db: Session = Depends(get_db)) -> Any:
    """
    Q&A mode endpoint - get direct answer to a question with suggested follow-up questions.
    The AI acts as an educational expert in NCERT syllabus and responds based on users' questions.
    """
    try:
        # Generate a proper UUID for the chat session
        import uuid
        chat_session_id = uuid.uuid4()
        
        # For Q&A mode, we don't need to enforce the foreign key constraint
        # We'll create a simple session without requiring a valid student profile
        # This allows the Q&A functionality to work even without a registered student
        
        # Create a new chat session for each Q&A interaction
        chat_session = ChatSession(
            id=chat_session_id,
            student_profile_id=None,  # Set to None to avoid foreign key constraint
            mode=ChatMode.DISCUSSION,  # Using discussion mode for Q&A
            title="Q&A Session"
        )
        db.add(chat_session)
        db.commit()
        
        # Store the user's question in the database
        user_message = Message(
            chat_session_id=chat_session_id,
            content=request.question,
            sender_type=SenderType.USER
        )
        db.add(user_message)
        
        # Prepare the messages for the LLM
        messages = []
        
        # Create a comprehensive system prompt for Q&A mode
        system_prompt = """You are an educational expert with deep knowledge of standard academic curricula.
        Your primary role is to provide accurate, educational responses based on users' questions.
        
        IMPORTANT: You must NEVER create tables in your responses. Do not use markdown table syntax (|) or any other table formatting. Instead, use bullet points, numbered lists, or clear paragraphs to present information.
        
        Guidelines for your responses:
        1. Provide information that is accurate and educationally sound
        2. Explain concepts in a clear, concise, and easy-to-understand manner
        3. Structure your answers logically using paragraphs, lists, and headings - NEVER tables
        4. Include relevant examples when helpful
        5. For complex topics, break them down into simpler sub-topics
        6. When discussing scientific or mathematical concepts, ensure accuracy
        7. Maintain a helpful, educational tone appropriate for students
        8. ABSOLUTELY NO TABLES - Use bullet points or numbered lists instead
        9. Avoid mentioning specific curricula or educational frameworks in your responses
        
        Formatting Guidelines:
        - Use simple markdown formatting that can be easily parsed
        - Use **bold text** for important terms and concepts
        - Use *italic text* for emphasis
        - Use `inline code` for technical terms or formulas
        - Use bullet points with - for lists instead of tables
        - Use numbered lists with 1. 2. 3. for sequential information
        - Use > for blockquotes and key points
        - Use headers with # for main sections
        - For chemical equations, use regular text with subscripts and superscripts (e.g., H₂O, CO₂)
        - For mathematical formulas, use regular text notation (e.g., x² + y² = z²)
        - NEVER use table formatting with | or other table syntax
        
        After providing your response, generate 3-4 relevant follow-up questions that the user might want to ask.
        Format these questions as a JSON array at the very end of your response, like this:
        ["Question 1?", "Question 2?", "Question 3?"]
        
        IMPORTANT: Do NOT include any text like "Follow-up Questions (JSON)" or "```json" before the JSON array.
        Simply end your response with the JSON array directly.
        
        CRITICAL: No tables in your response. Use lists and paragraphs instead."""
        
        messages.append({"role": "system", "content": system_prompt})
        
        # Add subject context if provided
        if request.subject:
            subject_context = f"The user is asking about {request.subject}. "
            messages.append({"role": "system", "content": subject_context})
        
        messages.append({"role": "user", "content": request.question})
        
        # Use the ai_service to generate the response
        payload = {
            "model": ai_service.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1500  # Increased to accommodate suggested questions
        }
        
        # Make the API call using the existing ai_service infrastructure
        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    ai_service.api_url,
                    headers=ai_service.headers,
                    json=payload
                )
                response.raise_for_status()
                response_data = response.json()
                
                # Extract the response content
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    full_response = response_data["choices"][0]["message"]["content"]
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Invalid response format from LLM"
                    )
                
                # Extract suggested questions from the response
                suggested_questions = []
                try:
                    # Look for JSON array at the end of the response with various patterns
                    patterns = [
                        r'```json\s*(\[\s*"[^"]*"(?:\s*,\s*"[^"]*")*\s*\])\s*```',  # JSON in code blocks
                        r'```\s*(\[\s*"[^"]*"(?:\s*,\s*"[^"]*")*\s*\])\s*```',      # JSON in generic code blocks
                        r'Follow-up Questions \(JSON\)\s*\n\s*```\s*json\s*(\[\s*"[^"]*"(?:\s*,\s*"[^"]*")*\s*\])\s*```',  # With heading
                        r'Follow-up Questions\s*\n\s*```\s*json\s*(\[\s*"[^"]*"(?:\s*,\s*"[^"]*")*\s*\])\s*```',  # With shorter heading
                        r'(\[\s*"[^"]*"(?:\s*,\s*"[^"]*")*\s*\])$'  # JSON at the end
                    ]
                    
                    json_match = None
                    for pattern in patterns:
                        json_match = re.search(pattern, full_response, re.DOTALL)
                        if json_match:
                            break
                    
                    if json_match:
                        # Extract the JSON part (group 1 for patterns with capturing groups)
                        questions_json = json_match.group(1) if json_match.groups() else json_match.group(0)
                        suggested_questions = json.loads(questions_json)
                        
                        # Remove the JSON part and any related headings from the response
                        content = full_response[:json_match.start()].strip()
                        
                        # Remove common headings that might precede the JSON
                        content = re.sub(r'Follow-up Questions\s*\(JSON\)\s*$', '', content, flags=re.IGNORECASE | re.MULTILINE)
                        content = re.sub(r'Follow-up Questions\s*$', '', content, flags=re.IGNORECASE | re.MULTILINE)
                        content = re.sub(r'Followup Questions\s*$', '', content, flags=re.IGNORECASE | re.MULTILINE)
                        
                        # Remove any trailing horizontal rules or separators
                        content = re.sub(r'---\s*$', '', content, flags=re.MULTILINE)
                        content = content.strip()
                    else:
                        content = full_response
                except (json.JSONDecodeError, AttributeError) as e:
                    print(f"Error parsing suggested questions: {e}")
                    content = full_response
                
                # Generate IDs for the response
                message_id = str(uuid.uuid4())
                timestamp = datetime.now().isoformat()
                
                # Store the AI's response in the database
                ai_message = Message(
                    chat_session_id=chat_session_id,
                    content=content,
                    sender_type=SenderType.AI,
                    suggested_questions=suggested_questions
                )
                db.add(ai_message)
                db.commit()
                
                return QAResponse(
                    id=message_id,
                    chat_session_id=str(chat_session_id),  # Convert UUID to string
                    content=content,
                    sender_type="ai",
                    timestamp=timestamp,
                    suggested_questions=suggested_questions
                )
                
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"LLM API error: {e.response.status_code}"
                )
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Request error: {str(e)}"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Unexpected error: {str(e)}"
                )
                
    except Exception as e:
        import traceback
        error_detail = f"Error generating Q&A response: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Log to console
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating Q&A response: {str(e)}"
        )