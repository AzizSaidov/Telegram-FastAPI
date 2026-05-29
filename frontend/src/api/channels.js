import api from './axios';

export const getChannels = () => api.get('/channels/');

export const createChannel = (formData) =>
  api.post('/channels/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export const searchChannels = (q) =>
  api.get('/channels/search', { params: { q } });

export const getChannelDetail = (channelId) =>
  api.get(`/channels/${channelId}`);

export const updateChannel = (channelId, formData) =>
  api.put(`/channels/${channelId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export const getChannelMembersCount = (channelId) =>
  api.get(`/channels/${channelId}/members/count`);

export const getChannelMembers = (channelId) =>
  api.get(`/channels/${channelId}/members`);

export const addChannelMember = (channelId, data) =>
  api.post(`/channels/${channelId}/members`, data);

export const removeChannelMember = (channelId, username) =>
  api.delete(`/channels/${channelId}/members/${username}`);

export const makeChannelAdmin = (channelId, username) =>
  api.post(`/channels/${channelId}/members/${username}/admin`);

export const subscribeChannel = (channelId) =>
  api.post(`/channels/${channelId}/subscribe`);

export const unsubscribeChannel = (channelId) =>
  api.delete(`/channels/${channelId}/subscribe`);

export const getChannelPosts = (channelId, params = {}) =>
  api.get(`/channels/${channelId}/posts`, { params });

export const createChannelPost = (channelId, formData) =>
  api.post(`/channels/${channelId}/posts`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export const editChannelPost = (channelId, postId, data) =>
  api.put(`/channels/${channelId}/posts/${postId}`, data);

export const deleteChannelPost = (channelId, postId) =>
  api.delete(`/channels/${channelId}/posts/${postId}`);

export const pinChannelPost = (channelId, postId) =>
  api.post(`/channels/${channelId}/posts/${postId}/pin`);

export const addChannelReaction = (channelId, postId, data) =>
  api.post(`/channels/${channelId}/posts/${postId}/reactions`, data);

export const unpinChannelPost = (channelId, postId) =>
  api.post(`/channels/${channelId}/posts/${postId}/unpin`);

export const deleteChannel = (channelId) => api.delete(`/channels/${channelId}`);
