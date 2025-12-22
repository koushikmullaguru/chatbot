import re
from typing import Union

def normalize_grade(grade: Union[str, int]) -> str:
    """
    Normalize grade format to "Grade X" format.
    
    Args:
        grade: The grade value as a string or integer
        
    Returns:
        Normalized grade in "Grade X" format
        
    Examples:
        >>> normalize_grade("10")
        "Grade 10"
        >>> normalize_grade("9th")
        "Grade 9"
        >>> normalize_grade("8th Grade")
        "Grade 8"
        >>> normalize_grade(7)
        "Grade 7"
    """
    if grade is None:
        return ""
    
    # Convert to string if it's an integer
    grade_str = str(grade)
    
    # Extract the numeric part using regex
    match = re.search(r'(\d+)', grade_str)
    if match:
        grade_number = match.group(1)
        return f"Grade {grade_number}"
    
    # If no numeric part found, return the original string
    return grade_str

def normalize_grade_for_display(grade: Union[str, int]) -> str:
    """
    Normalize grade for display purposes.
    This is an alias for normalize_grade function.
    
    Args:
        grade: The grade value as a string or integer
        
    Returns:
        Normalized grade in "Grade X" format
    """
    return normalize_grade(grade)