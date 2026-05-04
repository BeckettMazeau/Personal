import React from 'react';
import { FixedSizeList as List } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';

const VirtualizedFileList = ({ files, selectedFileIds, onToggleSelect, onPreview }) => {

  const getConfidenceColor = (level) => {
    switch(level) {
      case 1: return '#e53e3e'; // Red (Low confidence / Keep)
      case 2: return '#dd6b20'; // Orange (Medium confidence / Review)
      case 3: return '#38a169'; // Green (High confidence / Delete)
      default: return '#718096'; // Gray (Unknown)
    }
  };

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const Row = ({ index, style }) => {
    const file = files[index];
    const isSelected = selectedFileIds.has(file.id);

    return (
      <div
        style={{
          ...style,
          display: 'flex',
          alignItems: 'center',
          padding: '0 1rem',
          borderBottom: '1px solid #e2e8f0',
          backgroundColor: index % 2 === 0 ? '#f7fafc' : 'white',
          cursor: 'pointer'
        }}
        onClick={() => onPreview(file)}
      >
        <div style={{ marginRight: '1rem' }} onClick={(e) => e.stopPropagation()}>
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => onToggleSelect(file.id)}
          />
        </div>
        <div style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {file.name}
        </div>
        <div style={{ width: '100px', textAlign: 'right', color: '#718096', fontSize: '0.875rem' }}>
          {formatSize(file.size)}
        </div>
        <div style={{ width: '120px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <span style={{
            display: 'inline-block',
            width: '12px', height: '12px',
            borderRadius: '50%',
            backgroundColor: getConfidenceColor(file.confidence),
            marginRight: '0.5rem'
          }}></span>
          <span style={{ fontSize: '0.875rem', fontWeight: 'bold', color: getConfidenceColor(file.confidence) }}>
            Level {file.confidence}
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
