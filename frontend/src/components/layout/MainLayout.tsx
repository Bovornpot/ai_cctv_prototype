// frontend/src/components/layout/MainLayout.tsx
import React from 'react';
import { useLocation } from 'react-router-dom'; // Import useLocation
import Header from './Header';
import Sidebar from './Sidebar';
import './MainLayout.css';

interface MainLayoutProps {
  children: React.ReactNode;
  currentDate: Date;
  activeTab: 'Day' | 'Week' | 'Month';
  onDateChange: (newDate: Date) => void;
  onTabChange: (tab: 'Day' | 'Week' | 'Month') => void;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children, currentDate, activeTab, onDateChange, onTabChange }) => {
  const location = useLocation(); // useLocation hook is now correctly inside <Router> context

  // Determine dynamic page title based on current route
  const getPageTitle = (pathname: string): string => {
    switch (pathname) {
      case '/':
        return 'Dashboard Overview';
      case '/parking-violations':
        return 'Parking Violation';
      case '/table-occupancy':
        return 'Table Occupancy';
      case '/chilled-basket-alerts':
        return 'Chilled Basket Alert';
      case '/ai-settings':
        return 'AI Setting';
      default:
        return 'Dashboard';
    }
  };

  const dynamicPageTitle = getPageTitle(location.pathname);

  return (
    <div className="layout-container">
      <Header
        currentDate={currentDate}
        activeTab={activeTab}
        onDateChange={onDateChange}
        onTabChange={onTabChange}
      />
      <div className="content-area">
        <Sidebar />
        <main className="layout-content">
          {/* Dynamic Page Title, aligned with content area */}
          <h1 className="text-2xl font-bold text-gray-800 mb-4">{dynamicPageTitle}</h1> {/* Use dynamicPageTitle here */}
          {React.Children.map(children, child =>
            React.isValidElement(child)
              ? React.cloneElement(child as React.ReactElement<any>, { currentDate, activeTab })
              : child
          )}
        </main>
      </div>
    </div>
  );
};

export default MainLayout;