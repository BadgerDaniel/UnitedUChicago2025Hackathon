import React from 'react';
import { Moon, Sun, Plane, ArrowLeft } from 'lucide-react';

interface TopNavigationProps {
  isDarkMode: boolean;
  onThemeToggle: () => void;
  onGoBack: () => void;
}

const TopNavigation: React.FC<TopNavigationProps> = ({ isDarkMode, onThemeToggle, onGoBack }) => {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 h-20 bg-white dark:bg-slate-900 border-b-2 border-gray-200 dark:border-slate-600 px-8 flex items-center justify-between shadow-lg backdrop-blur-sm transition-all duration-300">
      {/* Left Section - Enhanced Logo */}
      <div className="flex items-center space-x-5">
        <div className="relative">
          <div className="w-14 h-14 bg-gradient-to-br from-blue-600 via-blue-700 to-blue-800 rounded-xl flex items-center justify-center shadow-lg transform hover:scale-105 transition-transform duration-200">
            <Plane className="w-7 h-7 text-white transform rotate-45" />
          </div>
          <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white dark:border-slate-900 animate-pulse"></div>
        </div>
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight relative overflow-hidden">
            <span className="relative z-10 bg-gradient-to-r from-blue-600 via-blue-800 to-blue-600 dark:from-blue-400 dark:via-blue-300 dark:to-blue-400 bg-clip-text text-transparent animate-gradient-x bg-[length:200%_200%]">
              United Airlines
            </span>
          </h1>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-300 tracking-wide">
            Flight Demand Forecaster
          </p>
        </div>
      </div>

      {/* Right Section - Go Back Button and Theme Toggle */}
      <div className="flex items-center space-x-4">
        <button
          onClick={onGoBack}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl border-2 border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-900 hover:bg-gray-50 dark:hover:bg-slate-800 transition-all duration-300 shadow-md hover:shadow-lg transform hover:scale-105"
        >
          <ArrowLeft className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Go Back</span>
        </button>
        <button
          onClick={onThemeToggle}
          className="p-3 rounded-xl border-2 border-blue-600 dark:border-blue-600 bg-white dark:bg-slate-900 hover:bg-blue-50 dark:hover:bg-slate-800 transition-all duration-300 shadow-md hover:shadow-lg transform hover:scale-105"
          aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {isDarkMode ? (
            <Sun className="w-5 h-5 text-blue-600" />
          ) : (
            <Moon className="w-5 h-5 text-blue-600" />
          )}
        </button>
      </div>
    </nav>
  );
};

export default TopNavigation;