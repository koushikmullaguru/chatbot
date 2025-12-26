import { useState, useEffect, useRef } from 'react';
import { Quiz, QuizQuestion } from '../types';
import { Check, X, ArrowRight, RotateCcw, Trophy, Loader } from 'lucide-react';
import { generateQuiz, submitQuiz } from '../api/service';

// Extend the QuizQuestion type to include the database question ID
interface ExtendedQuizQuestion extends QuizQuestion {
  dbQuestionId?: string;
}

interface QuizModeProps {
  onComplete: () => void;
  quizParams?: {
    class_id: string;
    subject_id: string;
    chapter_id: string;
    difficulty: string;
    num_questions: number;
    question_types: string[];
    duration: number;
  };
  studentProfileId?: string;
}

// Define the API response interface
interface QuizApiResponse {
  id?: string;
  assessment_id?: string;
  class?: string;
  subject?: string;
  chapter?: string;
  difficulty?: string;
  num_questions?: number;
  duration?: number;
  questions?: QuizQuestion[];
  error?: string;
  message?: string;
}

// Update the Quiz interface to use ExtendedQuizQuestion
interface ExtendedQuiz {
  id: string;
  title: string;
  totalQuestions: number;
  questions: ExtendedQuizQuestion[];
}

export function QuizModeFinal({ onComplete, quizParams, studentProfileId }: QuizModeProps) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({});
  const [showResults, setShowResults] = useState(false);
  const [shortAnswerInput, setShortAnswerInput] = useState('');
  const [quiz, setQuiz] = useState<ExtendedQuiz | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [quizGenerated, setQuizGenerated] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);
  
  // Debug log to check component state
  console.log('QuizMode render state:', { quiz, isLoading, error, quizGenerated });

  // Add a useEffect to log state changes
  useEffect(() => {
    console.log('QuizMode state changed:', { quiz, isLoading, error, quizGenerated });
  }, [quiz, isLoading, error, quizGenerated]);

  useEffect(() => {
    // Add a flag to prevent multiple API calls
    let isMounted = true;
    let requestController = new AbortController();
    
    const fetchQuiz = async () => {
      // Check if quiz has already been generated
      if (quiz) {
        console.log('Quiz already exists, skipping API call');
        return;
      }
      
      if (!quizParams) {
        setError('No quiz parameters provided');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        setIsRetrying(false);
        
        // Call the generate quiz API
        const response = await generateQuiz(quizParams) as QuizApiResponse;
        
        // Only update state if component is still mounted and request wasn't cancelled
        if (!isMounted || requestController.signal.aborted) return;
        
        // Log the entire response for debugging
        console.log('Full API response:', response);
        
        // Check if response has an error
        if (response.error) {
          console.error('API returned an error:', response.error);
          setError(`Failed to generate quiz: ${response.error}`);
          setIsLoading(false);
          return;
        }
        
        // Check if response has questions
        if (!response.questions || !Array.isArray(response.questions) || response.questions.length === 0) {
          console.error('API response does not contain valid questions:', response);
          setError('Failed to generate quiz questions. Please try again.');
          setIsLoading(false);
          return;
        }
        
        console.log('Response questions:', response?.questions);
        console.log('Questions type:', typeof response?.questions);
        console.log('Is questions an array:', Array.isArray(response?.questions));
        console.log('Questions length:', response?.questions?.length);
        
        // Ensure questions is an array
        const questions = Array.isArray(response.questions) ? response.questions : [response.questions];
        console.log('Processed questions array:', questions);
        
        // Transform the API response to match the Quiz interface
        const transformedQuiz: Quiz = {
          id: response.assessment_id || response.id || `quiz-${Date.now()}`,
          title: `${response.subject || 'General'} Quiz - ${response.chapter || 'General Knowledge'}`,
          totalQuestions: questions.length,
          questions: questions.map((q: any, index: number) => {
            // Log the question object for debugging
            console.log(`Question ${index + 1}:`, q);
            console.log(`Question ${index + 1} keys:`, Object.keys(q));
            
            // Ensure question text is properly extracted
            let questionText = '';
            if (q.question) {
              questionText = q.question;
            } else if (q.text) {
              questionText = q.text;
            } else if (q.title) {
              questionText = q.title;
            } else if (q.prompt) {
              questionText = q.prompt;
            }
            
            // Log if question text is missing
            if (!questionText) {
              console.warn(`Question ${index + 1} is missing question text. Available fields:`, Object.keys(q));
            }
            
            // Log options structure
            console.log(`Question ${index + 1} options:`, q.options);
            
            // Process options to ensure they're strings
            let processedOptions: string[] = [];
            if (q.options) {
              if (Array.isArray(q.options)) {
                processedOptions = q.options.map((option: any) =>
                  typeof option === 'string' ? option : String(option)
                );
              } else if (typeof q.options === 'object') {
                // If options is an object, try to extract values
                processedOptions = Object.values(q.options).map((val: any) =>
                  typeof val === 'string' ? val : String(val)
                );
              }
            }
            
            console.log(`Question ${index + 1} processed options:`, processedOptions);
            console.log(`Question ${index + 1} correctAnswer:`, q.correctAnswer);
            console.log(`Question ${index + 1} correctAnswer type:`, typeof q.correctAnswer);
            
            // Process correctAnswer to ensure it's in the right format
            let processedCorrectAnswer = q.correctAnswer;
            if (q.type === 'multiple-choice' && typeof q.correctAnswer === 'string') {
              // If correctAnswer is a string but question type is multiple-choice,
              // it might need to be converted to an array
              try {
                processedCorrectAnswer = JSON.parse(q.correctAnswer);
              } catch (e) {
                // If parsing fails, keep it as is
                console.warn(`Failed to parse correctAnswer for question ${index + 1}:`, e);
              }
            }
            
            console.log(`Question ${index + 1} processed correctAnswer:`, processedCorrectAnswer);
            
            return {
              // Use the actual question ID from the database if available
              id: q.id || `q${index + 1}`,
              // Store the database question ID separately for submission
              dbQuestionId: q.id || `q${index + 1}`,
              type: q.type || 'single-choice',
              question: questionText,
              options: processedOptions,
              correctAnswer: processedCorrectAnswer || '',
              explanation: q.explanation || ''
            };
          })
        };
        
        console.log('Setting quiz state:', transformedQuiz);
        // Use a callback to ensure we're using the latest state
        setQuiz(prevQuiz => {
          console.log('Previous quiz state:', prevQuiz);
          console.log('New quiz state:', transformedQuiz);
          return transformedQuiz;
        });
        
        // Use a timeout to ensure the state is updated before setting loading to false
        setTimeout(() => {
          if (isMounted) {
            // Mark quiz as generated only after successful completion
            setQuizGenerated(true);
            console.log('Quiz state set successfully');
            // Explicitly set loading to false
            setIsLoading(false);
          }
        }, 100);
      } catch (err) {
        console.error('Error generating quiz:', err);
        // Only update error state if component is still mounted and request wasn't cancelled
        if (isMounted && !requestController.signal.aborted) {
          setError('Failed to generate quiz. Please try again.');
        }
      } finally {
        // Only update loading state if component is still mounted and request wasn't cancelled
        if (isMounted && !requestController.signal.aborted) {
          setIsLoading(false);
        }
      }
    };

    fetchQuiz();
    
    // Cleanup function to set isMounted to false and abort any pending requests
    return () => {
      isMounted = false;
      requestController.abort();
    };
  }, [quizParams, quizGenerated]);

  // Show loading state
  if (isLoading) {
    console.log('Showing loading state');
    return (
      <div className="h-full flex items-center justify-center bg-gradient-to-br from-green-50 to-blue-50 dark:from-gray-900 dark:to-gray-800">
        <div className="text-center">
          <Loader className="w-12 h-12 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Generating quiz...</p>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="h-full flex items-center justify-center bg-gradient-to-br from-green-50 to-blue-50 dark:from-gray-900 dark:to-gray-800">
        <div className="text-center max-w-md">
          <div className="text-red-500 text-5xl mb-4">⚠️</div>
          <h2 className="text-2xl mb-2 dark:text-white">Error</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">{error}</p>
          <div className="flex gap-4 justify-center">
            <button
              onClick={() => {
                setError(null);
                setIsLoading(true);
                setQuizGenerated(false);
              }}
              disabled={isRetrying}
              className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
            >
              {isRetrying ? (
                <>
                  <Loader className="w-4 h-4 animate-spin inline mr-2" />
                  Retrying...
                </>
              ) : (
                'Try Again'
              )}
            </button>
            <button
              onClick={onComplete}
              className="px-6 py-3 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors dark:text-white"
            >
              Back to Chat
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Show empty state if no quiz
  if (!quiz) {
    console.log('Showing empty state - quiz is null');
    return (
      <div className="h-full flex items-center justify-center bg-gradient-to-br from-green-50 to-blue-50 dark:from-gray-900 dark:to-gray-800">
        <div className="text-center">
          <p className="text-gray-600 dark:text-gray-400">No quiz available</p>
        </div>
      </div>
    );
  }

  const currentQuestion = quiz.questions[currentQuestionIndex];

  const handleSingleChoice = (option: string) => {
    console.log(`Single choice selected: ${option} for question ${currentQuestion.id}`);
    setAnswers(prev => ({ ...prev, [currentQuestion.id]: option }));
  };

  const handleMultipleChoice = (option: string) => {
    const currentAnswers = (answers[currentQuestion.id] as string[]) || [];
    const newAnswers = currentAnswers.includes(option)
      ? currentAnswers.filter(a => a !== option)
      : [...currentAnswers, option];
    
    console.log(`Multiple choice selected: ${option} for question ${currentQuestion.id}`);
    console.log(`Current answers:`, currentAnswers);
    console.log(`New answers:`, newAnswers);
    
    setAnswers(prev => ({ ...prev, [currentQuestion.id]: newAnswers }));
  };

  const handleShortAnswer = () => {
    console.log(`Short answer submitted: ${shortAnswerInput.trim()} for question ${currentQuestion.id}`);
    setAnswers(prev => ({ ...prev, [currentQuestion.id]: shortAnswerInput.trim() }));
    setShortAnswerInput('');
  };

  const handleSubmitQuiz = async () => {
    if (!quiz || !studentProfileId) {
      console.error('Cannot submit quiz: missing quiz or student profile ID');
      return;
    }

    try {
      setIsSubmitting(true);
      
      // Prepare answers for submission
      const formattedAnswers = Object.entries(answers).map(([questionId, answer]) => {
        // Find the question to get the database question ID
        const question = quiz.questions.find(q => q.id === questionId);
        return {
          question_id: question?.dbQuestionId || questionId,
          answer: Array.isArray(answer) ? answer.join(', ') : String(answer),
          student_profile_id: studentProfileId
        };
      });
      
      console.log('Submitting quiz answers:', formattedAnswers);
      
      // Submit quiz answers
      const result = await submitQuiz(quiz.id, formattedAnswers, studentProfileId);
      console.log('Quiz submission result:', result);
      
      setShowResults(true);
    } catch (error) {
      console.error('Error submitting quiz:', error);
      setError('Failed to submit quiz. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleNext = () => {
    if (currentQuestion.type === 'short-answer' && shortAnswerInput.trim()) {
      handleShortAnswer();
    }

    if (currentQuestionIndex < quiz.questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
      setShortAnswerInput('');
    } else {
      handleSubmitQuiz();
    }
  };

  const checkAnswer = (question: QuizQuestion): boolean => {
    const userAnswer = answers[question.id];
    
    // Log for debugging
    console.log(`Checking answer for question ${question.id}:`);
    console.log(`User answer:`, userAnswer);
    console.log(`Correct answer:`, question.correctAnswer);
    console.log(`Question type:`, question.type);
    
    if (question.type === 'short-answer') {
      let correctAnswer = '';
      if (typeof question.correctAnswer === 'string') {
        correctAnswer = question.correctAnswer.toLowerCase().trim();
      } else if (question.correctAnswer) {
        correctAnswer = String(question.correctAnswer).toLowerCase().trim();
      }
      
      const userAnswerStr = (userAnswer as string || '').toLowerCase().trim();
      const isCorrect = userAnswerStr.includes(correctAnswer) || correctAnswer.includes(userAnswerStr);
      console.log(`Short answer comparison: "${userAnswerStr}" vs "${correctAnswer}" = ${isCorrect}`);
      return isCorrect;
    }
    
    if (question.type === 'multiple-choice') {
      let correctAnswers: string[] = [];
      if (Array.isArray(question.correctAnswer)) {
        correctAnswers = question.correctAnswer;
      } else if (typeof question.correctAnswer === 'string') {
        try {
          // Try to parse if it's a JSON string
          correctAnswers = JSON.parse(question.correctAnswer);
        } catch (e) {
          // If parsing fails, treat as a single answer
          correctAnswers = [question.correctAnswer];
        }
      } else if (question.correctAnswer) {
        correctAnswers = [String(question.correctAnswer)];
      }
      
      const userAnswers = (userAnswer as string[]) || [];
      const isCorrect = correctAnswers.length === userAnswers.length &&
        correctAnswers.every(a => userAnswers.includes(a));
      console.log(`Multiple choice comparison:`, { correctAnswers, userAnswers, isCorrect });
      return isCorrect;
    }
    
    // For single choice
    let correctAnswer = '';
    if (typeof question.correctAnswer === 'string') {
      correctAnswer = question.correctAnswer;
    } else if (question.correctAnswer) {
      correctAnswer = String(question.correctAnswer);
    }
    
    const isCorrect = String(userAnswer) === correctAnswer;
    console.log(`Single choice comparison: "${userAnswer}" vs "${correctAnswer}" = ${isCorrect}`);
    return isCorrect;
  };

  const calculateScore = () => {
    const correct = quiz.questions.filter(q => checkAnswer(q)).length;
    const percentage = Math.round((correct / quiz.totalQuestions) * 100);
    return { correct, percentage };
  };

  const canProceed = () => {
    if (currentQuestion.type === 'short-answer') {
      return shortAnswerInput.trim().length > 0;
    }
    return answers[currentQuestion.id] !== undefined && 
      (currentQuestion.type !== 'multiple-choice' || 
       (answers[currentQuestion.id] as string[])?.length > 0);
  };

  if (showResults) {
    const { correct, percentage } = calculateScore();
    
    return (
      <div className="h-full overflow-y-auto bg-gradient-to-br from-purple-50 to-pink-50 dark:from-gray-900 dark:to-gray-800 px-6 py-12">
        <div className="max-w-4xl mx-auto">
          {/* Results Header */}
          <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-xl p-8 mb-8 text-center">
            <Trophy className="w-20 h-20 text-yellow-500 mx-auto mb-4" />
            <h2 className="text-4xl mb-2 dark:text-white">Quiz Complete!</h2>
            <div className="text-6xl my-6 dark:text-white">{percentage}%</div>
            <p className="text-xl text-gray-600 dark:text-gray-300 mb-6">
              You got {correct} out of {quiz.totalQuestions} questions correct
            </p>
            
            <div className="flex gap-4 justify-center">
              <button
                onClick={() => {
                  setCurrentQuestionIndex(0);
                  setAnswers({});
                  setShowResults(false);
                  setShortAnswerInput('');
                  setQuiz(null);
                  setQuizGenerated(false);
                  setIsLoading(true);
                  setIsRetrying(true);
                }}
                className="flex items-center gap-2 px-6 py-3 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
              >
                <RotateCcw className="w-5 h-5" />
                Retake Quiz
              </button>
              <button
                onClick={onComplete}
                className="px-6 py-3 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors dark:text-white"
              >
                Back to Chat
              </button>
            </div>
          </div>

          {/* Answer Review */}
          <div className="space-y-6">
            <h3 className="text-2xl mb-4 dark:text-white">Review Your Answers</h3>
            {quiz.questions.map((question, index) => {
              const isCorrect = checkAnswer(question);
              const userAnswer = answers[question.id];
              
              return (
                <div key={question.id} className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                  <div className="flex items-start gap-3 mb-4">
                    <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                      isCorrect ? 'bg-green-100' : 'bg-red-100'
                    }`}>
                      {isCorrect ? (
                        <Check className="w-5 h-5 text-green-600" />
                      ) : (
                        <X className="w-5 h-5 text-red-600" />
                      )}
                    </div>
                    <div className="flex-1">
                      <h4 className="mb-3 dark:text-white">
                        <span className="text-gray-500 dark:text-gray-400">Q{index + 1}.</span> {question.question || "Question text not available"}
                      </h4>
                      
                      {question.type === 'short-answer' ? (
                        <div className="space-y-2">
                          <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Your answer:</p>
                            <p className="dark:text-white">{userAnswer as string || 'No answer provided'}</p>
                          </div>
                          <div className="p-3 bg-green-50 dark:bg-green-900/30 rounded-lg">
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Correct answer:</p>
                            <p className="text-green-700 dark:text-green-400">
                              {typeof question.correctAnswer === 'string'
                                ? question.correctAnswer
                                : String(question.correctAnswer)}
                            </p>
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          {question.options?.map((option, index) => {
                            const isUserAnswer = question.type === 'multiple-choice'
                              ? (userAnswer as string[])?.includes(option)
                              : userAnswer === option;
                            let isCorrectAnswer = false;
                            if (question.type === 'multiple-choice') {
                              let correctAnswers: string[] = [];
                              if (Array.isArray(question.correctAnswer)) {
                                correctAnswers = question.correctAnswer;
                              } else if (typeof question.correctAnswer === 'string') {
                                try {
                                  correctAnswers = JSON.parse(question.correctAnswer);
                                } catch (e) {
                                  correctAnswers = [question.correctAnswer];
                                }
                              } else if (question.correctAnswer) {
                                correctAnswers = [String(question.correctAnswer)];
                              }
                              isCorrectAnswer = correctAnswers.includes(option);
                            } else {
                              let correctAnswer = '';
                              if (typeof question.correctAnswer === 'string') {
                                correctAnswer = question.correctAnswer;
                              } else if (question.correctAnswer) {
                                correctAnswer = String(question.correctAnswer);
                              }
                              isCorrectAnswer = correctAnswer === option;
                            }
                            
                            return (
                              <div
                                key={option || index}
                                className={`p-3 rounded-lg border-2 ${
                                  isCorrectAnswer
                                    ? 'border-green-500 bg-green-50 dark:bg-green-900/30'
                                    : isUserAnswer
                                    ? 'border-red-500 bg-red-50 dark:bg-red-900/30'
                                    : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700'
                                }`}
                              >
                                <div className="flex items-center gap-2">
                                  {isCorrectAnswer && (
                                    <Check className="w-4 h-4 text-green-600 dark:text-green-400" />
                                  )}
                                  {isUserAnswer && !isCorrectAnswer && (
                                    <X className="w-4 h-4 text-red-600 dark:text-red-400" />
                                  )}
                                  <span className="dark:text-white">{option}</span>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                      
                      {question.explanation && (
                        <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
                          <p className="text-sm text-blue-900 dark:text-blue-200">
                            <strong>Explanation:</strong> {question.explanation}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-gradient-to-br from-green-50 to-blue-50 dark:from-gray-900 dark:to-gray-800 px-6 py-12">
      <div className="max-w-3xl mx-auto">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
            <span>Question {currentQuestionIndex + 1} of {quiz.totalQuestions}</span>
            <span>{Math.round(((currentQuestionIndex + 1) / quiz.totalQuestions) * 100)}%</span>
          </div>
          <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-green-500 to-blue-500 transition-all duration-300"
              style={{ width: `${((currentQuestionIndex + 1) / quiz.totalQuestions) * 100}%` }}
            />
          </div>
        </div>

        {/* Question Card */}
        <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-xl p-8">
          <div className="mb-8">
            <div className="inline-block px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full text-sm mb-4">
              {currentQuestion.type === 'single-choice' && 'Single Choice'}
              {currentQuestion.type === 'multiple-choice' && 'Multiple Choice - Select all that apply'}
              {currentQuestion.type === 'short-answer' && 'Short Answer'}
            </div>
            <h3 className="text-2xl dark:text-white">
              {currentQuestion.question || "Question text not available"}
            </h3>
          </div>

          {/* Answer Options */}
          <div className="space-y-3 mb-8">
            {currentQuestion.type === 'short-answer' ? (
              <div>
                <textarea
                  value={shortAnswerInput}
                  onChange={(e) => setShortAnswerInput(e.target.value)}
                  placeholder="Type your answer here..."
                  rows={4}
                  className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none dark:bg-gray-700 dark:text-white"
                />
              </div>
            ) : (
              currentQuestion.options?.map((option, index) => {
                const isSelected = currentQuestion.type === 'multiple-choice'
                  ? (answers[currentQuestion.id] as string[])?.includes(option)
                  : answers[currentQuestion.id] === option;

                return (
                  <button
                    key={option || index}
                    onClick={() => {
                      if (currentQuestion.type === 'multiple-choice') {
                        handleMultipleChoice(option);
                      } else {
                        handleSingleChoice(option);
                      }
                    }}
                    className={`w-full p-4 text-left rounded-xl border-2 transition-all ${
                      isSelected
                        ? 'border-green-500 bg-green-50 dark:bg-green-900/30'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-5 h-5 rounded ${
                        currentQuestion.type === 'multiple-choice' ? 'rounded-md' : 'rounded-full'
                      } border-2 flex items-center justify-center ${
                        isSelected
                          ? 'border-green-500 bg-green-500'
                          : 'border-gray-300 dark:border-gray-600'
                      }`}>
                        {isSelected && <Check className="w-3 h-3 text-white" />}
                      </div>
                      <span className="dark:text-white">{option}</span>
                    </div>
                  </button>
                );
              })
            )}
          </div>

          {/* Navigation */}
          <div className="flex justify-between items-center">
            <button
              onClick={() => setCurrentQuestionIndex(prev => prev - 1)}
              disabled={currentQuestionIndex === 0}
              className="px-6 py-3 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed dark:text-white"
            >
              Previous
            </button>

            <button
              onClick={handleNext}
              disabled={!canProceed() || isSubmitting}
              className="flex items-center gap-2 px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:bg-gray-300 dark:disabled:bg-gray-600 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  {currentQuestionIndex === quiz.questions.length - 1 ? 'Finish' : 'Next'}
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}