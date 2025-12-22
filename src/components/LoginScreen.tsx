import { useState } from 'react';
import { User, UserType } from '../types';
import { Mail, GraduationCap, Users, BookOpen, ArrowLeft } from 'lucide-react';
import { Moon, Sun } from 'lucide-react';
import { authService } from '../api/authService';

interface LoginScreenProps {
  onLogin: (user: User) => void;
  onShowRegister?: () => void;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
}

export function LoginScreen({ onLogin, onShowRegister, theme, onToggleTheme }: LoginScreenProps) {
  const [selectedType, setSelectedType] = useState<UserType | null>(null);
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const response = await authService.requestOtp(email);
      setOtpSent(true);
      console.log('OTP sent:', response.otp); // Remove in production
    } catch (err) {
      setError('Failed to send OTP. Please try again.');
      console.error('OTP request error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const { user } = await authService.verifyOtp(email, otp);
      onLogin(user);
    } catch (err) {
      setError('Invalid OTP. Please try again.');
      console.error('OTP verification error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const { user } = await authService.login(email, password);
      onLogin(user);
    } catch (err) {
      setError('Invalid email or password. Please try again.');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  const userTypes = [
    { type: 'teacher' as UserType, icon: GraduationCap, label: 'Teacher', color: 'bg-purple-500' },
    { type: 'parent' as UserType, icon: Users, label: 'Parent', color: 'bg-blue-500' },
    { type: 'student' as UserType, icon: BookOpen, label: 'Student', color: 'bg-green-500' },
  ];

  if (!selectedType) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-purple-50 to-pink-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4">
        <div className="absolute top-4 right-4">
          <button
            onClick={onToggleTheme}
            className="p-3 rounded-lg bg-white dark:bg-gray-800 shadow-lg hover:shadow-xl transition-all"
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          >
            {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5 text-yellow-400" />}
          </button>
        </div>
        
        <div className="w-full max-w-4xl">
          <div className="text-center mb-12">
            <h1 className="text-5xl mb-4 dark:text-white">EduChat AI</h1>
            <p className="text-gray-600 dark:text-gray-300">Select your role to get started</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-6">
            {userTypes.map(({ type, icon: Icon, label, color }) => (
              <button
                key={type}
                onClick={() => setSelectedType(type)}
                className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
              >
                <div className={`${color} w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4`}>
                  <Icon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl mb-2 dark:text-white">{label}</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">Sign in as {label.toLowerCase()}</p>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-purple-50 to-pink-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4">
      <div className="absolute top-4 right-4">
        <button
          onClick={onToggleTheme}
          className="p-3 rounded-lg bg-white dark:bg-gray-800 shadow-lg hover:shadow-xl transition-all"
          title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
        >
          {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5 text-yellow-400" />}
        </button>
      </div>
      
      <div className="w-full max-w-md">
        <button
          onClick={() => setSelectedType(null)}
          className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 mb-4"
        >
          ← Back to role selection
        </button>
        
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8">
          <div className="text-center mb-8">
            <div className={`${userTypes.find(t => t.type === selectedType)?.color} w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4`}>
              {(() => {
                const Icon = userTypes.find(t => t.type === selectedType)?.icon;
                return Icon ? <Icon className="w-8 h-8 text-white" /> : null;
              })()}
            </div>
            <h2 className="text-2xl mb-2">
              {selectedType === 'teacher' ? 'Teacher' : selectedType === 'parent' ? 'Parent' : 'Student'} Login
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {selectedType === 'parent' ? 'Sign in with OTP' : 'Sign in with your credentials'}
            </p>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
              {error}
            </div>
          )}

          {selectedType === 'parent' ? (
            // OTP Login for Parents
            !otpSent ? (
              <form onSubmit={handleSendOtp} className="space-y-4">
                <div>
                  <label className="block text-sm mb-2 text-gray-700 dark:text-gray-300">Email Address</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="parent@school.com"
                      className="w-full pl-11 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                      required
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  className="w-full bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
                  disabled={loading}
                >
                  {loading ? 'Sending...' : 'Send OTP'}
                </button>
                <p className="text-xs text-center text-gray-500 dark:text-gray-400">
                  Demo: Use any email, OTP will be displayed in console
                </p>
              </form>
            ) : (
              <form onSubmit={handleVerifyOtp} className="space-y-4">
                <div>
                  <label className="block text-sm mb-2 text-gray-700 dark:text-gray-300">Enter OTP</label>
                  <input
                    type="text"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    placeholder="123456"
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg text-center text-2xl tracking-widest focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                    maxLength={6}
                    required
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    OTP sent to {email}
                  </p>
                </div>
                <button
                  type="submit"
                  className="w-full bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
                  disabled={otp.length !== 6 || loading}
                >
                  {loading ? 'Verifying...' : 'Verify OTP'}
                </button>
                <button
                  type="button"
                  onClick={() => setOtpSent(false)}
                  className="w-full text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
                >
                  Change email
                </button>
                <p className="text-xs text-center text-gray-500 dark:text-gray-400">
                  Demo: Check console for OTP
                </p>
              </form>
            )
          ) : (
            // Password Login for Teachers and Students
            <form onSubmit={handlePasswordLogin} className="space-y-4">
              <div>
                <label className="block text-sm mb-2 text-gray-700 dark:text-gray-300">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder={selectedType === 'teacher' ? 'teacher@school.com' : 'student@school.com'}
                    className="w-full pl-11 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm mb-2 text-gray-700 dark:text-gray-300">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                  required
                />
              </div>
              <button
                type="submit"
                className={`w-full ${selectedType === 'teacher' ? 'bg-purple-500 hover:bg-purple-600' : 'bg-green-500 hover:bg-green-600'} text-white py-3 rounded-lg transition-colors disabled:opacity-50`}
                disabled={loading}
              >
                {loading ? 'Signing In...' : 'Sign In'}
              </button>
              <p className="text-xs text-center text-gray-500 dark:text-gray-400">
                Demo: Use any password with your email
              </p>
            </form>
          )}
          
          {onShowRegister && (
            <div className="text-center mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Don't have an account?{' '}
                <button
                  onClick={onShowRegister}
                  className="text-purple-600 dark:text-purple-400 hover:text-purple-800 dark:hover:text-purple-300 font-medium"
                >
                  Sign up
                </button>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}