// frontend/src/pages/ParkingViolationDetailsPage.tsx

import React, { useState, useEffect, useCallback,useMemo } from 'react';
import { ParkingViolationEvent, ParkingKpiData } from '../types/parkingViolation';

// Components
import ViolationsTable from '../components/parking/ViolationsTable';
import KpiCards from '../components/parking/KpiCards';
import ViolationsChart from '../components/parking/ViolationsChart';
import TopBranchesList from '../components/parking/TopBranchesList';

import { TimeSelection } from '../types/time';

import { 
  mockKpiData, 
  mockViolationData,
  mockTopBranches,
  mockSingleDayChartData,
  mockRangeDayChartData,
  mockSingleWeekChartData, 
  mockRangeWeekChartData,
  mockSingleMonthChartData,
  mockRangeMonthChartData
} from '../api/mockParkingData';

interface ParkingViolationDetailsPageProps {
  timeSelection: TimeSelection;
  branchQuery: string;
}

const ParkingViolationDetailsPage: React.FC<ParkingViolationDetailsPageProps> = ({ timeSelection, branchQuery }) => {
  const [violations, setViolations] = useState<ParkingViolationEvent[]>([]);
  const [kpiData, setKpiData] = useState<ParkingKpiData | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Logic การดึงข้อมูลจะใช้ข้อมูลที่ import เข้ามา
  const fetchData = useCallback(async () => {
    setLoading(true);
    console.log('Fetching data with new filters:');
    console.log('Time Selection:', timeSelection);
    console.log('Branch Query:', branchQuery);
    // console.log('ParkingViolationDetailsPage is fetching data with:', timeSelection);
    
    setTimeout(() => {
      setViolations(mockViolationData);
      setKpiData(mockKpiData);
      setLoading(false);
    }, 500);
  }, [timeSelection, branchQuery]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const { chartData, chartTitle } = useMemo(() => {
    // นี่คือ Logic ที่เราจะแทนที่ด้วย API call เดียวในอนาคต
    switch (timeSelection.activeTab) {
      case 'Day':
        return timeSelection.mode === 'range' 
          ? { chartData: mockRangeDayChartData, chartTitle: 'สถิติการละเมิดรายวัน' }
          : { chartData: mockSingleDayChartData, chartTitle: 'สถิติการละเมิดรายชั่วโมง (ใน 1 วัน)' };
      
      case 'Week':
        return timeSelection.mode === 'range'
          ? { chartData: mockRangeWeekChartData, chartTitle: 'สถิติการละเมิดรายสัปดาห์' }
          : { chartData: mockSingleWeekChartData, chartTitle: 'สถิติการละเมิดรายวัน (ในสัปดาห์)' };

      case 'Month':
        return timeSelection.mode === 'range'
          ? { chartData: mockRangeMonthChartData, chartTitle: 'สถิติการละเมิดรายเดือน' }
          : { chartData: mockSingleMonthChartData, chartTitle: 'สถิติการละเมิดรายวัน (ในเดือน)' };

      default:
        return { chartData: [], chartTitle: 'สถิติการละเมิด' };
    }
  }, [timeSelection]); // คำนวณใหม่ทุกครั้งที่ timeSelection เปลี่ยน

  if (loading) {
    return (
        <div className="flex items-center justify-center h-full py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <p className="ml-4 text-gray-600">กำลังโหลดข้อมูล...</p>
        </div>
    );
  }


  return (
    <div className="space-y-6">
      {/* <ViolationFilters onFilterChange={handleFilterChange} /> */}

      {loading ? (
        <div className="flex items-center justify-center h-full py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          <p className="ml-4 text-gray-600">กำลังโหลดข้อมูล...</p>
        </div>
      ) : kpiData ? (
        <>
          <KpiCards data={kpiData} />
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">{chartTitle}</h3>
              <ViolationsChart data={chartData} />
            </div>

            <div className="bg-white p-6 rounded-lg shadow flex flex-col h-full">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">Top 5 Violating Branches</h3>
              <TopBranchesList data={mockTopBranches} />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <ViolationsTable violations={violations} />
          </div>

        </>
      ) : (
        <div className="text-center py-20">
          <p className="text-gray-500">No data to display.</p>
        </div>
      )}
    </div>
  );
};

export default ParkingViolationDetailsPage;