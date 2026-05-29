import { useState, useEffect, useRef, useCallback } from 'react';
import useUIStore from '../../store/uiStore';
import useChatStore from '../../store/chatStore';
import { getUnifiedChats, searchChats } from '../../api/chats';
import ChatListItem from '../chat/ChatListItem';
import HamburgerMenu from '../sidebar/HamburgerMenu';
import StoryRow from '../sidebar/StoryRow';
import ProfilePanel from '../profile/ProfilePanel';

const TABS = [
  { key: 'all',     label: 'Все' },
  { key: 'private', label: 'Личные' },
  { key: 'group',   label: 'Группы' },
  { key: 'channel', label: 'Каналы' },
];

export default function Sidebar() {
  const {
    hamburgerOpen, setHamburgerOpen,
    sidebarTab, setSidebarTab,
    profileOpen, setProfileOpen,
    searchQuery, setSearchQuery,
  } = useUIStore();

  const { unifiedChats, setUnifiedChats, activeChat, setActiveChat } = useChatStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const searchTimeout = useRef(null);

  // ЕДИНСТВЕННАЯ загрузка чатов — либо все, либо поиск
  const loadChats = useCallback(async (query = '') => {
    setLoading(true);
    setError(null);
    try {
      let res;
      if (query.trim()) {
        res = await searchChats(query.trim());
      } else {
        res = await getUnifiedChats();
      }
      const data = Array.isArray(res.data) ? res.data : [];
      setUnifiedChats(data);
    } catch (err) {
      console.error('[Sidebar] loadChats error:', err);
      setError('Не удалось загрузить чаты');
    } finally {
      setLoading(false);
    }
  }, [setUnifiedChats]);

  // Первоначальная загрузка
  useEffect(() => {
    loadChats('');
  }, []);

  // Поиск с дебаунсом
  useEffect(() => {
    clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => {
      loadChats(searchQuery);
    }, searchQuery ? 300 : 0);
    return () => clearTimeout(searchTimeout.current);
  }, [searchQuery]);

  // Фильтрация по вкладке (из уже загруженных)
  const filteredChats = sidebarTab === 'all'
    ? unifiedChats
    : unifiedChats.filter((c) => c.type === sidebarTab);

  // Счётчики непрочитанных
  const tabCounts = {
    private: unifiedChats.filter(c => c.type === 'private' && c.unread_count > 0).length,
    group:   unifiedChats.filter(c => c.type === 'group'   && c.unread_count > 0).length,
    channel: unifiedChats.filter(c => c.type === 'channel' && c.unread_count > 0).length,
  };

  // Если открыты настройки — показываем ProfilePanel вместо сайдбара
  if (profileOpen) return <ProfilePanel onBack={() => setProfileOpen(false)} />;

  return (
    <>
      {hamburgerOpen && <HamburgerMenu onClose={() => setHamburgerOpen(false)} />}

      <div className="sidebar">
        {/* ===== Шапка ===== */}
        <div className="sidebar-header">
          <button className="hamburger-btn" onClick={() => setHamburgerOpen(true)} title="Меню">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>
            </svg>
          </button>

          <div className="search-wrapper">
            <svg className="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
            </svg>
            <input
              type="text"
              className="search-input"
              placeholder="Поиск"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <button className="edit-btn" title="Новый чат">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
            </svg>
          </button>
        </div>

        {/* ===== Вкладки ===== */}
        <div className="chat-tabs">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              className={`chat-tab${sidebarTab === tab.key ? ' active' : ''}`}
              onClick={() => setSidebarTab(tab.key)}
            >
              {tab.label}
              {tab.key !== 'all' && tabCounts[tab.key] > 0 && (
                <span className="tab-badge">{tabCounts[tab.key]}</span>
              )}
            </button>
          ))}
        </div>

        {/* ===== Сторис ===== */}
        <StoryRow />

        {/* ===== Список чатов ===== */}
        <div className="chat-list">
          {loading ? (
            <div className="flex-center" style={{ padding: '48px 0' }}>
              <div className="spinner" />
            </div>
          ) : error ? (
            <div style={{ padding: '24px 16px', textAlign: 'center' }}>
              <div style={{ color: 'var(--accent-danger)', fontSize: 14, marginBottom: 12 }}>{error}</div>
              <button
                className="btn btn-primary"
                style={{ padding: '8px 16px', fontSize: 13 }}
                onClick={() => loadChats('')}
              >
                Повторить
              </button>
            </div>
          ) : filteredChats.length === 0 ? (
            <div style={{
              padding: '40px 16px',
              textAlign: 'center',
              color: 'var(--text-secondary)',
              fontSize: 14,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 8,
            }}>
              {searchQuery ? (
                <>
                  <svg width="40" height="40" viewBox="0 0 24 24" fill="var(--text-muted)">
                    <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                  </svg>
                  Ничего не найдено
                </>
              ) : (
                <>
                  <svg width="40" height="40" viewBox="0 0 24 24" fill="var(--text-muted)">
                    <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/>
                  </svg>
                  Чатов пока нет
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    Начните новый диалог
                  </span>
                </>
              )}
            </div>
          ) : (
            filteredChats.map((chat) => (
              <ChatListItem
                key={`${chat.type}-${chat.id}`}
                chat={chat}
                isActive={activeChat?.id === chat.id && activeChat?.type === chat.type}
                onClick={() => setActiveChat(chat, chat.type)}
              />
            ))
          )}
        </div>

        {/* ===== FAB кнопка (написать) ===== */}
        <button
          style={{
            position: 'absolute',
            bottom: 20,
            right: 16,
            width: 52,
            height: 52,
            borderRadius: '50%',
            background: 'var(--accent)',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 16px rgba(135,116,225,0.5)',
            transition: 'all 0.2s',
            zIndex: 5,
          }}
          title="Новое сообщение"
          onMouseEnter={e => { e.currentTarget.style.transform = 'scale(1.1)'; e.currentTarget.style.boxShadow = '0 6px 20px rgba(135,116,225,0.7)'; }}
          onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)'; e.currentTarget.style.boxShadow = '0 4px 16px rgba(135,116,225,0.5)'; }}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>
          </svg>
        </button>
      </div>
    </>
  );
}
