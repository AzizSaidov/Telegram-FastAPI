import { useState } from 'react';
import { createPoll } from '../../api/polls';
import toast from 'react-hot-toast';

export default function CreatePollModal({ channelId, postId, onClose, onCreated }) {
  const [question, setQuestion] = useState('');
  const [options, setOptions] = useState(['', '']);
  const [isMultiple, setIsMultiple] = useState(false);
  const [loading, setLoading] = useState(false);

  const addOption = () => {
    if (options.length >= 10) { toast.error('Максимум 10 вариантов'); return; }
    setOptions(prev => [...prev, '']);
  };

  const removeOption = (idx) => {
    if (options.length <= 2) { toast.error('Минимум 2 варианта'); return; }
    setOptions(prev => prev.filter((_, i) => i !== idx));
  };

  const setOption = (idx, val) => {
    setOptions(prev => prev.map((o, i) => i === idx ? val : o));
  };

  const handleCreate = async () => {
    if (!question.trim()) { toast.error('Введите вопрос'); return; }
    const validOptions = options.filter(o => o.trim());
    if (validOptions.length < 2) { toast.error('Нужно минимум 2 варианта ответа'); return; }
    setLoading(true);
    try {
      const res = await createPoll(channelId, postId, {
        question: question.trim(),
        options: validOptions,
        is_multiple: isMultiple,
      });
      toast.success('Опрос создан!');
      onCreated?.(res.data);
      onClose();
    } catch {
      toast.error('Ошибка при создании опроса');
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
          <span className="modal-title">📊 Создать опрос</span>
          <button className="icon-btn" onClick={handleCreate} disabled={loading} style={{ color: 'var(--accent)' }}>
            {loading ? '...' : 'Создать'}
          </button>
        </div>

        <div style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 12 }}>
          <input
            className="form-input"
            placeholder="Вопрос..."
            value={question}
            onChange={e => setQuestion(e.target.value)}
            autoFocus
          />

          <div style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
            ВАРИАНТЫ ОТВЕТА
          </div>

          {options.map((opt, idx) => (
            <div key={idx} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input
                className="form-input"
                style={{ flex: 1 }}
                placeholder={`Вариант ${idx + 1}`}
                value={opt}
                onChange={e => setOption(idx, e.target.value)}
              />
              {options.length > 2 && (
                <button
                  className="icon-btn"
                  onClick={() => removeOption(idx)}
                  style={{ color: 'var(--accent-danger)', flexShrink: 0 }}
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
                </button>
              )}
            </div>
          ))}

          <button
            onClick={addOption}
            style={{
              display: 'flex', alignItems: 'center', gap: 8,
              color: 'var(--accent)', fontSize: 14, padding: '8px 0',
              fontWeight: 500,
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
            Добавить вариант
          </button>

          <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', padding: '4px 0' }}>
            <div
              onClick={() => setIsMultiple(!isMultiple)}
              style={{
                width: 44, height: 24, borderRadius: 12,
                background: isMultiple ? 'var(--accent)' : 'var(--bg-secondary)',
                position: 'relative', transition: 'background 0.2s', cursor: 'pointer',
              }}
            >
              <div style={{
                position: 'absolute', top: 2, left: isMultiple ? 22 : 2,
                width: 20, height: 20, borderRadius: '50%',
                background: '#fff', transition: 'left 0.2s', boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
              }} />
            </div>
            <span style={{ fontSize: 14, color: 'var(--text-primary)' }}>Несколько вариантов</span>
          </label>
        </div>
      </div>
    </div>
  );
}
