import { apiService } from './service';
import { API_ENDPOINTS, getApiUrl } from './config';
import { User } from '../types';

// Type definitions for API responses
interface AuthResponse {
  access_token: string;
  token_type: string;
}

interface OtpResponse {
  message: string;
  otp?: string;
}

// Authentication service for handling auth-related API calls
class AuthService {
  private isRefreshing = false;
  private refreshSubscribers: Array<(token: string) => void> = [];

  // Login with email and password
  async login(email: string, password: string): Promise<{ user: User; token: string }> {
    try {
      const response = await apiService.post<AuthResponse>(API_ENDPOINTS.LOGIN, {
        email,
        password
      });
      
      // Store the token
      apiService.setToken(response.access_token);
      
      // Get user details
      const user = await this.getCurrentUser();
      
      return {
        user,
        token: response.access_token
      };
    } catch (error) {
      console.error('Login failed:', error);
      throw this.handleError(error);
    }
  }

  // Register a new user
  async register(userData: {
    name: string;
    email: string;
    password: string;
    user_type: string;
    grade?: string;
    subject?: string;
    teacher_role?: string;
    teacher_subject?: string;
    teacher_class?: string;
  }): Promise<User> {
    try {
      const response = await apiService.post<User>(API_ENDPOINTS.REGISTER, userData);
      return response;
    } catch (error) {
      console.error('Registration failed:', error);
      throw this.handleError(error);
    }
  }

  // Request OTP for parent login
  async requestOtp(email: string): Promise<OtpResponse> {
    try {
      const response = await apiService.post<OtpResponse>(API_ENDPOINTS.REQUEST_OTP, {
        email
      });
      return response;
    } catch (error) {
      console.error('OTP request failed:', error);
      throw this.handleError(error);
    }
  }

  // Verify OTP and login
  async verifyOtp(email: string, otp: string): Promise<{ user: User; token: string }> {
    try {
      const response = await apiService.post<AuthResponse>(API_ENDPOINTS.VERIFY_OTP, {
        email,
        otp
      });
      
      // Store the token
      apiService.setToken(response.access_token);
      
      // Get user details
      const user = await this.getCurrentUser();
      
      return {
        user,
        token: response.access_token
      };
    } catch (error) {
      console.error('OTP verification failed:', error);
      throw this.handleError(error);
    }
  }

  // Refresh access token
  async refreshToken(): Promise<string> {
    try {
      const response = await apiService.post<AuthResponse>(API_ENDPOINTS.REFRESH_TOKEN);
      
      // Store the new token
      apiService.setToken(response.access_token);
      
      // Notify all subscribers
      this.refreshSubscribers.forEach(callback => callback(response.access_token));
      this.refreshSubscribers = [];
      
      return response.access_token;
    } catch (error) {
      console.error('Token refresh failed:', error);
      // Clear token if refresh fails
      apiService.clearToken();
      throw this.handleError(error);
    }
  }

  // Handle token refresh with queue
  async handleTokenRefresh(): Promise<string> {
    if (this.isRefreshing) {
      // If already refreshing, return a promise that will resolve with the new token
      return new Promise((resolve) => {
        this.refreshSubscribers.push(resolve);
      });
    }

    this.isRefreshing = true;
    
    try {
      const newToken = await this.refreshToken();
      this.isRefreshing = false;
      return newToken;
    } catch (error) {
      this.isRefreshing = false;
      throw error;
    }
  }

  // Logout user
  async logout(): Promise<void> {
    try {
      await apiService.post(API_ENDPOINTS.LOGOUT);
      
      // Clear the token
      apiService.clearToken();
    } catch (error) {
      console.error('Logout failed:', error);
      // Still clear token even if API call fails
      apiService.clearToken();
      throw this.handleError(error);
    }
  }

  // Get current user details
  async getCurrentUser(): Promise<User> {
    try {
      // Make an API call to get user details from the backend
      const response = await apiService.get<User>(API_ENDPOINTS.USER_PROFILE);
      
      // Transform the response to match the User interface
      return {
        id: response.id,
        name: response.name,
        email: response.email,
        userType: response.user_type,
        grade: response.grade,
        normalized_grade: response.normalized_grade,
        subject: response.subject,
        teacherRole: response.teacher_role,
        teacherSubject: response.teacher_subject,
        teacherClass: response.teacher_class
      };
    } catch (error) {
      console.error('Failed to get current user:', error);
      
      // If the API call fails, try to refresh the token and retry
      if (error.response && error.response.status === 401) {
        try {
          // Try to refresh the token
          await this.handleTokenRefresh();
          
          // Retry the API call with the new token
          const response = await apiService.get<User>(API_ENDPOINTS.USER_PROFILE);
          
          // Transform the response to match the User interface
          return {
            id: response.id,
            name: response.name,
            email: response.email,
            userType: response.user_type,
            grade: response.grade,
            normalized_grade: response.normalized_grade,
            subject: response.subject,
            teacherRole: response.teacher_role,
            teacherSubject: response.teacher_subject,
            teacherClass: response.teacher_class
          };
        } catch (refreshError) {
          // If refresh fails, clear token and throw error
          apiService.clearToken();
          throw new Error('Session expired. Please login again.');
        }
      }
      
      throw this.handleError(error);
    }
  }

  // Check if token is expired
  private isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const expiryTime = payload.exp * 1000; // Convert to milliseconds
      return Date.now() >= expiryTime;
    } catch (error) {
      console.error('Failed to check token expiration:', error);
      return true; // Assume expired if we can't check
    }
  }

  // Handle API errors
  private handleError(error: any): Error {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      
      if (status === 401) {
        // Unauthorized - clear token
        apiService.clearToken();
        return new Error('Session expired. Please login again.');
      } else if (status === 400) {
        return new Error(error.response.data?.detail || 'Invalid request');
      } else if (status === 404) {
        return new Error('Resource not found');
      } else if (status >= 500) {
        return new Error('Server error. Please try again later.');
      }
    } else if (error.request) {
      // Request made but no response received
      return new Error('Network error. Please check your connection.');
    }
    
    // Return original error if it's an Error instance
    if (error instanceof Error) {
      return error;
    }
    
    // Default error
    return new Error('An unexpected error occurred');
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    const token = apiService.getToken();
    if (!token) return false;
    
    // Check if token is expired
    return !this.isTokenExpired(token);
  }

  // Get token expiry time
  getTokenExpiry(): Date | null {
    const token = apiService.getToken();
    if (!token) return null;
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const expiryTime = payload.exp * 1000; // Convert to milliseconds
      return new Date(expiryTime);
    } catch (error) {
      console.error('Failed to get token expiry:', error);
      return null;
    }
  }
}

// Export a singleton instance
export const authService = new AuthService();

// Export class for custom instances if needed
export default AuthService;