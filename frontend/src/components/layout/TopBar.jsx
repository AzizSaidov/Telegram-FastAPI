import { useState } from 'react';
import Avatar from '../ui/Avatar';
import useChatStore from '../../store/chatStore';
import useUIStore from '../../store/uiStore';
import { formatLastSeen } from '../../hooks/useMediaUrl';
import ChatInfoPanel from '../modals/ChatInfoPanel';

export default function TopBar() {
  const activeChat = useChatStore((s) => s.activeChat);
  const [showInfo, setShowInfo] = useState(false);

  if (!activeChat) return null;

  const { type, title, avatar_url, is_online, last_seen, members_count } = activeChat;

  let statusText = '';
  if (type === 'private') {
    statusText = is_online ? 'в сети' : last_seen ? `был(а) ${formatLastSeen(last_seen)}` : 'не в сети';
  } else if (type === 'group') {
    statusText = members_count ? `${members_count} участников` : 'группа';
  } else if (type === 'channel') {
    statusText = members_count ? `${members_count} подписчиков` : 'канал';
  }

  return (
    <>
      {showInfo && (type === 'group' || type === 'channel') && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 500, display: 'flex', justifyContent: 'flex-end' }}>
          <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.4)' }} onClick={() => setShowInfo(false)} />
          <div style={{
            position: 'relative',
            width: 340,
            height: '100%',
            background: 'var(--bg-sidebar)',
            display: 'flex',
            flexDirection: 'column',
            overflowY: 'auto',
            zIndex: 1,
            borderLeft: '1px solid var(--border)',
          }}>
            <ChatInfoPanel chat={activeChat} onClose={() => setShowInfo(false)} />
          </div>
        </div>
      )}

      <div className="topbar">
        <div
          className="topbar-avatar-wrap"
          onClick={() => setShowInfo(true)}
          style={{ cursor: 'pointer' }}
        >
          <Avatar
            src={avatar_url}
            alt={title}
            size={40}
            online={type === 'private' && is_online}
          />
        </div>

        <div
          className="topbar-info"
          onClick={() => (type === 'group' || type === 'channel') && setShowInfo(true)}
          style={{ cursor: type !== 'private' ? 'pointer' : 'default' }}
        >
          <div className="topbar-name">{title}</div>
          <div className={`topbar-status${is_online && type === 'private' ? ' online' : ''}`}>
            {statusText}
          </div>
        </div>

        <div className="topbar-actions">
          {/* Поиск по чату */}
          <button className="icon-btn" title="Поиск сообщений">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
            </svg>
          </button>

          {/* Инфо о группе/канале */}
          {(type === 'group' || type === 'channel') && (
            <button className="icon-btn" title="Участники" onClick={() => setShowInfo(true)}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
              </svg>
            </button>
          )}

          {/* Меню */}
          <button className="icon-btn" title="Ещё">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
            </svg>
          </button>
        </div>
      </div>
    </>
  );
}
