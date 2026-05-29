import axios from 'axios';
import toast from 'react-hot-toast';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 20000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    const isAuthRoute = window.location.pathname === '/auth';

    if (status === 401 && !isAuthRoute) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      window.location.href = '/auth';
      return Promise.reject(error);
    }

    if (isAuthRoute) {
      return Promise.reject(error);
    }

    if (status === 422) {
      const detail = error.response?.data?.detail;
      const message = Array.isArray(detail)
        ? detail.map((item) => item.msg || String(item)).join(', ')
        : String(detail || 'Ошибка валидации');
      toast.error(message);
      return Promise.reject(error);
    }

    if (status >= 400 && status < 500) {
      const message = error.response?.data?.detail || error.response?.data?.message;
      if (message) toast.error(String(message));
      return Promise.reject(error);
    }

    if (status >= 500) {
      toast.error('Сервер временно недоступен');
      return Promise.reject(error);
    }

    return Promise.reject(error);
  }
);

export default api;
