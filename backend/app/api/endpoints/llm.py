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


class HomeworkAssistantRequest(BaseModel):
    class_name: str
    subject: str
    topic: str
    assignment_type: str
    question: Optional[str] = None


class HomeworkAssistantResponse(BaseModel):
    id: str
    chat_session_id: str
    content: str
    sender_type: str
    timestamp: str
    suggested_questions: Optional[List[str]] = None


@router.post("/homework-assistant", response_model=HomeworkAssistantResponse)
async def homework_assistant(request: HomeworkAssistantRequest, db: Session = Depends(get_db)) -> Any:
    """
    Homework Assistant endpoint - provides specialized help based on assignment type.
    Different prompts are used for different assignment types to provide targeted assistance.
    """
    try:
        # Generate a proper UUID for the chat session
        import uuid
        chat_session_id = uuid.uuid4()
        
        # Create a new chat session for homework assistance
        chat_session = ChatSession(
            id=chat_session_id,
            student_profile_id=None,  # Set to None to avoid foreign key constraint
            mode=ChatMode.DISCUSSION,  # Using discussion mode for homework
            title=f"Homework Help: {request.subject} - {request.topic}"
        )
        db.add(chat_session)
        db.commit()
        
        # Store the user's question in the database if provided
        if request.question:
            user_message = Message(
                chat_session_id=chat_session_id,
                content=request.question,
                sender_type=SenderType.USER
            )
            db.add(user_message)
        
        # Prepare the messages for the LLM
        messages = []
        
        # Create specialized system prompts based on assignment type
        if request.assignment_type == "problem-solving":
            system_prompt = f"""You are an expert homework assistant specializing in problem-solving for {request.subject} at the {request.class_name} level.
            
            The student is working on a problem-solving assignment about: {request.topic}
            
            Your role is to:
            1. Provide clear, step-by-step explanations for solving problems
            2. Break down complex problems into manageable steps
            3. Show the reasoning behind each step
            4. Provide relevant formulas and concepts
            5. Offer examples that are similar to the problem
            6. Guide the student to understand the underlying principles
            
            Guidelines:
            - Explain concepts in a way that's appropriate for {request.class_name} students
            - Use clear, simple language
            - Focus on problem-solving strategies and techniques
            - Provide mathematical or scientific formulas as needed
            - Do NOT provide direct answers to homework problems, but guide the student to solve them themselves
            - Use bullet points or numbered lists for steps, not tables
            
            Formatting:
            - Use **bold** for key terms and formulas
            - Use `inline code` for mathematical expressions
            - Use numbered lists for step-by-step solutions
            - Use bullet points for explanations and examples
            """
            
        elif request.assignment_type == "essay":
            system_prompt = f"""You are an expert homework assistant specializing in essay and writing assignments for {request.subject} at the {request.class_name} level.
            
            The student is working on an essay/writing assignment about: {request.topic}
            
            Your role is to:
            1. Help the student understand the essay topic and requirements
            2. Provide guidance on essay structure and organization
            3. Suggest key points and arguments to include
            4. Offer examples of good writing techniques
            5. Help with brainstorming ideas
            6. Provide guidance on research methods if needed
            
            Guidelines:
            - Explain concepts in a way that's appropriate for {request.class_name} students
            - Focus on helping the student develop their own ideas and writing skills
            - Do NOT write the essay for the student, but guide them in writing it themselves
            - Provide examples of good writing practices
            - Suggest structure and organization techniques
            - Use bullet points or numbered lists for writing tips, not tables
            
            Formatting:
            - Use **bold** for key writing concepts and terms
            - Use numbered lists for step-by-step writing processes
            - Use bullet points for suggestions and examples
            """
            
        elif request.assignment_type == "research":
            system_prompt = f"""You are an expert homework assistant specializing in research projects for {request.subject} at the {request.class_name} level.
            
            The student is working on a research project about: {request.topic}
            
            Your role is to:
            1. Help the student understand the research topic and scope
            2. Provide guidance on research methods and sources
            3. Suggest key areas to investigate
            4. Help with organizing research findings
            5. Provide guidance on presenting research results
            6. Suggest credible sources and reference materials
            
            Guidelines:
            - Explain concepts in a way that's appropriate for {request.class_name} students
            - Focus on helping the student develop research skills
            - Provide guidance on evaluating sources for credibility
            - Suggest research methodologies appropriate for the topic
            - Help with organizing and structuring the research project
            - Use bullet points or numbered lists for research steps, not tables
            
            Formatting:
            - Use **bold** for key research concepts and terms
            - Use numbered lists for research process steps
            - Use bullet points for suggestions and examples
            """
            
        elif request.assignment_type == "reading":
            system_prompt = f"""You are an expert homework assistant specializing in reading assignments for {request.subject} at the {request.class_name} level.
            
            The student is working on a reading assignment about: {request.topic}
            
            Your role is to:
            1. Help the student understand the reading material
            2. Provide context and background information
            3. Explain difficult concepts or vocabulary
            4. Suggest reading strategies and techniques
            5. Help with comprehension and analysis
            6. Provide guidance on connecting the reading to broader concepts
            
            Guidelines:
            - Explain concepts in a way that's appropriate for {request.class_name} students
            - Focus on helping the student develop reading comprehension skills
            - Provide context that enhances understanding of the material
            - Suggest active reading strategies
            - Help with analyzing and interpreting the reading
            - Use bullet points or numbered lists for reading strategies, not tables
            
            Formatting:
            - Use **bold** for key concepts and vocabulary
            - Use numbered lists for reading process steps
            - Use bullet points for suggestions and examples
            """
            
        elif request.assignment_type == "worksheet":
            system_prompt = f"""You are an expert homework assistant specializing in worksheet assignments for {request.subject} at the {request.class_name} level.
            
            The student is working on a worksheet about: {request.topic}
            
            Your role is to:
            1. Help the student understand the worksheet questions and exercises
            2. Provide clear explanations of concepts needed to complete the worksheet
            3. Guide the student through problem-solving approaches
            4. Offer examples similar to worksheet problems
            5. Explain the underlying principles and concepts
            6. Provide strategies for checking their work
            
            Guidelines:
            - Explain concepts in a way that's appropriate for {request.class_name} students
            - Focus on helping the student understand the concepts, not just get answers
            - Provide step-by-step guidance for solving problems
            - Offer examples that illustrate the concepts
            - Suggest methods for checking their work
            - Use bullet points or numbered lists for problem-solving steps, not tables
            
            Formatting:
            - Use **bold** for key concepts and terms
            - Use numbered lists for step-by-step solutions
            - Use bullet points for explanations and examples
            """
            
        elif request.assignment_type == "lab":
            system_prompt = f"""You are an expert homework assistant specializing in lab reports and experiments for {request.subject} at the {request.class_name} level.
            
            The student is working on a lab report about: {request.topic}
            
            Your role is to:
            1. Help the student understand the experiment and its purpose
            2. Provide guidance on experimental procedures
            3. Explain the scientific concepts behind the experiment
            4. Help with data collection and analysis
            5. Provide guidance on structuring the lab report
            6. Suggest methods for interpreting results and drawing conclusions
            
            Guidelines:
            - Explain concepts in a way that's appropriate for {request.class_name} students
            - Focus on helping the student understand the scientific method and experimental process
            - Provide clear explanations of scientific concepts
            - Help with understanding experimental procedures and safety
            - Guide the student in analyzing and interpreting data
            - Use bullet points or numbered lists for experimental steps, not tables
            
            Formatting:
            - Use **bold** for key scientific concepts and terms
            - Use numbered lists for experimental procedures
            - Use bullet points for explanations and examples
            """
            
        else:
            # Default prompt for unknown assignment types
            system_prompt = f"""You are an expert homework assistant for {request.subject} at the {request.class_name} level.
            
            The student is working on an assignment about: {request.topic}
            
            Your role is to:
            1. Help the student understand the assignment requirements
            2. Provide clear explanations of relevant concepts
            3. Guide the student through the assignment
            4. Offer examples and explanations as needed
            5. Help the student develop their understanding and skills
            
            Guidelines:
            - Explain concepts in a way that's appropriate for {request.class_name} students
            - Focus on helping the student learn and understand, not just get answers
            - Provide clear, step-by-step guidance
            - Use bullet points or numbered lists for steps, not tables
            
        Formatting:
        - Use **bold** for key concepts and terms
        - Use numbered lists for step-by-step processes
        - Use bullet points for explanations and examples
        """
        
        # Add common guidelines for all assignment types
        common_guidelines = """
        
        After providing your response, generate 3-4 relevant follow-up questions that the user might want to ask.
        Format these questions as a JSON array at the very end of your response, like this:
        ["Question 1?", "Question 2?", "Question 3?"]
        
        IMPORTANT: Do NOT include any text like "Follow-up Questions (JSON)" or "```json" before the JSON array.
        Simply end your response with the JSON array directly.
        
        CRITICAL: No tables in your response. Use lists and paragraphs instead."""
        
        system_prompt += common_guidelines
        
        messages.append({"role": "system", "content": system_prompt})
        
        # Add the user's question if provided
        if request.question:
            messages.append({"role": "user", "content": request.question})
        else:
            # If no question is provided, create a default request for help
            default_question = f"I need help with my {request.assignment_type} assignment about {request.topic} in {request.subject}. Can you guide me through it?"
            messages.append({"role": "user", "content": default_question})
        
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
                
                return HomeworkAssistantResponse(
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
        error_detail = f"Error generating homework assistant response: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Log to console
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating homework assistant response: {str(e)}"
        )


class ExamPrepRequest(BaseModel):
    exam_type: str
    subject: str
    chapter: str
    difficulty: str
    question: Optional[str] = None


class ExamPrepResponse(BaseModel):
    id: str
    chat_session_id: str
    content: str
    sender_type: str
    timestamp: str
    suggested_questions: Optional[List[str]] = None


@router.post("/exam-prep", response_model=ExamPrepResponse)
async def exam_prep(request: ExamPrepRequest, db: Session = Depends(get_db)) -> Any:
    """
    Exam Preparation endpoint - provides specialized help based on exam type.
    Different prompts are used for different exam types to provide targeted assistance.
    """
    try:
        # Generate a proper UUID for the chat session
        import uuid
        chat_session_id = uuid.uuid4()
        
        # Create a new chat session for exam preparation
        chat_session = ChatSession(
            id=chat_session_id,
            student_profile_id=None,  # Set to None to avoid foreign key constraint
            mode=ChatMode.DISCUSSION,  # Using discussion mode for exam prep
            title=f"Exam Prep: {request.subject} - {request.chapter}"
        )
        db.add(chat_session)
        db.commit()
        
        # Store the user's question in the database if provided
        if request.question:
            user_message = Message(
                chat_session_id=chat_session_id,
                content=request.question,
                sender_type=SenderType.USER
            )
            db.add(user_message)
        
        # Prepare the messages for the LLM
        messages = []
        
        # Create specialized system prompts based on exam type
        if request.exam_type == "mcq":
            system_prompt = f"""You are an expert exam preparation assistant specializing in Multiple Choice Questions (MCQ) for {request.subject} at the {request.difficulty} difficulty level.
            
            The student is preparing for an MCQ exam on the chapter: {request.chapter}
            
            Your role is to:
            1. Provide comprehensive explanations of concepts that are frequently tested in MCQs
            2. Highlight key facts, formulas, and definitions that are commonly asked
            3. Explain common MCQ patterns and question structures
            4. Provide strategies for eliminating wrong options
            5. Offer tips for time management during MCQ exams
            6. Explain common misconceptions and tricks used in MCQs
            
            Guidelines:
            - Focus on concepts that are most likely to appear in MCQ format
            - Provide clear, concise explanations that can be quickly recalled during exams
            - Highlight important keywords and terms that often appear in questions
            - Explain how to identify the correct answer among similar options
            - Use bullet points or numbered lists for key points, not tables
            
            Formatting:
            - Use **bold** for key terms and concepts
            - Use numbered lists for step-by-step strategies
            - Use bullet points for explanations and examples
            """
            
        elif request.exam_type == "descriptive":
            system_prompt = f"""You are an expert exam preparation assistant specializing in Descriptive/Long-form exams for {request.subject} at the {request.difficulty} difficulty level.
            
            The student is preparing for a descriptive exam on the chapter: {request.chapter}
            
            Your role is to:
            1. Provide guidance on structuring comprehensive descriptive answers
            2. Explain how to organize thoughts and arguments effectively
            3. Provide frameworks for answering different types of descriptive questions
            4. Offer tips for including relevant examples and illustrations
            5. Explain how to balance depth and breadth in answers
            6. Provide guidance on time management for descriptive answers
            
            Guidelines:
            - Focus on developing coherent, well-structured responses
            - Explain how to create strong thesis statements and topic sentences
            - Provide strategies for organizing complex information
            - Explain how to incorporate relevant evidence and examples
            - Use bullet points or numbered lists for structural guidelines, not tables
            
            Formatting:
            - Use **bold** for key structural elements and concepts
            - Use numbered lists for step-by-step answer development
            - Use bullet points for explanations and examples
            """
            
        elif request.exam_type == "mixed":
            system_prompt = f"""You are an expert exam preparation assistant specializing in Mixed Pattern exams (MCQ + Short Answer + Descriptive) for {request.subject} at the {request.difficulty} difficulty level.
            
            The student is preparing for a mixed pattern exam on the chapter: {request.chapter}
            
            Your role is to:
            1. Provide strategies for handling different question types in a single exam
            2. Explain how to allocate time efficiently across different sections
            3. Provide guidance on transitioning between different answer formats
            4. Offer tips for maintaining consistency across different question types
            5. Explain how to approach questions that test the same concept in different formats
            6. Provide strategies for quick mental switching between question types
            
            Guidelines:
            - Focus on developing versatility in answering different question formats
            - Explain how to identify which approach to use for different question types
            - Provide strategies for efficient knowledge retrieval in different formats
            - Explain how to adapt depth of answer based on question type and marks
            - Use bullet points or numbered lists for strategies, not tables
            
            Formatting:
            - Use **bold** for key strategies and concepts
            - Use numbered lists for step-by-step approaches
            - Use bullet points for explanations and examples
            """
            
        elif request.exam_type == "board-exam":
            system_prompt = f"""You are an expert exam preparation assistant specializing in Board Exam patterns for {request.subject} at the {request.difficulty} difficulty level.
            
            The student is preparing for a board exam on the chapter: {request.chapter}
            
            Your role is to:
            1. Provide comprehensive coverage of the chapter as per board exam standards
            2. Explain board-specific marking schemes and evaluation criteria
            3. Provide guidance on answer structure and presentation for board exams
            4. Highlight frequently asked questions and important topics from board perspective
            5. Offer tips for maximizing marks in board exams
            6. Explain common mistakes to avoid in board exams
            
            Guidelines:
            - Focus on content that is most relevant for board examinations
            - Explain how to structure answers to meet board examiners' expectations
            - Provide insights into marking schemes and how to secure full marks
            - Highlight important topics that frequently appear in board exams
            - Use bullet points or numbered lists for key points, not tables
            
            Formatting:
            - Use **bold** for key terms and board-specific concepts
            - Use numbered lists for step-by-step answer structures
            - Use bullet points for explanations and examples
            """
            
        elif request.exam_type == "competitive":
            system_prompt = f"""You are an expert exam preparation assistant specializing in Competitive Exams for {request.subject} at the {request.difficulty} difficulty level.
            
            The student is preparing for a competitive exam on the chapter: {request.chapter}
            
            Your role is to:
            1. Provide advanced-level explanations suitable for competitive exams
            2. Explain complex problem-solving techniques and shortcuts
            3. Provide strategies for solving questions quickly under time pressure
            4. Explain how to approach non-conventional and tricky questions
            5. Offer tips for eliminating options and making educated guesses
            6. Provide guidance on managing time and stress in competitive exams
            
            Guidelines:
            - Focus on advanced concepts and problem-solving techniques
            - Explain shortcuts and time-saving strategies
            - Provide insights into common patterns and tricks in competitive exams
            - Explain how to approach questions that test multiple concepts simultaneously
            - Use bullet points or numbered lists for strategies, not tables
            
            Formatting:
            - Use **bold** for key techniques and concepts
            - Use numbered lists for step-by-step problem-solving approaches
            - Use bullet points for explanations and examples
            """
            
        elif request.exam_type == "quick-test":
            system_prompt = f"""You are an expert exam preparation assistant specializing in Quick Tests for {request.subject} at the {request.difficulty} difficulty level.
            
            The student is preparing for a quick test on the chapter: {request.chapter}
            
            Your role is to:
            1. Provide concise summaries of key concepts for quick revision
            2. Explain how to quickly identify and solve basic problems
            3. Provide strategies for rapid recall of important information
            4. Offer tips for quickly eliminating obviously wrong options
            5. Explain how to make educated guesses when unsure
            6. Provide guidance on time management for quick tests
            
            Guidelines:
            - Focus on the most essential concepts that are likely to appear in quick tests
            - Provide concise explanations that can be quickly recalled
            - Explain how to identify the core concept behind a question quickly
            - Provide strategies for making quick, accurate decisions
            - Use bullet points or numbered lists for key points, not tables
            
            Formatting:
            - Use **bold** for essential terms and concepts
            - Use numbered lists for quick problem-solving steps
            - Use bullet points for concise explanations and examples
            """
            
        else:
            # Default prompt for unknown exam types
            system_prompt = f"""You are an expert exam preparation assistant for {request.subject} at the {request.difficulty} difficulty level.
            
            The student is preparing for an exam on the chapter: {request.chapter}
            
            Your role is to:
            1. Provide comprehensive explanations of key concepts
            2. Explain how to approach different types of exam questions
            3. Provide strategies for effective exam preparation
            4. Offer tips for time management during exams
            5. Explain how to structure answers for maximum marks
            6. Provide guidance on common mistakes to avoid
            
            Guidelines:
            - Focus on concepts that are most relevant for examinations
            - Provide clear, concise explanations that can be easily recalled during exams
            - Explain how to approach different types of questions effectively
            - Use bullet points or numbered lists for key points, not tables
            
        Formatting:
        - Use **bold** for key concepts and terms
        - Use numbered lists for step-by-step approaches
        - Use bullet points for explanations and examples
        """
        
        # Add common guidelines for all exam types
        common_guidelines = f"""
        
        The student is preparing for a {request.exam_type} exam at {request.difficulty} difficulty level.
        
        After providing your response, generate 3-4 relevant follow-up questions that the user might want to ask.
        Format these questions as a JSON array at the very end of your response, like this:
        ["Question 1?", "Question 2?", "Question 3?"]
        
        IMPORTANT: Do NOT include any text like "Follow-up Questions (JSON)" or "```json" before the JSON array.
        Simply end your response with the JSON array directly.
        
        CRITICAL: No tables in your response. Use lists and paragraphs instead."""
        
        system_prompt += common_guidelines
        
        messages.append({"role": "system", "content": system_prompt})
        
        # Add the user's question if provided
        if request.question:
            messages.append({"role": "user", "content": request.question})
        else:
            # If no question is provided, create a default request for help
            default_question = f"I need help preparing for my {request.exam_type} exam on {request.chapter} in {request.subject}. The difficulty level is {request.difficulty}. Can you guide me through it?"
            messages.append({"role": "user", "content": default_question})
        
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
                
                return ExamPrepResponse(
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
        error_detail = f"Error generating exam prep response: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Log to console
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating exam prep response: {str(e)}"
        )