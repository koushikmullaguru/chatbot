import { useState, useRef, useEffect } from 'react';
import { ExamConfig } from '../types';
import { Clock, CheckCircle, XCircle, AlertCircle, Flag, Send, ArrowLeft } from 'lucide-react';
import { chatService, ExamPrepRequest, ExamPrepResponse } from '../api/chatService';
import { MarkdownRenderer } from './MarkdownRenderer';

interface ExamModeProps {
  config: ExamConfig;
  onComplete: () => void;
}

interface ExamQuestion {
  id: number;
  type: 'mcq' | 'short-answer' | 'descriptive';
  question: string;
  options?: string[];
  answer?: string;
  marks: number;
}

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: string;
  suggestedQuestions?: string[];
}

export function ExamMode({ config, onComplete }: ExamModeProps) {
  const [questions, setQuestions] = useState<ExamQuestion[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [markedForReview, setMarkedForReview] = useState<Set<number>>(new Set());
  const [timeLeft, setTimeLeft] = useState(config.duration * 60); // Convert to seconds
  const [showSubmitConfirm, setShowSubmitConfirm] = useState(false);
  const [examSubmitted, setExamSubmitted] = useState(false);
  const [showPrepMode, setShowPrepMode] = useState(false);
  const [prepMessages, setPrepMessages] = useState<Message[]>([]);
  const [prepInput, setPrepInput] = useState('');
  const [isLoadingPrep, setIsLoadingPrep] = useState(false);
  const [prepSessionId, setPrepSessionId] = useState<string | null>(null);
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Generate questions based on exam config using AI
    const generateExamQuestions = async () => {
      setIsLoadingQuestions(true);
      try {
        const request: ExamPrepRequest = {
          exam_type: config.examType,
          subject: config.subject,
          chapter: config.chapter,
          difficulty: config.difficulty,
          question: `Generate ${config.questionCount} questions for a ${config.examType} exam on ${config.chapter} in ${config.subject}. The difficulty level is ${config.difficulty}. Please provide a mix of question types appropriate for this exam pattern.`
        };

        const response = await chatService.examPrep(request);
        
        // Parse the AI response to extract questions
        const parsedQuestions = parseQuestionsFromResponse(response.content, config.examType, config.questionCount);
        setQuestions(parsedQuestions);
      } catch (error) {
        console.error('Error generating exam questions:', error);
        // Fallback to default questions if AI generation fails
        setQuestions(generateFallbackQuestions(config));
      } finally {
        setIsLoadingQuestions(false);
      }
    };

    generateExamQuestions();
  }, [config]);

  useEffect(() => {
    // Timer countdown
    if (timeLeft > 0 && !examSubmitted) {
      const timer = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            handleSubmitExam();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [timeLeft, examSubmitted]);

  useEffect(() => {
    // Scroll to bottom of prep messages
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [prepMessages]);

  const parseQuestionsFromResponse = (content: string, examType: string, questionCount: number): ExamQuestion[] => {
    const questions: ExamQuestion[] = [];
    
    try {
      // Split content by lines
      const lines = content.split('\n');
      
      // Process the content to extract questions and options
      let currentQuestion: Partial<ExamQuestion> = {};
      let questionIndex = 0;
      let inQuestion = false;
      let inOptions = false;
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        // Skip empty lines
        if (!line) continue;
        
        // Check if this line starts a new question
        if (line.match(/^Question \d+/i) || line.match(/^\d+\./) || line.match(/^\d+\)/)) {
          // Save previous question if it exists
          if (currentQuestion.question && currentQuestion.question.trim()) {
            questions.push({
              id: questionIndex + 1,
              type: currentQuestion.type || getQuestionType(examType, questionIndex),
              question: currentQuestion.question.trim(),
              options: currentQuestion.options || [],
              marks: currentQuestion.marks || getQuestionMarks(examType, questionIndex)
            });
            questionIndex++;
          }
          
          // Start new question
          currentQuestion = {
            question: line,
            type: getQuestionType(examType, questionIndex),
            marks: getQuestionMarks(examType, questionIndex)
          };
          inQuestion = true;
          inOptions = false;
        } 
        // Check if this line is an option (a, b, c, d or A, B, C, D)
        else if (line.match(/^[a-d]\)/i) || line.match(/^[a-d]\./i) || line.match(/^[A-D]\)/i) || line.match(/^[A-D]\./i)) {
          if (!currentQuestion.options) {
            currentQuestion.options = [];
          }
          
          // Clean up the option text
          let optionText = line.replace(/^[a-d]\.?\s*/i, '').replace(/^[A-D]\.?\s*/i, '').trim();
          
          // Add the option
          currentQuestion.options.push(optionText);
          inOptions = true;
        }
        // If we're in a question and not in options yet, append to the question text
        else if (inQuestion && !inOptions && currentQuestion.question) {
          currentQuestion.question += ' ' + line;
        }
        // If we're in options, this might be a continuation of the previous option
        else if (inOptions && currentQuestion.options && currentQuestion.options.length > 0) {
          // Append to the last option
          const lastOptionIndex = currentQuestion.options.length - 1;
          currentQuestion.options[lastOptionIndex] += ' ' + line;
        }
      }
      
      // Add the last question if it exists
      if (currentQuestion.question && currentQuestion.question.trim()) {
        questions.push({
          id: questionIndex + 1,
          type: currentQuestion.type || getQuestionType(examType, questionIndex),
          question: currentQuestion.question.trim(),
          options: currentQuestion.options || [],
          marks: currentQuestion.marks || getQuestionMarks(examType, questionIndex)
        });
        questionIndex++;
      }
      
      // If we couldn't parse enough questions, generate some fallback ones
      while (questions.length < Math.min(questionCount, 20)) {
        questions.push(generateFallbackQuestion(config, questions.length + 1));
      }
      
      // Ensure we don't exceed the requested question count
      return questions.slice(0, Math.min(questionCount, 20));
    } catch (error) {
      console.error('Error parsing questions from AI response:', error);
      return generateFallbackQuestions(config);
    }
  };

  const getQuestionType = (examType: string, questionIndex: number): 'mcq' | 'short-answer' | 'descriptive' => {
    if (examType === 'mcq' || examType === 'competitive') {
      return 'mcq';
    } else if (examType === 'descriptive') {
      return 'descriptive';
    } else if (examType === 'mixed' || examType === 'board-exam') {
      // For mixed and board exams, vary the question types
      if (questionIndex < 10) return 'mcq';
      if (questionIndex < 20) return 'short-answer';
      return 'descriptive';
    } else if (examType === 'quick-test') {
      return 'mcq';
    }
    return 'mcq';
  };

  const getQuestionMarks = (examType: string, questionIndex: number): number => {
    if (examType === 'mcq' || examType === 'competitive' || examType === 'quick-test') {
      return 1;
    } else if (examType === 'descriptive') {
      return 10;
    } else if (examType === 'mixed' || examType === 'board-exam') {
      if (questionIndex < 10) return 1; // MCQ questions
      if (questionIndex < 20) return 2; // Short answer questions
      return 5; // Descriptive questions
    }
    return 1;
  };

  const generateFallbackQuestion = (config: ExamConfig, id: number): ExamQuestion => {
    const questionTypes = ['mcq', 'short-answer', 'descriptive'];
    const type = questionTypes[Math.floor(Math.random() * questionTypes.length)] as 'mcq' | 'short-answer' | 'descriptive';
    
    const questionTemplates = [
      `Explain the concept of [concept] in ${config.chapter} and its significance in ${config.subject}.`,
      `Discuss the main principles of [principle] as they relate to ${config.chapter} in ${config.subject}.`,
      `Analyze the impact of [factor] on the study of ${config.chapter} within ${config.subject}.`,
      `Compare and contrast [element1] and [element2] in the context of ${config.chapter}.`,
      `Evaluate the importance of [concept] in modern ${config.subject} with reference to ${config.chapter}.`
    ];
    
    const concepts = [
      'fundamental principles', 'key theories', 'core concepts', 'essential elements',
      'critical components', 'primary factors', 'major aspects', 'central themes'
    ];
    
    const randomTemplate = questionTemplates[Math.floor(Math.random() * questionTemplates.length)];
    const randomConcept = concepts[Math.floor(Math.random() * concepts.length)];
    
    const questionText = randomTemplate.replace('[concept]', randomConcept)
                                     .replace('[principle]', randomConcept)
                                     .replace('[factor]', randomConcept)
                                     .replace('[element1]', concepts[Math.floor(Math.random() * concepts.length)])
                                     .replace('[element2]', concepts[Math.floor(Math.random() * concepts.length)]);
    
    if (type === 'mcq') {
      const options = [
        `Option A: This is the first possible answer related to ${questionText.substring(0, 30)}...`,
        `Option B: This is the second possible answer related to ${questionText.substring(0, 30)}...`,
        `Option C: This is the third possible answer related to ${questionText.substring(0, 30)}...`,
        `Option D: This is the fourth possible answer related to ${questionText.substring(0, 30)}...`
      ];
      
      return {
        id,
        type,
        question: `Question ${id}: ${questionText}`,
        options,
        marks: 1,
      };
    } else if (type === 'short-answer') {
      return {
        id,
        type,
        question: `Question ${id}: ${questionText} (Write a concise answer in 50-100 words.)`,
        marks: 3,
      };
    } else {
      return {
        id,
        type,
        question: `Question ${id}: ${questionText} (Provide a detailed explanation with examples.)`,
        marks: 10,
      };
    }
  };

  const generateFallbackQuestions = (config: ExamConfig): ExamQuestion[] => {
    const questions: ExamQuestion[] = [];
    const questionCount = Math.min(config.questionCount, 20); // Limit to 20 questions
    
    for (let i = 0; i < questionCount; i++) {
      questions.push(generateFallbackQuestion(config, i + 1));
    }
    
    return questions;
  };

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const handleAnswerChange = (questionId: number, answer: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: answer }));
  };

  const toggleMarkForReview = (questionId: number) => {
    setMarkedForReview(prev => {
      const newSet = new Set(prev);
      if (newSet.has(questionId)) {
        newSet.delete(questionId);
      } else {
        newSet.add(questionId);
      }
      return newSet;
    });
  };

  const handleSubmitExam = () => {
    setExamSubmitted(true);
    setShowSubmitConfirm(false);
  };

  const getQuestionStatus = (questionId: number) => {
    if (answers[questionId]) return 'answered';
    if (markedForReview.has(questionId)) return 'review';
    return 'not-answered';
  };

  const calculateStats = () => {
    const answered = Object.keys(answers).length;
    const notAnswered = questions.length - answered;
    const marked = markedForReview.size;
    return { answered, notAnswered, marked };
  };

  const stats = calculateStats();
  const currentQuestion = questions[currentIndex];
  const timeWarning = timeLeft < 300; // Less than 5 minutes

  const initializePrepMode = async () => {
    setIsLoadingPrep(true);
    try {
      const request: ExamPrepRequest = {
        exam_type: config.examType,
        subject: config.subject,
        chapter: config.chapter,
        difficulty: config.difficulty,
        question: `I need help preparing for my ${config.examType} exam on ${config.chapter} in ${config.subject}. The difficulty level is ${config.difficulty}. Can you guide me through it?`
      };

      const response = await chatService.examPrep(request);
      setPrepSessionId(response.chat_session_id);
      
      // Add the AI response to messages
      setPrepMessages([{
        id: response.id,
        content: response.content,
        sender: 'ai',
        timestamp: response.timestamp,
        suggestedQuestions: response.suggested_questions
      }]);
    } catch (error) {
      console.error('Error initializing prep mode:', error);
      
      // Add an error message
      setPrepMessages([{
        id: 'error',
        content: "I'm sorry, I'm having trouble starting your exam preparation session right now. Please try again later.",
        sender: 'ai',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsLoadingPrep(false);
    }
  };

  const handleSendPrepMessage = async () => {
    if (!prepInput.trim() || isLoadingPrep || !prepSessionId) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: prepInput,
      sender: 'user',
      timestamp: new Date().toISOString()
    };

    // Add user message to the list
    setPrepMessages(prev => [...prev, userMessage]);
    setPrepInput('');
    setIsLoadingPrep(true);

    try {
      const request: ExamPrepRequest = {
        exam_type: config.examType,
        subject: config.subject,
        chapter: config.chapter,
        difficulty: config.difficulty,
        question: prepInput
      };

      const response = await chatService.examPrep(request);
      
      // Add AI response to messages
      setPrepMessages(prev => [...prev, {
        id: response.id,
        content: response.content,
        sender: 'ai',
        timestamp: response.timestamp,
        suggestedQuestions: response.suggested_questions
      }]);
    } catch (error) {
      console.error('Error sending prep message:', error);
      
      // Add an error message
      setPrepMessages(prev => [...prev, {
        id: 'error-' + Date.now().toString(),
        content: "I'm sorry, I'm having trouble responding right now. Please try again later.",
        sender: 'ai',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsLoadingPrep(false);
    }
  };

  const handlePrepKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendPrepMessage();
    }
  };

  const handleSuggestedQuestionClick = (question: string) => {
    setPrepInput(question);
  };

  const getExamTypeIcon = (type: string) => {
    switch (type) {
      case 'mcq': return '✓';
      case 'descriptive': return '✍️';
      case 'mixed': return '📝';
      case 'board-exam': return '🎓';
      case 'competitive': return '⚡';
      case 'quick-test': return '⏱️';
      default: return '📚';
    }
  };

  const getExamTypeName = (type: string) => {
    switch (type) {
      case 'mcq': return 'Multiple Choice Questions';
      case 'descriptive': return 'Descriptive Exam';
      case 'mixed': return 'Mixed Pattern';
      case 'board-exam': return 'Board Exam Pattern';
      case 'competitive': return 'Competitive Exam';
      case 'quick-test': return 'Quick Test';
      default: return 'Exam';
    }
  };

  if (showPrepMode) {
    return (
      <div className="h-full flex flex-col bg-gradient-to-br from-purple-50 via-pink-50 to-indigo-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowPrepMode(false)}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2">
              <div className="text-2xl">{getExamTypeIcon(config.examType)}</div>
              <div>
                <h2 className="text-lg font-semibold dark:text-white">
                  {getExamTypeName(config.examType)} Preparation
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {config.subject} • {config.chapter} • {config.difficulty}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {prepMessages.length === 0 && !isLoadingPrep && (
            <div className="text-center py-8">
              <div className="text-5xl mb-4">{getExamTypeIcon(config.examType)}</div>
              <h3 className="text-xl font-semibold mb-2 dark:text-white">
                Getting your exam preparation assistant ready...
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                I'm preparing to help you with your {getExamTypeName(config.examType).toLowerCase()}.
              </p>
            </div>
          )}

          {prepMessages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl p-4 ${
                  message.sender === 'user'
                    ? 'bg-purple-500 text-white rounded-br-none'
                    : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-bl-none shadow-sm'
                }`}
              >
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <MarkdownRenderer content={message.content} />
                </div>
                
                {message.sender === 'ai' && message.suggestedQuestions && message.suggestedQuestions.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-xs font-medium mb-2 text-gray-600 dark:text-gray-400">
                      You might want to ask:
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {message.suggestedQuestions.map((question, index) => (
                        <button
                          key={index}
                          onClick={() => handleSuggestedQuestionClick(question)}
                          className="text-xs bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 px-2 py-1 rounded-full transition-colors"
                        >
                          {question}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoadingPrep && (
            <div className="flex justify-start">
              <div className="bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-2xl p-4 rounded-bl-none shadow-sm max-w-[80%]">
                <div className="flex items-center gap-2">
                  <div className="animate-spin w-4 h-4 border-2 border-purple-500 border-t-transparent rounded-full" />
                  <span className="text-sm">Thinking...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <div className="flex gap-2">
            <textarea
              value={prepInput}
              onChange={(e) => setPrepInput(e.target.value)}
              onKeyDown={handlePrepKeyPress}
              placeholder="Ask a question about your exam preparation..."
              className="flex-1 resize-none rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 p-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
              rows={2}
              disabled={isLoadingPrep}
            />
            <button
              onClick={handleSendPrepMessage}
              disabled={!prepInput.trim() || isLoadingPrep}
              className="self-end p-3 bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (examSubmitted) {
    return (
      <div className="h-full overflow-y-auto bg-gradient-to-br from-purple-50 to-pink-50 px-6 py-12">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-xl p-8 text-center">
            <CheckCircle className="w-20 h-20 text-green-500 mx-auto mb-4" />
            <h2 className="text-4xl mb-4 dark:text-white">Exam Submitted Successfully!</h2>
            <p className="text-gray-600 mb-8">
              Your exam has been submitted. In a real scenario, your answers would be evaluated.
            </p>
            
            <div className="bg-gray-50 dark:bg-gray-700 rounded-2xl p-6 mb-8">
              <h3 className="text-xl mb-4 dark:text-white">Exam Summary</h3>
              <div className="grid md:grid-cols-2 gap-4 text-left">
                <div className="flex items-center justify-between p-3 bg-white dark:bg-gray-600 rounded-lg">
                  <span className="text-gray-600 dark:text-gray-300">Total Questions:</span>
                  <span className="dark:text-white">{questions.length}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-white dark:bg-gray-600 rounded-lg">
                  <span className="text-gray-600 dark:text-gray-300">Answered:</span>
                  <span className="text-green-600 dark:text-green-400">{stats.answered}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-white dark:bg-gray-600 rounded-lg">
                  <span className="text-gray-600 dark:text-gray-300">Not Answered:</span>
                  <span className="text-red-600 dark:text-red-400">{stats.notAnswered}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-white dark:bg-gray-600 rounded-lg">
                  <span className="text-gray-600 dark:text-gray-300">Time Used:</span>
                  <span className="dark:text-white">{formatTime(config.duration * 60 - timeLeft)}</span>
                </div>
              </div>
            </div>

            <button
              onClick={onComplete}
              className="px-8 py-3 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
            >
              Back to Chat
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (isLoadingQuestions) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p>Generating exam questions...</p>
        </div>
      </div>
    );
  }

  if (!currentQuestion) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p>Loading exam questions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Exam Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl dark:text-white">{config.examType.toUpperCase()} - {config.subject}</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">{config.chapter} • {config.difficulty}</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                setShowPrepMode(true);
                if (prepMessages.length === 0) {
                  initializePrepMode();
                }
              }}
              className="px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition-colors"
            >
              Get Help
            </button>
            <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
              timeWarning ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
            }`}>
              <Clock className="w-5 h-5" />
              <span className="text-lg">{formatTime(timeLeft)}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Question Navigation Panel */}
        <div className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 overflow-y-auto p-4">
          <div className="mb-6">
            <h4 className="mb-3 dark:text-white">Question Palette</h4>
            <div className="grid grid-cols-5 gap-2">
              {questions.map((q) => {
                const status = getQuestionStatus(q.id);
                return (
                  <button
                    key={q.id}
                    onClick={() => setCurrentIndex(q.id - 1)}
                    className={`w-10 h-10 rounded-lg flex items-center justify-center text-sm transition-all ${
                      currentIndex === q.id - 1
                        ? 'ring-2 ring-purple-500'
                        : ''
                    } ${
                      status === 'answered'
                        ? 'bg-green-500 text-white'
                        : status === 'review'
                        ? 'bg-orange-500 text-white'
                        : 'bg-gray-200 text-gray-600'
                    }`}
                  >
                    {q.id}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="space-y-3 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-green-500 rounded" />
              <span className="dark:text-gray-300">Answered ({stats.answered})</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-gray-200 rounded" />
              <span className="dark:text-gray-300">Not Answered ({stats.notAnswered})</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-orange-500 rounded" />
              <span className="dark:text-gray-300">Marked for Review ({stats.marked})</span>
            </div>
          </div>
        </div>

        {/* Question Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-8">
            <div className="max-w-4xl mx-auto">
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8">
                <div className="flex items-start justify-between mb-6">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-4">
                      <span className="px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 rounded-full text-sm">
                        Question {currentQuestion.id} of {questions.length}
                      </span>
                      <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded-full text-sm">
                        {currentQuestion.marks} {currentQuestion.marks === 1 ? 'Mark' : 'Marks'}
                      </span>
                      <span className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full text-sm capitalize">
                        {currentQuestion.type === 'mcq' ? 'Multiple Choice' : currentQuestion.type === 'short-answer' ? 'Short Answer' : 'Descriptive'}
                      </span>
                    </div>
                    <p className="text-lg dark:text-white">{currentQuestion.question}</p>
                  </div>
                  <button
                    onClick={() => toggleMarkForReview(currentQuestion.id)}
                    className={`flex-shrink-0 p-2 rounded-lg transition-colors ${
                      markedForReview.has(currentQuestion.id)
                        ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-400 hover:text-orange-600 dark:hover:text-orange-400'
                    }`}
                    title="Mark for review"
                  >
                    <Flag className="w-5 h-5" />
                  </button>
                </div>

                {/* Answer Input */}
                <div className="mt-6">
                  {currentQuestion.type === 'mcq' && currentQuestion.options ? (
                    <div className="space-y-3">
                      {currentQuestion.options.map((option, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleAnswerChange(currentQuestion.id, option)}
                          className={`w-full p-4 text-left rounded-xl border-2 transition-all ${
                            answers[currentQuestion.id] === option
                              ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20 dark:text-white'
                              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700/50 dark:text-white'
                          }`}
                        >
                          {option}
                        </button>
                      ))}
                    </div>
                  ) : currentQuestion.type === 'short-answer' ? (
                    <textarea
                      value={answers[currentQuestion.id] || ''}
                      onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                      placeholder="Write your answer here (50-100 words)..."
                      rows={5}
                      className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-700 dark:text-white rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                    />
                  ) : (
                    <textarea
                      value={answers[currentQuestion.id] || ''}
                      onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                      placeholder="Write your detailed answer here..."
                      rows={10}
                      className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-700 dark:text-white rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                    />
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Navigation Footer */}
          <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-8 py-4">
            <div className="max-w-4xl mx-auto flex items-center justify-between">
              <div className="flex gap-3">
                <button
                  onClick={() => setCurrentIndex(prev => Math.max(0, prev - 1))}
                  disabled={currentIndex === 0}
                  className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>
                <button
                  onClick={() => setCurrentIndex(prev => Math.min(questions.length - 1, prev + 1))}
                  disabled={currentIndex === questions.length - 1}
                  className="px-6 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                </button>
              </div>

              <button
                onClick={() => setShowSubmitConfirm(true)}
                className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
              >
                Submit Exam
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Submit Confirmation Modal */}
      {showSubmitConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full">
            <AlertCircle className="w-12 h-12 text-orange-500 mx-auto mb-4" />
            <h3 className="text-2xl mb-4 text-center">Submit Exam?</h3>
            <p className="text-gray-600 mb-6 text-center">
              Are you sure you want to submit the exam? You have answered {stats.answered} out of {questions.length} questions.
            </p>
            {stats.notAnswered > 0 && (
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-6">
                <p className="text-sm text-orange-700">
                  ⚠️ You have {stats.notAnswered} unanswered question{stats.notAnswered !== 1 ? 's' : ''}.
                </p>
              </div>
            )}
            <div className="flex gap-3">
              <button
                onClick={() => setShowSubmitConfirm(false)}
                className="flex-1 px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitExam}
                className="flex-1 px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
              >
                Submit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}