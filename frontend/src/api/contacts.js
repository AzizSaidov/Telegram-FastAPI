import api from './axios';

export const getContacts = () => api.get('/contacts/');

export const addContact = (data) => api.post('/contacts/', data);

export const deleteContact = (contactId) =>
  api.delete(`/contacts/${contactId}`);
