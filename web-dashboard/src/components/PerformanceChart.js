import React, { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';
import '../styles/PerformanceChart.css';

const PerformanceChart = ({ data, metric, timeRange, height = 400 }) => {
    const chartRef = useRef(null);
    const chartInstance = useRef(null);

    useEffect(() => {
        if (chartInstance.current) {
            chartInstance.current.destroy();
        }
        
        renderChart();
        
        return () => {
            if (chartInstance.current) {
                chartInstance.current.destroy();
            }
        };
    }, [data, metric, timeRange]);

    const getChartConfig = () => {
        const chartData = processDataForChart();
        
        const baseConfig = {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#333',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                
                                const value = context.parsed.y;
                                if (metric === 'revenue') {
                                    label += new Intl.NumberFormat('th-TH', {
                                        style: 'currency',
                                        currency: 'THB'
                                    }).format(value);
                                } else {
                                    label += value.toLocaleString();
                                }
                                
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Time'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: getYAxisTitle()
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            callback: function(value) {
                                if (metric === 'revenue') {
                                    return '฿' + value.toLocaleString();
                                }
                                return value.toLocaleString();
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                },
                elements: {
                    point: {
                        radius: 4,
                        hoverRadius: 6
                    },
                    line: {
                        tension: 0.1
                    }
                }
            }
        };

        return baseConfig;
    };

    const processDataForChart = () => {
        if (!data || data.length === 0) {
            return {
                labels: [],
                datasets: []
            };
        }

        // Group data by platform
        const platformData = {};
        const labels = [];

        data.forEach(item => {
            const date = new Date(item.date || item.created_at).toLocaleDateString();
            if (!labels.includes(date)) {
                labels.push(date);
            }

            const platform = item.platform || 'unknown';
            if (!platformData[platform]) {
                platformData[platform] = {};
            }
            
            platformData[platform][date] = item[metric] || 0;
        });

        // Sort labels chronologically
        labels.sort((a, b) => new Date(a) - new Date(b));

        // Create datasets for each platform
        const datasets = Object.keys(platformData).map((platform, index) => {
            const color = getPlatformColor(platform, index);
            const values = labels.map(label => platformData[platform][label] || 0);

            return {
                label: platform.charAt(0).toUpperCase() + platform.slice(1),
                data: values,
                borderColor: color,
                backgroundColor: color + '20',
                fill: false,
                tension: 0.1,
                pointBackgroundColor: color,
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            };
        });

        return {
            labels,
            datasets
        };
    };

    const getPlatformColor = (platform, index) => {
        const colors = {
            'youtube': '#FF0000',
            'tiktok': '#000000',
            'instagram': '#E4405F',
            'facebook': '#1877F2',
            'twitter': '#1DA1F2'
        };

        return colors[platform] || `hsl(${index * 60}, 70%, 50%)`;
    };

    const getYAxisTitle = () => {
        const titles = {
            'views': 'Views',
            'likes': 'Likes',
            'comments': 'Comments',
            'shares': 'Shares',
            'revenue': 'Revenue (THB)'
        };
        
        return titles[metric] || metric.charAt(0).toUpperCase() + metric.slice(1);
    };

    const renderChart = () => {
        const ctx = chartRef.current.getContext('2d');
        const config = getChartConfig();
        
        chartInstance.current = new Chart(ctx, config);
    };

    const getChartSummary = () => {
        if (!data || data.length === 0) return null;

        const total = data.reduce((sum, item) => sum + (item[metric] || 0), 0);
        const average = total / data.length;
        const latest = data[data.length - 1]?.[metric] || 0;
        const previous = data[data.length - 2]?.[metric] || 0;
        const change = latest - previous;
        const changePercent = previous > 0 ? ((change / previous) * 100) : 0;

        return {
            total,
            average,
            latest,
            change,
            changePercent
        };
    };

    const summary = getChartSummary();

    return (
        <div className="performance-chart-container">
            <div className="chart-header">
                <h3>{getYAxisTitle()} Performance</h3>
                {summary && (
                    <div className="chart-summary">
                        <div className="summary-item">
                            <span className="summary-label">Total:</span>
                            <span className="summary-value">
                                {metric === 'revenue' 
                                    ? new Intl.NumberFormat('th-TH', {
                                        style: 'currency',
                                        currency: 'THB'
                                    }).format(summary.total)
                                    : summary.total.toLocaleString()
                                }
                            </span>
                        </div>
                        <div className="summary-item">
                            <span className="summary-label">Average:</span>
                            <span className="summary-value">
                                {metric === 'revenue' 
                                    ? new Intl.NumberFormat('th-TH', {
                                        style: 'currency',
                                        currency: 'THB'
                                    }).format(summary.average)
                                    : Math.round(summary.average).toLocaleString()
                                }
                            </span>
                        </div>
                        <div className="summary-item">
                            <span className="summary-label">Change:</span>
                            <span className={`summary-value ${summary.change >= 0 ? 'positive' : 'negative'}`}>
                                {summary.change >= 0 ? '+' : ''}{summary.changePercent.toFixed(1)}%
                            </span>
                        </div>
                    </div>
                )}
            </div>
            
            <div className="chart-wrapper" style={{ height: `${height}px` }}>
                <canvas ref={chartRef}></canvas>
            </div>
            
            {(!data || data.length === 0) && (
                <div className="chart-empty-state">
                    <p>No data available for the selected time range</p>
                    <span>Try adjusting your filters or wait for more content to be published</span>
                </div>
            )}
        </div>
    );
};

export default PerformanceChart;