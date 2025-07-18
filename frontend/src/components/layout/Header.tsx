// frontend/src/components/layout/Header.tsx
import React, { useState, useEffect, useRef } from 'react'; 
import { ChevronLeft, ChevronRight, Search } from 'lucide-react';
import { TimeSelection } from '../../types/time';
import {
  formatTimeSelectionDisplay, //
  generateCalendarData,
  getWeekRangeForDate,
  getWeekNumber,
  generateWeekGrid,
  getWeekRangeFromWeekNumber,
} from '../../utils/dateUtils';
import './Header.css';

interface HeaderProps {
  timeSelection: TimeSelection;
  onTimeSelectionChange: (selection: TimeSelection) => void;
}

const Header: React.FC<HeaderProps> = ({ timeSelection, onTimeSelectionChange }) => {
  const [showDatePicker, setShowDatePicker] = useState(false);

  const [mode, setMode] = useState<'single' | 'range'>('single');
  const [rangeStart, setRangeStart] = useState<Date | number | null>(null);
  const [viewDate, setViewDate] = useState(new Date());

  const pickerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (timeSelection.activeTab === 'Day') {
        setViewDate(timeSelection.startDate);
    } else if (timeSelection.activeTab === 'Week' || timeSelection.activeTab === 'Month') {
        setViewDate(new Date(timeSelection.year, 0, 1));
    }
  }, [timeSelection]);

  const navigateDate = (direction: number) => {
    if (timeSelection.activeTab === 'Day') {
      const newDate = new Date(timeSelection.startDate);
      newDate.setDate(newDate.getDate() + direction);
      onTimeSelectionChange({ ...timeSelection, startDate: newDate, endDate: newDate });
    } else if (timeSelection.activeTab === 'Week') {
      // For week, we navigate by week, not just one day
      const tempDate = getWeekRangeFromWeekNumber(timeSelection.year, timeSelection.week).start;
      tempDate.setDate(tempDate.getDate() + (direction * 7));
      const newYear = tempDate.getFullYear();
      const newWeek = getWeekNumber(tempDate);
      onTimeSelectionChange({ ...timeSelection, year: newYear, week: newWeek, startWeek: newWeek, endWeek: newWeek });
    } else { // Month
      const currentMonthDate = new Date(timeSelection.year, timeSelection.month, 1);
      currentMonthDate.setMonth(currentMonthDate.getMonth() + direction);
      const newYear = currentMonthDate.getFullYear();
      const newMonth = currentMonthDate.getMonth();
      onTimeSelectionChange({ ...timeSelection, year: newYear, month: newMonth, startMonth: newMonth, endMonth: newMonth });
    }
  };

  const handleTabClick = (tab: 'Day' | 'Week' | 'Month') => {
    setMode('single');
    setRangeStart(null);
    const now = new Date();
    let newSelection: TimeSelection;

    if (tab === 'Day') {
        newSelection = { activeTab: 'Day', mode: 'single', startDate: now, endDate: now };
    } else if (tab === 'Week') {
        const week = getWeekNumber(now);
        newSelection = { activeTab: 'Week', mode: 'single', year: now.getFullYear(), week, startWeek: week, endWeek: week };
    } else { // Month
        newSelection = { activeTab: 'Month', mode: 'single', year: now.getFullYear(), month: now.getMonth(), startMonth: now.getMonth(), endMonth: now.getMonth() };
    }
    onTimeSelectionChange(newSelection);
  };

  const handleDaySelect = (day: Date) => {
    if (timeSelection.activeTab !== 'Day') return;
    if (mode === 'single') {
        onTimeSelectionChange({ ...timeSelection, mode, startDate: day, endDate: day });
        setShowDatePicker(false);
    } else { // range
        if (!rangeStart) {
            setRangeStart(day);
        } else {
            const start = rangeStart < day ? (rangeStart as Date) : day;
            const end = rangeStart < day ? day : (rangeStart as Date);
            onTimeSelectionChange({ ...timeSelection, mode, startDate: start, endDate: end });
            setRangeStart(null);
            setShowDatePicker(false);
        }
    }
  };

  const handleWeekSelect = (weekNum: number) => {
      if (timeSelection.activeTab !== 'Week') return;
      // const year = timeSelection.year;
      if (mode === 'single') {
          onTimeSelectionChange({ ...timeSelection, mode, year: timeSelection.year, week: weekNum, startWeek: weekNum, endWeek: weekNum });
          setShowDatePicker(false);
      } else { // range
          if (!rangeStart) {
              setRangeStart(weekNum);
          } else {
              const start = Math.min(rangeStart as number, weekNum);
              const end = Math.max(rangeStart as number, weekNum);
              onTimeSelectionChange({ ...timeSelection, mode, year: timeSelection.year, week: start, startWeek: start, endWeek: end });
              setRangeStart(null);
              setShowDatePicker(false);
          }
      }
  };

  const handleMonthSelect = (monthIndex: number) => {
      if (timeSelection.activeTab !== 'Month') return;
      // const year = timeSelection.year;
      if (mode === 'single') {
          onTimeSelectionChange({ ...timeSelection, mode, year: timeSelection.year, month: monthIndex, startMonth: monthIndex, endMonth: monthIndex });
          setShowDatePicker(false);
      } else { // range
          if (!rangeStart) {
              setRangeStart(monthIndex);
          } else {
              const start = Math.min(rangeStart as number, monthIndex);
              const end = Math.max(rangeStart as number, monthIndex);
              onTimeSelectionChange({ ...timeSelection, mode, year: timeSelection.year, month: start, startMonth: start, endMonth: end });
              setRangeStart(null);
              setShowDatePicker(false);
          }
      }
  };

  const handleWeekDaySelect = (day: Date) => {
    if (timeSelection.activeTab !== 'Week') return;
    const year = day.getFullYear();
    const weekNum = getWeekNumber(day);
    onTimeSelectionChange({ ...timeSelection, mode: 'single', year, week: weekNum, startWeek: weekNum, endWeek: weekNum });
    setShowDatePicker(false);
}


  // Close date picker when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      // ใช้ ref แทน getElementById เพื่อความปลอดภัย
      if (pickerRef.current && !pickerRef.current.contains(event.target as Node)) {
        // เมื่อคลิกข้างนอก ให้ปิด popup และเคลียร์ range selection ที่ค้างอยู่
        setShowDatePicker(false);
        setRangeStart(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <header className="header-container">
      {/* --- ส่วนซ้าย: Logo and App Name (คงเดิม ไม่มีการเปลี่ยนแปลง) --- */}
      <div className="header-left-section">
        <img src="/ai-cctv-logo.svg" alt="AI CCTV Logo" className="header-logo" />
        <span className="header-app-name">AI CCTV</span>
      </div>

      {/* --- ส่วนขวา: Controls ทั้งหมด (คงโครงสร้างเดิมไว้) --- */}
      <div className="header-right-controls">
        <span className="header-time-label">Time</span>
        <div className="header-date-nav">
          {/* --- ปุ่มลูกศรซ้าย (คงเดิม) --- */}
          <button
            onClick={() => navigateDate(-1)}
            className="header-nav-btn"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          {/* ✨ ADD: เพิ่ม div ครอบปุ่มและ popup เพื่อใช้กับ ref สำหรับการคลิกนอกพื้นที่ */}
          <div ref={pickerRef} className="relative">
            {/* 🔄️ EDIT: แก้ไข button เดิมเล็กน้อย */}
            <button
              id="date-display-button"
              // ✅ onClick ยังคงใช้ state เดิมในการเปิด/ปิด
              onClick={() => setShowDatePicker(!showDatePicker)}
              className="header-date-display-btn"
            >
              {/* 🔄️ EDIT: เปลี่ยนไปใช้ฟังก์ชัน format ใหม่ที่รับ TimeSelection object */}
              {formatTimeSelectionDisplay(timeSelection)}
              {/* * 🗑️ REMOVE: โค้ดแสดงผลเดิมถูกลบออกเพื่อใช้ตัวใหม่
               * {formatDateDisplay(currentDate, activeTab)} 
               */}
            </button> 

            {/* 🔄️ EDIT: เงื่อนไขการแสดงผลยังเหมือนเดิม แต่เนื้อหาข้างในถูกยกเครื่องใหม่ทั้งหมด */}
            {showDatePicker && (
              <div id="date-picker-popup" className="header-date-picker-popup">
                
                {/* ✨ ADD: ส่วนควบคุม Mode Toggle (Single/Range) ใหม่ทั้งหมด */}
                <div className="flex justify-center bg-gray-100 rounded-lg p-1 mb-4">
                  {(['single', 'range'] as const).map(m => (
                    <button 
                      key={m} 
                      onClick={() => setMode(m)}
                      className={`w-1/2 px-4 py-1 text-sm font-semibold rounded-md transition-colors capitalize ${
                        mode === m 
                        ? 'bg-white text-blue-600 shadow' 
                        : 'text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {m === 'single' ? 'เลือกเดี่ยว' : 'เลือกช่วง'}
                    </button>
                  ))}
                </div>
                
                {/* --- 🗑️ REMOVE: โครงสร้าง Popup เดิมทั้งหมดด้านล่างนี้จะถูกลบออก และแทนที่ด้วย Logic ใหม่ --- */}

                {/* --- ✨ ADD: ส่วนแสดงผลหลักของ Picker ที่เปลี่ยนตาม Tab และ Mode --- */}

                {/* --- กรณี 1: Tab "Day" ถูกเลือก --- */}
                {timeSelection.activeTab === 'Day' && (
                  <div>
                    {/* ส่วน Header ของปฏิทิน (สำหรับเลื่อนเดือน) */}
                    <div className="flex items-center justify-between mb-2">
                      <button onClick={() => setViewDate(prev => new Date(prev.getFullYear(), prev.getMonth() - 1, 1))} className="p-1 hover:bg-gray-100 rounded"><ChevronLeft className="w-5 h-5" /></button>
                      <h3 className="font-medium text-gray-800">{viewDate.toLocaleDateString('th-TH', { month: 'long', year: 'numeric' })}</h3>
                      <button onClick={() => setViewDate(prev => new Date(prev.getFullYear(), prev.getMonth() + 1, 1))} className="p-1 hover:bg-gray-100 rounded"><ChevronRight className="w-5 h-5" /></button>
                    </div>
                    {/* ส่วนหัวตารางปฏิทิน (อา-ส) */}
                    <div className="grid grid-cols-7 gap-1 text-xs text-center text-gray-500 font-medium my-2">
                      {['อา', 'จ', 'อ', 'พ', 'พฤ', 'ศ', 'ส'].map(day => <div key={day}>{day}</div>)}
                    </div>
                    {/* ส่วนตารางปฏิทิน */}
                    <div className="grid grid-cols-7 gap-1">
                      {generateCalendarData(viewDate).map((week, weekIndex) => (
                        week.map((day, dayIndex) => {
                          if (!day) return <div key={`${weekIndex}-${dayIndex}`} />;
                          
                          // Logic การ highlight วันที่เลือก
                          const dayString = day.toDateString();
                          const isSelected = mode === 'single' && timeSelection.activeTab === 'Day' && timeSelection.startDate.toDateString() === dayString;
                          const isInRange = mode === 'range' && timeSelection.activeTab === 'Day' && day >= timeSelection.startDate && day <= timeSelection.endDate;
                          const isRangeEndpoint = isInRange && (day.toDateString() === timeSelection.startDate.toDateString() || day.toDateString() === timeSelection.endDate.toDateString());
                          const isPending = mode === 'range' && rangeStart && (rangeStart as Date).toDateString() === dayString;

                          return (
                            <button key={dayString} onClick={() => handleDaySelect(day)}
                              className={`p-2 text-sm rounded-md transition-colors ${
                                isPending ? 'bg-blue-500 text-white ring-2 ring-blue-300' :
                                isRangeEndpoint ? 'bg-blue-500 text-white' :
                                isInRange ? 'bg-blue-200 hover:bg-blue-300' :
                                isSelected ? 'bg-blue-500 text-white' : 'hover:bg-gray-100'
                              }`}>
                              {day.getDate()}
                            </button>
                          );
                        })
                      ))}
                    </div>
                  </div>
                )}

                {/* --- กรณี 2: Tab "Week" ถูกเลือก --- */}
                {timeSelection.activeTab === 'Week' && (
                  // 🔄️ EDIT: เปลี่ยนทั้งบล็อกนี้
                  mode === 'single' ? (
                    // ✨ ให้แสดง UI ปฏิทินเหมือนของ Day แต่เรียกใช้ handler ใหม่
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <button onClick={() => setViewDate(prev => new Date(prev.getFullYear(), prev.getMonth() - 1, 1))} className="p-1 hover:bg-gray-100 rounded"><ChevronLeft className="w-5 h-5" /></button>
                        <h3 className="font-medium text-gray-800">{viewDate.toLocaleDateString('th-TH', { month: 'long', year: 'numeric' })}</h3>
                        <button onClick={() => setViewDate(prev => new Date(prev.getFullYear(), prev.getMonth() + 1, 1))} className="p-1 hover:bg-gray-100 rounded"><ChevronRight className="w-5 h-5" /></button>
                      </div>
                      <div className="grid grid-cols-7 gap-1 text-xs text-center text-gray-500 font-medium my-2">
                        {['อา', 'จ', 'อ', 'พ', 'พฤ', 'ศ', 'ส'].map(day => <div key={day}>{day}</div>)}
                      </div>
                      <div className="grid grid-cols-7 gap-1">
                        {generateCalendarData(viewDate).map((week, weekIndex) => (
                          week.map((day, dayIndex) => {
                            if (!day) return <div key={`${weekIndex}-${dayIndex}`} />;
                            const { start } = getWeekRangeForDate(day);
                            const isSelected = timeSelection.activeTab === 'Week' && timeSelection.week === getWeekNumber(day) && timeSelection.year === day.getFullYear();

                            return (
                              <button key={day.toDateString()} onClick={() => handleWeekDaySelect(day)}
                                className={`p-2 text-sm rounded-md transition-colors ${isSelected ? 'bg-blue-200' : 'hover:bg-gray-100'}`}>
                                {day.getDate()}
                              </button>
                            );
                          })
                        ))}
                      </div>
                    </div>
                  ) : (
                    // ส่วนของ Range Mode (ถูกต้องอยู่แล้ว)
                    <div>
                      {/* ส่วน Header สำหรับเลื่อนปี */}
                      <div className="flex items-center justify-between mb-4">
                          <button onClick={() => setViewDate(new Date(viewDate.getFullYear() - 1, 0, 1))} className="p-1 hover:bg-gray-100 rounded">
                              <ChevronLeft className="w-5 h-5" />
                          </button>
                          <h3 className="font-medium text-gray-800">ปี {viewDate.getFullYear()}</h3>
                          <button onClick={() => setViewDate(new Date(viewDate.getFullYear() + 1, 0, 1))} className="p-1 hover:bg-gray-100 rounded">
                              <ChevronRight className="w-5 h-5" />
                          </button>
                      </div>
                      {/* ส่วน Grid แสดงสัปดาห์ */}
                      <div className="grid grid-cols-8 gap-2">
                        {generateWeekGrid(viewDate.getFullYear()).map((weekNum) => {
                          const { startWeek, endWeek } = timeSelection.activeTab === 'Week' ? timeSelection : { startWeek: -1, endWeek: -1 };
                          const isInRange = mode === 'range' && weekNum >= startWeek && weekNum <= endWeek;
                          const isRangeEndpoint = isInRange && (weekNum === startWeek || weekNum === endWeek);
                          const isPending = rangeStart === weekNum;

                          return (
                            <button key={weekNum} onClick={() => handleWeekSelect(weekNum)}
                              className={`flex items-center justify-center h-8 text-xs rounded-md transition-colors ${
                                isPending ? 'bg-blue-500 text-white ring-2 ring-blue-300' :
                                isRangeEndpoint ? 'bg-blue-500 text-white' :
                                isInRange ? 'bg-blue-200 hover:bg-blue-300' :
                                'hover:bg-gray-100'
                              }`}>
                              {weekNum}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )
                )}

                {/* --- กรณี 3: Tab "Month" ถูกเลือก --- */}
                {timeSelection.activeTab === 'Month' && (
                  <div>
                    <div className="flex items-center justify-between mb-4">
                        <button onClick={() => setViewDate(new Date(viewDate.getFullYear() - 1, 0, 1))} className="p-1 hover:bg-gray-100 rounded"><ChevronLeft className="w-5 h-5" /></button>
                        <h3 className="font-medium text-gray-800">ปี {viewDate.getFullYear()}</h3>
                        <button onClick={() => setViewDate(new Date(viewDate.getFullYear() + 1, 0, 1))} className="p-1 hover:bg-gray-100 rounded"><ChevronRight className="w-5 h-5" /></button>
                    </div>
                    <div className="grid grid-cols-4 gap-2">
                      {Array.from({ length: 12 }).map((_, monthIndex) => {
                        // Logic การ highlight เดือนที่เลือก
                        const { month, startMonth, endMonth } = timeSelection.activeTab === 'Month' ? timeSelection : { month: -1, startMonth: -1, endMonth: -1 };
                        const isSelected = mode === 'single' && month === monthIndex;
                        const isInRange = mode === 'range' && monthIndex >= startMonth && monthIndex <= endMonth;
                        const isRangeEndpoint = isInRange && (monthIndex === startMonth || monthIndex === endMonth);
                        const isPending = rangeStart === monthIndex;

                        return (
                          <button key={monthIndex} onClick={() => handleMonthSelect(monthIndex)}
                            className={`p-3 text-sm rounded-md transition-colors ${
                              isPending ? 'bg-blue-500 text-white ring-2 ring-blue-300' :
                              isRangeEndpoint ? 'bg-blue-500 text-white' :
                              isInRange ? 'bg-blue-200 hover:bg-blue-300' :
                              isSelected ? 'bg-blue-500 text-white' : 'hover:bg-gray-100'
                            }`}>
                            {new Date(0, monthIndex).toLocaleDateString('th-TH', { month: 'short' })}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* 🗑️ REMOVE: ส่วน Quick actions และ Data Updated เดิมถูกนำออกทั้งหมด */}
              </div>
            )}
          </div>
          {/* ปุ่มเลือกเวลาที่ต้องการจะดู จบ*/}

          {/* --- ปุ่มลูกศรขวา (คงเดิม) --- */}
          <button
            onClick={() => navigateDate(1)}
            className="header-nav-btn"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* --- ปุ่ม Tab Day/Week/Month (คงเดิม) --- */}
        <div className="header-filter-tabs">
          {/* 🔄️ EDIT: แก้ไข Logic การเปรียบเทียบ active tab และ handler */}
          {(['Day', 'Week', 'Month'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => handleTabClick(tab)}
              className={`header-tab-btn ${
                timeSelection.activeTab === tab // 🔄️ ใช้ timeSelection.activeTab
                  ? 'header-tab-btn-active'
                  : ''
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* --- ปุ่ม Search สาขา (คงเดิม ไม่มีการเปลี่ยนแปลง) --- */}
        <input type="text" placeholder="สาขา" className="header-branch-input" />
        <button className="header-search-btn">
          <Search className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
};

export default Header;