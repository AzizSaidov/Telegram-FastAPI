import api from './axios';

export const getMyProfile = () => api.get('/profiles/me');

export const updateMyProfile = (formData) =>
  api.put('/profiles/me', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export const getProfileByUsername = (username) =>
  api.get(`/profiles/${username}`);
