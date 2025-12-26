#!/usr/bin/env python3
"""
Test script for worksheet generation functionality
"""

import asyncio
import json
import sys
from typing import Dict, Any

# Mock the AI service for testing
class MockAIService:
    async def generate_quiz(
        self,
        subject: str,
        topic: str,
        difficulty: str = "medium",
        num_questions: int = 10,
        question_types: list = None,
        duration: int = 30
    ) -> Dict[str, Any]:
        """Mock implementation of generate_quiz for testing"""
        if question_types is None:
            question_types = ["multiple-choice"]
        
        # Create a distribution of question types
        question_type_distribution = {}
        if len(question_types) == 1:
            question_type_distribution[question_types[0]] = num_questions
        else:
            base_count = num_questions // len(question_types)
            remainder = num_questions % len(question_types)
            
            for i, q_type in enumerate(question_types):
                question_type_distribution[q_type] = base_count + (1 if i < remainder else 0)
        
        # Generate mock questions
        questions = []
        question_id = 1
        
        for q_type, count in question_type_distribution.items():
            for _ in range(count):
                if q_type == "multiple-choice":
                    questions.append({
                        "question": f"Multiple choice question {question_id} about {topic}",
                        "type": "multiple-choice",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "correctAnswer": "Option A",
                        "explanation": f"Explanation for multiple choice question {question_id}"
                    })
                elif q_type == "short-answer":
                    questions.append({
                        "question": f"Short answer question {question_id} about {topic}",
                        "type": "short-answer",
                        "options": [],
                        "correctAnswer": f"Answer for short answer question {question_id}",
                        "explanation": f"Explanation for short answer question {question_id}"
                    })
                elif q_type == "long-answer":
                    questions.append({
                        "question": f"Long answer question {question_id} about {topic}",
                        "type": "long-answer",
                        "options": [],
                        "correctAnswer": f"Detailed answer for long answer question {question_id}",
                        "explanation": f"Explanation for long answer question {question_id}"
                    })
                elif q_type == "true-false":
                    questions.append({
                        "question": f"True/False question {question_id} about {topic}",
                        "type": "true-false",
                        "options": ["True", "False"],
                        "correctAnswer": "True",
                        "explanation": f"Explanation for true/false question {question_id}"
                    })
                elif q_type == "fill-blank":
                    questions.append({
                        "question": f"Fill in the blank question {question_id} about {topic}",
                        "type": "fill-blank",
                        "options": [],
                        "correctAnswer": "answer",
                        "explanation": f"Explanation for fill in the blank question {question_id}"
                    })
                elif q_type == "matching":
                    questions.append({
                        "question": f"Matching question {question_id} about {topic}",
                        "type": "matching",
                        "options": ["Term 1", "Term 2", "Term 3"],
                        "correctAnswer": "1-a, 2-b, 3-c",
                        "explanation": f"Explanation for matching question {question_id}"
                    })
                
                question_id += 1
        
        # Return mock AI response
        return {
            "choices": [
                {
                    "message": {
                        "content": f"```json\n{json.dumps({'questions': questions})}\n```"
                    }
                }
            ]
        }

async def test_worksheet_generation():
    """Test the worksheet generation functionality"""
    print("Testing worksheet generation...")
    
    # Create mock AI service
    ai_service = MockAIService()
    
    # Test parameters
    test_cases = [
        {
            "subject": "Mathematics",
            "topic": "Algebra",
            "difficulty": "medium",
            "num_questions": 6,
            "question_types": ["multiple-choice", "short-answer"],
            "duration": 30
        },
        {
            "subject": "Science",
            "topic": "Photosynthesis",
            "difficulty": "hard",
            "num_questions": 9,
            "question_types": ["multiple-choice", "short-answer", "long-answer", "true-false"],
            "duration": 45
        },
        {
            "subject": "English",
            "topic": "Grammar",
            "difficulty": "easy",
            "num_questions": 5,
            "question_types": ["fill-blank", "matching"],
            "duration": 20
        }
    ]
    
    # Run test cases
    for i, test_case in enumerate(test_cases):
        print(f"\nTest Case {i+1}:")
        print(f"Subject: {test_case['subject']}")
        print(f"Topic: {test_case['topic']}")
        print(f"Difficulty: {test_case['difficulty']}")
        print(f"Number of Questions: {test_case['num_questions']}")
        print(f"Question Types: {', '.join(test_case['question_types'])}")
        print(f"Duration: {test_case['duration']} minutes")
        
        # Generate worksheet
        result = await ai_service.generate_quiz(**test_case)
        
        # Check for errors
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            continue
        
        # Extract questions
        try:
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            json_match = content.find("```json\n")
            if json_match != -1:
                json_end = content.find("\n```", json_match + 8)
                json_content = content[json_match + 8:json_end]
            else:
                json_content = content
            
            data = json.loads(json_content)
            questions = data.get("questions", [])
            
            print(f"✅ Successfully generated {len(questions)} questions")
            
            # Verify question types
            question_types_found = set()
            for question in questions:
                question_types_found.add(question.get("type", "unknown"))
            
            print(f"Question types found: {', '.join(sorted(question_types_found))}")
            
            # Verify all requested types are present
            missing_types = set(test_case["question_types"]) - question_types_found
            if missing_types:
                print(f"⚠️  Missing question types: {', '.join(missing_types)}")
            else:
                print("✅ All requested question types are present")
            
        except Exception as e:
            print(f"❌ Error parsing response: {str(e)}")
    
    print("\n✅ Worksheet generation test completed")

if __name__ == "__main__":
    asyncio.run(test_worksheet_generation())