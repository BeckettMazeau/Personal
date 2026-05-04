import React, { useState } from 'react';

const SafetyLockModal = ({ isOpen, fileCount, onConfirm, onCancel }) => {
  const [confirmationText, setConfirmationText] = useState('');

  if (!isOpen) return null;

  const handleConfirm = () => {
    if (confirmationText === 'DELETE') {
      onConfirm();
    }
  };

  return (
    <div className="modal-overlay" style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)', display: 'flex',
      alignItems: 'center', justifyContent: 'center', zIndex: 1000
    }}>
      <div className="modal-content" style={{
        backgroundColor: 'white', padding: '2rem', borderRadius: '8px',
        maxWidth: '400px', width: '100%', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
      }}>
        <h2 style={{ marginTop: 0, color: '#e53e3e' }}>Safety Lock</h2>
        <p>You are about to move <strong>{fileCount}</strong> files to the Trash.</p>
        <p>To proceed, please type <strong>DELETE</strong> below:</p>

        <input
          type="text"
          value={confirmationText}
          onChange={(e) => setConfirmationText(e.target.value)}
          placeholder="Type DELETE"
          style={{
            width: '100%', padding: '0.5rem', marginBottom: '1rem',
            border: '1px solid #ccc', borderRadius: '4px', boxSizing: 'border-box'
          }}
        />

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
          <button
            onClick={onCancel}
            style={{
              padding: '0.5rem 1rem', border: '1px solid #ccc', borderRadius: '4px',
              backgroundColor: 'white', cursor: 'pointer'
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={confirmationText !== 'DELETE'}
            style={{
              padding: '0.5rem 1rem', border: 'none', borderRadius: '4px',
              backgroundColor: confirmationText === 'DELETE' ? '#e53e3e' : '#fc8181',
              color: 'white', cursor: confirmationText === 'DELETE' ? 'pointer' : 'not-allowed'
            }}
          >
            Confirm Execution
          </button>
        </div>
      </div>
    </div>
  );
};

export default SafetyLockModal;
