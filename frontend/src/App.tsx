// frontend/src/App.tsx
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import DashboardOverviewPage from './pages/DashboardOverviewPage';
import ParkingViolationDetailsPage from './pages/ParkingViolationDetailsPage';
import './index.css';

function App() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [activeTab, setActiveTab] = useState<'Day' | 'Week' | 'Month'>('Day');

  const handleDateChange = (newDate: Date) => {
    setCurrentDate(newDate);
  };

  const handleTabChange = (tab: 'Day' | 'Week' | 'Month') => {
    setActiveTab(tab);
    if (tab === 'Day' || tab === 'Week') {
      setCurrentDate(new Date());
    } else {
      setCurrentDate(new Date(new Date().getFullYear(), new Date().getMonth(), 1));
    }
  };

  return (
    <Router>
      <MainLayout
        currentDate={currentDate}
        activeTab={activeTab}
        onDateChange={handleDateChange}
        onTabChange={handleTabChange}
        // pageTitle prop is now handled internally by MainLayout
      >
        <Routes>
          <Route
            path="/"
            element={
              <DashboardOverviewPage
                currentDate={currentDate}
                activeTab={activeTab}
              />
            }
          />
          {/* <Route path="/parking-violations" element={<div className="p-6"><h2>Parking Violation Page</h2><p>Details will go here.</p></div>} /> */}
          <Route
            path="/parking-violations"
            element={<ParkingViolationDetailsPage />} // <-- แก้จาก div เป็น Component ของเรา
          />

          <Route path="/table-occupancy" element={<div className="p-6"><h2>Table Occupancy Page</h2><p>Details will go here.</p></div>} />
          <Route path="/chilled-basket-alerts" element={<div className="p-6"><h2>Chilled Basket Alert Page</h2><p>Details will go here.</p></div>} />
          <Route path="/ai-settings" element={<div className="p-6"><h2>AI Setting Page</h2><p>Details will go here.</p></div>} />
          <Route path="*" element={<div className="p-6 text-center text-xl text-gray-600">404 - Page Not Found</div>} />
        </Routes>
      </MainLayout>
    </Router>
  );
}

export default App;