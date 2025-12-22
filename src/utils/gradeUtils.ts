/**
 * Normalize grade format to "Grade X" format.
 * 
 * @param grade The grade value as a string or number
 * @returns Normalized grade in "Grade X" format
 * 
 * Examples:
 * normalizeGrade("10") -> "Grade 10"
 * normalizeGrade("9th") -> "Grade 9"
 * normalizeGrade("8th Grade") -> "Grade 8"
 * normalizeGrade(7) -> "Grade 7"
 */
export function normalizeGrade(grade: string | number | undefined | null): string {
  if (grade === undefined || grade === null) {
    return "";
  }
  
  // Convert to string if it's a number
  const gradeStr = String(grade);
  
  // Extract the numeric part using regex
  const match = gradeStr.match(/(\d+)/);
  if (match) {
    const gradeNumber = match[1];
    return `Grade ${gradeNumber}`;
  }
  
  // If no numeric part found, return the original string
  return gradeStr;
}

/**
 * Normalize grade for display purposes.
 * This is an alias for normalizeGrade function.
 * 
 * @param grade The grade value as a string or number
 * @returns Normalized grade in "Grade X" format
 */
export function normalizeGradeForDisplay(grade: string | number | undefined | null): string {
  return normalizeGrade(grade);
}