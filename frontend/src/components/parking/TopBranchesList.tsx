import React from 'react';
import { ChevronRight } from 'lucide-react';

interface BranchData {
  name: string;
  count: number;
}

interface TopBranchesListProps {
  data: BranchData[];
}

const TopBranchesList: React.FC<TopBranchesListProps> = ({ data }) => {
  return (
    <ul className="space-y-3">
      {data.map((branch, index) => (
        <li 
          key={index} 
          className="flex items-center justify-between p-2 rounded-md hover:bg-gray-50 cursor-pointer"
        >
          <div className="flex items-center">
            <span className="text-sm font-medium text-gray-500 w-6">{index + 1}.</span>
            <span className="text-sm text-gray-800">{branch.name}</span>
          </div>
          <div className="flex items-center">
            <span className="text-sm font-semibold text-red-600 mr-2">{branch.count.toLocaleString()}</span>
            <ChevronRight size={16} className="text-gray-400" />
          </div>
        </li>
      ))}
    </ul>
  );
};

export default TopBranchesList;