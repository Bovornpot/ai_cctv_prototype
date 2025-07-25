import React from 'react';
import { ChevronRight } from 'lucide-react';
import ParkingAlertCard from '../common/ParkingAlertCard';

interface BranchData {
  name: string;
  code: string;
  count: number;
}

interface TopBranchesListProps {
  data: BranchData[];
}

const TopBranchesList: React.FC<TopBranchesListProps> = ({ data }) => {
  return (
    <div className="flex-grow flex flex-col justify-between space-y-2">
      {data.map((branch, index) => (
        <ParkingAlertCard
          key={index}
          title={branch.name}
          count={branch.count}
          subtitle={`รหัสร้าน ${branch.code}`} // ส่งรหัสร้านไปที่ subtitle
          bgColor="bg-red-50"                 // ใช้สีแดงเพื่อสื่อถึง Violation
          textColor="text-red-600"
        />
      ))}
    </div>
  );
};

export default TopBranchesList;