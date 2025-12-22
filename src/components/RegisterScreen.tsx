import { useState } from 'react';
import { User, UserType, TeacherRole } from '../types';
import { Mail, Lock, User as UserIcon, GraduationCap, Users, BookOpen, ArrowLeft } from 'lucide-react';
import { authService } from '../api/authService';

interface RegisterScreenProps {
  onRegister: (user: User) => void;
  onBackToLogin: () => void;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
}

export function RegisterScreen({ onRegister, onBackToLogin, theme, onToggleTheme }: RegisterScreenProps) {
  const [selectedType, setSelectedType] = useState<UserType | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    user_type: '',
    grade: '',
    subject: '',
    teacher_role: '',
    teacher_subject: '',
    teacher_class: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const userTypes = [
    { type: 'teacher' as UserType, icon: GraduationCap, label: 'Teacher', color: 'bg-purple-500' },
    { type: 'parent' as UserType, icon: Users, label: 'Parent', color: 'bg-blue-500' },
    { type: 'student' as UserType, icon: BookOpen, label: 'Student', color: 'bg-green-500' },
  ];

  const teacherRoles: TeacherRole[] = ['subject-teacher', 'class-head', 'principal'];

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    try {
      const userData = {
        name: formData.name,
        email: formData.email,
        password: formData.password,
        user_type: formData.user_type,
        grade: formData.grade || undefined,
        subject: formData.subject || undefined,
        teacher_role: formData.teacher_role || undefined,
        teacher_subject: formData.teacher_subject || undefined,
        teacher_class: formData.teacher_class || undefined
      };

      const user = await authService.register(userData);
      onRegister(user);
    } catch (err) {
      setError('Registration failed. Please try again.');
      console.error('Registration error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!selectedType) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-purple-50 to-pink-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4">
        <div className="absolute top-4 right-4">
          <button
            onClick={onToggleTheme}
            className="p-3 rounded-lg bg-white dark:bg-gray-800 shadow-lg hover:shadow-xl transition-all"
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          >
            {theme === 'light' ? 
              <div className="w-5 h-5 rounded-full bg-gray-700" /> : 
              <div className="w-5 h-5 rounded-full bg-yellow-400" />
            }
          </button>
        </div>
        
        <div className="w-full max-w-4xl">
          <div className="text-center mb-12">
            <h1 className="text-5xl mb-4 dark:text-white">EduChat AI</h1>
            <p className="text-gray-600 dark:text-gray-300">Create a new account</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-6">
            {userTypes.map(({ type, icon: Icon, label, color }) => (
              <button
                key={type}
                onClick={() => {
                  setSelectedType(type);
                  setFormData(prev => ({ ...prev, user_type: type }));
                }}
                className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
              >
                <div className={`${color} w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4`}>
                  <Icon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl mb-2 dark:text-white">{label}</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">Register as {label.toLowerCase()}</p>
              </button>
            ))}
          </div>
          
          <div className="text-center mt-8">
            <button
              onClick={onBackToLogin}
              className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 flex items-center justify-center"
            >
              <ArrowLeft className="w-4 h-4 mr-1" />
              Back to Login
            </button>
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
          {theme === 'light' ? 
            <div className="w-5 h-5 rounded-full bg-gray-700" /> : 
            <div className="w-5 h-5 rounded-full bg-yellow-400" />
          }
        </button>
      </div>
      
      <div className="w-full max-w-md">
        <button
          onClick={() => setSelectedType(null)}
          className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 mb-4 flex items-center"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to user type selection
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
              Create {selectedType === 'teacher' ? 'Teacher' : selectedType === 'parent' ? 'Parent' : 'Student'} Account
            </h2>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm mb-2 text-gray-700 dark:text-gray-300">Full Name</label>
              <div className="relative">
                <UserIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="John Doe"
                  className="w-full pl-11 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm mb-2 text-gray-700 dark:text-gray-300">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  placeholder="john@example.com"
                  className="w-full pl-11 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm mb-2 text-gray-700 dark:text-gray-300">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  placeholder="••••••••"
                  className="w-full pl-11 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm mb-2 text-gray-700 dark:text-gray-300">Confirm Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  placeholder="••••••••"
                  className="w-full pl-11 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                  required
                />
              </div>
            </div>

            {selectedType === 'student' && (
              <div>
                <label className="block text-sm mb-2 text-gray-700 dark:text-gray-300">Grade</label>
                <select
                  name="grade"
                  value={formData.grade}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                  required
                >
                  <option value="">Select Grade</option>
                  {Array.from({ length: 12 }, (_, i) => (
                    <option key={i + 1} value={`Grade ${i + 1}`}>
                      Grade {i + 1}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {selectedType === 'teacher' && (
              <>
                <div>
                  <label className="block text-sm mb-2 text-gray-700 dark:text-gray-300">Teacher Role</label>
                  <select
                    name="teacher_role"
                    value={formData.teacher_role}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                    required
                  >
                    <option value="">Select Role</option>
                    {teacherRoles.map(role => (
                      <option key={role} value={role}>
                        {role.split('-').map(word => 
                          word.charAt(0).toUpperCase() + word.slice(1)
                        ).join(' ')}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm mb-2 text-gray-700 dark:text-gray-300">Subject</label>
                  <input
                    type="text"
                    name="teacher_subject"
                    value={formData.teacher_subject}
                    onChange={handleInputChange}
                    placeholder="Mathematics"
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                    required
                  />
                </div>

                {formData.teacher_role === 'class-head' && (
                  <div>
                    <label className="block text-sm mb-2 text-gray-700 dark:text-gray-300">Class</label>
                    <input
                      type="text"
                      name="teacher_class"
                      value={formData.teacher_class}
                      onChange={handleInputChange}
                      placeholder="10"
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                      required
                    />
                  </div>
                )}
              </>
            )}

            <button
              type="submit"
              className={`w-full ${userTypes.find(t => t.type === selectedType)?.color.replace('bg-', 'bg-')} hover:${userTypes.find(t => t.type === selectedType)?.color.replace('bg-', 'bg-').replace('500', '600')} text-white py-3 rounded-lg transition-colors disabled:opacity-50`}
              disabled={loading}
            >
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>

          <div className="text-center mt-6">
            <button
              onClick={onBackToLogin}
              className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 flex items-center justify-center"
            >
              <ArrowLeft className="w-4 h-4 mr-1" />
              Already have an account? Login
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}