const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function mediaUrl(path) {
  if (!path) return null;
  if (path.startsWith('http')) return path;
  return `${BASE_URL}${path}`;
}

export function useMediaUrl(path) {
  return mediaUrl(path);
}

const NAME_COLORS = [
  '#ff6b6b',
  '#4dabf7',
  '#20c997',
  '#ffd43b',
  '#ff922b',
  '#9775fa',
  '#f06595',
  '#22b8cf',
];

export function nameColor(userId) {
  return NAME_COLORS[(userId || 0) % NAME_COLORS.length];
}

export function formatTime(dateString) {
  if (!dateString) return '';
  return new Date(dateString).toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatChatDate(dateString) {
  if (!dateString) return '';

  const date = new Date(dateString);
  const now = new Date();
  const today = date.toDateString() === now.toDateString();
  const yesterday = new Date(now.getTime() - 86400000).toDateString() === date.toDateString();
  const sameWeek = now.getTime() - date.getTime() < 7 * 86400000;

  if (today) return formatTime(dateString);
  if (yesterday) return 'Вч';
  if (sameWeek) return date.toLocaleDateString('ru-RU', { weekday: 'short' });
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
}

export function formatSeparatorDate(dateString) {
  if (!dateString) return '';

  const date = new Date(dateString);
  const now = new Date();
  const today = date.toDateString() === now.toDateString();
  const yesterday = new Date(now.getTime() - 86400000).toDateString() === date.toDateString();

  if (today) return 'Сегодня';
  if (yesterday) return 'Вчера';
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

export function formatLastSeen(dateString) {
  if (!dateString) return 'был(а) давно';

  const date = new Date(dateString);
  const diff = Math.floor((Date.now() - date.getTime()) / 1000);

  if (diff < 60) return 'только что';
  if (diff < 3600) return `${Math.floor(diff / 60)} мин назад`;
  if (diff < 86400) return `был(а) в ${formatTime(dateString)}`;

  return `был(а) ${date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
  })}`;
}
