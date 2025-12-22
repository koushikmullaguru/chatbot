import { useState, useEffect } from 'react';
import { LoginScreen } from './components/LoginScreen';
import { RegisterScreen } from './components/RegisterScreen';
import { ProfileSelector } from './components/ProfileSelector';
import { ChatInterface } from './components/ChatInterface';
import { ProtectedRoute } from './components/ProtectedRoute';
import { User, StudentProfile } from './types';
import { useTheme } from './hooks/useTheme';
import { authService } from './api/authService';

type AuthScreen = 'login' | 'register';

export default function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [selectedProfile, setSelectedProfile] = useState<StudentProfile | null>(null);
  const [showProfileSelector, setShowProfileSelector] = useState(false);
  const [authScreen, setAuthScreen] = useState<AuthScreen>('login');
  const [isLoading, setIsLoading] = useState(true);
  const { theme, toggleTheme } = useTheme();

  useEffect(() => {
    // Check for existing session
    const checkAuth = async () => {
      try {
        if (authService.isAuthenticated()) {
          const user = await authService.getCurrentUser();
          setCurrentUser(user);
          
          // If parent, show profile selector
          if (user.userType === 'parent') {
            setShowProfileSelector(true);
          }
        }
      } catch (error) {
        console.error('Authentication check failed:', error);
        // Clear invalid token
        localStorage.removeItem('authToken');
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const handleLogin = (user: User) => {
    setCurrentUser(user);
    // Reset selected profile when logging in with a different user
    setSelectedProfile(null);
    
    // Show profile selector for parents
    if (user.userType === 'parent') {
      setShowProfileSelector(true);
    }
  };

  const handleRegister = (user: User) => {
    setCurrentUser(user);
    // Reset selected profile when registering with a new user
    setSelectedProfile(null);
    
    // Show profile selector for parents
    if (user.userType === 'parent') {
      setShowProfileSelector(true);
    }
    
    // Switch back to login screen
    setAuthScreen('login');
  };

  const handleProfileSelect = (profile: StudentProfile) => {
    setSelectedProfile(profile);
    setShowProfileSelector(false);
  };

  const handleSwitchProfile = () => {
    setShowProfileSelector(true);
    setSelectedProfile(null);
  };

  const handleLogout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setCurrentUser(null);
      setSelectedProfile(null);
      setShowProfileSelector(false);
    }
  };

  const handleShowRegister = () => {
    setAuthScreen('register');
  };

  const handleBackToLogin = () => {
    setAuthScreen('login');
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-100 via-purple-50 to-pink-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-300">Loading...</p>
        </div>
      </div>
    );
  }

  // Not logged in
  if (!currentUser) {
    if (authScreen === 'register') {
      return (
        <RegisterScreen
          onRegister={handleRegister}
          onBackToLogin={handleBackToLogin}
          theme={theme}
          onToggleTheme={toggleTheme}
        />
      );
    }
    
    return (
      <LoginScreen
        onLogin={handleLogin}
        onShowRegister={handleShowRegister}
        theme={theme}
        onToggleTheme={toggleTheme}
      />
    );
  }

  // Parent needs to select profile
  if (currentUser.userType === 'parent' && showProfileSelector) {
    return (
      <ProfileSelector
        parentId={currentUser.id}
        onSelectProfile={handleProfileSelect}
        onLogout={handleLogout}
        theme={theme}
        onToggleTheme={toggleTheme}
      />
    );
  }

  // Show chat interface (protected route)
  return (
    <ProtectedRoute>
      <ChatInterface
        user={currentUser}
        selectedProfile={selectedProfile}
        onSwitchProfile={currentUser.userType === 'parent' ? handleSwitchProfile : undefined}
        onLogout={handleLogout}
        theme={theme}
        onToggleTheme={toggleTheme}
      />
    </ProtectedRoute>
  );
}