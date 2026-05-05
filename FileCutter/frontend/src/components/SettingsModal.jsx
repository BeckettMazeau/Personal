import React, { useState, useEffect } from 'react';
import { getModels, getHealth, getSettings, updateSettings } from '../api';

const SettingsModal = ({ isOpen, onClose }) => {
  const [models, setModels] = useState([]);
  const [healthStatus, setHealthStatus] = useState('Checking...');
  const [settings, setSettings] = useState({
    active_model: '',
    downloads_path: '',
  });
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchSettings();
      fetchModels();
      checkHealth();
      const interval = setInterval(checkHealth, 5000); // Check heartbeat every 5s
      return () => clearInterval(interval);
    }
  }, [isOpen]);

  const fetchSettings = async () => {
    try {
      const data = await getSettings();
      setSettings(data);
    } catch (error) {
      console.error("Failed to fetch settings:", error);
    }
  };

  const fetchModels = async () => {
    try {
      const data = await getModels();
      // Assuming data.data is the list of models from LM Studio /v1/models format
      setModels(data.data || []);
    } catch (error) {
      console.error("Failed to fetch models:", error);
    }
  };

  const checkHealth = async () => {
    try {
      await getHealth();
      setHealthStatus('Connected');
    } catch (error) {
      setHealthStatus('Disconnected');
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setSettings((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await updateSettings(settings);
      onClose();
    } catch (error) {
      console.error("Failed to save settings:", error);
      alert("Failed to save settings.");
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '2rem',
        borderRadius: '8px',
        width: '400px',
        maxWidth: '90%'
      }}>
        <h2 style={{ marginTop: 0 }}>Settings</h2>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            LM Studio Connection:
          </label>
          <div style={{
            display: 'inline-block',
            padding: '0.25rem 0.5rem',
            borderRadius: '4px',
            backgroundColor: healthStatus === 'Connected' ? '#c6f6d5' : healthStatus === 'Checking...' ? '#e2e8f0' : '#fed7d7',
            color: healthStatus === 'Connected' ? '#22543d' : healthStatus === 'Checking...' ? '#4a5568' : '#742a2a',
            fontWeight: 'bold',
            fontSize: '0.875rem'
          }}>
            <span style={{
              display: 'inline-block',
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: healthStatus === 'Connected' ? '#48bb78' : healthStatus === 'Checking...' ? '#a0aec0' : '#f56565',
              marginRight: '0.5rem'
            }}></span>
            {healthStatus}
          </div>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label htmlFor="active_model" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            Active Model:
          </label>
          <select
            id="active_model"
            name="active_model"
            value={settings.active_model || ''}
            onChange={handleChange}
            style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #cbd5e0' }}
          >
            <option value="">Select a model...</option>
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.id}
              </option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label htmlFor="downloads_path" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            Downloads Path Override:
          </label>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
             <input
              type="text"
              id="downloads_path"
              name="downloads_path"
              value={settings.downloads_path || ''}
              onChange={handleChange}
              style={{ flex: 1, padding: '0.5rem', borderRadius: '4px', border: '1px solid #cbd5e0' }}
              placeholder="/path/to/downloads"
            />
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
          <button
            onClick={onClose}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#e2e8f0',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#4299e1',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: isSaving ? 'not-allowed' : 'pointer'
            }}
          >
            {isSaving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
