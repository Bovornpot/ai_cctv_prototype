// frontend/src/types/time.ts

// รูปแบบการเลือก: เดี่ยว หรือ ช่วง
export type SelectionMode = 'single' | 'range';

// การเลือกวันที่ (สำหรับแท็บ DAY)
export interface DaySelection {
  activeTab: 'Day';
  mode: SelectionMode;
  startDate: Date;
  endDate: Date; // ในโหมด single, startDate จะเท่ากับ endDate
}

// การเลือกสัปดาห์ (สำหรับแท็บ WEEK)
export interface WeekSelection {
  activeTab: 'Week';
  mode: 'single';
  year: number;
  week: number;
}

export interface WeekRangeSelection {
  activeTab: 'Week';
  mode: 'range';
  year: number;
  startWeek: number;
  endWeek: number;
}

// การเลือกเดือน (สำหรับแท็บ MONTH)
export interface MonthSelection {
  activeTab: 'Month';
  mode: 'single';
  year: number;
  month: number; // 0-11
}

export interface MonthRangeSelection {
  activeTab: 'Month';
  mode: 'range';
  year: number;
  startMonth: number;
  endMonth: number;
}

// Union Type ที่รวมทุกรูปแบบการเลือกเวลาที่เป็นไปได้
export type TimeSelection = 
  | DaySelection
  | WeekSelection
  | WeekRangeSelection
  | MonthSelection
  | MonthRangeSelection;