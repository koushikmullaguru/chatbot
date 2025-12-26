import { useState, useEffect, useRef } from 'react';
import { ArrowLeft, Send, Loader2 } from 'lucide-react';
import { HomeworkTopic } from './HomeworkSetup';
import { chatService, HomeworkAssistantRequest, HomeworkAssistantResponse } from '../api/chatService';
import { MarkdownRenderer } from './MarkdownRenderer';

interface HomeworkModeProps {
  homeworkConfig: HomeworkTopic;
  onBack: () => void;
  isDark?: boolean;
}

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: string;
  suggestedQuestions?: string[];
}

export function HomeworkMode({ homeworkConfig, onBack, isDark = false }: HomeworkModeProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [chatSessionId, setChatSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize the homework session
  useEffect(() => {
    const initializeHomework = async () => {
      setIsLoading(true);
      
      try {
        const request: HomeworkAssistantRequest = {
          class_name: homeworkConfig.class,
          subject: homeworkConfig.subject,
          topic: homeworkConfig.chapter,
          assignment_type: homeworkConfig.assignmentType,
          question: `I need help with my ${homeworkConfig.assignmentType} assignment about ${homeworkConfig.chapter} in ${homeworkConfig.subject}. Can you guide me through it?`
        };

        const response = await chatService.homeworkAssistant(request);
        
        setChatSessionId(response.chat_session_id);
        
        // Add the AI response to messages
        setMessages([{
          id: response.id,
          content: response.content,
          sender: 'ai',
          timestamp: response.timestamp,
          suggestedQuestions: response.suggested_questions
        }]);
      } catch (error) {
        console.error('Error initializing homework session:', error);
        
        // Add an error message
        setMessages([{
          id: 'error',
          content: "I'm sorry, I'm having trouble starting your homework session right now. Please try again later.",
          sender: 'ai',
          timestamp: new Date().toISOString()
        }]);
      } finally {
        setIsLoading(false);
      }
    };

    initializeHomework();
  }, [homeworkConfig]);

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading || !chatSessionId) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: 'user',
      timestamp: new Date().toISOString()
    };

    // Add user message to the list
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const request: HomeworkAssistantRequest = {
        class_name: homeworkConfig.class,
        subject: homeworkConfig.subject,
        topic: homeworkConfig.chapter,
        assignment_type: homeworkConfig.assignmentType,
        question: inputValue
      };

      const response = await chatService.homeworkAssistant(request);
      
      // Add AI response to messages
      setMessages(prev => [...prev, {
        id: response.id,
        content: response.content,
        sender: 'ai',
        timestamp: response.timestamp,
        suggestedQuestions: response.suggested_questions
      }]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Add an error message
      setMessages(prev => [...prev, {
        id: 'error-' + Date.now().toString(),
        content: "I'm sorry, I'm having trouble responding right now. Please try again later.",
        sender: 'ai',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSuggestedQuestionClick = (question: string) => {
    setInputValue(question);
  };

  const getAssignmentTypeIcon = (type: string) => {
    switch (type) {
      case 'problem-solving': return '🧮';
      case 'essay': return '✍️';
      case 'research': return '🔬';
      case 'reading': return '📖';
      case 'worksheet': return '📝';
      case 'lab': return '🧪';
      default: return '📚';
    }
  };

  const getAssignmentTypeName = (type: string) => {
    switch (type) {
      case 'problem-solving': return 'Problem Solving';
      case 'essay': return 'Essay/Writing';
      case 'research': return 'Research Project';
      case 'reading': return 'Reading Assignment';
      case 'worksheet': return 'Worksheet';
      case 'lab': return 'Lab Report';
      default: return 'Homework';
    }
  };

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-pink-50 via-rose-50 to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <div className="text-2xl">{getAssignmentTypeIcon(homeworkConfig.assignmentType)}</div>
            <div>
              <h2 className="text-lg font-semibold dark:text-white">
                {getAssignmentTypeName(homeworkConfig.assignmentType)}
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {homeworkConfig.class} • {homeworkConfig.subject} • {homeworkConfig.chapter}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !isLoading && (
          <div className="text-center py-8">
            <div className="text-5xl mb-4">{getAssignmentTypeIcon(homeworkConfig.assignmentType)}</div>
            <h3 className="text-xl font-semibold mb-2 dark:text-white">
              Getting your homework assistant ready...
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              I'm preparing to help you with your {getAssignmentTypeName(homeworkConfig.assignmentType).toLowerCase()}.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl p-4 ${
                message.sender === 'user'
                  ? 'bg-pink-500 text-white rounded-br-none'
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

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-2xl p-4 rounded-bl-none shadow-sm max-w-[80%]">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
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
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Ask a question about your homework..."
            className="flex-1 resize-none rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 p-3 focus:outline-none focus:ring-2 focus:ring-pink-500"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="self-end p-3 bg-pink-500 hover:bg-pink-600 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}