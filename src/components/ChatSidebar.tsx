import { useState, useEffect } from 'react';
import { MessageSquarePlus, Menu, X } from 'lucide-react';
import { ChatMode } from '../types';
import { chatService, ChatSession } from '../api/chatService';

interface ChatSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  onNewChat: () => void;
  currentMode: ChatMode;
  onSelectChat?: (chatSession: ChatSession) => void;
  refreshChats?: () => void;
  refreshTrigger?: number;
}

export function ChatSidebar({ isOpen, onToggle, onNewChat, onSelectChat, refreshChats, refreshTrigger }: ChatSidebarProps) {
  const [recentChats, setRecentChats] = useState<ChatSession[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Load recent chats when component mounts or when refresh is triggered
  useEffect(() => {
    const loadRecentChats = async () => {
      if (!isOpen) return; // Only load when sidebar is open
      
      setIsLoading(true);
      try {
        console.log('Loading recent chats...');
        const chats = await chatService.getChatSessions();
        console.log('Loaded chats:', chats);
        setRecentChats(chats);
      } catch (error) {
        console.error('Error loading recent chats:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadRecentChats();
  }, [isOpen, refreshTrigger]);

  // Function to refresh recent chats
  const handleRefreshChats = async () => {
    setIsLoading(true);
    try {
      const chats = await chatService.getChatSessions();
      setRecentChats(chats);
    } catch (error) {
      console.error('Error refreshing recent chats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Expose refresh function to parent
  useEffect(() => {
    if (refreshChats) {
      handleRefreshChats();
    }
  }, [refreshChats]);

  // Format date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffInDays === 0) return 'Today';
    if (diffInDays === 1) return 'Yesterday';
    if (diffInDays < 7) return `${diffInDays} days ago`;
    
    return date.toLocaleDateString();
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-20 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed lg:relative z-30 h-full bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-300 ${
          isOpen ? 'w-72' : 'w-0 lg:w-16'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <button
              onClick={onToggle}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              {isOpen ? <X className="w-5 h-5 dark:text-white" /> : <Menu className="w-5 h-5 dark:text-white" />}
            </button>
          </div>

          {isOpen && (
            <>
              {/* New Chat Button */}
              <div className="p-4">
                <button
                  onClick={onNewChat}
                  className="w-full flex items-center gap-3 px-4 py-3 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition-colors"
                >
                  <MessageSquarePlus className="w-5 h-5" />
                  <span>New Chat</span>
                </button>
              </div>

              {/* Recent Chats */}
              <div className="flex-1 overflow-y-auto p-4">
                <h3 className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-3 px-2">
                  Recent Chats
                </h3>
                <div className="space-y-2">
                  {isLoading ? (
                    <div className="px-3 py-2 text-center text-gray-500 dark:text-gray-400">
                      Loading chats...
                    </div>
                  ) : recentChats.length === 0 ? (
                    <div className="px-3 py-2 text-center text-gray-500 dark:text-gray-400">
                      No recent chats
                    </div>
                  ) : (
                    recentChats.map((chat) => (
                      <button
                        key={chat.id}
                        onClick={() => onSelectChat && onSelectChat(chat)}
                        className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors group"
                      >
                        <div className="text-sm mb-1 line-clamp-1 dark:text-white">
                          {chat.title || `${chat.mode.toUpperCase()} Session`}
                        </div>
                        <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                          <span className="capitalize">{chat.mode}</span>
                          <span>•</span>
                          <span>{formatDate(chat.updated_at)}</span>
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}