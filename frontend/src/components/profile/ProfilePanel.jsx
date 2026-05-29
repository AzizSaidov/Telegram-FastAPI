import { useState } from 'react';
import Avatar from '../ui/Avatar';
import useAuthStore from '../../store/authStore';
import useUIStore from '../../store/uiStore';
import useTheme from '../../hooks/useTheme';
import { getMyProfile, updateMyProfile } from '../../api/profiles';
import { logout } from '../../api/auth';
import socketManager from '../../socket/socket';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

export default function ProfilePanel({ onBack }) {
  const { user, clearAuth, updateUser } = useAuthStore();
  const { toggleTheme, theme } = useTheme();
  const navigate = useNavigate();
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);

  const [form, setForm] = useState({
    full_name: user?.profile?.full_name || '',
    username: user?.profile?.username || '',
    bio: user?.profile?.bio || '',
  });

  const handleSave = async () => {
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append('full_name', form.full_name);
      fd.append('username', form.username);
      fd.append('bio', form.bio);
      const res = await updateMyProfile(fd);
      updateUser({ profile: res.data });
      setEditing(false);
      toast.success('Профиль обновлён');
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('avatar', file);
    try {
      const res = await updateMyProfile(fd);
      updateUser({ profile: res.data });
      toast.success('Аватар обновлён');
    } catch {}
  };

  const handleLogout = async () => {
    try { await logout(); } catch {}
    socketManager.disconnect();
    clearAuth();
    navigate('/auth');
  };

  return (
    <div className="profile-panel">
      {/* Header */}
      <div className="profile-panel-header">
        <button className="icon-btn" onClick={onBack}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
          </svg>
        </button>
        <span className="profile-panel-header-title">Настройки</span>
        {!editing ? (
          <button className="icon-btn" onClick={() => setEditing(true)}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
            </svg>
          </button>
        ) : (
          <button className="icon-btn" onClick={() => setEditing(false)}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        )}
      </div>

      {/* Body */}
      <div className="profile-panel-body">
        {/* Аватар */}
        <div className="profile-avatar-section">
          <div className="profile-avatar-wrap">
            <Avatar
              src={user?.profile?.avatar_url}
              alt={user?.profile?.full_name}
              size={96}
            />
            <label className="profile-avatar-edit" htmlFor="avatar-upload">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 15.2A3.2 3.2 0 0 1 8.8 12 3.2 3.2 0 0 1 12 8.8a3.2 3.2 0 0 1 3.2 3.2 3.2 3.2 0 0 1-3.2 3.2M18.5 2h-13A2.5 2.5 0 0 0 3 4.5v15A2.5 2.5 0 0 0 5.5 22h13a2.5 2.5 0 0 0 2.5-2.5v-15A2.5 2.5 0 0 0 18.5 2z"/>
              </svg>
            </label>
            <input id="avatar-upload" type="file" accept="image/*" style={{ display: 'none' }} onChange={handleAvatarChange} />
          </div>

          {editing ? (
            <input
              className="form-input"
              style={{ width: '100%', textAlign: 'center', fontWeight: 700, fontSize: 18 }}
              value={form.full_name}
              onChange={e => setForm(p => ({ ...p, full_name: e.target.value }))}
              placeholder="Полное имя"
            />
          ) : (
            <>
              <div className="profile-full-name">{user?.profile?.full_name}</div>
              <div className="profile-status">в сети</div>
            </>
          )}
        </div>

        {/* Поля */}
        <div className="profile-field">
          <div className="profile-field-label">Телефон</div>
          <div className="profile-field-value">{user?.phone_number}</div>
        </div>

        <div className="profile-field">
          <div className="profile-field-label">Имя пользователя</div>
          {editing ? (
            <input className="form-input" value={form.username} onChange={e => setForm(p => ({ ...p, username: e.target.value }))} placeholder="@username" />
          ) : (
            <div className="profile-field-value">@{user?.profile?.username}</div>
          )}
        </div>

        <div className="profile-field">
          <div className="profile-field-label">О себе</div>
          {editing ? (
            <textarea
              className="form-input"
              value={form.bio}
              onChange={e => setForm(p => ({ ...p, bio: e.target.value }))}
              placeholder="Расскажите о себе..."
              rows={3}
              style={{ resize: 'none' }}
            />
          ) : (
            <div className="profile-field-value">{user?.profile?.bio || '—'}</div>
          )}
        </div>

        {editing && (
          <button className="btn btn-primary" onClick={handleSave} disabled={loading}>
            {loading ? 'Сохранение...' : 'Сохранить'}
          </button>
        )}

        {/* Настройки */}
        <div className="profile-section-title">Настройки</div>

        <div className="profile-setting-item" onClick={toggleTheme}>
          <span className="profile-setting-icon">
            {theme === 'dark' ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M6.76 4.84l-1.8-1.79-1.41 1.41 1.79 1.79 1.42-1.41zM4 10.5H1v2h3v-2zm9-9.95h-2V3.5h2V.55zm7.45 3.91l-1.41-1.41-1.79 1.79 1.41 1.41 1.79-1.79zm-3.21 13.7l1.79 1.8 1.41-1.41-1.8-1.79-1.4 1.4zM20 10.5v2h3v-2h-3zm-8-5c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6zm-1 16.95h2V19.5h-2v2.95zm-7.45-3.91l1.41 1.41 1.79-1.8-1.41-1.41-1.79 1.8z"/></svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 3a9 9 0 1 0 9 9c0-.46-.04-.92-.1-1.36a5.389 5.389 0 0 1-4.4 2.26 5.403 5.403 0 0 1-3.14-9.8c-.44-.06-.9-.1-1.36-.1z"/></svg>
            )}
          </span>
          {theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}
        </div>

        <div className="profile-setting-item danger" onClick={handleLogout}>
          <span className="profile-setting-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/>
            </svg>
          </span>
          Выйти
        </div>
      </div>
    </div>
  );
}
