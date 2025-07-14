// frontend/src/components/parking/ViolationFilters.tsx

import React, { useState } from 'react';
import { Search, Download } from 'lucide-react';

export interface ParkingFilters {
  startDate: string;
  endDate: string;
  branchId: string;
  status: string;
  vehicleId: string;
}

interface ViolationFiltersProps {
  onFilterChange: (filters: ParkingFilters) => void;
}

const ViolationFilters: React.FC<ViolationFiltersProps> = ({ onFilterChange }) => {
  // State ภายในสำหรับเก็บค่าของแต่ละฟิลเตอร์
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [branchId, setBranchId] = useState('all');
  const [status, setStatus] = useState('all');
  const [vehicleId, setVehicleId] = useState('');

  const handleApplyFilters = () => {
    onFilterChange({ startDate, endDate, branchId, status, vehicleId });
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Date Filters */}
        <div>
          <label htmlFor="start-date" className="block text-sm font-medium text-gray-700">Start Date</label>
          <input
            type="date"
            id="start-date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
          />
        </div>
        <div>
          <label htmlFor="end-date" className="block text-sm font-medium text-gray-700">End Date</label>
          <input
            type="date"
            id="end-date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
          />
        </div>

        {/* Branch & Status Filters */}
        <div>
          <label htmlFor="branch" className="block text-sm font-medium text-gray-700">Branch</label>
          <select
            id="branch"
            value={branchId}
            onChange={(e) => setBranchId(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border bg-white"
          >
            <option value="all">All Branches</option>
            <option value="BKK01">สาขาสุขุมวิท</option>
            <option value="BKK02">สาขาลาดพร้าว</option>
            <option value="BKK03">สาขาปิ่นเกล้า</option>
          </select>
        </div>
        <div>
          <label htmlFor="status" className="block text-sm font-medium text-gray-700">Status</label>
          <select
            id="status"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border bg-white"
          >
            <option value="all">All Statuses</option>
            <option value="Ongoing">Ongoing</option>
            <option value="Completed">Completed</option>
            <option value="Acknowledged">Acknowledged</option>
          </select>
        </div>

        {/* Vehicle ID Search */}
        <div>
          <label htmlFor="vehicle-id" className="block text-sm font-medium text-gray-700">Vehicle ID</label>
          <input
            type="text"
            id="vehicle-id"
            placeholder="e.g., กท-1234"
            value={vehicleId}
            onChange={(e) => setVehicleId(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
          />
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end items-center mt-4 pt-4 border-t">
        <button 
          className="flex items-center gap-2 bg-gray-200 text-gray-800 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-300 mr-2"
          onClick={() => alert('Exporting data...')}
        >
          <Download size={16} />
          Export
        </button>
        <button
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
          onClick={handleApplyFilters}
        >
          <Search size={16} />
          Apply Filters
        </button>
      </div>
    </div>
  );
};

export default ViolationFilters;