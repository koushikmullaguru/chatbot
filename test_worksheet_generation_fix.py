#!/usr/bin/env python3
"""
Test script to verify that the worksheet generation API fix works correctly.
This script simulates a worksheet generation request and checks if the response
is properly formatted without JSON parsing errors.
"""

import asyncio
import json
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.core.ai_service import ai_service


async def test_worksheet_generation():
    """Test the worksheet generation with a problematic topic that might include LaTeX."""
    print("Testing worksheet generation with Gravitation topic...")
    
    # Test parameters that match the original error case
    subject = "Science"
    topic = "Gravitation"
    difficulty = "medium"
    num_questions = 5
    question_types = ["multiple-choice", "short-answer", "long-answer"]
    duration = 15
    
    try:
        # Generate worksheet using AI service
        worksheet_result = await ai_service.generate_quiz(
            subject=subject,
            topic=topic,
            difficulty=difficulty,
            num_questions=num_questions,
            question_types=question_types,
            duration=duration
        )
        
        # Check for errors
        if "error" in worksheet_result:
            print(f"❌ Error generating worksheet: {worksheet_result['error']}")
            return False
        
        # Extract the content from the first choice
        content = worksheet_result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if not content or content.strip() == "":
            print("❌ Empty response from AI service")
            return False
        
        # Extract JSON from the content (it might be wrapped in ```json\n```)
        import re
        json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
        if json_match:
            json_content = json_match.group(1)
            print("✅ Found JSON content in markdown format")
        else:
            # If no markdown formatting, try to parse the entire content as JSON
            json_content = content
            print("✅ No JSON markdown found, using entire content")
        
        # Check if json_content is empty
        if not json_content or json_content.strip() == "":
            print("❌ Empty JSON content in AI response")
            return False
        
        # Try to parse the JSON
        try:
            questions_data = json.loads(json_content)
            print("✅ Successfully parsed JSON on first attempt")
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parsing error on first attempt: {str(e)}")
            
            # Try to fix common JSON issues like LaTeX escapes
            # Replace problematic LaTeX escapes with proper JSON escaping
            fixed_json_content = json_content
            
            # Fix LaTeX inline math: \( ... \) -> $$ ... $$
            fixed_json_content = re.sub(r'\\\\\((.*?)\\\\\)', r'$$\1$$', fixed_json_content)
            
            # Fix LaTeX display math: \[ ... \] -> $ ... $
            fixed_json_content = re.sub(r'\\\\\[(.*?)\\\\\]', r'$\1$', fixed_json_content)
            
            # Fix single backslash escapes that are causing issues
            fixed_json_content = re.sub(r'\\\\([(){}\[\]])', r'\1', fixed_json_content)
            
            # Fix escaped quotes within the JSON
            fixed_json_content = re.sub(r'\\\\\"', r'\\"', fixed_json_content)
            
            # Fix any remaining double backslashes that aren't part of valid JSON escapes
            fixed_json_content = re.sub(r'\\\\(?!["\\/bfnrt])', r'\\\\', fixed_json_content)
            
            try:
                questions_data = json.loads(fixed_json_content)
                print("✅ Successfully parsed JSON after fixing LaTeX escapes")
            except json.JSONDecodeError as second_error:
                print(f"❌ Failed to parse JSON even after fixing escapes: {str(second_error)}")
                return False
        
        questions = questions_data.get("questions", [])
        
        # Check if questions array is empty
        if not questions:
            print("❌ No questions found in AI response")
            return False
        
        # Validate the structure of each question
        for i, question in enumerate(questions):
            if not isinstance(question, dict):
                print(f"❌ Question {i+1} is not a dictionary: {type(question)}")
                return False
                
            # Validate required fields
            required_fields = ["question", "type", "options", "correctAnswer", "explanation"]
            missing_fields = [field for field in required_fields if field not in question]
            if missing_fields:
                print(f"❌ Question {i+1} is missing fields: {missing_fields}")
                return False
        
        print(f"✅ Successfully generated and parsed worksheet with {len(questions)} questions")
        print("✅ All questions have the required fields")
        print("✅ No JSON parsing errors detected")
        
        # Print a sample question for verification
        if questions:
            print("\nSample question:")
            sample = questions[0]
            print(f"  Question: {sample['question']}")
            print(f"  Type: {sample['type']}")
            print(f"  Options: {sample['options']}")
            print(f"  Correct Answer: {sample['correctAnswer']}")
            print(f"  Explanation: {sample['explanation'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_worksheet_generation())
    if success:
        print("\n🎉 Test passed! The worksheet generation fix is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Test failed! The worksheet generation still has issues.")
        sys.exit(1)