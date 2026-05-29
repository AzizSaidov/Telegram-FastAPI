import { useState } from 'react';
import { createChat } from '../../api/chats';
import { searchUsers } from '../../api/auth';
import Avatar from '../ui/Avatar';
import useChatStore from '../../store/chatStore';
import toast from 'react-hot-toast';

export default function NewChatModal({ onClose }) {
  const [searchQ, setSearchQ] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const { setActiveChat, unifiedChats } = useChatStore();

  const handleSearch = async (q) => {
    setSearchQ(q);
    if (q.length < 2) { setResults([]); return; }
    try {
      const res = await searchUsers(q);
      setResults(res.data);
    } catch {}
  };

  const handleSelect = async (user) => {
    // Проверяем есть ли уже чат
    const existing = unifiedChats.find(c => c.type === 'private' && c.user?.id === user.id);
    if (existing) {
      setActiveChat(existing, 'private');
      onClose();
      return;
    }

    setLoading(true);
    try {
      const res = await createChat({ user_id: user.id });
      setActiveChat({ ...res.data, type: 'private' }, 'private');
      toast.success(`Чат с ${user.profile?.full_name || user.phone_number} открыт`);
      onClose();
    } catch {
      toast.error('Не удалось создать чат');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <button className="icon-btn" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
          </button>
          <span className="modal-title">Новое сообщение</span>
        </div>

        <div style={{ padding: '12px 20px' }}>
          <input
            className="form-input"
            placeholder="Поиск пользователей..."
            value={searchQ}
            onChange={e => handleSearch(e.target.value)}
            autoFocus
          />
        </div>

        <div style={{ maxHeight: 360, overflowY: 'auto' }}>
          {results.length === 0 && searchQ.length >= 2 && (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: 13 }}>
              Пользователь не найден
            </div>
          )}
          {results.length === 0 && searchQ.length < 2 && (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
              Введите имя или номер телефона
            </div>
          )}
          {results.map(user => (
            <div
              key={user.id}
              onClick={() => handleSelect(user)}
              style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '10px 20px', cursor: 'pointer', transition: 'background 0.1s',
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <Avatar src={user.profile?.avatar_url} alt={user.profile?.full_name} size={44} />
              <div>
                <div style={{ fontWeight: 500, fontSize: 14, color: 'var(--text-primary)' }}>
                  {user.profile?.full_name || user.phone_number}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                  {user.profile?.username ? `@${user.profile.username}` : user.phone_number}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
