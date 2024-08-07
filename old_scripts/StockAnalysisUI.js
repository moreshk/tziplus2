import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Select, Card, CardHeader, CardContent } from '@/components/ui/card';

const StockAnalysisUI = ({ data }) => {
  const [selectedPeriod, setSelectedPeriod] = useState('1 month');
  const [selectedGrouping, setSelectedGrouping] = useState('company');
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    if (data && data[selectedPeriod]) {
      let groupedData;
      if (selectedGrouping === 'company') {
        groupedData = data[selectedPeriod];
      } else {
        groupedData = data[selectedPeriod].groupby('Industry')['Returns'].mean().reset_index();
      }
      setChartData(groupedData.sort((a, b) => b.Returns - a.Returns).slice(0, 10));
    }
  }, [data, selectedPeriod, selectedGrouping]);

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <h2 className="text-2xl font-bold">Stock Performance Analysis</h2>
        <div className="flex justify-between mt-4">
          <Select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="w-40"
          >
            <option value="1 month">1 Month</option>
            <option value="3 months">3 Months</option>
            <option value="6 months">6 Months</option>
          </Select>
          <Select
            value={selectedGrouping}
            onChange={(e) => setSelectedGrouping(e.target.value)}
            className="w-40"
          >
            <option value="company">By Company</option>
            <option value="industry">By Industry</option>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={selectedGrouping === 'company' ? 'Symbol' : 'Industry'} />
            <YAxis label={{ value: 'Returns (%)', angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="Returns" fill="#8884d8" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

export default StockAnalysisUI;