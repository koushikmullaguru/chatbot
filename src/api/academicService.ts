import { apiService } from './service';

// Types for academic hierarchy
export interface Class {
  id: string;
  name: string;
  created_at?: string;
  updated_at?: string;
}

export interface Subject {
  id: string;
  name: string;
  class_id: string;
  created_at?: string;
  updated_at?: string;
}

export interface Chapter {
  id: string;
  name: string;
  subject_id: string;
  created_at?: string;
  updated_at?: string;
}

export interface Topic {
  id: string;
  name: string;
  chapter_id: string;
  created_at?: string;
  updated_at?: string;
}

// Academic API service
export const academicService = {
  // Get all classes
  getClasses: async (): Promise<Class[]> => {
    return apiService.get<Class[]>('/academic/classes');
  },

  // Get subjects for a class
  getSubjects: async (classId: string): Promise<Subject[]> => {
    return apiService.get<Subject[]>(`/academic/subjects?class_id=${classId}`);
  },

  // Get chapters for a subject
  getChapters: async (subjectId: string): Promise<Chapter[]> => {
    return apiService.get<Chapter[]>(`/academic/chapters?subject_id=${subjectId}`);
  },

  // Get topics for a subject or chapter
  getTopics: async (subjectId?: string, chapterId?: string): Promise<Topic[]> => {
    let url = '/academic/topics?';
    if (chapterId) {
      url += `chapter_id=${chapterId}`;
    } else if (subjectId) {
      url += `subject_id=${subjectId}`;
    }
    return apiService.get<Topic[]>(url);
  }
};