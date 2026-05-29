import { useState } from 'react';
import Avatar from '../ui/Avatar';
import useAuthStore from '../../store/authStore';
import useUIStore from '../../store/uiStore';
import { logout } from '../../api/auth';
import socketManager from '../../socket/socket';
import { useNavigate } from 'react-router-dom';
import CreateGroupModal from '../modals/CreateGroupModal';
import CreateChannelModal from '../modals/CreateChannelModal';
import NewChatModal from '../modals/NewChatModal';
import useChatStore from '../../store/chatStore';

export default function HamburgerMenu({ onClose }) {
  const { user, clearAuth } = useAuthStore();
  const { setProfileOpen } = useUIStore();
  const { setActiveChat, unifiedChats, setUnifiedChats } = useChatStore();
  const navigate = useNavigate();
  const [modal, setModal] = useState(null); // 'group' | 'channel' | 'newchat'

  const handleLogout = async () => {
    try { await logout(); } catch {}
    socketManager.disconnect();
    clearAuth();
    navigate('/auth');
    onClose();
  };

  const afterGroupCreated = (group) => {
    setUnifiedChats([{ ...group, type: 'group' }, ...unifiedChats]);
    setActiveChat({ ...group, type: 'group' }, 'group');
  };

  const afterChannelCreated = (channel) => {
    setUnifiedChats([{ ...channel, type: 'channel' }, ...unifiedChats]);
    setActiveChat({ ...channel, type: 'channel' }, 'channel');
  };

  const menuItems = [
    {
      icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/></svg>,
      label: 'Новое сообщение',
      action: () => { setModal('newchat'); },
    },
    {
      icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>,
      label: 'Создать группу',
      action: () => { setModal('group'); },
    },
    {
      icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>,
      label: 'Создать канал',
      action: () => { setModal('channel'); },
    },
    {
      icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/></svg>,
      label: 'Контакты',
      action: () => { setModal('newchat'); },
    },
    {
      icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/></svg>,
      label: 'Уведомления',
      action: onClose,
    },
    {
      icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58a.49.49 0 0 0 .12-.61l-1.92-3.32a.49.49 0 0 0-.59-.22l-2.39.96a7.02 7.02 0 0 0-1.62-.94l-.36-2.54a.484.484 0 0 0-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96a.477.477 0 0 0-.59.22L2.74 8.87a.47.47 0 0 0 .12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58a.49.49 0 0 0-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32a.47.47 0 0 0-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>,
      label: 'Настройки',
      action: () => { setProfileOpen(true); onClose(); },
    },
  ];

  return (
    <>
      {modal === 'group' && (
        <CreateGroupModal onClose={() => setModal(null)} onCreate={afterGroupCreated} />
      )}
      {modal === 'channel' && (
        <CreateChannelModal onClose={() => setModal(null)} onCreate={afterChannelCreated} />
      )}
      {modal === 'newchat' && (
        <NewChatModal onClose={() => { setModal(null); onClose(); }} />
      )}

      <div className="hamburger-overlay" onClick={onClose} />
      <div className="hamburger-panel">
        {/* Профиль */}
        <div
          className="hamburger-top"
          onClick={() => { setProfileOpen(true); onClose(); }}
          style={{ cursor: 'pointer' }}
        >
          <Avatar
            src={user?.profile?.avatar_url}
            alt={user?.profile?.full_name}
            size={48}
          />
          <div className="hamburger-user-info">
            <div className="hamburger-name">{user?.profile?.full_name || 'Без имени'}</div>
            <div className="hamburger-username">
              {user?.profile?.username ? `@${user.profile.username}` : user?.phone_number}
            </div>
          </div>
        </div>

        {/* Пункты меню */}
        <div className="hamburger-items">
          {menuItems.map((item) => (
            <div key={item.label} className="hamburger-item" onClick={item.action}>
              <span className="hamburger-item-icon">{item.icon}</span>
              <span>{item.label}</span>
            </div>
          ))}

          <div className="hamburger-divider" />

          <div className="hamburger-item" style={{ color: '#e17055' }} onClick={handleLogout}>
            <span className="hamburger-item-icon" style={{ color: '#e17055' }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/>
              </svg>
            </span>
            <span>Выйти</span>
          </div>
        </div>
      </div>
    </>
  );
}
