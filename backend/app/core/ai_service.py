import httpx
import json
from typing import Dict, List, Any, Optional
from .config import settings


class AIService:
    """
    Service for interacting with OpenRouter AI API
    """
    
    def __init__(self):
        self.api_url = settings.AI_API_URL
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.AI_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://localhost:8000",  # Replace with your domain in production
            "X-Title": "School Chat Application",
            "Content-Type": "application/json"
        }
    
    async def generate_chat_response(
        self,
        message: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        include_suggestions: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a response for chat messages with optional suggested questions
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if chat_history:
            messages.extend(chat_history)
        
        messages.append({"role": "user", "content": message})
        
        # Add instruction for generating suggested questions if requested
        if include_suggestions:
            messages.append({
                "role": "system",
                "content": "After providing your response, generate 3-4 relevant follow-up questions that the user might want to ask. Format these questions as a JSON array at the end of your response, like this: [\"Question 1?\", \"Question 2?\", \"Question 3?\"]"
            })
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1500  # Increased to accommodate suggested questions
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                return {"error": f"HTTP error: {e.response.status_code}"}
            except httpx.RequestError as e:
                return {"error": f"Request error: {str(e)}"}
            except Exception as e:
                return {"error": f"Unexpected error: {str(e)}"}
    
    async def generate_quiz(
        self,
        subject: str,
        topic: str,
        difficulty: str = "medium",
        num_questions: int = 10,
        question_types: List[str] = None,
        duration: int = 30
    ) -> Dict[str, Any]:
        """
        Generate quiz questions
        """
        if question_types is None:
            question_types = ["multiple-choice"]
        
        system_prompt = f"You are an expert teacher creating educational content for {subject}."
        
        prompt = f"""
        Create a {difficulty} level quiz about {topic} in {subject}.
        The quiz should have {num_questions} questions of the following types: {', '.join(question_types)}.
        The quiz should be designed to be completed in {duration} minutes.
        
        For each question, provide:
        1. The question text (in a field called "question")
        2. The question type (in a field called "type")
        3. Options (if multiple choice, in a field called "options" as an array of text strings)
        4. The correct answer (in a field called "correctAnswer")
        5. An explanation of the answer (in a field called "explanation")
        
        Format your response as a valid JSON object with a "questions" array containing each question object.
        Each question object must have the exact field names: "question", "type", "options", "correctAnswer", "explanation".
        
        Example format:
        {{
          "questions": [
            {{
              "question": "What is the capital of France?",
              "type": "single-choice",
              "options": ["London", "Berlin", "Paris", "Madrid"],
              "correctAnswer": "Paris",
              "explanation": "Paris is the capital and most populous city of France."
            }}
          ]
        }}
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                return {"error": f"HTTP error: {e.response.status_code}"}
            except httpx.RequestError as e:
                return {"error": f"Request error: {str(e)}"}
            except Exception as e:
                return {"error": f"Unexpected error: {str(e)}"}
    
    async def generate_exam(
        self, 
        class_name: str, 
        subject: str, 
        duration: int,
        total_marks: int,
        sections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a full exam paper
        """
        system_prompt = f"You are an expert teacher creating a formal examination for {class_name} {subject}."
        
        sections_text = "\n".join([
            f"- {section.get('name', 'Section')} with {section.get('num_questions', 0)} questions worth {section.get('marks', 0)} marks each"
            for section in sections
        ])
        
        prompt = f"""
        Create a formal {subject} examination for {class_name}.
        
        Exam details:
        - Duration: {duration} minutes
        - Total marks: {total_marks}
        
        Sections:
        {sections_text}
        
        For each section, create appropriate questions based on the section's requirements.
        Include a variety of question types (multiple choice, short answer, essay, etc.)
        
        Format your response as a JSON object with:
        1. An "exam_title"
        2. "instructions" for students
        3. A "sections" array containing each section with its questions
        4. A "marking_scheme" if applicable
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 3000
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                return {"error": f"HTTP error: {e.response.status_code}"}
            except httpx.RequestError as e:
                return {"error": f"Request error: {str(e)}"}
            except Exception as e:
                return {"error": f"Unexpected error: {str(e)}"}
    
    async def generate_revision_notes(
        self, 
        subject: str, 
        topics: List[str],
        revision_type: str = "notes"
    ) -> Dict[str, Any]:
        """
        Generate revision materials
        """
        system_prompt = f"You are an expert teacher creating revision materials for {subject}."
        
        topics_text = "\n".join([f"- {topic}" for topic in topics])
        
        prompt = f"""
        Create {revision_type} for {subject} covering the following topics:
        
        {topics_text}
        
        The revision materials should:
        1. Cover all key concepts
        2. Include clear explanations
        3. Provide examples where appropriate
        4. Be structured in a logical way
        
        Format your response as a JSON object with:
        1. A "title" for the revision materials
        2. The "content" organized by topic
        3. "key_points" for each topic
        4. "examples" where applicable
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 2000
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                return {"error": f"HTTP error: {e.response.status_code}"}
            except httpx.RequestError as e:
                return {"error": f"Request error: {str(e)}"}
            except Exception as e:
                return {"error": f"Unexpected error: {str(e)}"}
    
    async def generate_homework(
        self, 
        class_name: str, 
        subject: str, 
        topic: str,
        difficulty: str = "medium",
        num_questions: int = 5
    ) -> Dict[str, Any]:
        """
        Generate homework assignments
        """
        system_prompt = f"You are an expert teacher creating homework assignments for {class_name} {subject}."
        
        prompt = f"""
        Create a {difficulty} level homework assignment about {topic} in {subject} for {class_name}.
        The homework should have {num_questions} questions.
        
        Include a mix of question types (multiple choice, short answer, problem-solving, etc.)
        Make sure the questions are appropriate for the grade level and difficulty.
        
        Format your response as a JSON object with:
        1. A "title" for the homework
        2. "instructions" for students
        3. A "questions" array with each question
        4. A "due_date" placeholder
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1500
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                return {"error": f"HTTP error: {e.response.status_code}"}
            except httpx.RequestError as e:
                return {"error": f"Request error: {str(e)}"}
            except Exception as e:
                return {"error": f"Unexpected error: {str(e)}"}
    
    async def generate_teacher_notes(
        self, 
        class_name: str, 
        subject: str, 
        topic: str,
        additional_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate teacher lecture notes
        """
        system_prompt = f"You are an expert teacher creating lecture notes for {class_name} {subject}."
        
        additional_text = ""
        if additional_info:
            additional_text = "\n\nAdditional requirements:\n"
            for key, value in additional_info.items():
                additional_text += f"- {key}: {value}\n"
        
        prompt = f"""
        Create comprehensive lecture notes for teaching {topic} in {subject} to {class_name}.
        
        The notes should include:
        1. Learning objectives
        2. Key concepts and definitions
        3. Detailed explanations
        4. Examples and illustrations
        5. Classroom activities or discussion points
        6. Assessment ideas{additional_text}
        
        Format your response as a JSON object with:
        1. A "title" for the lecture
        2. "learning_objectives"
        3. The "content" organized logically
        4. "examples" and "illustrations"
        5. "activities" and "discussion_points"
        6. "assessment_ideas"
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 2500
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                return {"error": f"HTTP error: {e.response.status_code}"}
            except httpx.RequestError as e:
                return {"error": f"Request error: {str(e)}"}
            except Exception as e:
                return {"error": f"Unexpected error: {str(e)}"}


# Create a singleton instance
ai_service = AIService()