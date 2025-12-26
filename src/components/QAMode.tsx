import { useState, useRef, useEffect } from 'react';
import { Send, BookOpen, HelpCircle } from 'lucide-react';
import { Message } from '../types';
import { chatService } from '../api/chatService';
import { MarkdownRenderer } from './MarkdownRenderer';

interface QAModeProps {
  onSendMessage?: (message: string) => void;
  studentProfileId: string;
  subject?: string;
}

export function QAMode({ onSendMessage, studentProfileId, subject }: QAModeProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: "Hi! I'm your AI Q&A assistant. Ask me any question related to your studies, and I'll provide clear, educational answers with suggested follow-up questions.",
      sender: 'ai',
      timestamp: new Date(),
      suggestedQuestions: [
        'What is photosynthesis?',
        'Explain the water cycle',
        'How do plants make food?',
        'What are the parts of a cell?'
      ]
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Function to extract suggested questions from response content
  const extractSuggestedQuestions = (content: string): { content: string, suggestedQuestions: string[] } => {
    let cleanContent = content;
    let suggestedQuestions: string[] = [];
    
    // Try to find JSON array at the end of the content, with or without backticks
    const jsonMatch = content.match(/```json\s*\[\s*"([^"]+)"(?:\s*,\s*"([^"]+)")*\s*\]\s*```$/);
    const simpleJsonMatch = content.match(/\[\s*"([^"]+)"(?:\s*,\s*"([^"]+)")*\s*\]$/);
    
    const match = jsonMatch || simpleJsonMatch;
    
    if (match) {
      try {
        // Extract the JSON part
        let jsonPart = match[0];
        
        // Remove backticks and "json" if present
        if (jsonPart.startsWith('```json')) {
          jsonPart = jsonPart.replace(/```json\s*/, '').replace(/\s*```$/, '');
        } else if (jsonPart.startsWith('```')) {
          jsonPart = jsonPart.replace(/```\s*/, '').replace(/\s*```$/, '');
        }
        
        suggestedQuestions = JSON.parse(jsonPart);
        
        // Remove all variations of "Follow-up Questions" headings and everything after them
        cleanContent = content.replace(/Follow-up Questions[\s\S]*$/i, '').trim();
        cleanContent = cleanContent.replace(/Follow-up Questions[\s\S]*$/i, '').trim();
        cleanContent = cleanContent.replace(/Followup Questions[\s\S]*$/i, '').trim();
        cleanContent = cleanContent.replace(/Follow up Questions[\s\S]*$/i, '').trim();
        cleanContent = cleanContent.replace(/Follow-up Questions \(JSON\)[\s\S]*$/i, '').trim();
        
        // Also remove the JSON part if it's still there
        cleanContent = cleanContent.replace(match[0], '').trim();
        
        // Remove any empty lines that might be left at the end
        cleanContent = cleanContent.replace(/\n\s*$/m, '').trim();
        
        // Remove any horizontal rules or separators before the end
        cleanContent = cleanContent.replace(/---[\s]*$/m, '').trim();
      } catch (error) {
        console.error('Error parsing suggested questions JSON:', error);
      }
    }
    
    return { content: cleanContent, suggestedQuestions };
  };

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      // Use the Q&A API endpoint
      const response = await chatService.askQuestion({
        question: content,
        student_profile_id: studentProfileId,
        subject: subject
      });

      // Extract suggested questions from content if they're included
      const { content: cleanContent, suggestedQuestions } = extractSuggestedQuestions(response.content);

      // Convert API response to frontend format
      const aiMessage: Message = {
        id: response.id,
        content: cleanContent,
        sender: 'ai',
        timestamp: new Date(response.timestamp),
        suggestedQuestions: suggestedQuestions.length > 0 ? suggestedQuestions : (response.suggested_questions || [])
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error getting Q&A response:', error);
      
      // Fallback response on error
      const fallbackMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: "I'm sorry, I'm having trouble answering your question right now. Please try again later.",
        sender: 'ai',
        timestamp: new Date(),
        suggestedQuestions: [
          'Can you try rephrasing your question?',
          'What specifically would you like to know about this topic?',
          'Would you like me to explain a different concept?'
        ]
      };

      setMessages(prev => [...prev, fallbackMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestedQuestionClick = (question: string) => {
    handleSendMessage(question);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Q&A Header */}
      <div className="bg-gradient-to-r from-blue-500 to-indigo-500 text-white px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <h3 className="text-xl mb-1 flex items-center gap-2">
            <BookOpen className="w-5 h-5" />
            Q&A Mode
          </h3>
          <p className="text-sm text-blue-50">
            Ask questions and get educational answers with suggested follow-up questions
          </p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900 px-6 py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.map((message) => (
            <div key={message.id}>
              <div
                className={`flex gap-4 ${
                  message.sender === 'user' ? 'flex-row-reverse' : 'flex-row'
                }`}
              >
                <div
                  className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-xl ${
                    message.sender === 'user'
                      ? 'bg-blue-500'
                      : 'bg-gradient-to-br from-indigo-500 to-purple-500'
                  }`}
                >
                  {message.sender === 'user' ? '👤' : '🤖'}
                </div>

                <div
                  className={`flex-1 ${
                    message.sender === 'user' ? 'text-right' : 'text-left'
                  }`}
                >
                  <div
                    className={`inline-block max-w-3xl px-5 py-3 rounded-2xl ${
                      message.sender === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-white dark:bg-gray-800 shadow-md dark:text-white'
                    }`}
                  >
                    <MarkdownRenderer content={message.content} />
                  </div>

                  {message.sender === 'ai' && message.suggestedQuestions && (
                    <div className="mt-4 space-y-2">
                      <p className="text-sm text-gray-500 dark:text-gray-400 mb-2 flex items-center gap-1">
                        <HelpCircle className="w-4 h-4" />
                        You might also want to ask:
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {message.suggestedQuestions.map((question, index) => (
                          <button
                            key={index}
                            onClick={() => handleSuggestedQuestionClick(question)}
                            disabled={isLoading}
                            className="text-sm px-4 py-2 bg-white dark:bg-gray-700 border border-blue-200 dark:border-blue-600 hover:bg-blue-50 dark:hover:bg-gray-600 rounded-lg transition-colors dark:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {question}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                    {new Date(message.timestamp).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </div>
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-3 items-end">
            {/* Text Input */}
            <div className="flex-1 relative">
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage(inputText);
                  }
                }}
                placeholder="Ask your question here..."
                rows={1}
                disabled={isLoading}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent max-h-32 dark:bg-gray-700 dark:text-white disabled:opacity-50"
              />
            </div>

            {/* Send Button */}
            <button
              type="button"
              onClick={() => handleSendMessage(inputText)}
              disabled={!inputText.trim() || isLoading}
              className="flex-shrink-0 p-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:bg-gray-300 dark:disabled:bg-gray-600 disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>

          <p className="text-xs text-gray-500 dark:text-gray-400 text-center mt-3">
            Press Enter to send • AI will provide answers with suggested follow-up questions
          </p>
        </div>
      </div>
    </div>
  );
}