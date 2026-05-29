import { useState } from 'react';
import { createGroup } from '../../api/groups';
import { searchUsers } from '../../api/auth';
import Avatar from '../ui/Avatar';
import toast from 'react-hot-toast';

export default function CreateGroupModal({ onClose, onCreate }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [avatar, setAvatar] = useState(null);
  const [avatarPreview, setAvatarPreview] = useState(null);
  const [searchQ, setSearchQ] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selected, setSelected] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (q) => {
    setSearchQ(q);
    if (q.length < 2) { setSearchResults([]); return; }
    try {
      const res = await searchUsers(q);
      setSearchResults(res.data);
    } catch {}
  };

  const toggleUser = (user) => {
    setSelected((prev) =>
      prev.find(u => u.id === user.id)
        ? prev.filter(u => u.id !== user.id)
        : [...prev, user]
    );
  };

  const handleAvatarChange = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    setAvatar(f);
    setAvatarPreview(URL.createObjectURL(f));
  };

  const handleCreate = async () => {
    if (!title.trim()) { toast.error('Введите название группы'); return; }
    if (selected.length < 1) { toast.error('Добавьте хотя бы одного участника'); return; }
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append('title', title.trim());
      if (description.trim()) fd.append('description', description.trim());
      if (avatar) fd.append('avatar', avatar);
      selected.forEach(u => fd.append('member_ids', u.id));
      const res = await createGroup(fd);
      toast.success('Группа создана!');
      onCreate?.(res.data);
      onClose();
    } catch {
      toast.error('Ошибка при создании группы');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <button className="icon-btn" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
          </button>
          <span className="modal-title">Новая группа</span>
          <button className="icon-btn" onClick={handleCreate} disabled={loading} style={{ color: 'var(--accent)' }}>
            {loading ? '...' : 'Создать'}
          </button>
        </div>

        {/* Аватар + имя */}
        <div style={{ display: 'flex', gap: 16, padding: '16px 20px', alignItems: 'center' }}>
          <label style={{ cursor: 'pointer', position: 'relative', flexShrink: 0 }}>
            <div style={{
              width: 64, height: 64, borderRadius: '50%',
              background: avatarPreview ? 'none' : 'var(--accent)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              overflow: 'hidden',
            }}>
              {avatarPreview
                ? <img src={avatarPreview} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                : <svg width="28" height="28" viewBox="0 0 24 24" fill="white"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
              }
            </div>
            <input type="file" accept="image/*" style={{ display: 'none' }} onChange={handleAvatarChange} />
          </label>
          <div style={{ flex: 1 }}>
            <input
              className="form-input"
              placeholder="Название группы"
              value={title}
              onChange={e => setTitle(e.target.value)}
              maxLength={64}
            />
            <input
              className="form-input"
              style={{ marginTop: 8 }}
              placeholder="Описание (необязательно)"
              value={description}
              onChange={e => setDescription(e.target.value)}
            />
          </div>
        </div>

        {/* Выбранные участники */}
        {selected.length > 0 && (
          <div style={{ display: 'flex', gap: 8, padding: '0 20px 12px', flexWrap: 'wrap' }}>
            {selected.map(u => (
              <div key={u.id} style={{ display: 'flex', alignItems: 'center', gap: 4, background: 'var(--accent)', color: '#fff', borderRadius: 20, padding: '4px 10px', fontSize: 13 }}>
                <Avatar src={u.profile?.avatar_url} alt={u.profile?.full_name} size={20} />
                {u.profile?.full_name || u.phone_number}
                <button onClick={() => toggleUser(u)} style={{ color: '#fff', marginLeft: 4, fontSize: 14 }}>✕</button>
              </div>
            ))}
          </div>
        )}

        {/* Поиск пользователей */}
        <div style={{ padding: '0 20px 8px' }}>
          <input
            className="form-input"
            placeholder="Добавить участника..."
            value={searchQ}
            onChange={e => handleSearch(e.target.value)}
          />
        </div>

        <div style={{ maxHeight: 280, overflowY: 'auto' }}>
          {searchResults.map(user => {
            const isSelected = selected.find(u => u.id === user.id);
            return (
              <div
                key={user.id}
                onClick={() => toggleUser(user)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 12,
                  padding: '10px 20px', cursor: 'pointer',
                  background: isSelected ? 'var(--bg-hover)' : 'transparent',
                  transition: 'background 0.1s',
                }}
                onMouseEnter={e => !isSelected && (e.currentTarget.style.background = 'var(--bg-hover)')}
                onMouseLeave={e => !isSelected && (e.currentTarget.style.background = 'transparent')}
              >
                <Avatar src={user.profile?.avatar_url} alt={user.profile?.full_name} size={40} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500, fontSize: 14, color: 'var(--text-primary)' }}>
                    {user.profile?.full_name || user.phone_number}
                  </div>
                  {user.profile?.username && (
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>@{user.profile.username}</div>
                  )}
                </div>
                {isSelected && (
                  <div style={{ width: 22, height: 22, borderRadius: '50%', background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="white"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                  </div>
                )}
              </div>
            );
          })}
          {searchQ.length >= 2 && searchResults.length === 0 && (
            <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: 13 }}>
              Пользователь не найден
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
