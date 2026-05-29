import { useState } from 'react';
import { createChannel } from '../../api/channels';
import { searchUsers } from '../../api/auth';
import Avatar from '../ui/Avatar';
import toast from 'react-hot-toast';

export default function CreateChannelModal({ onClose, onCreate }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [username, setUsername] = useState('');
  const [avatar, setAvatar] = useState(null);
  const [avatarPreview, setAvatarPreview] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAvatarChange = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    setAvatar(f);
    setAvatarPreview(URL.createObjectURL(f));
  };

  const handleCreate = async () => {
    if (!title.trim()) { toast.error('Введите название канала'); return; }
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append('title', title.trim());
      if (description.trim()) fd.append('description', description.trim());
      if (username.trim()) fd.append('username', username.trim());
      if (avatar) fd.append('avatar', avatar);
      const res = await createChannel(fd);
      toast.success('Канал создан!');
      onCreate?.(res.data);
      onClose();
    } catch {
      toast.error('Ошибка при создании канала');
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
          <span className="modal-title">Новый канал</span>
          <button className="icon-btn" onClick={handleCreate} disabled={loading} style={{ color: 'var(--accent)' }}>
            {loading ? '...' : 'Создать'}
          </button>
        </div>

        <div style={{ display: 'flex', gap: 16, padding: '16px 20px', alignItems: 'center' }}>
          <label style={{ cursor: 'pointer', flexShrink: 0 }}>
            <div style={{
              width: 64, height: 64, borderRadius: '50%',
              background: avatarPreview ? 'none' : '#00acc1',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              overflow: 'hidden',
            }}>
              {avatarPreview
                ? <img src={avatarPreview} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                : <svg width="28" height="28" viewBox="0 0 24 24" fill="white"><path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>
              }
            </div>
            <input type="file" accept="image/*" style={{ display: 'none' }} onChange={handleAvatarChange} />
          </label>
          <div style={{ flex: 1 }}>
            <input
              className="form-input"
              placeholder="Название канала"
              value={title}
              onChange={e => setTitle(e.target.value)}
              maxLength={64}
            />
            <input
              className="form-input"
              style={{ marginTop: 8 }}
              placeholder="@username (необязательно)"
              value={username}
              onChange={e => setUsername(e.target.value.replace(/[^a-zA-Z0-9_]/g, ''))}
            />
            <textarea
              className="form-input"
              style={{ marginTop: 8, resize: 'none' }}
              placeholder="Описание канала..."
              value={description}
              onChange={e => setDescription(e.target.value)}
              rows={3}
            />
          </div>
        </div>

        <div style={{ padding: '0 20px 16px', fontSize: 13, color: 'var(--text-secondary)' }}>
          📢 Канал — публичная лента. Только администраторы могут публиковать посты.
        </div>
      </div>
    </div>
  );
}
