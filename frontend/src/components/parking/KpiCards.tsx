// frontend/src/components/parking/KpiCards.tsx

import React from 'react';
import StatCard from '../common/StatCard';
import { ParkingKpiData } from '../../types/parkingViolation';

interface KpiCardsProps {
  data: ParkingKpiData;
}

const KpiCards: React.FC<KpiCardsProps> = ({ data }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* ++ การ์ดที่ 1 ที่หายไป ++ */}
      <StatCard
        title="เหตุการณ์ที่เกิดขึ้นทั้งหมด"
        value={data.totalViolations.toLocaleString()}
        subtitle="รายการ"
        color="text-blue-600"
      />

      {/* การ์ดที่ 2 */}
      <StatCard
        title="การละเมิดที่ดำเนินอยู่"
        value={data.ongoingViolations.toLocaleString()}
        subtitle="รายการ"
        color="text-red-600"
      />

      {/* การ์ดที่ 3 */}
      <StatCard
        title="เวลาละเมิดเฉลี่ย"
        value={`${data.avgViolationDuration.toFixed(0)} นาที`}
        subtitle="เฉลี่ย"
        color="text-orange-600"
      />

      {/* การ์ดที่ 4 ที่แก้ไขล่าสุด */}
      <StatCard
        title="เวลาจอดเฉลี่ย (ปกติ)"
        value={`${data.avgNormalParkingTime.toFixed(0)} นาที`}
        subtitle="รถไม่ละเมิด"
        color="text-green-600"
      />
    </div>
  );
};

export default KpiCards;