// API Configuration for the School Chat Application

// Base URL for the backend API
export const API_BASE_URL = 'http://localhost:8000/api/v1';

// API endpoints
export const API_ENDPOINTS = {
  // Authentication
  LOGIN: '/auth/login',
  LOGOUT: '/auth/logout',
  REFRESH_TOKEN: '/auth/refresh',
  
  // Users
  USERS: '/users',
  USER_PROFILE: '/users/profile',
  
  // Academic
  SUBJECTS: '/academic/subjects',
  CLASSES: '/academic/classes',
  TOPICS: '/academic/topics',
  
  // Chat
  CHAT_SESSIONS: '/chat/sessions',
  CHAT_MESSAGES: '/chat/messages',
  
  // Assessments
  QUIZZES: '/assessment/quizzes',
  EXAMS: '/assessment/exams',
  WORKSHEETS: '/assessment/worksheets',
  
  // Planner
  PLANNER_TASKS: '/planner/tasks',
  PLANNER_SCHEDULE: '/planner/schedule',
  
  // Performance
  PERFORMANCE_REPORTS: '/performance/reports',
  PERFORMANCE_STATS: '/performance/stats',
};

// Default request options
export const DEFAULT_REQUEST_OPTIONS = {
  headers: {
    'Content-Type': 'application/json',
  },
};

// Function to get the full URL for an endpoint
export const getApiUrl = (endpoint: string): string => {
  return `${API_BASE_URL}${endpoint}`;
};

// Function to get auth headers
export const getAuthHeaders = (token: string) => {
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
};