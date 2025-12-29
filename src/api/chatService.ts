import { apiService } from './service';

// Types for chat functionality
export interface ChatSession {
  id: string;
  user_id: string;
  student_profile_id: string;
  mode: string;
  title?: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  chat_session_id: string;
  content: string;
  sender_type: 'user' | 'ai';
  timestamp: string;
  suggested_questions?: string[];
}

export interface ChatSessionCreate {
  student_profile_id: string;
  mode: string;
  title?: string;
}

export interface MessageCreate {
  content: string;
}

export interface QARequest {
  question: string;
  student_profile_id: string;
  subject?: string;
}

export interface QAResponse {
  id: string;
  chat_session_id: string;
  content: string;
  sender_type: string;
  timestamp: string;
  suggested_questions?: string[];
}

export interface HomeworkAssistantRequest {
  class_name: string;
  subject: string;
  topic: string;
  assignment_type: string;
  question?: string;
}

export interface HomeworkAssistantResponse {
  id: string;
  chat_session_id: string;
  content: string;
  sender_type: string;
  timestamp: string;
  suggested_questions?: string[];
}

export interface ExamPrepRequest {
  exam_type: string;
  subject: string;
  chapter: string;
  difficulty: string;
  question?: string;
}

export interface ExamPrepResponse {
  id: string;
  chat_session_id: string;
  content: string;
  sender_type: string;
  timestamp: string;
  suggested_questions?: string[];
}

// Chat API service
export const chatService = {
  // Get all chat sessions for the current user
  getChatSessions: async (): Promise<ChatSession[]> => {
    console.log('Fetching chat sessions from API...');
    const response = await apiService.get<ChatSession[]>('/chat/sessions');
    console.log('API response for chat sessions:', response);
    return response;
  },

  // Create a new chat session
  createChatSession: async (sessionData: ChatSessionCreate): Promise<ChatSession> => {
    return apiService.post<ChatSession>('/chat/sessions', sessionData);
  },

  // Get a specific chat session with messages
  getChatSession: async (sessionId: string): Promise<ChatSession & { messages: Message[] }> => {
    return apiService.get<ChatSession & { messages: Message[] }>(`/chat/sessions/${sessionId}`);
  },

  // Get messages for a chat session
  getChatMessages: async (sessionId: string): Promise<Message[]> => {
    return apiService.get<Message[]>(`/chat/sessions/${sessionId}/messages`);
  },

  // Send a message and get AI response
  sendMessage: async (sessionId: string, messageData: MessageCreate): Promise<Message> => {
    return apiService.post<Message>(`/chat/sessions/${sessionId}/messages`, messageData);
  },

  // Q&A mode endpoint - get direct answer to a question
  askQuestion: async (qaData: QARequest): Promise<QAResponse> => {
    return apiService.post<QAResponse>('/llm/qa', qaData);
  },

  // Homework Assistant endpoint - get specialized help based on assignment type
  homeworkAssistant: async (homeworkData: HomeworkAssistantRequest): Promise<HomeworkAssistantResponse> => {
    return apiService.post<HomeworkAssistantResponse>('/llm/homework-assistant', homeworkData);
  },

  // Exam Preparation endpoint - get specialized help based on exam type
  examPrep: async (examData: ExamPrepRequest): Promise<ExamPrepResponse> => {
    return apiService.post<ExamPrepResponse>('/llm/exam-prep', examData);
  }
};