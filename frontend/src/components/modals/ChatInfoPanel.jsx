import { useState, useEffect } from 'react';
import Avatar from '../ui/Avatar';
import { getGroupMembers, addGroupMember, removeGroupMember, makeGroupAdmin } from '../../api/groups';
import { getChannelMembers, addChannelMember, removeChannelMember, makeChannelAdmin, subscribeChannel, unsubscribeChannel } from '../../api/channels';
import { searchUsers } from '../../api/auth';
import useAuthStore from '../../store/authStore';
import toast from 'react-hot-toast';

export default function ChatInfoPanel({ chat, onClose }) {
  const currentUser = useAuthStore((s) => s.user);
  const [members, setMembers] = useState([]);
  const [searchQ, setSearchQ] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('members'); // 'members' | 'add'

  const isGroup = chat.type === 'group';
  const isChannel = chat.type === 'channel';
  const myMembership = members.find(m => m.user?.id === currentUser?.id);
  const myRole = myMembership?.role || 'member';
  const isAdmin = myRole === 'admin' || myRole === 'owner';

  useEffect(() => {
    loadMembers();
  }, [chat.id]);

  const loadMembers = async () => {
    setLoading(true);
    try {
      let res;
      if (isGroup) res = await getGroupMembers(chat.id);
      else if (isChannel) res = await getChannelMembers(chat.id);
      setMembers(Array.isArray(res?.data) ? res.data : []);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (q) => {
    setSearchQ(q);
    if (q.length < 2) { setSearchResults([]); return; }
    try {
      const res = await searchUsers(q);
      setSearchResults(res.data);
    } catch {}
  };

  const handleAddMember = async (user) => {
    try {
      if (isGroup) await addGroupMember(chat.id, { username: user.profile?.username || user.phone_number });
      else await addChannelMember(chat.id, { username: user.profile?.username || user.phone_number });
      toast.success(`${user.profile?.full_name} добавлен`);
      loadMembers();
      setSearchQ('');
      setSearchResults([]);
      setTab('members');
    } catch {
      toast.error('Не удалось добавить');
    }
  };

  const handleRemoveMember = async (member) => {
    try {
      const uname = member.user?.profile?.username || member.user?.phone_number;
      if (isGroup) await removeGroupMember(chat.id, uname);
      else await removeChannelMember(chat.id, uname);
      toast.success('Участник удалён');
      setMembers(prev => prev.filter(m => m.user?.id !== member.user?.id));
    } catch {
      toast.error('Не удалось удалить');
    }
  };

  const handleMakeAdmin = async (member) => {
    try {
      const uname = member.user?.profile?.username;
      if (isGroup) await makeGroupAdmin(chat.id, uname);
      else await makeChannelAdmin(chat.id, uname);
      toast.success('Назначен администратором');
      loadMembers();
    } catch {
      toast.error('Не удалось назначить');
    }
  };

  const handleSubscribe = async () => {
    try {
      await subscribeChannel(chat.id);
      toast.success('Вы подписались');
      loadMembers();
    } catch {}
  };

  const handleUnsubscribe = async () => {
    try {
      await unsubscribeChannel(chat.id);
      toast.success('Вы отписались');
      loadMembers();
    } catch {}
  };

  return (
    <div className="chat-info-panel">
      <div className="chat-info-header">
        <button className="icon-btn" onClick={onClose}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
        </button>
        <span className="modal-title">{isGroup ? 'Группа' : 'Канал'}</span>
      </div>

      {/* Аватар + info */}
      <div style={{ textAlign: 'center', padding: '20px' }}>
        <Avatar src={chat.avatar_url} alt={chat.title} size={80} />
        <div style={{ fontWeight: 700, fontSize: 18, marginTop: 10, color: 'var(--text-primary)' }}>{chat.title}</div>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
          {members.length} {isChannel ? 'подписчиков' : 'участников'}
        </div>
        {chat.description && (
          <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 8, padding: '0 16px' }}>{chat.description}</div>
        )}
        {isChannel && !myMembership && (
          <button className="btn btn-primary" style={{ marginTop: 12 }} onClick={handleSubscribe}>
            Подписаться
          </button>
        )}
        {isChannel && myMembership && myRole === 'subscriber' && (
          <button onClick={handleUnsubscribe} style={{ marginTop: 12, color: 'var(--accent-danger)', fontSize: 13 }}>
            Отписаться
          </button>
        )}
      </div>

      {/* Вкладки */}
      {isAdmin && (
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', marginBottom: 8 }}>
          <button
            onClick={() => setTab('members')}
            style={{
              flex: 1, padding: '10px', fontSize: 13, fontWeight: tab === 'members' ? 600 : 400,
              color: tab === 'members' ? 'var(--accent)' : 'var(--text-secondary)',
              borderBottom: tab === 'members' ? '2px solid var(--accent)' : '2px solid transparent',
            }}
          >
            Участники
          </button>
          <button
            onClick={() => setTab('add')}
            style={{
              flex: 1, padding: '10px', fontSize: 13, fontWeight: tab === 'add' ? 600 : 400,
              color: tab === 'add' ? 'var(--accent)' : 'var(--text-secondary)',
              borderBottom: tab === 'add' ? '2px solid var(--accent)' : '2px solid transparent',
            }}
          >
            Добавить
          </button>
        </div>
      )}

      {/* Список участников */}
      {tab === 'members' && (
        <div style={{ overflowY: 'auto', flex: 1 }}>
          {loading ? (
            <div style={{ padding: 20, textAlign: 'center' }}><div className="spinner" /></div>
          ) : members.map((member) => (
            <div key={member.user?.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 16px' }}>
              <Avatar src={member.user?.profile?.avatar_url} alt={member.user?.profile?.full_name} size={40} />
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 500, fontSize: 14, color: 'var(--text-primary)' }}>
                  {member.user?.profile?.full_name || member.user?.phone_number}
                </div>
                <div style={{ fontSize: 12, color: 'var(--accent)' }}>
                  {member.role === 'admin' || member.role === 'owner' ? '⚡ Администратор' : ''}
                </div>
              </div>
              {isAdmin && member.user?.id !== currentUser?.id && (
                <div style={{ display: 'flex', gap: 4 }}>
                  {member.role !== 'admin' && member.role !== 'owner' && (
                    <button className="icon-btn" title="Сделать админом" onClick={() => handleMakeAdmin(member)}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="var(--accent)"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/></svg>
                    </button>
                  )}
                  <button className="icon-btn" title="Удалить" onClick={() => handleRemoveMember(member)}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="var(--accent-danger)"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Добавить участника */}
      {tab === 'add' && isAdmin && (
        <div style={{ padding: '12px 16px' }}>
          <input
            className="form-input"
            placeholder="Поиск пользователей..."
            value={searchQ}
            onChange={e => handleSearch(e.target.value)}
            autoFocus
          />
          <div style={{ marginTop: 8 }}>
            {searchResults.map(user => (
              <div
                key={user.id}
                onClick={() => handleAddMember(user)}
                style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 0', cursor: 'pointer' }}
              >
                <Avatar src={user.profile?.avatar_url} alt={user.profile?.full_name} size={40} />
                <div>
                  <div style={{ fontWeight: 500, fontSize: 14, color: 'var(--text-primary)' }}>
                    {user.profile?.full_name || user.phone_number}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>@{user.profile?.username}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
