import React, { useState, useEffect } from 'react';
import PasswordAuth from './components/PasswordAuth';
import TopNavigation from './components/TopNavigation';
import FlightRouteMap from './components/FlightRouteMap';
import ChatInterfaceConnected from './components/ChatInterfaceConnected';

function AppConnected() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isMapCollapsed, setIsMapCollapsed] = useState(false);

  // Initialize dark mode from localStorage or system preference
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
      setIsDarkMode(true);
      document.documentElement.classList.add('dark');
    }
  }, []);

  const handleAuthentication = () => {
    setIsAuthenticated(true);
  };

  const handleGoBack = () => {
    setIsAuthenticated(false);
  };

  const toggleTheme = () => {
    const newDarkMode = !isDarkMode;
    setIsDarkMode(newDarkMode);
    
    if (newDarkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  };

  const toggleMapCollapse = () => {
    setIsMapCollapsed(!isMapCollapsed);
  };

  // Show password authentication page if not authenticated
  if (!isAuthenticated) {
    return (
      <PasswordAuth 
        onAuthenticate={handleAuthentication}
        isDarkMode={isDarkMode}
        onThemeToggle={toggleTheme}
      />
    );
  }

  // Show main dashboard if authenticated
  return (
    <div className="h-screen bg-gray-300 dark:bg-slate-700 transition-colors duration-300 overflow-hidden">
      {/* Top Navigation */}
      <TopNavigation 
        isDarkMode={isDarkMode} 
        onThemeToggle={toggleTheme}
        onGoBack={handleGoBack}
      />
      
      {/* Main Content - Adjusted padding for taller nav */}
      <div className="h-full pt-28 px-6 pb-6">
        <div className="flex space-x-6 h-full">
          {/* Flight Route Map */}
          <div className={`transition-all duration-300 ${isMapCollapsed ? 'w-24' : 'w-3/5'}`}>
            <FlightRouteMap 
              isCollapsed={isMapCollapsed}
              onToggleCollapse={toggleMapCollapse}
            />
          </div>
          
          {/* Chat Interface - Using Connected Version */}
          <div className={`transition-all duration-300 ${isMapCollapsed ? 'w-full' : 'w-2/5'}`}>
            <ChatInterfaceConnected isExpanded={!isMapCollapsed} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default AppConnected;