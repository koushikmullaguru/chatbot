import { useState, useEffect } from 'react';
import { BookOpen, FileText, Target, Clock, ArrowRight, Zap, Calendar } from 'lucide-react';
import { AddToPlannerButton } from './AddToPlannerButton';
import { academicService, Class, Subject, Chapter } from '../api/academicService';
import { User } from '../types';

interface ExamConfig {
  examType: string;
  subject: string;
  chapter: string;
  difficulty: string;
  duration: number;
  questionCount: number;
}

interface Task {
  id: string;
  subject: string;
  title: string;
  description: string;
  dueDate: string;
  reminderDate: string;
  reminderTime: string;
  priority: 'low' | 'medium' | 'high';
  status: 'pending' | 'in-progress' | 'completed';
  createdAt: string;
}

interface ExamSetupProps {
  onStartExam: (config: ExamConfig) => void;
  onAddTask?: (task: Omit<Task, 'id' | 'createdAt'>) => void;
  isDark?: boolean;
  user?: User;
  selectedProfile?: any;
}

export function ExamSetup({ onStartExam, onAddTask, isDark = false, user, selectedProfile }: ExamSetupProps) {
  const [selectedExamType, setSelectedExamType] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('');
  const [selectedChapter, setSelectedChapter] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState('');
  
  // Data from backend
  const [classes, setClasses] = useState<Class[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  
  // Loading states
  const [loadingClasses, setLoadingClasses] = useState(true);
  const [loadingSubjects, setLoadingSubjects] = useState(false);
  const [loadingChapters, setLoadingChapters] = useState(false);

  // Fetch classes on component mount
  useEffect(() => {
    const fetchClasses = async () => {
      try {
        setLoadingClasses(true);
        const classesData = await academicService.getClasses();
        setClasses(classesData);
      } catch (error) {
        console.error('Error fetching classes:', error);
        // Fallback to default classes if API fails
        setClasses([
          { id: '1', name: '6th Grade' },
          { id: '2', name: '7th Grade' },
          { id: '3', name: '8th Grade' },
          { id: '4', name: '9th Grade' },
          { id: '5', name: '10th Grade' },
          { id: '6', name: '11th Grade' },
          { id: '7', name: '12th Grade' }
        ]);
      } finally {
        setLoadingClasses(false);
      }
    };

    fetchClasses();
  }, []);

  // Fetch subjects when a class is selected
  useEffect(() => {
    const fetchSubjects = async () => {
      if (!selectedExamType) {
        setSubjects([]);
        return;
      }

      try {
        setLoadingSubjects(true);
        
        // Get the user's class or use the first class as fallback
        let userClassId = '';
        const userGrade = selectedProfile?.grade || user?.grade || user?.normalized_grade;
        
        if (userGrade) {
          // Find the class that matches the user's grade
          const userClass = classes.find(cls => 
            cls.name.toLowerCase().includes(userGrade.toLowerCase()) ||
            cls.name.replace(/\s+/g, '').toLowerCase().includes(userGrade.toLowerCase())
          );
          if (userClass) {
            userClassId = userClass.id;
          }
        }
        
        // If no user class found, use the first class as fallback
        if (!userClassId && classes.length > 0) {
          userClassId = classes[0].id;
        }
        
        // If still no class ID, use a default
        if (!userClassId) {
          userClassId = '1';
        }
        
        const subjectsData = await academicService.getSubjects(userClassId);
        setSubjects(subjectsData);
      } catch (error) {
        console.error('Error fetching subjects:', error);
        // Fallback to default subjects if API fails
        setSubjects([
          { id: '1', name: 'Mathematics', class_id: '1' },
          { id: '2', name: 'Science', class_id: '1' },
          { id: '3', name: 'English', class_id: '1' },
          { id: '4', name: 'History', class_id: '1' },
          { id: '5', name: 'Geography', class_id: '1' },
          { id: '6', name: 'Computer Science', class_id: '1' }
        ]);
      } finally {
        setLoadingSubjects(false);
      }
    };

    fetchSubjects();
  }, [selectedExamType, classes, user, selectedProfile]);

  // Fetch chapters when a subject is selected
  useEffect(() => {
    const fetchChapters = async () => {
      if (!selectedSubject) {
        setChapters([]);
        return;
      }

      try {
        setLoadingChapters(true);
        const chaptersData = await academicService.getChapters(selectedSubject);
        setChapters(chaptersData);
      } catch (error) {
        console.error('Error fetching chapters:', error);
        // Fallback to default chapters if API fails
        const subjectChapters: Record<string, Chapter[]> = {
          '1': [ // Mathematics
            { id: '1', name: 'Number Systems', subject_id: '1' },
            { id: '2', name: 'Algebra', subject_id: '1' },
            { id: '3', name: 'Geometry', subject_id: '1' },
            { id: '4', name: 'Mensuration', subject_id: '1' },
            { id: '5', name: 'Statistics', subject_id: '1' }
          ],
          '2': [ // Science
            { id: '6', name: 'Matter in Our Surroundings', subject_id: '2' },
            { id: '7', name: 'Is Matter Around Us Pure', subject_id: '2' },
            { id: '8', name: 'Atoms and Molecules', subject_id: '2' },
            { id: '9', name: 'Structure of the Atom', subject_id: '2' },
            { id: '10', name: 'The Fundamental Unit of Life', subject_id: '2' }
          ]
          // Add more subjects as needed
        };
        setChapters(subjectChapters[selectedSubject] || []);
      } finally {
        setLoadingChapters(false);
      }
    };

    fetchChapters();
  }, [selectedSubject]);

  const examTypes = [
    {
      id: 'mcq',
      name: 'Multiple Choice Questions',
      description: 'Objective questions with 4 options',
      icon: '✓',
      duration: 30,
      questions: 20,
    },
    {
      id: 'descriptive',
      name: 'Descriptive Exam',
      description: 'Long-form written answers',
      icon: '✍️',
      duration: 60,
      questions: 5,
    },
    {
      id: 'mixed',
      name: 'Mixed Pattern',
      description: 'MCQ + Short Answer + Descriptive',
      icon: '📝',
      duration: 45,
      questions: 15,
    },
    {
      id: 'board-exam',
      name: 'Board Exam Pattern',
      description: 'Follows standard board exam format',
      icon: '🎓',
      duration: 90,
      questions: 25,
    },
    {
      id: 'competitive',
      name: 'Competitive Exam',
      description: 'Fast-paced competitive format',
      icon: '⚡',
      duration: 40,
      questions: 50,
    },
    {
      id: 'quick-test',
      name: 'Quick Test',
      description: 'Short quiz to test basics',
      icon: '⏱️',
      duration: 15,
      questions: 10,
    },
  ];

  const difficulties = [
    { id: 'easy', name: 'Easy', description: 'Basic concepts', color: 'bg-green-500' },
    { id: 'medium', name: 'Medium', description: 'Moderate difficulty', color: 'bg-yellow-500' },
    { id: 'hard', name: 'Hard', description: 'Advanced level', color: 'bg-red-500' },
  ];

  const selectedExamTypeData = examTypes.find(e => e.id === selectedExamType);
  const selectedSubjectName = subjects.find(s => s.id === selectedSubject)?.name || '';
  const selectedChapterName = chapters.find(c => c.id === selectedChapter)?.name || '';

  const handleStartExam = () => {
    if (selectedExamType && selectedSubject && selectedChapter && selectedDifficulty) {
      const examTypeData = examTypes.find(e => e.id === selectedExamType)!;
      onStartExam({
        examType: selectedExamType,
        subject: selectedSubjectName,
        chapter: selectedChapterName,
        difficulty: selectedDifficulty,
        duration: examTypeData.duration,
        questionCount: examTypeData.questions,
      });
    }
  };

  return (
    <div className="h-full overflow-y-auto bg-gradient-to-br from-purple-50 via-pink-50 to-indigo-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 px-6 py-12">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <FileText className="w-10 h-10 text-white" />
          </div>
          <h2 className="text-4xl mb-4 dark:text-white">Exam Preparation</h2>
          <p className="text-xl text-gray-600 dark:text-gray-300">
            Configure your exam pattern and get started
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-xl p-8 space-y-8">
          {/* Step 1: Select Exam Type */}
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
                <FileText className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h3 className="text-xl dark:text-white">Step 1: Select Exam Type</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">Choose the exam pattern you want to practice</p>
              </div>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {examTypes.map((examType) => (
                <button
                  key={examType.id}
                  onClick={() => {
                    setSelectedExamType(examType.id);
                    setSelectedSubject('');
                    setSelectedChapter('');
                    setSelectedDifficulty('');
                  }}
                  className={`p-4 rounded-xl border-2 transition-all text-left group hover:shadow-lg ${
                    selectedExamType === examType.id
                      ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20 shadow-md'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="text-2xl">{examType.icon}</div>
                    <div className="flex-1">
                      <h4 className="mb-1 dark:text-white">{examType.name}</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">{examType.description}</p>
                      <div className="flex gap-3 text-xs text-gray-500 dark:text-gray-400">
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {examType.duration} min
                        </div>
                        <div className="flex items-center gap-1">
                          <Target className="w-3 h-3" />
                          {examType.questions} Q
                        </div>
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Step 2: Select Subject */}
          {selectedExamType && (
            <div className="animate-fadeIn">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-pink-100 dark:bg-pink-900/30 rounded-lg flex items-center justify-center">
                  <BookOpen className="w-6 h-6 text-pink-600 dark:text-pink-400" />
                </div>
                <div>
                  <h3 className="text-xl dark:text-white">Step 2: Select Subject</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Choose the subject for your exam</p>
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {loadingSubjects ? (
                  <div className="col-span-full text-center py-4">Loading subjects...</div>
                ) : (
                  subjects.map((subject) => (
                    <button
                      key={subject.id}
                      onClick={() => {
                        setSelectedSubject(subject.id);
                        setSelectedChapter('');
                        setSelectedDifficulty('');
                      }}
                      className={`p-4 rounded-xl border-2 transition-all ${
                        selectedSubject === subject.id
                          ? 'border-pink-500 bg-pink-50 dark:bg-pink-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                      }`}
                    >
                      <div className="text-sm dark:text-white">{subject.name}</div>
                    </button>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Step 3: Select Chapter */}
          {selectedSubject && (
            <div className="animate-fadeIn">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg flex items-center justify-center">
                    <Target className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
                  </div>
                  <div>
                    <h3 className="text-xl dark:text-white">Step 3: Select Chapter</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Pick the specific chapter to focus on</p>
                  </div>
                </div>
                {selectedChapter && onAddTask && (
                  <AddToPlannerButton
                    subject={selectedSubjectName}
                    topic={selectedChapterName}
                    onAddTask={(task) => {
                      onAddTask(task);
                      alert('Task added to your planner! View it by clicking the Planner button in the header.');
                    }}
                    isDark={isDark}
                  />
                )}
              </div>
              <div className="grid md:grid-cols-2 gap-3">
                {loadingChapters ? (
                  <div className="col-span-full text-center py-4">Loading chapters...</div>
                ) : (
                  chapters.map((chapter) => (
                    <button
                      key={chapter.id}
                      onClick={() => {
                        setSelectedChapter(chapter.id);
                        setSelectedDifficulty('');
                      }}
                      className={`p-3 rounded-xl border-2 transition-all text-left ${
                        selectedChapter === chapter.id
                          ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                      }`}
                    >
                      <div className="text-sm dark:text-white">{chapter.name}</div>
                    </button>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Step 4: Select Difficulty */}
          {selectedChapter && (
            <div className="animate-fadeIn">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center">
                  <Zap className="w-6 h-6 text-orange-600 dark:text-orange-400" />
                </div>
                <div>
                  <h3 className="text-xl dark:text-white">Step 4: Select Difficulty Level</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Choose how challenging you want the exam</p>
                </div>
              </div>
              <div className="grid md:grid-cols-3 gap-4">
                {difficulties.map((difficulty) => (
                  <button
                    key={difficulty.id}
                    onClick={() => setSelectedDifficulty(difficulty.id)}
                    className={`p-5 rounded-xl border-2 transition-all text-left ${
                      selectedDifficulty === difficulty.id
                        ? 'border-orange-500 bg-orange-50 dark:bg-orange-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                    }`}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <div className={`w-3 h-3 rounded-full ${difficulty.color}`} />
                      <h4 className="dark:text-white">{difficulty.name}</h4>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{difficulty.description}</p>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Start Exam Button */}
          {selectedDifficulty && (
            <div className="pt-6 border-t border-gray-200 dark:border-gray-700 animate-fadeIn">
              <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-2xl p-6">
                <h4 className="mb-3 dark:text-white">Exam Configuration Summary</h4>
                <div className="grid md:grid-cols-2 gap-4 mb-4 text-sm">
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Exam Type:</span>
                    <span className="ml-2 dark:text-white">{selectedExamTypeData?.name}</span>
                  </div>
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Subject:</span>
                    <span className="ml-2 dark:text-white">{selectedSubjectName}</span>
                  </div>
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Chapter:</span>
                    <span className="ml-2 dark:text-white">{selectedChapterName}</span>
                  </div>
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Difficulty:</span>
                    <span className="ml-2 capitalize dark:text-white">{selectedDifficulty}</span>
                  </div>
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Duration:</span>
                    <span className="ml-2 dark:text-white">{selectedExamTypeData?.duration} minutes</span>
                  </div>
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Questions:</span>
                    <span className="ml-2 dark:text-white">{selectedExamTypeData?.questions}</span>
                  </div>
                </div>
                <button
                  onClick={handleStartExam}
                  className="w-full flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl hover:from-purple-600 hover:to-pink-600 transition-all shadow-lg hover:shadow-xl"
                >
                  <span className="text-lg">Start Exam</span>
                  <ArrowRight className="w-6 h-6" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}