import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000', // Assuming FastAPI runs on 8000
});

export const getFiles = async () => {
  const response = await api.get('/files');
  return response.data;
};

export const executeCleanup = async (fileIds, confirmationToken) => {
  const response = await api.post('/cleanup', {
    file_ids: fileIds,
    confirmation_token: confirmationToken,
  });
  return response.data;
};

export const getModels = async () => {
  const response = await api.get('/api/models');
  return response.data;
};

export const getHealth = async () => {
  const response = await api.get('/api/health/lm_studio');
  return response.data;
};

export const getSettings = async () => {
  const response = await api.get('/api/settings');
  return response.data;
};

export const updateSettings = async (settings) => {
  const response = await api.post('/api/settings', settings);
  return response.data;
};

export default api;
