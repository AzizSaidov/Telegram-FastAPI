import api from './axios';

export const requestLoginOTP = (data) => api.post('/users/login/request-otp', data);

export const verifyLoginOTP = (data) => api.post('/users/login/verify-otp', data);

export const requestRegisterOTP = (data) => api.post('/users/register/request-otp', data);

export const verifyRegisterOTP = (data) => api.post('/users/register/verify-otp', data);

export const logout = () => api.post('/users/logout');

const normalizePhoneSearch = (query) => {
  const raw = query.trim();
  const digits = raw.replace(/\D/g, '');
  const isPhoneLike = /^[+\d\s().-]+$/.test(raw) && digits.length >= 9;

  if (!isPhoneLike) return null;

  if (digits.length === 9) {
    return `+992${digits}`;
  }

  if (digits.length === 12 && digits.startsWith('992')) {
    return `+${digits}`;
  }

  if (raw.startsWith('+')) {
    return `+${digits}`;
  }

  return `+${digits}`;
};

const normalizeUsernameSearch = (query) => query.trim().replace(/^@+/, '');

export const searchUsersByPhone = (phoneNumber) =>
  api.get('/users/search/phone', {
    params: { phone_number: phoneNumber },
    validateStatus: (status) => status === 200 || status === 404,
  });

export const searchUsers = async (q) => {
  const query = q.trim();
  const phoneNumber = normalizePhoneSearch(query);

  if (phoneNumber) {
    const response = await searchUsersByPhone(phoneNumber);

    return {
      ...response,
      data: response.status === 404 || !response.data ? [] : [response.data],
    };
  }

  return api.get('/users/search', {
    params: { q: normalizeUsernameSearch(query) },
  });
};
