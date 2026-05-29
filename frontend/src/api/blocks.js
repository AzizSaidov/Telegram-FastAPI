import api from './axios';

export const getBlockedUsers = () => api.get('/blocks/');

export const blockUser = (data) => api.post('/blocks/', data);

export const unblockUser = (username) => api.delete(`/blocks/${username}`);
