import { useState } from 'react';
import { MessageSquarePlus, Menu, X } from 'lucide-react';
import { ChatMode } from '../types';

interface ChatSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  onNewChat: () => void;
  currentMode: ChatMode;
}

export function ChatSidebar({ isOpen, onToggle, onNewChat }: ChatSidebarProps) {

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

              {/* Mode Options */}
              <div className="flex-1 overflow-y-auto p-4">
                <h3 className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-3 px-2">
                  Modes
                </h3>
                <div className="space-y-2">
                  <div className="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">
                    Select a mode to start chatting
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}