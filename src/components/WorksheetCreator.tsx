import { useState } from 'react';
import { ClassConfig } from './TeacherClassSelector';
import { FileText, Download, Eye, Loader } from 'lucide-react';
import { generateWorksheet } from '../api/worksheetService';

interface WorksheetCreatorProps {
  classConfig: ClassConfig;
  onBack: () => void;
}

interface QuestionType {
  id: string;
  label: string;
  icon: string;
  description: string;
}

export function WorksheetCreator({ classConfig, onBack }: WorksheetCreatorProps) {
  const [topic, setTopic] = useState('');
  const [selectedQuestionTypes, setSelectedQuestionTypes] = useState<string[]>(['multiple-choice', 'short-answer', 'long-answer']);
  const [difficulty, setDifficulty] = useState('medium');
  const [questionCount, setQuestionCount] = useState(10);
  const [generatedWorksheet, setGeneratedWorksheet] = useState<any>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const questionTypes: QuestionType[] = [
    {
      id: 'multiple-choice',
      label: 'Multiple Choice',
      icon: '✓',
      description: 'Questions with 4 options where only one is correct'
    },
    {
      id: 'short-answer',
      label: 'Short Answer',
      icon: '✍️',
      description: 'Questions requiring brief text responses (1-2 sentences)'
    },
    {
      id: 'long-answer',
      label: 'Long Answer',
      icon: '📝',
      description: 'Questions requiring detailed explanations (paragraphs)'
    },
    {
      id: 'essay',
      label: 'Essay',
      icon: '📄',
      description: 'Questions requiring extended writing with structured arguments'
    },
    {
      id: 'true-false',
      label: 'True/False',
      icon: 'T/F',
      description: 'Statements to be marked as true or false'
    },
    {
      id: 'fill-blank',
      label: 'Fill in the Blanks',
      icon: '___',
      description: 'Sentences with missing words to be filled in'
    },
    {
      id: 'matching',
      label: 'Matching',
      icon: '↔️',
      description: 'Pairs of items to be matched'
    },
  ];

  const toggleQuestionType = (typeId: string) => {
    if (selectedQuestionTypes.includes(typeId)) {
      setSelectedQuestionTypes(selectedQuestionTypes.filter(id => id !== typeId));
    } else {
      setSelectedQuestionTypes([...selectedQuestionTypes, typeId]);
    }
  };

  const generateWorksheetHandler = async () => {
    if (!topic || selectedQuestionTypes.length === 0) return;
    
    setIsGenerating(true);
    setError(null);
    
    try {
      // Call the backend API to generate worksheet
      const response = await generateWorksheet({
        class_id: classConfig.class,
        subject_id: classConfig.subject,
        chapter_id: topic, // Use topic as chapter_id
        difficulty,
        num_questions: questionCount,
        question_types: selectedQuestionTypes,
        duration: 30 // Default duration
      });
      
      setGeneratedWorksheet(response);
    } catch (err: any) {
      console.error('Error generating worksheet:', err);
      setError(err.message || 'Failed to generate worksheet. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const renderQuestion = (question: any) => {
    switch (question.type) {
      case 'multiple-choice':
        return (
          <div className="mb-6 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <p className="font-medium mb-3 text-lg dark:text-white">{question.number || 'Q'}. {question.question}</p>
            <div className="ml-4 space-y-2">
              {question.options?.map((option: string, index: number) => (
                <div key={index} className="flex items-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
                  <span className="mr-3 font-medium text-gray-700 dark:text-gray-300">{String.fromCharCode(97 + index)}.</span>
                  <span className="dark:text-gray-200">{option}</span>
                </div>
              ))}
            </div>
            <div className="mt-3 text-sm text-gray-600 dark:text-gray-400">
              Answer: ________
            </div>
          </div>
        );
      
      case 'true-false':
        return (
          <div className="mb-6 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <p className="font-medium mb-3 text-lg dark:text-white">{question.number || 'Q'}. {question.question}</p>
            <div className="mt-3 text-sm text-gray-600 dark:text-gray-400">
              Answer: ________ (Circle one: True / False)
            </div>
          </div>
        );
      
      case 'short-answer':
        return (
          <div className="mb-6 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <p className="font-medium mb-3 text-lg dark:text-white">{question.number || 'Q'}. {question.question}</p>
            <div className="mt-3 text-sm text-gray-600 dark:text-gray-400">
              Answer:
              <div className="border-b border-gray-300 dark:border-gray-600 my-3 h-8"></div>
            </div>
          </div>
        );
      
      case 'long-answer':
        return (
          <div className="mb-6 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <p className="font-medium mb-3 text-lg dark:text-white">{question.number || 'Q'}. {question.question}</p>
            <div className="mt-3 text-sm text-gray-600 dark:text-gray-400">
              Answer:
              <div className="border-b border-gray-300 dark:border-gray-600 my-3 h-8"></div>
              <div className="border-b border-gray-300 dark:border-gray-600 my-3 h-8"></div>
              <div className="border-b border-gray-300 dark:border-gray-600 my-3 h-8"></div>
            </div>
          </div>
        );
      
      case 'essay':
        return (
          <div className="mb-6 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <p className="font-medium mb-3 text-lg dark:text-white">{question.number || 'Q'}. {question.question}</p>
            <div className="mt-3 text-sm text-gray-600 dark:text-gray-400">
              Answer:
              <div className="border-b border-gray-300 dark:border-gray-600 my-3 h-8"></div>
              <div className="border-b border-gray-300 dark:border-gray-600 my-3 h-8"></div>
              <div className="border-b border-gray-300 dark:border-gray-600 my-3 h-8"></div>
              <div className="border-b border-gray-300 dark:border-gray-600 my-3 h-8"></div>
              <div className="border-b border-gray-300 dark:border-gray-600 my-3 h-8"></div>
            </div>
          </div>
        );
      
      case 'fill-blank':
        return (
          <div className="mb-6 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <p className="font-medium mb-3 text-lg dark:text-white">
              {question.number || 'Q'}. {question.question.replace('________', '__________')}
            </p>
            <div className="mt-3 text-sm text-gray-600 dark:text-gray-400">
              Answer: ____________________
            </div>
          </div>
        );
      
      case 'matching':
        return (
          <div className="mb-6 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <p className="font-medium mb-3 text-lg dark:text-white">{question.number || 'Q'}. {question.question}</p>
            <div className="grid grid-cols-2 gap-4 ml-4 mt-4">
              <div>
                <p className="font-medium mb-2 dark:text-gray-300">Column A</p>
                {question.options?.slice(0, 3).map((option: string, index: number) => (
                  <div key={index} className="mb-2 p-2 bg-gray-50 dark:bg-gray-700 rounded">
                    <span className="font-medium text-gray-700 dark:text-gray-300">{index + 1}.</span> {option}
                  </div>
                ))}
              </div>
              <div>
                <p className="font-medium mb-2 dark:text-gray-300">Column B</p>
                {['a', 'b', 'c'].map((letter, index) => (
                  <div key={index} className="mb-2 p-2 bg-gray-50 dark:bg-gray-700 rounded">
                    <span className="font-medium text-gray-700 dark:text-gray-300">{letter})</span> Definition {index + 1}
                  </div>
                ))}
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
              Answers: 1-____, 2-____, 3-____
            </div>
          </div>
        );
      
      default:
        return (
          <div className="mb-6 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <p className="font-medium mb-3 text-lg dark:text-white">{question.number || 'Q'}. {question.question}</p>
            <div className="mt-3 text-sm text-gray-600 dark:text-gray-400">
              Answer: ____________________
            </div>
          </div>
        );
    }
  };

  return (
    <div className="h-full overflow-y-auto px-6 py-8">
      <div className="max-w-6xl mx-auto">
        <button
          onClick={onBack}
          className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white mb-4 text-sm"
        >
          ← Back
        </button>

        <div className="mb-6">
          <h1 className="text-2xl mb-1 dark:text-white">Worksheet Creator</h1>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            {classConfig.class} • {classConfig.subject}
            {classConfig.section && ` • Section ${classConfig.section}`}
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-4">
          {/* Configuration Panel */}
          <div className="space-y-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-md border border-gray-100 dark:border-gray-700">
              <h3 className="mb-3 dark:text-white">Settings</h3>
              
              <div className="space-y-3">
                <div>
                  <label className="block text-xs mb-2 dark:text-gray-300">Topic</label>
                  <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                    placeholder="e.g., Quadratic Equations"
                  />
                </div>

                <div>
                  <label className="block text-xs mb-2 dark:text-gray-300">Question Types</label>
                  <div className="space-y-2">
                    {questionTypes.map((type) => (
                      <div 
                        key={type.id}
                        onClick={() => toggleQuestionType(type.id)}
                        className={`p-3 rounded-lg cursor-pointer transition-all ${
                          selectedQuestionTypes.includes(type.id)
                            ? 'bg-green-500 text-white'
                            : 'bg-gray-50 dark:bg-gray-700 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-600'
                        }`}
                      >
                        <div className="flex items-center">
                          <div className="mr-3 text-lg">{type.icon}</div>
                          <div>
                            <div className="text-sm font-medium">{type.label}</div>
                            <div className="text-xs opacity-80">{type.description}</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                    Selected: {selectedQuestionTypes.length} types
                  </div>
                </div>

                <div>
                  <label className="block text-xs mb-2 dark:text-gray-300">Difficulty</label>
                  <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                  >
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs mb-1 dark:text-gray-300">Questions: {questionCount}</label>
                  <input
                    type="range"
                    min="5"
                    max="30"
                    value={questionCount}
                    onChange={(e) => setQuestionCount(Number(e.target.value))}
                    className="w-full"
                  />
                </div>

                {error && (
                  <div className="p-3 bg-red-50 dark:bg-red-900/30 rounded-lg">
                    <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
                  </div>
                )}

                <button
                  onClick={generateWorksheetHandler}
                  disabled={!topic || selectedQuestionTypes.length === 0 || isGenerating}
                  className="w-full px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:bg-gray-300 dark:disabled:bg-gray-600 disabled:cursor-not-allowed text-sm"
                >
                  {isGenerating ? (
                    <>
                      <Loader className="w-4 h-4 animate-spin inline mr-2" />
                      Generating...
                    </>
                  ) : (
                    'Generate'
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Preview Panel */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md min-h-[500px] border border-gray-100 dark:border-gray-700">
              {!generatedWorksheet ? (
                <div className="flex items-center justify-center h-full text-gray-400 dark:text-gray-500">
                  <div className="text-center">
                    <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p className="text-sm">Configure and generate worksheet</p>
                  </div>
                </div>
              ) : (
                <>
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-lg dark:text-white">Worksheet Preview</h2>
                    <button className="px-3 py-1.5 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors text-sm flex items-center gap-2">
                      <Download className="w-4 h-4" />
                      Download
                    </button>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-900 p-6 rounded-lg border border-gray-200 dark:border-gray-700 dark:text-gray-200 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 200px)' }}>
                    <div className="mb-6">
                      <h1 className="text-2xl font-bold mb-2 dark:text-white">{generatedWorksheet.title || `${topic} Worksheet`}</h1>
                      <div className="text-sm text-gray-600 dark:text-gray-400 grid grid-cols-2 gap-2">
                        <p><strong>Subject:</strong> {generatedWorksheet.subject || classConfig.subject}</p>
                        <p><strong>Class:</strong> {generatedWorksheet.class || classConfig.class}{generatedWorksheet.section ? ` - Section ${generatedWorksheet.section}` : ''}</p>
                        <p><strong>Difficulty:</strong> {generatedWorksheet.difficulty || difficulty}</p>
                        <p><strong>Total Marks:</strong> {generatedWorksheet.total_marks || questionCount * 2}</p>
                      </div>
                    </div>
                    
                    <div className="mb-6 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                      <p className="font-medium mb-2 dark:text-white">Instructions:</p>
                      <p className="text-sm dark:text-gray-300">Answer all questions. Show your work where necessary. Write neatly and legibly.</p>
                    </div>
                    
                    <hr className="my-6 border-gray-300 dark:border-gray-700" />
                    
                    <div>
                      {generatedWorksheet.questions?.map((question: any, index: number) => {
                        // Add question number if not present
                        const questionWithNumber = {
                          ...question,
                          number: question.number || (index + 1)
                        };
                        return renderQuestion(questionWithNumber);
                      })}
                    </div>
                    
                    <hr className="my-6 border-gray-300 dark:border-gray-700" />
                    
                    <div className="mt-6 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                      <p className="font-medium mb-2 dark:text-white">Bonus Question:</p>
                      <p className="text-sm mb-3 dark:text-gray-300">[Challenge question for advanced students]</p>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        Answer:
                        <div className="border-b border-gray-300 dark:border-gray-600 my-3 h-8"></div>
                        <div className="border-b border-gray-300 dark:border-gray-600 my-3 h-8"></div>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}