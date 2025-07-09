// frontend/src/components/layout/Header.tsx
import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Search } from 'lucide-react';
import { formatDateDisplay, generateCalendarData, getWeekRangeForDate, getUpdateEndDate } from '../../utils/dateUtils';
import './Header.css';

interface HeaderProps {
  currentDate: Date;
  activeTab: 'Day' | 'Week' | 'Month';
  onDateChange: (newDate: Date) => void;
  onTabChange: (tab: 'Day' | 'Week' | 'Month') => void;
}

const Header: React.FC<HeaderProps> = ({ currentDate, activeTab, onDateChange, onTabChange }) => {
  const [showDatePicker, setShowDatePicker] = useState(false);

  const navigateDate = (direction: number) => {
    const newDate = new Date(currentDate);
    if (activeTab === 'Day') {
      newDate.setDate(currentDate.getDate() + direction);
    } else if (activeTab === 'Week') {
      newDate.setDate(currentDate.getDate() + (direction * 7));
    } else { // Month
      newDate.setMonth(currentDate.getMonth() + direction);
    }
    onDateChange(newDate);
  };

  const handleTabClick = (tab: 'Day' | 'Week' | 'Month') => {
    onTabChange(tab);
    setShowDatePicker(false);
  };

  const handleDaySelect = (date: Date) => {
    onDateChange(date);
    setShowDatePicker(false);
  };

  const handleWeekSelect = (date: Date) => {
    onDateChange(date);
    setShowDatePicker(false);
  };

  const isDateInSelectedWeek = (date: Date) => {
    if (!date) return false;
    const { start, end } = getWeekRangeForDate(currentDate);
    return date >= start && date <= end;
  };

  // Close date picker when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const datePickerPopup = document.getElementById('date-picker-popup');
      const dateDisplayButton = document.getElementById('date-display-button');
      if (datePickerPopup && !datePickerPopup.contains(event.target as Node) &&
          dateDisplayButton && !dateDisplayButton.contains(event.target as Node)) {
        setShowDatePicker(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <header className="header-container">
      {/* Left Section: Logo and App Name */}
      <div className="header-left-section">
        <img src="/ai-cctv-logo.svg" alt="AI CCTV Logo" className="header-logo" />
        <span className="header-app-name">AI CCTV</span>
        {/* Dynamic Page Title (h1) has been moved to MainLayout.tsx */}
      </div>

      {/* Right Section: Combined Time, Date Filters, Branch Input, Search Button */}
      <div className="header-right-controls">
        <span className="header-time-label">Time</span>
        <div className="header-date-nav">
          <button
            onClick={() => navigateDate(-1)}
            className="header-nav-btn"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            id="date-display-button"
            onClick={() => setShowDatePicker(!showDatePicker)}
            className="header-date-display-btn"
          >
            {formatDateDisplay(currentDate, activeTab)}
            {showDatePicker && (
              <div id="date-picker-popup" className="header-date-picker-popup">
                {/* Date Picker Header */}
                <div className="flex items-center justify-between mb-4">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      const newDate = new Date(currentDate);
                      newDate.setMonth(currentDate.getMonth() - 1);
                      onDateChange(newDate);
                    }}
                    className="p-1 hover:bg-gray-100 rounded"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <h3 className="font-medium text-gray-800">
                    {currentDate.toLocaleDateString('th-TH', { month: 'long', year: 'numeric' })}
                  </h3>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      const newDate = new Date(currentDate);
                      newDate.setMonth(currentDate.getMonth() + 1);
                      onDateChange(newDate);
                    }}
                    className="p-1 hover:bg-gray-100 rounded"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>

                {/* Calendar for Day/Week selection */}
                {(activeTab === 'Day' || activeTab === 'Week') && (
                  <div className="space-y-2">
                    {/* Day headers */}
                    <div className="grid grid-cols-7 gap-1 text-xs text-gray-500 font-medium">
                      {['อา', 'จ', 'อ', 'พ', 'พฤ', 'ศ', 'ส'].map(day => (
                        <div key={day} className="text-center p-1">{day}</div>
                      ))}
                    </div>

                    {/* Calendar days */}
                    {generateCalendarData(currentDate).map((week, weekIndex) => (
                      <div key={weekIndex} className="grid grid-cols-7 gap-1">
                        {week.map((date, dayIndex) => {
                          const isSelected = activeTab === 'Day'
                            ? date && date.toDateString() === currentDate.toDateString()
                            : date && isDateInSelectedWeek(date);
                          const isToday = date && date.toDateString() === new Date().toDateString();

                          return (
                            <button
                              key={dayIndex}
                              onClick={(e) => {
                                e.stopPropagation();
                                if (date) {
                                  if (activeTab === 'Week') {
                                    handleWeekSelect(date);
                                  } else {
                                    handleDaySelect(date);
                                  }
                                }
                              }}
                              className={`
                                text-xs p-2 rounded hover:bg-gray-100 transition-colors
                                ${!date ? 'invisible' : ''}
                                ${isSelected ? 'bg-blue-500 text-white hover:bg-blue-600' : ''}
                                ${isToday && !isSelected ? 'bg-blue-100 text-blue-600' : ''}
                                ${activeTab === 'Week' && date && isDateInSelectedWeek(date) ? 'bg-blue-200' : ''}
                              `}
                              disabled={!date}
                            >
                              {date?.getDate()}
                            </button>
                          );
                        })}
                      </div>
                    ))}

                    {/* Week selection helper for Week tab */}
                    {activeTab === 'Week' && (
                      <div className="mt-4 p-3 bg-gray-50 rounded text-sm text-gray-600">
                        <div className="font-medium mb-1">คลิกวันใดวันหนึ่งเพื่อเลือกสัปดาห์</div>
                        <div className="text-xs">
                          สัปดาห์ที่เลือก: {(() => {
                            const { start, end } = getWeekRangeForDate(currentDate);
                            return `${start.getDate()}/${start.getMonth() + 1} - ${end.getDate()}/${end.getMonth() + 1}`;
                          })()}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Month selection */}
                {activeTab === 'Month' && (
                  <div className="grid grid-cols-3 gap-2">
                    {Array.from({ length: 12 }, (_, i) => {
                      const monthDate = new Date(currentDate.getFullYear(), i, 1);
                      const isSelected = i === currentDate.getMonth();
                      return (
                        <button
                          key={i}
                          onClick={(e) => {
                            e.stopPropagation();
                            onDateChange(monthDate);
                            setShowDatePicker(false);
                          }}
                          className={`
                            p-2 text-sm rounded hover:bg-gray-100 transition-colors
                            ${isSelected ? 'bg-blue-500 text-white hover:bg-blue-600' : ''}
                          `}
                        >
                          {monthDate.toLocaleDateString('th-TH', { month: 'short' })}
                        </button>
                      );
                    })}
                  </div>
                )}

                {/* Quick actions */}
                <div className="flex gap-2 mt-4 pt-3 border-t">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDateChange(new Date());
                      setShowDatePicker(false);
                    }}
                    className="flex-1 px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded"
                  >
                    ตอนนี้
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowDatePicker(false);
                    }}
                    className="flex-1 px-3 py-1 text-sm bg-blue-500 text-white hover:bg-blue-600 rounded"
                  >
                    ปิด
                  </button>
                </div>
                {/* Data updated until message */}
                <div className="text-xs text-gray-500 mt-4 text-center">
                  ข้อมูลอัปเดตถึง: {getUpdateEndDate(currentDate, activeTab)}
                </div>
              </div>
            )}
          </button>
          <button
            onClick={() => navigateDate(1)}
            className="header-nav-btn"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        <div className="header-filter-tabs">
          {['Day', 'Week', 'Month'].map((tab) => (
            <button
              key={tab}
              onClick={() => handleTabClick(tab as 'Day' | 'Week' | 'Month')}
              className={`header-tab-btn ${
                activeTab === tab
                  ? 'header-tab-btn-active'
                  : ''
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
        <input type="text" placeholder="สาขา" className="header-branch-input" />
        <button className="header-search-btn">
          <Search className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
};

export default Header;