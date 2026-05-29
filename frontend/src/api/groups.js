import api from './axios';

export const getGroups = () => api.get('/groups/');

export const createGroup = (formData) =>
  api.post('/groups/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export const searchGroups = (q) =>
  api.get('/groups/search', { params: { q } });

export const getGroupDetail = (groupId) =>
  api.get(`/groups/${groupId}`);

export const updateGroup = (groupId, formData) =>
  api.put(`/groups/${groupId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export const getGroupMembersCount = (groupId) =>
  api.get(`/groups/${groupId}/members/count`);

export const getGroupMembers = (groupId) =>
  api.get(`/groups/${groupId}/members`);

export const addGroupMember = (groupId, data) =>
  api.post(`/groups/${groupId}/members`, data);

export const removeGroupMember = (groupId, username) =>
  api.delete(`/groups/${groupId}/members/${username}`);

export const makeGroupAdmin = (groupId, username) =>
  api.post(`/groups/${groupId}/members/${username}/admin`);

export const getGroupMessages = (groupId, params = {}) =>
  api.get(`/groups/${groupId}/messages`, { params });

export const sendGroupMessage = (groupId, formData) =>
  api.post(`/groups/${groupId}/messages`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export const editGroupMessage = (groupId, messageId, data) =>
  api.put(`/groups/${groupId}/messages/${messageId}`, data);

export const deleteGroupMessage = (groupId, messageId) =>
  api.delete(`/groups/${groupId}/messages/${messageId}`);

export const pinGroupMessage = (groupId, messageId) =>
  api.post(`/groups/${groupId}/messages/${messageId}/pin`);

export const addGroupReaction = (groupId, messageId, data) =>
  api.post(`/groups/${groupId}/messages/${messageId}/reactions`, data);

export const unpinGroupMessage = (groupId, messageId) =>
  api.post(`/groups/${groupId}/messages/${messageId}/unpin`);

export const deleteGroup = (groupId) => api.delete(`/groups/${groupId}`);
