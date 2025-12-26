import { apiService } from './service';

// Generate worksheet
export const generateWorksheet = async (worksheetData: {
  class_id: string;
  subject_id: string;
  chapter_id: string;
  difficulty: string;
  num_questions: number;
  question_types: string[];
  duration: number;
}) => {
  try {
    const response = await apiService.post('/generator/worksheet', worksheetData);
    return response;
  } catch (error) {
    console.error('Error generating worksheet:', error);
    throw error;
  }
};