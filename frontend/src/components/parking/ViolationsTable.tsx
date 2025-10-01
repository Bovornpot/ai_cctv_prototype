// frontend/src/components/parking/ViolationsTable.tsx

import React, { useState } from 'react';
import { ParkingViolationEvent, ViolationStatus } from '../../types/parkingViolation';
import './ViolationsTable.css'; // เราจะสร้างไฟล์ CSS นี้ในขั้นตอนถัดไป

// Helper component สำหรับแสดงสถานะพร้อมสี
const StatusBadge: React.FC<{ status: ViolationStatus }> = ({ status }) => {
  const statusInfo = {
    Violate: { text: 'Violate', colorClass: 'status-violate' },
    Normal: { text: 'Normal', colorClass: 'status-normal' },
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
                        <img src={violation.imageUrl} alt={`Evidence for vehicle ${violation.vehicleId}`} />
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

type ActiveTab = 'in-progress' | 'violations' | 'all';
interface ViolationsTableProps {
  violations: ParkingViolationEvent[];
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
}


const ViolationsTable: React.FC<ViolationsTableProps> = ({ violations, currentPage, totalPages, onPageChange, activeTab ,onTabChange }) => {
//   const [activeTab, setActiveTab] = useState<'all' | 'violations'>('violations');
  const [selectedViolation, setSelectedViolation] = useState<ParkingViolationEvent | null>(null);

    // ฟิลเตอร์ข้อมูลตาม activeTab
    let filteredViolations = violations;

    if (activeTab === 'in-progress') {
    // แสดงเฉพาะ Violate และยังไม่ออก (exitTime == null)
    filteredViolations = violations.filter(v => v.status === 'Violate' && !v.exitTime);
    } else if (activeTab === 'violations') {
    // รถที่ Violate ทั้งหมด (ไม่สนว่าออกหรือยัง)
    filteredViolations = violations.filter(v => v.status === 'Violate');
    } else if (activeTab === 'all') {
    // รถทั้งหมด (ไม่กรอง)
    filteredViolations = violations;
    }


  return (
        <div>
            {/* --- Tab buttons (เปลี่ยนชื่อ Tab) --- */}
            <div className="tabs-container">
                <button
                    className={`tab-button ${activeTab === 'in-progress' ? 'active' : ''}`}
                    onClick={() => onTabChange('in-progress')}
                >
                    กำลังจอดรถเกิน
                </button>
                <button
                    className={`tab-button ${activeTab === 'violations' ? 'active' : ''}`}
                    onClick={() => onTabChange('violations')}
                >
                    รถจอดเกินเวลา
                </button>
                <button
                    className={`tab-button ${activeTab === 'all' ? 'active' : ''}`}
                    onClick={() => onTabChange('all')}
                >
                    รถเข้าออกทั้งหมด
                </button>
            </div>

            {/* --- Table (ปรับปรุงคอลัมน์) --- */}
            {filteredViolations.length > 0 ? (
                <div className="table-container">
                    <table className="violations-table">
                        <thead>
                            <tr>
                                <th>ลำดับ</th>    
                                <th>สถานะ</th>
                                <th>ID รถ</th>
                                <th>ชื่อสาขา</th>
                                <th>รหัสสาขา</th>
                                <th>Camera Link (IP)</th>
                                <th>เวลาเข้า</th>
                                <th>เวลาออก</th>
                                <th>จำนวนเวลา (นาที)</th>
                                <th>รายละเอียด</th>
                            </tr>
                        </thead>
                        <tbody>
                            {/* ใช้ข้อมูลที่ผ่านการกรองและเรียงลำดับแล้ว */}
                            {filteredViolations.map((violation, index) => (
                                <tr key={violation.id}>
                                    <td>{(currentPage - 1) * 20 + index + 1}</td>
                                    <td><StatusBadge status={violation.status} /></td>
                                    <td className="font-mono">{violation.vehicleId}</td>
                                    <td>{violation.branch.name}</td>
                                    <td>{violation.branch.id}</td>
                                    <td>{violation.camera.id}</td>
                                    <td>{formatDateTime(violation.entryTime)}</td>
                                    <td>{formatDateTime(violation.exitTime)}</td>
                                    <td>{violation.durationMinutes.toFixed(0)}</td>
                                    <td>
                                        <button 
                                            className="action-button view-button"
                                            onClick={() => setSelectedViolation(violation)}
                                        >
                                            View
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {/* 2. เพิ่มส่วนของ Pagination UI */}
                    {totalPages > 1 && (
                        <div className="flex items-center justify-between p-4 border-t border-gray-200">
                        <button
                            onClick={() => onPageChange(currentPage - 1)}
                            disabled={currentPage === 1}
                            className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Previous
                        </button>
                        <span className="text-sm text-gray-700">
                            Page {currentPage} of {totalPages}
                        </span>
                        <button
                            onClick={() => onPageChange(currentPage + 1)}
                            disabled={currentPage >= totalPages}
                            className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Next
                        </button>
                        </div>
                    )}
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