import React from 'react';
import { FixedSizeList as List } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';

const VirtualizedFileList = ({ files, selectedFilePaths, onToggleSelect, onPreview, activeIndex }) => {

  const getConfidenceColor = (level) => {
    switch(level) {
      case 1: return '#38a169'; // Green (Low confidence / Keep)
      case 2: return '#dd6b20'; // Orange (Medium confidence / Review)
      case 3: return '#e53e3e'; // Red (High confidence / Delete)
      default: return '#718096'; // Gray (Unknown)
    }
  };

  const formatSize = (sizeMb) => {
    if (sizeMb === 0) return '0 MB';
    if (sizeMb < 1) {
      return (sizeMb * 1024).toFixed(2) + ' KB';
    }
    return sizeMb.toFixed(2) + ' MB';
  };

  const Row = ({ index, style }) => {
    const file = files[index];
    const isSelected = selectedFilePaths.has(file.path);
    const isActive = index === activeIndex;

    return (
      <div
        style={{
          ...style,
          display: 'flex',
          alignItems: 'center',
          padding: '0 1rem',
          borderBottom: '1px solid #e2e8f0',
          backgroundColor: isActive ? '#bee3f8' : (index % 2 === 0 ? '#f7fafc' : 'white'),
          cursor: 'pointer'
        }}
        onClick={() => onPreview(file)}
      >
        <div style={{ marginRight: '1rem' }} onClick={(e) => e.stopPropagation()}>
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => onToggleSelect(file.path)}
          />
        </div>
        <div style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {file.filename}
        </div>
        <div style={{ width: '100px', textAlign: 'right', color: '#718096', fontSize: '0.875rem' }}>
          {formatSize(file.size_mb)}
        </div>
        <div style={{ width: '120px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <span style={{
            display: 'inline-block',
            width: '12px', height: '12px',
            borderRadius: '50%',
            backgroundColor: getConfidenceColor(file.confidence_score),
            marginRight: '0.5rem'
          }}></span>
          <span style={{ fontSize: '0.875rem', fontWeight: 'bold', color: getConfidenceColor(file.confidence_score) }}>
            Level {file.confidence_score}
          </span>
        </div>
      </div>
    );
  };

  return (
    <div style={{ flex: 1, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{
        display: 'flex',
        padding: '0.5rem 1rem',
        backgroundColor: '#edf2f7',
        fontWeight: 'bold',
        borderBottom: '2px solid #cbd5e0'
      }}>
        <div style={{ width: '24px', marginRight: '1rem' }}></div>
        <div style={{ flex: 1 }}>Filename</div>
        <div style={{ width: '100px', textAlign: 'right' }}>Size</div>
        <div style={{ width: '120px', textAlign: 'center' }}>Confidence</div>
      </div>

      <div style={{ flex: 1 }}>
        <AutoSizer>
          {({ height, width }) => (
            <List
              height={height}
              itemCount={files.length}
              itemSize={50}
              width={width}
            >
              {Row}
            </List>
          )}
        </AutoSizer>
      </div>
    </div>
  );
};

export default VirtualizedFileList;
