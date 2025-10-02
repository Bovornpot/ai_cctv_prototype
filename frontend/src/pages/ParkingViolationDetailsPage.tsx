// frontend/src/pages/ParkingViolationDetailsPage.tsx

import React, { useState, useEffect } from 'react';
import { ParkingViolationEvent, ViolationSummaryResponse } from '../types/parkingViolation';
import { fetchViolationSummary, fetchViolationEvents, ChartGroupByUnit, ViolationFilters } from '../api/parkingApiService';
import { TimeSelection } from '../types/time';
import { getDateRangeFromSelection } from '../utils/dateUtils';

// Components
import ViolationsTable from '../components/parking/ViolationsTable';
import KpiCards from '../components/parking/KpiCards';
import ViolationsChart from '../components/parking/ViolationsChart';
import TopBranchesList from '../components/parking/TopBranchesList';

interface ParkingViolationDetailsPageProps {
  timeSelection: TimeSelection;
  branchQuery: string;
}

type ActiveTab = 'in-progress' | 'violations' | 'all';

const ParkingViolationDetailsPage: React.FC<ParkingViolationDetailsPageProps> = ({ timeSelection, branchQuery }) => {
  const [summaryData, setSummaryData] = useState<ViolationSummaryResponse | null>(null);
  const [eventsData, setEventsData] = useState<ParkingViolationEvent[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [activeTab, setActiveTab] = useState<'in-progress' | 'violations' | 'all'>('in-progress'); // Default เป็น violations

  useEffect(() => {
    // ฟังก์ชันสำหรับดึงข้อมูล โดยใช้ค่า filter ล่าสุด
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // เตรียมค่า Filters ที่จะส่งไป API
        const { startDate, endDate } = getDateRangeFromSelection(timeSelection);

        const toYYYYMMDD = (date: Date) => {
          const y = date.getFullYear();
          const m = String(date.getMonth() + 1).padStart(2, '0'); // +1 เพราะ getMonth() เริ่มจาก 0
          const d = String(date.getDate()).padStart(2, '0');
          return `${y}-${m}-${d}`;
        };

        let groupByUnit: ChartGroupByUnit = 'day'; // ค่าเริ่มต้น
        if (timeSelection.activeTab === 'Day' && timeSelection.mode === 'single') {
          groupByUnit = 'hour';
        } else if (timeSelection.activeTab === 'Week' && timeSelection.mode === 'range') {
          groupByUnit = 'week';
        } else if (timeSelection.activeTab === 'Month' && timeSelection.mode === 'range') {
          groupByUnit = 'month';
        }

        // ---------------------------
      // summaryFilters => ใช้สำหรับ summary/chart (ยังคงถูกจำกัดด้วยวันที่ตาม timeSelection)
      // ---------------------------
      const summaryFilters: ViolationFilters = {
        branchId: branchQuery || undefined,
        startDate: toYYYYMMDD(startDate),
        endDate: toYYYYMMDD(endDate),
        groupByUnit,
      };

      // ---------------------------
      // eventsFilters => ใช้สำหรับตาราง (ปรับตาม activeTab)
      // - in-progress: ไม่ใส่ start/end date, ใส่ inProgressOnly = true
      // - violations: ใส่ start/end date และ isViolationOnly = true
      // - all: ใส่ start/end date (ไม่ใส่ isViolationOnly)
      // ---------------------------
      const eventsFilters: ViolationFilters = {
        branchId: branchQuery || undefined,
        groupByUnit,
      };

      if (activeTab === 'in-progress') {
        eventsFilters.isViolationOnly = true;    // เราต้องการเฉพาะ violation
        eventsFilters.inProgressOnly = true;     // แต่ขอเฉพาะที่ยังไม่ออก (exitTime == null)
        // intentionally DO NOT set startDate/endDate -> show all
      } else if (activeTab === 'violations') {
        eventsFilters.isViolationOnly = true;
        eventsFilters.startDate = toYYYYMMDD(startDate);
        eventsFilters.endDate = toYYYYMMDD(endDate);
      } else { // 'all'
        eventsFilters.startDate = toYYYYMMDD(startDate);
        eventsFilters.endDate = toYYYYMMDD(endDate);
      }

      console.log("Summary filters to backend:", summaryFilters);
      console.log("Events filters to backend:", eventsFilters);

      const [summary, paginatedEvents] = await Promise.all([
        fetchViolationSummary(summaryFilters),
        fetchViolationEvents(currentPage, 20, eventsFilters),
      ]);
        
        setSummaryData(summary);
        // อัปเดต events และ totalPages
        setEventsData(paginatedEvents.events);
        setTotalPages(paginatedEvents.total_pages);
        
      } catch (err) {
        console.error("Failed to fetch data:", err);
        setError("ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์ได้");
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [timeSelection, branchQuery, currentPage, activeTab]);

  // ฟังก์ชันสำหรับจัดการการกดปุ่ม
  const handlePageChange = (newPage: number) => {
    if (newPage > 0 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

  // สร้างฟังก์ชันสำหรับเปลี่ยน Tab และรีเซ็ตหน้าเป็น 1
  const handleTabChange = (tab: ActiveTab) => {
    setActiveTab(tab);
    setCurrentPage(1); // กลับไปหน้า 1 เสมอเมื่อเปลี่ยน Tab
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <p className="ml-4 text-gray-600">กำลังโหลดข้อมูลตามเงื่อนไข...</p>
      </div>
    );
  }

  if (error) {
    return <div className="text-center py-20 text-red-500 font-semibold">{error}</div>;
  }

  return (
    <div className="space-y-6">
      {summaryData ? (
        // ถ้ามี summaryData ให้แสดงผลข้อมูลทั้งหมด
        <>
          <KpiCards data={summaryData.kpi} />
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">สถิติการละเมิด</h3>
              <ViolationsChart data={summaryData.chart_data} />
            </div>

            <div className="bg-white p-6 rounded-lg shadow flex flex-col h-full">
              {/* <h3 className="text-lg font-semibold mb-4 text-gray-800">Top 5 Violating Branches</h3> */}
              <TopBranchesList data={summaryData.top_branches} timeSelection={timeSelection} />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <ViolationsTable 
            violations={eventsData}
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={handlePageChange}
            activeTab={activeTab}
            onTabChange={handleTabChange}
            />
          </div>
        </>
      ) : (
        // ถ้าไม่มี summaryData (หลังจากโหลดเสร็จแล้ว) ให้แสดงว่าไม่พบข้อมูล
        <div className="text-center py-20">
          <p className="text-gray-500">ไม่พบข้อมูลที่จะแสดงผลตามเงื่อนไขที่เลือก</p>
        </div>
      )}
    </div>
  );
};

export default ParkingViolationDetailsPage;