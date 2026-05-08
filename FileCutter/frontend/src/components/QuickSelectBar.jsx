import React from 'react';

const QuickSelectBar = ({ onSelectByConfidence, onClearSelection }) => {
  return (
    <div className="quick-select-bar">
      <span>Quick Select:</span>
      <button onClick={() => onSelectByConfidence(3)} className="quick-select-btn">All Level 3 (Safe to Delete)</button>
      <button onClick={() => onSelectByConfidence(2)} className="quick-select-btn">All Level 2 (Review)</button>
      <button onClick={() => onSelectByConfidence(1)} className="quick-select-btn">All Level 1 (Keep)</button>
      <button onClick={onClearSelection} className="clear-select-btn">Clear Selection</button>
    </div>
  );
};

export default QuickSelectBar;
