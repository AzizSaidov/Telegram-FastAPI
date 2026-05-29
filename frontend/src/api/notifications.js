import api from './axios';

export const getNotifications = (params = {}) =>
  api.get('/notifications/', { params });

export const markAsRead = (notificationId) =>
  api.post(`/notifications/${notificationId}/read`);

export const markAllAsRead = () =>
  api.post('/notifications/read-all');
