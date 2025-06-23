import React, { useState } from 'react';
import { Lock, Plane, Eye, EyeOff, Moon, Sun } from 'lucide-react';

interface PasswordAuthProps {
  onAuthenticate: () => void;
  isDarkMode: boolean;
  onThemeToggle: () => void;
}

const PasswordAuth: React.FC<PasswordAuthProps> = ({ onAuthenticate, isDarkMode, onThemeToggle }) => {
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    // Simulate a brief loading state for better UX
    await new Promise(resolve => setTimeout(resolve, 500));

    if (password === '12345') {
      onAuthenticate();
    } else {
      setError('Incorrect password. Please try again.');
      setPassword('');
    }
    
    setIsLoading(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit(e as any);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-100 via-gray-200 to-gray-300 dark:from-slate-900 dark:via-slate-800 dark:to-slate-700 flex items-center justify-center p-6 transition-all duration-500 relative">
      {/* Theme Toggle Button - Top Right */}
      <button
        onClick={onThemeToggle}
        className="fixed top-6 right-6 z-50 p-3 rounded-xl border-2 border-blue-600 dark:border-blue-500 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm hover:bg-blue-50 dark:hover:bg-slate-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105"
        aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
      >
        {isDarkMode ? (
          <Sun className="w-5 h-5 text-blue-600" />
        ) : (
          <Moon className="w-5 h-5 text-blue-600" />
        )}
      </button>

      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-30 dark:opacity-20">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-400/10 via-purple-400/10 to-blue-400/10 dark:from-blue-500/20 dark:via-purple-500/20 dark:to-blue-500/20"></div>
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-400/20 dark:bg-blue-500/30 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-xl animate-pulse"></div>
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-purple-400/20 dark:bg-purple-500/30 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-xl animate-pulse" style={{ animationDelay: '2s' }}></div>
        <div className="absolute bottom-1/4 left-1/3 w-96 h-96 bg-indigo-400/20 dark:bg-indigo-500/30 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-xl animate-pulse" style={{ animationDelay: '4s' }}></div>
      </div>

      <div className="w-full max-w-md relative z-10">
        {/* Logo Section */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-600 via-blue-700 to-blue-800 dark:from-blue-500 dark:via-blue-600 dark:to-blue-700 rounded-2xl shadow-2xl mb-6 transform hover:scale-105 transition-all duration-300">
            <Plane className="w-10 h-10 text-white transform rotate-45" />
            <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent rounded-2xl"></div>
          </div>
          <h1 className="text-3xl font-bold tracking-tight mb-2">
            <span className="bg-gradient-to-r from-blue-600 via-blue-800 to-blue-600 dark:from-blue-400 dark:via-blue-300 dark:to-blue-500 bg-clip-text text-transparent animate-gradient-x bg-[length:200%_200%]">
              United Airlines
            </span>
          </h1>
          <p className="text-gray-600 dark:text-slate-300 font-medium tracking-wide">
            Flight Demand Forecaster
          </p>
        </div>

        {/* Authentication Form */}
        <div className="bg-white/80 dark:bg-slate-800/90 backdrop-blur-xl rounded-2xl shadow-2xl border border-gray-200/50 dark:border-slate-600/50 p-8 transition-all duration-300 hover:shadow-3xl">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-blue-100 to-blue-200 dark:from-blue-900/50 dark:to-blue-800/50 rounded-xl mb-4 shadow-lg">
              <Lock className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-slate-100 tracking-tight mb-2">
              Secure Access Required
            </h2>
            <p className="text-sm text-gray-600 dark:text-slate-400 font-medium">
              Enter your password to access the dashboard
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Enter password"
                className="w-full px-4 py-4 bg-gray-50/80 dark:bg-slate-700/80 backdrop-blur-sm border-2 border-gray-300 dark:border-slate-500 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 dark:focus:ring-blue-400/50 dark:focus:border-blue-400 text-gray-900 dark:text-slate-100 placeholder-gray-500 dark:placeholder-slate-400 font-medium transition-all duration-300 pr-12 shadow-lg hover:border-gray-400 dark:hover:border-slate-400"
                disabled={isLoading}
                autoFocus
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300 transition-colors duration-200"
                disabled={isLoading}
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>

            {error && (
              <div className="text-red-600 dark:text-red-400 text-sm font-medium text-center bg-red-50/80 dark:bg-red-900/30 backdrop-blur-sm py-2 px-4 rounded-lg border border-red-200/50 dark:border-red-800/50 shadow-lg">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={!password || isLoading}
              className={`w-full py-4 font-semibold rounded-xl transition-all duration-300 transform shadow-xl backdrop-blur-sm border-2 ${
                !password || isLoading
                  ? 'bg-gradient-to-r from-gray-400 to-gray-500 dark:from-slate-600 dark:to-slate-700 text-white cursor-not-allowed border-gray-500 dark:border-slate-500 shadow-lg'
                  : 'bg-gradient-to-r from-blue-600 to-blue-700 dark:from-blue-500 dark:to-blue-600 hover:from-blue-700 hover:to-blue-800 dark:hover:from-blue-600 dark:hover:to-blue-700 text-white hover:scale-[1.02] hover:shadow-2xl border-blue-700 dark:border-blue-500'
              }`}
            >
              {isLoading ? (
                <div className="flex items-center justify-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white/70 border-t-white rounded-full animate-spin"></div>
                  <span>Authenticating...</span>
                </div>
              ) : (
                'Access Dashboard'
              )}
            </button>
          </form>
        </div>

        {/* Footer */}
        <div className="text-center mt-8">
          <p className="text-xs text-gray-500 dark:text-slate-400 font-medium">
            Authorized personnel only • Secure access required
          </p>
        </div>
      </div>
    </div>
  );
};

export default PasswordAuth;