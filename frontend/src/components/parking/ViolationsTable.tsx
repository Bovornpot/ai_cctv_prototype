// frontend/src/components/parking/ViolationsTable.tsx

import React, { useState,useMemo } from 'react';
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

const EvidenceModal: React.FC<{ violation: ParkingViolationEvent; onClose: () => void }> = ({ violation, onClose }) => {
    if (!violation) return null;

    return (
        <div className="modal-backdrop" onClick={onClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h3 className="modal-title">Violation Details (ID: {violation.id})</h3>
                    <button onClick={onClose} className="modal-close-button">&times;</button>
                </div>
                <div className="modal-body">
                    <div className="modal-image-container">
                        <img src={violation.evidenceImageUrl} alt={`Evidence for vehicle ${violation.vehicleId}`} />
                    </div>
                    <div className="modal-details">
                        <p><strong>Vehicle ID:</strong> <span className="font-mono">{violation.vehicleId}</span></p>
                        <p><strong>Status:</strong> {violation.status}</p>
                        <p><strong>Branch:</strong> {violation.branch.name} ({violation.branch.id})</p>
                        <p><strong>Camera IP:</strong> {violation.camera.id}</p>
                        <p><strong>Entry Time:</strong> {formatDateTime(violation.entryTime)}</p>
                        <p><strong>Exit Time:</strong> {formatDateTime(violation.exitTime)}</p>
                        <p><strong>Duration:</strong> {violation.durationMinutes.toFixed(0)} minutes</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

interface ViolationsTableProps {
  violations: ParkingViolationEvent[];
}

const ViolationsTable: React.FC<ViolationsTableProps> = ({ violations }) => {
  const [activeTab, setActiveTab] = useState<'violation' | 'all'>('violation');
  const [selectedViolation, setSelectedViolation] = useState<ParkingViolationEvent | null>(null);
  
  // กรองข้อมูลตาม Tab ที่เลือก
  const sortedAndFilteredViolations = useMemo(() => {
        let filtered = violations;

        // ขั้นตอนที่ 1: กรองข้อมูลตาม Tab ที่เลือก
        if (activeTab === 'violation') {
            filtered = violations.filter(v => 
                v.status === 'Ongoing' && v.durationMinutes > 15
            );
        }

        // ขั้นตอนที่ 2: เรียงลำดับข้อมูลจากใหม่ไปเก่า (ใช้กับทุก Tab)
        // สร้าง Array ใหม่ด้วย [...filtered] ก่อน sort เพื่อไม่ให้กระทบ state เดิม
        return [...filtered].sort((a, b) => 
            new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        );

  }, [violations, activeTab]); // คำนวณใหม่เมื่อ violations หรือ activeTab เปลี่ยน

  return (
        <div>
            {/* --- Tab buttons (เปลี่ยนชื่อ Tab) --- */}
            <div className="tabs-container">
                <button
                    className={`tab-button ${activeTab === 'violation' ? 'active' : ''}`}
                    onClick={() => setActiveTab('violation')}
                >
                    Active Violations
                </button>
                <button
                    className={`tab-button ${activeTab === 'all' ? 'active' : ''}`}
                    onClick={() => setActiveTab('all')}
                >
                    Joined Parking Sessions
                </button>
            </div>

            {/* --- Table (ปรับปรุงคอลัมน์) --- */}
            {sortedAndFilteredViolations.length > 0 ? (
                <div className="table-container">
                    <table className="violations-table">
                        <thead>
                            <tr>
                                <th>Status</th>
                                <th>Vehicle ID</th>
                                <th>Branch</th>
                                <th>Branch ID</th>
                                <th>Camera Link (IP)</th>
                                <th>Entry Time</th>
                                <th>Exit Time</th>
                                <th>Duration (Mins)</th>
                                <th>Evidence</th>
                            </tr>
                        </thead>
                        <tbody>
                            {/* ใช้ข้อมูลที่ผ่านการกรองและเรียงลำดับแล้ว */}
                            {sortedAndFilteredViolations.map((v) => (
                                <tr key={v.id}>
                                    <td><StatusBadge status={v.status} /></td>
                                    <td className="font-mono">{v.vehicleId}</td>
                                    <td>{v.branch.name}</td>
                                    <td>{v.branch.id}</td>
                                    <td>{v.camera.id}</td>
                                    <td>{formatDateTime(v.entryTime)}</td>
                                    <td>{formatDateTime(v.exitTime)}</td>
                                    <td>{v.durationMinutes.toFixed(0)}</td>
                                    <td>
                                        <button 
                                            className="action-button view-button"
                                            onClick={() => setSelectedViolation(v)}
                                        >
                                            View
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
              <div className="empty-state-container">
                    <p>ไม่พบรายการที่ตรงตามเงื่อนไข</p>
                </div>
            )}

            {/* --- แสดง Modal เมื่อมี v ที่ถูกเลือก --- */}
            {selectedViolation && (
                <EvidenceModal violation={selectedViolation} onClose={() => setSelectedViolation(null)} />
            )}
        </div>
    );
};

export default ViolationsTable;