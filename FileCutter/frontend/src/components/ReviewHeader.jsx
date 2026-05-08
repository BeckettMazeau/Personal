import React from 'react';

const ReviewHeader = ({ selectedCount, onExecuteClick }) => {
  return (
    <header className="header">
      <h1 className="header-title">FileCutter Review</h1>
      <div className="header-actions">
        <span className="file-count">{selectedCount} files selected</span>
        <button
          onClick={onExecuteClick}
          disabled={selectedCount === 0}
          className={`execute-btn ${selectedCount > 0 ? 'active' : 'disabled'}`}
        >
          Execute Cleanup
        </button>
      </div>
    </header>
  );
};

export default ReviewHeader;
