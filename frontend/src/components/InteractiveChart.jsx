import React, { useState, useEffect } from 'react';
import { 
  AreaChart, Area, 
  BarChart, Bar, 
  PieChart, Pie, Cell, 
  ScatterChart, Scatter, 
  XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { BarChart3, LineChart as LineIcon, PieChart as PieIcon, ScatterChart as ScatterIcon } from 'lucide-react';

const COLORS = ['#636efa', '#00cc96', '#ab63fa', '#ffa15a', '#19d3f3', '#ff6692', '#b6e880', '#ff97ff'];

export default function InteractiveChart({ data, chartInfo }) {
  const [chartType, setChartType] = useState('bar');
  const [xAxisCol, setXAxisCol] = useState('');
  const [yAxisCol, setYAxisCol] = useState('');
  
  const allColumns = data && data.length > 0 ? Object.keys(data[0]) : [];

  // Reset local state if recommended chart_info changes
  useEffect(() => {
    if (chartInfo && chartInfo.recommended_type !== 'none') {
      setChartType(chartInfo.recommended_type === 'line' ? 'area' : chartInfo.recommended_type);
      setXAxisCol(chartInfo.x_axis || allColumns[0] || '');
      setYAxisCol(chartInfo.y_axis || allColumns[1] || '');
    } else if (allColumns.length >= 2) {
      setChartType('bar');
      setXAxisCol(allColumns[0]);
      setYAxisCol(allColumns[1]);
    }
  }, [chartInfo, data]);

  if (!data || data.length === 0) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        No numeric result fields returned to visualize.
      </div>
    );
  }

  // Clean data values to numbers if needed
  const chartData = data.map(item => {
    const cleaned = { ...item };
    if (xAxisCol && !isNaN(Number(cleaned[xAxisCol]))) cleaned[xAxisCol] = Number(cleaned[xAxisCol]);
    if (yAxisCol && !isNaN(Number(cleaned[yAxisCol]))) cleaned[yAxisCol] = Number(cleaned[yAxisCol]);
    return cleaned;
  });

  const customTooltipStyle = {
    backgroundColor: 'rgba(20, 20, 26, 0.9)',
    backdropFilter: 'blur(10px)',
    border: '1px solid #222230',
    borderRadius: '8px',
    boxShadow: 'var(--shadow-md)',
    color: '#f3f4f6',
    fontSize: '0.8rem',
    fontFamily: 'var(--font-sans)',
    padding: '0.5rem 0.75rem'
  };

  const renderChart = () => {
    switch (chartType) {
      case 'area':
      case 'line':
        return (
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.35}/>
                <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1d1d26" vertical={false} />
            <XAxis dataKey={xAxisCol} stroke="#64748b" fontSize={11} tickLine={false} />
            <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
            <Tooltip contentStyle={customTooltipStyle} />
            <Legend verticalAlign="top" height={36} iconType="circle" />
            <Area 
              type="monotone" 
              dataKey={yAxisCol} 
              stroke="var(--primary)" 
              strokeWidth={2} 
              fillOpacity={1} 
              fill="url(#areaGradient)" 
              activeDot={{ r: 6, strokeWidth: 0 }} 
            />
          </AreaChart>
        );
      case 'pie':
        return (
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
              outerRadius={80}
              innerRadius={50}
              paddingAngle={3}
              fill="#8884d8"
              dataKey={yAxisCol}
              nameKey={xAxisCol}
              fontSize={10}
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="rgba(20,20,26,0.5)" strokeWidth={2} />
              ))}
            </Pie>
            <Tooltip contentStyle={customTooltipStyle} />
            <Legend verticalAlign="top" height={36} iconType="circle" />
          </PieChart>
        );
      case 'scatter':
        return (
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" stroke="#1d1d26" />
            <XAxis type="number" dataKey={xAxisCol} name={xAxisCol} stroke="#64748b" fontSize={11} tickLine={false} />
            <YAxis type="number" dataKey={yAxisCol} name={yAxisCol} stroke="#64748b" fontSize={11} tickLine={false} />
            <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={customTooltipStyle} />
            <Legend verticalAlign="top" height={36} iconType="circle" />
            <Scatter name={`${yAxisCol} vs ${xAxisCol}`} data={chartData} fill="#ab63fa" />
          </ScatterChart>
        );
      case 'bar':
      default:
        return (
          <BarChart data={chartData}>
            <defs>
              <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#00cc96" stopOpacity={0.95}/>
                <stop offset="95%" stopColor="#00cc96" stopOpacity={0.45}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1d1d26" vertical={false} />
            <XAxis dataKey={xAxisCol} stroke="#64748b" fontSize={11} tickLine={false} />
            <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
            <Tooltip contentStyle={customTooltipStyle} />
            <Legend verticalAlign="top" height={36} iconType="circle" />
            <Bar dataKey={yAxisCol} fill="url(#barGradient)" radius={[4, 4, 0, 0]} barSize={32} />
          </BarChart>
        );
    }
  };

  return (
    <div className="chart-container-wrapper" style={{ marginTop: '0.5rem', borderRadius: '10px' }}>
      <div className="chart-controls">
        {/* Chart Type Toggles */}
        <div style={{ display: 'flex', gap: '0.15rem', backgroundColor: 'var(--bg-sidebar)', padding: '0.2rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <button 
            className={`btn-icon ${chartType === 'bar' ? 'active' : ''}`}
            style={{ padding: '0.35rem', borderRadius: '5px', backgroundColor: chartType === 'bar' ? 'var(--primary)' : 'transparent', color: chartType === 'bar' ? 'white' : 'var(--text-secondary)' }}
            onClick={() => setChartType('bar')}
            title="Bar Chart"
          >
            <BarChart3 size={14} />
          </button>
          <button 
            className={`btn-icon ${chartType === 'area' || chartType === 'line' ? 'active' : ''}`}
            style={{ padding: '0.35rem', borderRadius: '5px', backgroundColor: chartType === 'area' || chartType === 'line' ? 'var(--primary)' : 'transparent', color: chartType === 'area' || chartType === 'line' ? 'white' : 'var(--text-secondary)' }}
            onClick={() => setChartType('area')}
            title="Area Chart"
          >
            <LineIcon size={14} />
          </button>
          <button 
            className={`btn-icon ${chartType === 'pie' ? 'active' : ''}`}
            style={{ padding: '0.35rem', borderRadius: '5px', backgroundColor: chartType === 'pie' ? 'var(--primary)' : 'transparent', color: chartType === 'pie' ? 'white' : 'var(--text-secondary)' }}
            onClick={() => setChartType('pie')}
            title="Donut Chart"
          >
            <PieIcon size={14} />
          </button>
          <button 
            className={`btn-icon ${chartType === 'scatter' ? 'active' : ''}`}
            style={{ padding: '0.35rem', borderRadius: '5px', backgroundColor: chartType === 'scatter' ? 'var(--primary)' : 'transparent', color: chartType === 'scatter' ? 'white' : 'var(--text-secondary)' }}
            onClick={() => setChartType('scatter')}
            title="Scatter Plot"
          >
            <ScatterIcon size={14} />
          </button>
        </div>

        {/* X Axis Selector */}
        <div className="chart-select-group">
          <span className="chart-select-label" style={{ fontSize: '0.7rem' }}>X-Axis:</span>
          <select 
            className="chart-select" 
            value={xAxisCol} 
            onChange={(e) => setXAxisCol(e.target.value)}
            style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem', borderRadius: '6px' }}
          >
            {allColumns.map(col => (
              <option key={col} value={col}>{col}</option>
            ))}
          </select>
        </div>

        {/* Y Axis Selector */}
        <div className="chart-select-group">
          <span className="chart-select-label" style={{ fontSize: '0.7rem' }}>Y-Axis:</span>
          <select 
            className="chart-select" 
            value={yAxisCol} 
            onChange={(e) => setYAxisCol(e.target.value)}
            style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem', borderRadius: '6px' }}
          >
            {allColumns.map(col => (
              <option key={col} value={col}>{col}</option>
            ))}
          </select>
        </div>
      </div>

      <div style={{ width: '100%', height: 280, marginTop: '0.5rem' }}>
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
