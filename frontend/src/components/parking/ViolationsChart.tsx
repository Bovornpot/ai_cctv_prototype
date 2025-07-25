import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface ChartData {
  label: string;
  value: number;
}

interface ViolationsChartProps {
  data: ChartData[];
}

const ViolationsChart: React.FC<ViolationsChartProps> = ({ data }) => {
  return (
    // กำหนดความสูงของพื้นที่กราฟ
    <div style={{ width: '100%', height: 300 }}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="label" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip cursor={{fill: 'rgba(239, 68, 68, 0.1)'}} />
          <Bar dataKey="value" fill="#ef4444" name="จำนวนการละเมิด" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ViolationsChart;