// frontend/src/utils/dateUtils.ts

// Helper function to get week number (ISO week date system)
export const getWeekNumber = (date: Date): number => {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const dayNum = d.getUTCDay() || 7; // make Sunday (0) = 7
  d.setUTCDate(d.getUTCDate() + 4 - dayNum); // Set to nearest Thursday
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);
};

// Helper function to get week range (Monday to Sunday) for a given date
export const getWeekRangeForDate = (date: Date) => {
  const startOfWeek = new Date(date);
  const day = startOfWeek.getDay(); // 0 = Sunday, 1 = Monday
  // Adjust to Monday: If day is 0 (Sunday), diff is -6. Otherwise, diff is 1 - day.
  const diff = startOfWeek.getDate() - day + (day === 0 ? -6 : 1);
  startOfWeek.setDate(diff);
  startOfWeek.setHours(0, 0, 0, 0); // Start of day

  const endOfWeek = new Date(startOfWeek);
  endOfWeek.setDate(startOfWeek.getDate() + 6);
  endOfWeek.setHours(23, 59, 59, 999); // End of day

  return { start: startOfWeek, end: endOfWeek };
};

// Helper function to get week range for display (Monday to Sunday)
const getWeekRangeForDisplay = (date: Date) => {
    const week = getWeekNumber(date);
    const year = date.getFullYear();

    const firstDayOfYear = new Date(year, 0, 1);
    const firstDayOfYearDay = firstDayOfYear.getDay() || 7;
    const dayOffsetForFirstMonday = (firstDayOfYearDay <= 4) ? (1 - firstDayOfYearDay) : (8 - firstDayOfYearDay);
    const firstMondayOfYear = new Date(year, 0, 1 + dayOffsetForFirstMonday);

    const monday = new Date(firstMondayOfYear.getTime() + (week - 1) * 7 * 24 * 60 * 60 * 1000);
    const sunday = new Date(monday.getTime() + 6 * 24 * 60 * 60 * 1000);

    return { week, year, monday, sunday };
};


// Format date display based on active tab
export const formatDateDisplay = (date: Date, activeTab: string): string => {
  const thaiMonths = ['มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน', 'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'];
  const now = new Date();

  if (activeTab === 'Day') {
    const isToday = date.toDateString() === now.toDateString();
    return `${date.getDate().toString().padStart(2, '0')}/${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getFullYear()}${isToday ? ' (Today)' : ''}`;
  } else if (activeTab === 'Week') {
    const { monday, sunday } = getWeekRangeForDisplay(date);
    const { start: currentWeekStart } = getWeekRangeForDate(now);
    const isThisWeek = monday.toDateString() === currentWeekStart.toDateString();
    return `สัปดาห์ที่ ${getWeekNumber(date)}, ${date.getFullYear()} (${monday.getDate()} ${thaiMonths[monday.getMonth()]} - ${sunday.getDate()} ${thaiMonths[sunday.getMonth()]})${isThisWeek ? ' (สัปดาห์นี้)' : ''}`;
  } else { // Month
    const isThisMonth = date.getFullYear() === now.getFullYear() && date.getMonth() === now.getMonth();
    return `${thaiMonths[date.getMonth()]} ${date.getFullYear()}${isThisMonth ? ' (เดือนนี้)' : ''}`;
  }
};

// Get the end date for "Data updated until" message
export const getUpdateEndDate = (date: Date, activeTab: string): string => {
    const now = new Date(); // Get current time for the update timestamp
    const timeString = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;

    let displayDate: Date;

    if (activeTab === 'Day') {
        displayDate = date;
    } else if (activeTab === 'Week') {
        const { sunday } = getWeekRangeForDisplay(date);
        displayDate = sunday;
    } else { // Month
        displayDate = new Date(date.getFullYear(), date.getMonth() + 1, 0); // Last day of the month
    }

    const formattedDate = displayDate.toLocaleDateString('th-TH', { day: 'numeric', month: 'long', year: 'numeric' });
    return `${formattedDate} เวลา ${timeString} น.`; // Include time
};

// Function to generate calendar data for date picker
export const generateCalendarData = (currentDate: Date) => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const firstDayOfWeek = firstDay.getDay(); // 0 for Sunday, 6 for Saturday
    const daysInMonth = lastDay.getDate();

    const calendar = [];
    let week = [];

    // Add empty cells for days before the first day of the month
    for (let i = 0; i < firstDayOfWeek; i++) {
        week.push(null);
    }

    // Add all days of the month
    for (let day = 1; day <= daysInMonth; day++) {
        week.push(new Date(year, month, day));

        if (week.length === 7) {
            calendar.push(week);
            week = [];
        }
    }

    // Add remaining days to complete the last week
    while (week.length < 7 && week.length > 0) {
        week.push(null);
    }

    if (week.length > 0) {
        calendar.push(week);
    }

    return calendar;
};