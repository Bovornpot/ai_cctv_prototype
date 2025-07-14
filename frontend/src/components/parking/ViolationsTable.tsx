// frontend/src/components/parking/ViolationsTable.tsx

import React from 'react';
import { ParkingViolationEvent, ViolationStatus } from '../../types/parkingViolation';
import './ViolationsTable.css'; // เราจะสร้างไฟล์ CSS นี้ในขั้นตอนถัดไป

// Helper component สำหรับแสดงสถานะพร้อมสี
const StatusBadge: React.FC<{ status: ViolationStatus }> = ({ status }) => {
  const statusInfo = {
    Ongoing: { text: 'Ongoing', colorClass: 'status-ongoing' },
    Completed: { text: 'Completed', colorClass: 'status-completed' },
    Acknowledged: { text: 'Acknowledged', colorClass: 'status-acknowledged' },
  };

  const { text, colorClass } = statusInfo[status];

  return (
    <div className="status-badge-container">
      <span className={`status-dot ${colorClass}`}></span>
      <span>{text}</span>
    </div>
  );
};

// Helper function สำหรับจัดรูปแบบวันที่
const formatDateTime = (isoString: string | null) => {
  if (!isoString) return '-';
  const date = new Date(isoString);
  return date.toLocaleString('th-TH', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

interface ViolationsTableProps {
  violations: ParkingViolationEvent[];
}

const ViolationsTable: React.FC<ViolationsTableProps> = ({ violations }) => {
  return (
    <div className="table-container">
      <table className="violations-table">
        <thead>
          <tr>
            <th>Status</th>
            <th>Vehicle ID</th>
            <th>Branch / Camera</th>
            <th>Entry Time</th>
            <th>Exit Time</th>
            <th>Duration (Mins)</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {violations.map((v) => (
            <tr key={v.id}>
              <td><StatusBadge status={v.status} /></td>
              <td className="font-mono">{v.vehicleId}</td>
              <td>{v.branch.name} / <span className="text-gray-500">{v.camera.id}</span></td>
              <td>{formatDateTime(v.entryTime)}</td>
              <td>{formatDateTime(v.exitTime)}</td>
              <td>{v.durationMinutes.toFixed(0)}</td>
              <td>
                <button className="action-button">...</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ViolationsTable;