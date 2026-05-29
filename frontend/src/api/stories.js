import api from './axios';

export const getStories = (params = {}) =>
  api.get('/stories/', { params });

export const createStory = (formData) =>
  api.post('/stories/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export const viewStory = (storyId) =>
  api.post(`/stories/view/${storyId}`);

export const getStoryViews = (storyId) =>
  api.get(`/stories/${storyId}/views`);
