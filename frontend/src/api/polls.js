import api from './axios';

export const createPoll = (channelId, postId, data) =>
  api.post(`/channels/${channelId}/posts/${postId}/polls`, data);

export const getPollDetail = (pollId) =>
  api.get(`/polls/${pollId}`);

export const votePoll = (pollId, data) =>
  api.post(`/polls/${pollId}/vote`, data);
