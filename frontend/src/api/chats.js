import api from './axios';

export const getChats = () => api.get('/chats/');

export const createChat = (data) => api.post('/chats/', data);

export const getUnifiedChats = () => api.get('/chats/all');

export const searchChats = (q) =>
  api.get('/chats/search', { params: { q } });

export const getChatMessages = (chatId, params = {}) =>
  api.get(`/chats/${chatId}/messages`, { params });

export const sendMessage = (chatId, formData) =>
  api.post(`/chats/${chatId}/messages`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export const editMessage = (chatId, messageId, data) =>
  api.put(`/chats/${chatId}/messages/${messageId}`, data);

export const deleteMessage = (chatId, messageId) =>
  api.delete(`/chats/${chatId}/messages/${messageId}`);

export const pinMessage = (chatId, messageId) =>
  api.post(`/chats/${chatId}/messages/${messageId}/pin`);

export const addReaction = (chatId, messageId, data) =>
  api.post(`/chats/${chatId}/messages/${messageId}/reactions`, data);

export const unpinMessage = (chatId, messageId) =>
  api.post(`/chats/${chatId}/messages/${messageId}/unpin`);

export const deleteChat = (chatId) => api.delete(`/chats/${chatId}`);
