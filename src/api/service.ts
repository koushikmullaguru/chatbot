import { API_BASE_URL, DEFAULT_REQUEST_OPTIONS, getAuthHeaders } from './config';
import { authService } from './authService';

// API Service for handling HTTP requests

class ApiService {
  private baseUrl: string;
  private token: string | null = null;
  private isRefreshing = false;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    
    // Check for token in localStorage on initialization
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('authToken');
    }
  }

  // Set authentication token
  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('authToken', token);
    }
  }

  // Clear authentication token
  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('authToken');
    }
  }

  // Get current token
  getToken(): string | null {
    return this.token;
  }

  // Handle token refresh
  private async handleTokenRefresh(): Promise<string> {
    if (this.isRefreshing) {
      // If already refreshing, wait for it to complete
      return new Promise((resolve) => {
        const checkToken = setInterval(() => {
          if (!this.isRefreshing) {
            clearInterval(checkToken);
            resolve(this.token || '');
          }
        }, 100);
      });
    }

    this.isRefreshing = true;
    
    try {
      const newToken = await authService.refreshToken();
      this.isRefreshing = false;
      return newToken;
    } catch (error) {
      this.isRefreshing = false;
      throw error;
    }
  }

  // Generic request method
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryCount = 1
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: Record<string, string> = {
      ...DEFAULT_REQUEST_OPTIONS.headers as Record<string, string>,
      ...(options.headers as Record<string, string> || {}),
    };

    // Add authorization header if token exists
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const config: RequestInit = {
      ...DEFAULT_REQUEST_OPTIONS,
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);
      
      // Handle 401 Unauthorized - possibly expired token
      if (response.status === 401 && retryCount > 0 && this.token) {
        try {
          // Try to refresh the token
          const newToken = await this.handleTokenRefresh();
          
          // Update the token
          this.token = newToken;
          headers['Authorization'] = `Bearer ${newToken}`;
          
          // Retry the request with new token
          return this.request<T>(endpoint, options, retryCount - 1);
        } catch (refreshError) {
          // If refresh fails, clear token and throw error
          this.clearToken();
          throw new Error('Session expired. Please login again.');
        }
      }
      
      // Handle other HTTP errors
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error = new Error(errorData.message || `HTTP error! status: ${response.status}`);
        
        // Add response status to error for better handling
        (error as any).status = response.status;
        (error as any).response = errorData;
        
        throw error;
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // GET request
  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  // POST request
  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // PUT request
  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // DELETE request
  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  // PATCH request
  async patch<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }
}

// Get subjects by class ID
export const getSubjectsByClass = async (classId: string) => {
  try {
    const response = await apiService.get(`/academic/subjects?class_id=${classId}`);
    return response;
  } catch (error) {
    console.error('Error fetching subjects:', error);
    throw error;
  }
};

// Generate quiz
export const generateQuiz = async (quizData: {
  class_id: string;
  subject_id: string;
  chapter_id: string;
  difficulty: string;
  num_questions: number;
  question_types: string[];
  duration: number;
}) => {
  try {
    const response = await apiService.post('/generator/quiz', quizData);
    return response;
  } catch (error) {
    console.error('Error generating quiz:', error);
    throw error;
  }
};

// Export a singleton instance
export const apiService = new ApiService();

// Export class for custom instances if needed
export default ApiService;