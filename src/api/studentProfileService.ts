import { apiService } from './service';
import { API_ENDPOINTS } from './config';
import { StudentProfile } from '../types';

// Get all student profiles for a parent
export const getStudentProfiles = async (): Promise<StudentProfile[]> => {
  try {
    const response = await apiService.get<StudentProfile[]>(API_ENDPOINTS.STUDENT_PROFILES);
    return response;
  } catch (error) {
    console.error('Error fetching student profiles:', error);
    throw error;
  }
};

// Get a specific student profile by user ID
export const getStudentProfileByUserId = async (userId: string): Promise<StudentProfile> => {
  try {
    const response = await apiService.get<StudentProfile>(`${API_ENDPOINTS.STUDENT_PROFILE}/${userId}`);
    return response;
  } catch (error) {
    console.error('Error fetching student profile:', error);
    throw error;
  }
};

// Get a specific student profile by its own ID
export const getStudentProfileById = async (profileId: string): Promise<StudentProfile> => {
  try {
    // We need to create a new endpoint for this, but for now we'll use the existing one
    // This is a temporary workaround and should be fixed properly
    const response = await apiService.get<StudentProfile>(`${API_ENDPOINTS.STUDENT_PROFILE}/${profileId}`);
    return response;
  } catch (error) {
    console.error('Error fetching student profile by ID:', error);
    throw error;
  }
};

// Verify student PIN
export const verifyStudentPin = async (studentProfileId: string, pin: string): Promise<any> => {
  try {
    const response = await apiService.post<any>(`${API_ENDPOINTS.STUDENT_PROFILE}/verify-pin`, {
      student_profile_id: studentProfileId,
      pin
    });
    return response;
  } catch (error) {
    console.error('Error verifying student PIN:', error);
    throw error;
  }
};

// Get student interests
export const getStudentInterests = async (studentProfileId: string): Promise<any[]> => {
  try {
    const response = await apiService.get<any[]>(`${API_ENDPOINTS.STUDENT_PROFILE}/${studentProfileId}/interests`);
    return response;
  } catch (error) {
    console.error('Error fetching student interests:', error);
    throw error;
  }
};

// Update student interests
export const updateStudentInterests = async (studentProfileId: string, interests: string[]): Promise<any[]> => {
  try {
    const response = await apiService.put<any[]>(`${API_ENDPOINTS.STUDENT_PROFILE}/${studentProfileId}/interests`, {
      interests: interests.map(interest => ({ interest_name: interest }))
    });
    return response;
  } catch (error) {
    console.error('Error updating student interests:', error);
    throw error;
  }
};

// Get student achievements
export const getStudentAchievements = async (studentProfileId: string): Promise<any[]> => {
  try {
    const response = await apiService.get<any[]>(`${API_ENDPOINTS.STUDENT_PROFILE}/${studentProfileId}/achievements`);
    return response;
  } catch (error) {
    console.error('Error fetching student achievements:', error);
    throw error;
  }
};

// Add student achievement
export const addStudentAchievement = async (studentProfileId: string, achievement: {
  title: string;
  date: string;
  icon?: string;
}): Promise<any> => {
  try {
    const response = await apiService.post<any>(`${API_ENDPOINTS.STUDENT_PROFILE}/${studentProfileId}/achievements`, {
      ...achievement,
      student_profile_id: studentProfileId
    });
    return response;
  } catch (error) {
    console.error('Error adding student achievement:', error);
    throw error;
  }
};

// Get student report cards
export const getStudentReportCards = async (studentProfileId: string): Promise<any[]> => {
  try {
    const response = await apiService.get<any[]>(`${API_ENDPOINTS.STUDENT_PROFILE}/${studentProfileId}/report-cards`);
    return response;
  } catch (error) {
    console.error('Error fetching student report cards:', error);
    throw error;
  }
};