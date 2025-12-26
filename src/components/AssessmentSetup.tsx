import { useState, useEffect } from 'react';
import { BookOpen, Clock, Target, Brain, Award, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import { getSubjectsByClass, generateQuiz } from '../api/service';

export type AssessmentType = 'worksheet' | 'quiz' | 'exam';

export interface AssessmentConfig {
  type: AssessmentType;
  subject: string;
  subjectId: string;
  chapters: string[];
  chapterIds: string[];
  classId: string;
  duration: number;
  questionCount: number;
  difficulty: 'easy' | 'medium' | 'hard';
  includeExplanations?: boolean;
  questionTypes?: string[];
  questions?: any[];
}

interface AssessmentSetupProps {
  type: AssessmentType;
  onStartAssessment: (config: AssessmentConfig) => void;
  userGrade?: string;
}

const assessmentInfo = {
  worksheet: {
    title: 'Worksheet Practice',
    subtitle: 'Practice & Learning',
    icon: FileText,
    color: 'blue',
    stakes: 'Low Stakes',
    goal: 'Build skills through practice',
    defaultDuration: 15,
    defaultQuestions: 10,
    frequency: 'Daily/Weekly',
    features: ['Step-by-step solutions', 'Unlimited attempts', 'Instant feedback', 'Progress tracking']
  },
  quiz: {
    title: 'Quick Quiz',
    subtitle: 'Understanding Check',
    icon: Brain,
    color: 'purple',
    stakes: 'Medium Stakes',
    goal: 'Test your understanding',
    defaultDuration: 10,
    defaultQuestions: 5,
    frequency: 'Weekly/Unit-based',
    features: ['Auto-graded', 'Time-bound', 'Score report', 'Topic mastery']
  },
  exam: {
    title: 'Formal Exam',
    subtitle: 'Comprehensive Evaluation',
    icon: Award,
    color: 'red',
    stakes: 'High Stakes',
    goal: 'Formal assessment',
    defaultDuration: 60,
    defaultQuestions: 30,
    frequency: 'Term/Annual',
    features: ['Timed environment', 'No retakes', 'Detailed analytics', 'Performance report']
  }
};

const subjects = [
  'Mathematics',
  'Physics',
  'Chemistry',
  'Biology',
  'English',
  'History',
  'Geography',
  'Computer Science'
];

const topicsBySubject: Record<string, string[]> = {
  'Mathematics': ['Algebra', 'Geometry', 'Trigonometry', 'Calculus', 'Statistics', 'Probability'],
  'Physics': ['Mechanics', 'Thermodynamics', 'Optics', 'Electromagnetism', 'Modern Physics'],
  'Chemistry': ['Organic Chemistry', 'Inorganic Chemistry', 'Physical Chemistry', 'Analytical Chemistry'],
  'Biology': ['Cell Biology', 'Genetics', 'Evolution', 'Ecology', 'Human Physiology'],
  'English': ['Grammar', 'Literature', 'Writing', 'Comprehension', 'Poetry'],
  'History': ['Ancient History', 'Medieval History', 'Modern History', 'World Wars', 'Indian Independence'],
  'Geography': ['Physical Geography', 'Human Geography', 'Climate', 'Resources', 'Mapping'],
  'Computer Science': ['Programming', 'Data Structures', 'Algorithms', 'Databases', 'Networks']
};

const questionTypeOptions = [
  { id: 'multiple-choice', name: 'Multiple Choice', description: 'Select one correct answer from options' },
  { id: 'short-answer', name: 'Short Answer', description: 'Brief response to a question' },
  { id: 'long-answer', name: 'Long Answer', description: 'Detailed explanation or analysis' },
  { id: 'true-false', name: 'True/False', description: 'Determine if a statement is true or false' },
  { id: 'fill-blank', name: 'Fill in the Blank', description: 'Complete the missing information' },
  { id: 'matching', name: 'Matching', description: 'Match items from two columns' }
];

export function AssessmentSetup({ type, onStartAssessment, userGrade }: AssessmentSetupProps) {
  const info = assessmentInfo[type];
  const Icon = info.icon;
  
  const [subjects, setSubjects] = useState<Array<{id: string, name: string}>>([]);
  const [subject, setSubject] = useState<{id: string, name: string}>({id: '', name: 'Mathematics'});
  const [chapters, setChapters] = useState<Array<{id: string, name: string}>>([]);
  const [selectedChapters, setSelectedChapters] = useState<Array<{id: string, name: string}>>([]);
  const [classId, setClassId] = useState<string>('');
  const [duration, setDuration] = useState(info.defaultDuration);
  const [questionCount, setQuestionCount] = useState(info.defaultQuestions);
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium');
  const [includeExplanations, setIncludeExplanations] = useState(type === 'worksheet');
  const [selectedQuestionTypes, setSelectedQuestionTypes] = useState<string[]>(
    type === 'quiz' ? ['multiple-choice'] : ['multiple-choice']
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chaptersLoading, setChaptersLoading] = useState(false);

  const toggleChapter = (chapter: {id: string, name: string}) => {
    setSelectedChapters(prev =>
      prev.some(c => c.id === chapter.id)
        ? prev.filter(c => c.id !== chapter.id)
        : [...prev, chapter]
    );
  };

  const toggleQuestionType = (questionTypeId: string) => {
    setSelectedQuestionTypes(prev =>
      prev.includes(questionTypeId)
        ? prev.filter(id => id !== questionTypeId)
        : [...prev, questionTypeId]
    );
  };

  // Fetch chapters based on selected subject
  useEffect(() => {
    const fetchChapters = async () => {
      if (!subject || !subject.id) {
        setChapters([]);
        return;
      }

      try {
        setChaptersLoading(true);
        
        // Get chapters for the selected subject
        const response = await fetch(`http://localhost:8000/api/v1/academic/chapters?subject_id=${encodeURIComponent(subject.id)}`);
        
        if (response.ok) {
          const data = await response.json();
          if (Array.isArray(data)) {
            setChapters(data.length > 0 ? data : []);
          } else {
            // Fallback to default chapters if API response is invalid
            setChapters([]);
          }
        } else {
          console.error('Failed to fetch chapters:', response.statusText);
          setChapters([]);
        }
      } catch (err) {
        console.error('Failed to fetch chapters:', err);
        setChapters([]);
      } finally {
        setChaptersLoading(false);
      }
    };

    fetchChapters();
  }, [subject]);

  // Fetch subjects based on user's grade
  useEffect(() => {
    const fetchSubjects = async () => {
      if (!userGrade) {
        // Fallback to default subjects if no grade is provided
        setSubjects([{id: 'default', name: 'Mathematics'}]);
        setClassId('default');
        return;
      }

      try {
        setLoading(true);
        setError(null);
        
        // Format grade for API (remove spaces, convert to lowercase if needed)
        const formattedGrade = userGrade.replace(/\s+/g, '');
        const response = await getSubjectsByClass(formattedGrade);
        
        if (response && Array.isArray(response)) {
          // Store the subjects with their IDs
          setSubjects(response);
          
          // Set first subject as default if current subject is not in the list
          if (response.length > 0 && (!subject.id || !response.some(s => s.id === subject.id))) {
            setSubject(response[0]);
          }
          
          // Try to get the class ID from the API response
          if (response.length > 0 && response[0].class_id) {
            setClassId(response[0].class_id);
          } else {
            setClassId(formattedGrade);
          }
        } else {
          // Fallback to default subjects if API response is invalid
          setSubjects([{id: 'default', name: 'Mathematics'}]);
          setClassId('default');
        }
      } catch (err) {
        console.error('Failed to fetch subjects:', err);
        setError('Failed to load subjects. Using default subjects.');
        // Fallback to default subjects on error
        setSubjects([{id: 'default', name: 'Mathematics'}]);
        setClassId('default');
      } finally {
        setLoading(false);
      }
    };

    fetchSubjects();
  }, [userGrade]);

  const handleStart = async () => {
    if (selectedChapters.length === 0) {
      alert('Please select at least one chapter');
      return;
    }

    if (type !== 'quiz' && selectedQuestionTypes.length === 0) {
      alert('Please select at least one question type');
      return;
    }

    try {
      // For now, we'll just use the first chapter for the API call
      // In a real implementation, you might want to make multiple API calls or modify the backend
      const chapter = selectedChapters[0];
      
      // Generate quiz using the API
      const quizData = {
        class_id: classId,
        subject_id: subject.id,
        chapter_id: chapter.id,
        difficulty: difficulty,
        num_questions: questionCount,
        question_types: type === 'quiz' ? ['multiple-choice'] : selectedQuestionTypes,
        duration: duration
      };
      
      const response: any = await generateQuiz(quizData);
      console.log('Generated quiz:', response);
      
      // Pass the generated quiz data to the assessment component
      onStartAssessment({
        type,
        subject: subject.name,
        subjectId: subject.id,
        chapters: selectedChapters.map(c => c.name),
        chapterIds: selectedChapters.map(c => c.id),
        classId: classId,
        duration,
        questionCount,
        difficulty,
        includeExplanations,
        questionTypes: type === 'quiz' ? ['multiple-choice'] : selectedQuestionTypes,
        // Include the generated questions if available
        questions: response.questions || []
      });
    } catch (error) {
      console.error('Error generating quiz:', error);
      alert('Failed to generate quiz. Please try again.');
      
      // Fallback to starting assessment without generated questions
      onStartAssessment({
        type,
        subject: subject.name,
        subjectId: subject.id,
        chapters: selectedChapters.map(c => c.name),
        chapterIds: selectedChapters.map(c => c.id),
        classId: classId,
        duration,
        questionCount,
        difficulty,
        includeExplanations,
        questionTypes: type === 'quiz' ? ['multiple-choice'] : selectedQuestionTypes
      });
    }
  };

  const getColorClasses = () => {
    const colors = {
      blue: {
        bg: 'bg-blue-50 dark:bg-blue-900/20',
        border: 'border-blue-200 dark:border-blue-800',
        text: 'text-blue-600 dark:text-blue-400',
        button: 'bg-blue-500 hover:bg-blue-600',
        icon: 'text-blue-500'
      },
      purple: {
        bg: 'bg-purple-50 dark:bg-purple-900/20',
        border: 'border-purple-200 dark:border-purple-800',
        text: 'text-purple-600 dark:text-purple-400',
        button: 'bg-purple-500 hover:bg-purple-600',
        icon: 'text-purple-500'
      },
      red: {
        bg: 'bg-red-50 dark:bg-red-900/20',
        border: 'border-red-200 dark:border-red-800',
        text: 'text-red-600 dark:text-red-400',
        button: 'bg-red-500 hover:bg-red-600',
        icon: 'text-red-500'
      }
    };
    return colors[info.color as keyof typeof colors];
  };

  const colors = getColorClasses();

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      {/* Header */}
      <div className={`${colors.bg} rounded-2xl p-6 mb-6 border ${colors.border}`}>
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className={`w-16 h-16 ${colors.bg} rounded-2xl flex items-center justify-center border-2 ${colors.border}`}>
              <Icon className={`w-8 h-8 ${colors.icon}`} />
            </div>
            <div>
              <h1 className="text-3xl mb-1 dark:text-white">{info.title}</h1>
              <p className={`text-sm ${colors.text}`}>{info.subtitle}</p>
            </div>
          </div>
          <div className={`px-4 py-2 ${colors.bg} rounded-full border ${colors.border}`}>
            <span className={`text-sm ${colors.text}`}>{info.stakes}</span>
          </div>
        </div>

        <div className="grid md:grid-cols-4 gap-4 mb-4">
          <div className="flex items-center gap-2">
            <Target className={`w-5 h-5 ${colors.icon}`} />
            <div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Goal</div>
              <div className="text-sm dark:text-white">{info.goal}</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Clock className={`w-5 h-5 ${colors.icon}`} />
            <div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Duration</div>
              <div className="text-sm dark:text-white">{info.defaultDuration} minutes</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <FileText className={`w-5 h-5 ${colors.icon}`} />
            <div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Questions</div>
              <div className="text-sm dark:text-white">{info.defaultQuestions} problems</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <AlertCircle className={`w-5 h-5 ${colors.icon}`} />
            <div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Frequency</div>
              <div className="text-sm dark:text-white">{info.frequency}</div>
            </div>
          </div>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-3">
          {info.features.map((feature, idx) => (
            <div key={idx} className="flex items-center gap-2 text-sm dark:text-gray-300">
              <CheckCircle className={`w-4 h-4 ${colors.icon}`} />
              <span>{feature}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Configuration */}
      <div className="grid md:grid-cols-2 gap-6 mb-6">
        {/* Left Column */}
        <div className="space-y-6">
          {/* Subject Selection */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md border border-gray-100 dark:border-gray-700">
            <label className="block mb-3 dark:text-white flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-gray-400" />
              Select Subject
            </label>
            {loading ? (
              <div className="flex items-center justify-center py-3">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                <span className="ml-2 text-gray-600 dark:text-gray-400">Loading subjects...</span>
              </div>
            ) : error ? (
              <div className="text-red-500 text-sm py-2">{error}</div>
            ) : (
              <select
                value={subject.id}
                onChange={(e) => {
                  const selectedSubject = subjects.find(s => s.id === e.target.value) || subjects[0];
                  setSubject(selectedSubject);
                  setSelectedChapters([]);
                }}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              >
                {subjects.map(subj => (
                  <option key={subj.id} value={subj.id}>{subj.name}</option>
                ))}
              </select>
            )}
          </div>

          {/* Duration & Questions */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md border border-gray-100 dark:border-gray-700">
            <h3 className="mb-4 dark:text-white">Test Configuration</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm mb-2 dark:text-gray-300">
                  Duration: {duration} minutes
                </label>
                <input
                  type="range"
                  min={type === 'worksheet' ? 5 : type === 'quiz' ? 5 : 30}
                  max={type === 'worksheet' ? 30 : type === 'quiz' ? 20 : 180}
                  step={5}
                  value={duration}
                  onChange={(e) => setDuration(Number(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
                  <span>{type === 'worksheet' ? '5' : type === 'quiz' ? '5' : '30'} min</span>
                  <span>{type === 'worksheet' ? '30' : type === 'quiz' ? '20' : '180'} min</span>
                </div>
              </div>

              <div>
                <label className="block text-sm mb-2 dark:text-gray-300">
                  Number of Questions: {questionCount}
                </label>
                <input
                  type="range"
                  min={type === 'worksheet' ? 5 : type === 'quiz' ? 3 : 20}
                  max={type === 'worksheet' ? 20 : type === 'quiz' ? 10 : 50}
                  step={type === 'worksheet' ? 1 : type === 'quiz' ? 1 : 5}
                  value={questionCount}
                  onChange={(e) => setQuestionCount(Number(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
                  <span>{type === 'worksheet' ? '5' : type === 'quiz' ? '3' : '20'} questions</span>
                  <span>{type === 'worksheet' ? '20' : type === 'quiz' ? '10' : '50'} questions</span>
                </div>
              </div>
            </div>
          </div>

          {/* Difficulty */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md border border-gray-100 dark:border-gray-700">
            <h3 className="mb-4 dark:text-white">Difficulty Level</h3>
            <div className="grid grid-cols-3 gap-3">
              {['easy', 'medium', 'hard'].map((level) => (
                <button
                  key={level}
                  onClick={() => setDifficulty(level as any)}
                  className={`px-4 py-3 rounded-lg border-2 transition-all ${
                    difficulty === level
                      ? `${colors.border} ${colors.bg} ${colors.text}`
                      : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  {level.charAt(0).toUpperCase() + level.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Question Types - Only show for worksheet mode */}
          {type === 'worksheet' && (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md border border-gray-100 dark:border-gray-700">
              <h3 className="mb-4 dark:text-white">
                Question Types
                {selectedQuestionTypes.length > 0 && (
                  <span className={`ml-2 text-sm ${colors.text}`}>
                    ({selectedQuestionTypes.length} selected)
                  </span>
                )}
              </h3>
              <div className="space-y-3">
                {questionTypeOptions.map((questionType) => (
                  <label
                    key={questionType.id}
                    className={`flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-all ${
                      selectedQuestionTypes.includes(questionType.id)
                        ? `${colors.border} ${colors.bg}`
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedQuestionTypes.includes(questionType.id)}
                      onChange={() => toggleQuestionType(questionType.id)}
                      className="w-5 h-5 text-blue-500 rounded"
                    />
                    <div>
                      <div className="dark:text-white">{questionType.name}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">{questionType.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Options */}
          {type === 'worksheet' && (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md border border-gray-100 dark:border-gray-700">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeExplanations}
                  onChange={(e) => setIncludeExplanations(e.target.checked)}
                  className="w-5 h-5 text-blue-500 rounded"
                />
                <div>
                  <div className="dark:text-white">Include step-by-step explanations</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">Show detailed solutions for each problem</div>
                </div>
              </label>
            </div>
          )}
        </div>

        {/* Right Column - Chapter Selection */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md border border-gray-100 dark:border-gray-700">
          <h3 className="mb-4 dark:text-white">
            Select Chapters
            {selectedChapters.length > 0 && (
              <span className={`ml-2 text-sm ${colors.text}`}>
                ({selectedChapters.length} selected)
              </span>
            )}
          </h3>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {chaptersLoading ? (
              <div className="flex items-center justify-center py-3">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                <span className="ml-2 text-gray-600 dark:text-gray-400">Loading chapters...</span>
              </div>
            ) : chapters.length > 0 ? (
              chapters.map((chapter) => (
                <label
                  key={chapter.id}
                  className={`flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-all ${
                    selectedChapters.some(c => c.id === chapter.id)
                      ? `${colors.border} ${colors.bg}`
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedChapters.some(c => c.id === chapter.id)}
                    onChange={() => toggleChapter(chapter)}
                    className="w-5 h-5 text-blue-500 rounded"
                  />
                  <span className="dark:text-white">{chapter.name}</span>
                </label>
              ))
            ) : (
              <div className="text-center py-4 text-gray-500 dark:text-gray-400">
                {subject ? `No chapters found for ${subject}` : 'Please select a subject first'}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Start Button */}
      <div className="flex justify-center">
        <button
          onClick={handleStart}
          disabled={selectedChapters.length === 0 || (type !== 'quiz' && selectedQuestionTypes.length === 0)}
          className={`px-8 py-4 ${colors.button} text-white rounded-xl hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-3 text-lg`}
        >
          <Icon className="w-6 h-6" />
          Start {info.title}
        </button>
      </div>
    </div>
  );
}
