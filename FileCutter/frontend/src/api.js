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

export default api;
