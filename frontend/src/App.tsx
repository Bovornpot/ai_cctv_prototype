// frontend/src/App.tsx
import React, { useState} from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import DashboardOverviewPage from './pages/DashboardOverviewPage';
import ParkingViolationDetailsPage from './pages/ParkingViolationDetailsPage';
import { TimeSelection } from './types/time';
import { getWeekNumber } from './utils/dateUtils';
import './index.css';

function App() {
  //ADD: State ใหม่ที่ใช้ TimeSelection
  const [timeSelection, setTimeSelection] = useState<TimeSelection>({
    activeTab: 'Day',
    mode: 'single',
    startDate: new Date(),
    endDate: new Date(),
  });

  //ADD: ฟังก์ชัน Handler ใหม่เพียงหนึ่งเดียวสำหรับอัปเดต TimeSelection object
  const handleTimeSelectionChange = (newSelection: TimeSelection) => {
    setTimeSelection(newSelection);
  };

  

  return (
    <Router>
      <MainLayout
        timeSelection={timeSelection}
        onTimeSelectionChange={handleTimeSelectionChange}
        // pageTitle prop is now handled internally by MainLayout
      >
        <Routes>
          <Route
            path="/"
            element={
              <DashboardOverviewPage
                timeSelection={timeSelection}
              />
            }
          />
          {/* <Route path="/parking-violations" element={<div className="p-6"><h2>Parking Violation Page</h2><p>Details will go here.</p></div>} /> */}
          <Route
            path="/parking-violations"
            element={<ParkingViolationDetailsPage timeSelection={timeSelection}/>}
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