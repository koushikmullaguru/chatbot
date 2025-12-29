export type UserType = 'teacher' | 'parent' | 'student';

export type ChatMode = 'qa' | 'exam' | 'quiz' | 'worksheet' | 'homework' | 'revision' | 'discussion' | 'planner';

export type TeacherMode = 'student-chat' | 'content-creation' | 'curriculum-planner' | 'worksheet-creator' | 'exam-creator' | 'insights';

export type TeacherRole = 'subject-teacher' | 'class-head' | 'principal';

export type Theme = 'light' | 'dark';

export interface User {
  id: string;
  name: string;
  email: string;
  userType: UserType;
  grade?: string;
  normalized_grade?: string;
  subject?: string;
  teacherRole?: TeacherRole;
  teacherSubject?: string;
  teacherClass?: string;
}

export interface StudentProfile {
  id: string;
  name: string;
  grade: string;
  normalized_grade?: string;
  avatar: string;
  pin: string;
  roll_number?: string;
  date_of_birth?: string;
  blood_group?: string;
  admission_date?: string;
  email?: string;
  phone?: string;
  address?: string;
  section?: string;
  parent_name?: string;
  parent_email?: string;
  parent_phone?: string;
}

export interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  suggestedQuestions?: string[];
}

export interface ChatSession {
  id: string;
  mode: ChatMode;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

export interface QuizQuestion {
  id: string;
  type: 'multiple-choice' | 'single-choice' | 'short-answer' | 'long-answer';
  question: string;
  options?: string[];
  correctAnswer: string | string[];
  explanation?: string;
  userAnswer?: string | string[];
}

export interface Quiz {
  id: string;
  title: string;
  questions: QuizQuestion[];
  score?: number;
  totalQuestions: number;
}

export interface RevisionTopic {
  class: string;
  subject: string;
  topic: string;
}

export interface ExamConfig {
  examType: string;
  subject: string;
  chapter: string;
  difficulty: string;
  duration: number;
  questionCount: number;
}

export interface HomeworkTopic {
  class: string;
  subject: string;
  chapter: string;
  assignmentType: string;
}