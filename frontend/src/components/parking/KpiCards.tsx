// frontend/src/components/parking/KpiCards.tsx

import React from 'react';
import StatCard from '../common/StatCard';
import { ParkingKpiData } from '../../types/parkingViolation';

interface KpiCardsProps {
  data: ParkingKpiData;
}

const KpiCards: React.FC<KpiCardsProps> = ({ data }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
      {/* ++ การ์ดที่ 1 */}
      <StatCard
        title="รถที่เข้าใช้บริการทั้งหมด"
        value={data.total_parking_sessions.toLocaleString()}
        subtitle="คัน"
        color="text-black-600"
        subtitleColor="text-black-600"
      />
        {/* การ์ดที่ 2 */}
      <StatCard
        title="เหตุการณ์ที่เกิดขึ้นทั้งหมด"
        value={data.totalViolations.toLocaleString()}
        subtitle="รายการ"
        color="text-blue-600"
        subtitleColor="text-blue-600"
      />

      {/* การ์ดที่ 3 */}
      <StatCard
        title="การละเมิดที่ดำเนินอยู่"
        value={data.ongoingViolations.toLocaleString()}
        subtitle="รายการ"
        color="text-red-600"
        subtitleColor="text-red-600"
      />

      {/* การ์ดที่ 4 */}
      <StatCard
        title="เวลาละเมิดเฉลี่ย"
        value={data.avgViolationDuration.toFixed(0)}
        subtitle="นาที"
        color="text-orange-600"
        subtitleColor="text-orange-600"
      />

      {/* การ์ดที่ 5 */}
      <StatCard
        title="เวลาจอดเฉลี่ย (ปกติ)"
        value={data.avgNormalParkingTime.toFixed(0)}
        subtitle="นาที"
        color="text-green-600"
        subtitleColor="text-green-600"
      />
    </div>
  );
};

export default KpiCards;