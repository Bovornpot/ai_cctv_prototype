// frontend/src/pages/ParkingViolationDetailsPage.tsx

import React, { useState, useEffect, useCallback } from 'react';
import { ParkingViolationEvent, ParkingKpiData } from '../types/parkingViolation';

// Components
import ViolationsTable from '../components/parking/ViolationsTable';
import KpiCards from '../components/parking/KpiCards';
import ViolationFilters, { ParkingFilters } from '../components/parking/ViolationFilters';
import { TimeSelection } from '../types/time';

// --- Mock Data (ย้ายมาไว้ที่นี่เพื่อให้หาเจอ) ---
const mockViolationData: ParkingViolationEvent[] = [
  {
    id: 1, status: 'Ongoing', timestamp: '2025-07-11T17:30:00Z',
    branch: { id: 'BKK01', name: 'สาขาสุขุมวิท' }, camera: { id: 'Cam01' },
    vehicleId: 'กท-1234', entryTime: '2025-07-11T14:30:00Z', exitTime: null,
    durationMinutes: 180, isViolation: true, evidenceImageUrl: 'https://via.placeholder.com/150'
  },
  {
    id: 2, status: 'Completed', timestamp: '2025-07-11T15:10:00Z',
    branch: { id: 'BKK02', name: 'สาขาลาดพร้าว' }, camera: { id: 'Cam05' },
    vehicleId: 'ขข-5678', entryTime: '2025-07-11T13:00:00Z', exitTime: '2025-07-11T15:10:00Z',
    durationMinutes: 130, isViolation: true, evidenceImageUrl: 'https://via.placeholder.com/150'
  },
  {
    id: 3, status: 'Acknowledged', timestamp: '2025-07-10T11:45:00Z',
    branch: { id: 'BKK03', name: 'สาขาปิ่นเกล้า' }, camera: { id: 'Cam02' },
    vehicleId: 'คค-9012', entryTime: '2025-07-10T10:00:00Z', exitTime: '2025-07-10T11:45:00Z',
    durationMinutes: 105, isViolation: true, evidenceImageUrl: 'https://via.placeholder.com/150'
  },
];

const mockKpiData: ParkingKpiData = {
  totalViolations: 1256,
  ongoingViolations: 78,
  avgViolationDuration: 45,
  avgNormalParkingTime: 15,
};
// --- End of Mock Data ---
interface ParkingViolationDetailsPageProps {
  timeSelection: TimeSelection;
}

const ParkingViolationDetailsPage: React.FC<ParkingViolationDetailsPageProps> = ({ timeSelection }) => {
  const [violations, setViolations] = useState<ParkingViolationEvent[]>([]);
  const [kpiData, setKpiData] = useState<ParkingKpiData | null>(null);
  const [loading, setLoading] = useState(true);
  
  const fetchData = useCallback(async () => {
    setLoading(true);
    console.log('ParkingViolationDetailsPage is fetching data with:', timeSelection);
    
    setTimeout(() => {
      setViolations(mockViolationData);
      setKpiData(mockKpiData);
      setLoading(false);
    }, 500);
  }, [timeSelection]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);


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