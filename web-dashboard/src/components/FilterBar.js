import React, { useState } from 'react';
import '../styles/FilterBar.css';

const FilterBar = ({ filter, onFilterChange, options, showSearch = true, showSort = true }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');

    const handleFilterChange = (key, value) => {
        onFilterChange({ [key]: value });
    };

    const handleSearchChange = (e) => {
        const query = e.target.value;
        setSearchQuery(query);
        onFilterChange({ search: query });
    };

    const clearAllFilters = () => {
        const clearedFilters = {};
        Object.keys(filter).forEach(key => {
            if (key === 'search') {
                clearedFilters[key] = '';
            } else {
                clearedFilters[key] = 'all';
            }
        });
        onFilterChange(clearedFilters);
        setSearchQuery('');
    };

    const getActiveFilterCount = () => {
        return Object.entries(filter).filter(([key, value]) => {
            if (key === 'search') return value && value.length > 0;
            return value && value !== 'all';
        }).length;
    };

    const formatFilterLabel = (key) => {
        const labels = {
            'status': 'Status',
            'platform': 'Platform',
            'dateRange': 'Date Range',
            'category': 'Category',
            'roi': 'ROI',
            'competition': 'Competition',
            'priority': 'Priority',
            'cost': 'Cost Range',
            'sortBy': 'Sort By',
            'sortOrder': 'Order'
        };
        return labels[key] || key.charAt(0).toUpperCase() + key.slice(1);
    };

    const formatOptionLabel = (option) => {
        if (option === 'all') return 'All';
        return option.charAt(0).toUpperCase() + option.slice(1).replace('_', ' ');
    };

    const activeFilterCount = getActiveFilterCount();

    return (
        <div className="filter-bar">
            <div className="filter-bar-main">
                {showSearch && (
                    <div className="search-container">
                        <input
                            type="text"
                            className="search-input"
                            placeholder="Search..."
                            value={searchQuery}
                            onChange={handleSearchChange}
                        />
                        <span className="search-icon">🔍</span>
                    </div>
                )}

                <div className="primary-filters">
                    {Object.entries(options).slice(0, 3).map(([key, optionList]) => (
                        <div key={key} className="filter-group">
                            <label className="filter-label">{formatFilterLabel(key)}</label>
                            <select
                                className="filter-select"
                                value={filter[key] || 'all'}
                                onChange={(e) => handleFilterChange(key, e.target.value)}
                            >
                                {optionList.map(option => (
                                    <option key={option} value={option}>
                                        {formatOptionLabel(option)}
                                    </option>
                                ))}
                            </select>
                        </div>
                    ))}
                </div>

                <div className="filter-controls">
                    {activeFilterCount > 0 && (
                        <button 
                            className="clear-filters-button"
                            onClick={clearAllFilters}
                            title="Clear all filters"
                        >
                            Clear ({activeFilterCount})
                        </button>
                    )}
                    
                    {Object.keys(options).length > 3 && (
                        <button
                            className="expand-filters-button"
                            onClick={() => setIsExpanded(!isExpanded)}
                        >
                            {isExpanded ? 'Less Filters' : 'More Filters'}
                            <span className={`expand-icon ${isExpanded ? 'expanded' : ''}`}>
                                ▼
                            </span>
                        </button>
                    )}
                </div>
            </div>

            {isExpanded && Object.keys(options).length > 3 && (
                <div className="filter-bar-expanded">
                    <div className="secondary-filters">
                        {Object.entries(options).slice(3).map(([key, optionList]) => (
                            <div key={key} className="filter-group">
                                <label className="filter-label">{formatFilterLabel(key)}</label>
                                <select
                                    className="filter-select"
                                    value={filter[key] || 'all'}
                                    onChange={(e) => handleFilterChange(key, e.target.value)}
                                >
                                    {optionList.map(option => (
                                        <option key={option} value={option}>
                                            {formatOptionLabel(option)}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Quick Filter Chips */}
            <div className="quick-filters">
                <div className="quick-filter-chips">
                    {Object.entries(filter).map(([key, value]) => {
                        if (!value || value === 'all' || (key === 'search' && !value)) return null;
                        
                        return (
                            <div key={key} className="filter-chip">
                                <span className="chip-label">{formatFilterLabel(key)}:</span>
                                <span className="chip-value">
                                    {key === 'search' ? `"${value}"` : formatOptionLabel(value)}
                                </span>
                                <button
                                    className="chip-remove"
                                    onClick={() => {
                                        const newValue = key === 'search' ? '' : 'all';
                                        handleFilterChange(key, newValue);
                                        if (key === 'search') setSearchQuery('');
                                    }}
                                    title="Remove filter"
                                >
                                    ✕
                                </button>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Filter Presets */}
            <div className="filter-presets">
                <span className="presets-label">Quick Filters:</span>
                <div className="preset-buttons">
                    <button
                        className="preset-button"
                        onClick={() => onFilterChange({ 
                            status: 'ready', 
                            platform: 'all', 
                            dateRange: 'all' 
                        })}
                    >
                        Ready to Publish
                    </button>
                    
                    <button
                        className="preset-button"
                        onClick={() => onFilterChange({ 
                            roi: 'high', 
                            competition: 'low',
                            priority: 'high' 
                        })}
                    >
                        High Value
                    </button>
                    
                    <button
                        className="preset-button"
                        onClick={() => onFilterChange({ 
                            dateRange: 'today',
                            status: 'all' 
                        })}
                    >
                        Today's Activity
                    </button>
                    
                    <button
                        className="preset-button"
                        onClick={() => onFilterChange({ 
                            cost: 'low',
                            status: 'pending' 
                        })}
                    >
                        Budget Friendly
                    </button>
                </div>
            </div>
        </div>
    );
};

export default FilterBar;