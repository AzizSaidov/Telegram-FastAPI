import { useState, useRef, useEffect, useCallback } from 'react';
import useAuthStore from '../../store/authStore';
import useUIStore from '../../store/uiStore';
import useChatStore from '../../store/chatStore';
import socketManager from '../../socket/socket';
import { sendMessage, editMessage as apiEditMessage } from '../../api/chats';
import { sendGroupMessage, editGroupMessage } from '../../api/groups';
import { createChannelPost, editChannelPost } from '../../api/channels';
import CreatePollModal from '../modals/CreatePollModal';
import toast from 'react-hot-toast';

export default function InputPanel({ chatId, chatType, currentUserRole, activeChatData }) {
  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [showAttach, setShowAttach] = useState(false);
  const [showPollModal, setShowPollModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const textareaRef = useRef(null);
  const typingTimer = useRef(null);
  const fileRef = useRef(null);

  const { replyTo, clearReplyTo, editMessage, clearEditMessage } = useUIStore();
  const { addMessage, updateMessage } = useChatStore();

  // Канал: только admin/owner может писать
  const isChannelSubscriber = chatType === 'channel' && (currentUserRole === 'subscriber' || currentUserRole === 'member');

  useEffect(() => {
    if (editMessage) {
      setText(editMessage.text || '');
      textareaRef.current?.focus();
    } else {
      setText('');
    }
  }, [editMessage]);

  // Сброс файла при смене чата
  useEffect(() => {
    setSelectedFile(null);
    setText('');
    clearReplyTo();
    clearEditMessage();
  }, [chatId]);

  const adjustHeight = () => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 150) + 'px';
  };

  const handleChange = (e) => {
    setText(e.target.value);
    adjustHeight();
    handleTyping();
  };

  const handleTyping = useCallback(() => {
    if (!isTyping) {
      setIsTyping(true);
      socketManager.send('typing_started', { chat_id: chatId, chat_type: chatType, to_user_ids: [] });
    }
    clearTimeout(typingTimer.current);
    typingTimer.current = setTimeout(() => {
      setIsTyping(false);
      socketManager.send('typing_stopped', { chat_id: chatId, chat_type: chatType, to_user_ids: [] });
    }, 2000);
  }, [isTyping, chatId, chatType]);

  const send = async () => {
    const trimmed = text.trim();
    if (!trimmed && !selectedFile) return;
    setSending(true);
    try {
      if (editMessage) {
        let res;
        if (chatType === 'private') res = await apiEditMessage(chatId, editMessage.id, { text: trimmed });
        else if (chatType === 'group') res = await editGroupMessage(chatId, editMessage.id, { text: trimmed });
        else res = await editChannelPost(chatId, editMessage.id, { text: trimmed });
        updateMessage(res.data);
        clearEditMessage();
      } else {
        const fd = new FormData();
        if (trimmed) fd.append('text', trimmed);
        if (replyTo) fd.append('reply_to_id', replyTo.id);
        if (selectedFile) fd.append('media', selectedFile);

        let res;
        if (chatType === 'private') res = await sendMessage(chatId, fd);
        else if (chatType === 'group') res = await sendGroupMessage(chatId, fd);
        else res = await createChannelPost(chatId, fd);

        addMessage(res.data);
        clearReplyTo();
        setSelectedFile(null);
      }
      setText('');
      if (textareaRef.current) textareaRef.current.style.height = 'auto';
      textareaRef.current?.focus();
    } catch {
      toast.error('Не удалось отправить');
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
    if (e.key === 'Escape') {
      clearReplyTo();
      clearEditMessage();
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setSelectedFile(file);
    setShowAttach(false);
    toast.success(`Файл: ${file.name}`, { duration: 2000 });
  };

  const cancelReplyOrEdit = () => {
    clearReplyTo();
    clearEditMessage();
    setText('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  // Канал-подписчик — показываем заглушку
  if (isChannelSubscriber) {
    return (
      <div className="input-panel" style={{ justifyContent: 'center' }}>
        <div style={{ color: 'var(--text-muted)', fontSize: 14, padding: '12px 0' }}>
          Только администраторы могут публиковать в этом канале
        </div>
      </div>
    );
  }

  const hasContent = text.trim() || selectedFile;

  return (
    <>
      {showPollModal && chatType === 'channel' && (
        <CreatePollModal
          channelId={chatId}
          postId={null}
          onClose={() => setShowPollModal(false)}
          onCreated={() => {}}
        />
      )}

      <div className="input-panel">
        {/* Reply/Edit bar */}
        {(replyTo || editMessage) && (
          <div className="reply-bar">
            <div className="reply-bar-line" style={{ background: editMessage ? '#fdcb6e' : 'var(--accent)' }} />
            <div className="reply-bar-content">
              <div className="reply-bar-name">
                {editMessage
                  ? '✏️ Редактирование'
                  : `↩ ${replyTo?.sender?.profile?.full_name || 'Пользователь'}`}
              </div>
              <div className="reply-bar-text">
                {editMessage
                  ? editMessage.text
                  : replyTo?.text || (replyTo?.media_url ? '📷 Медиа' : '')}
              </div>
            </div>
            <button className="reply-bar-close icon-btn" onClick={cancelReplyOrEdit}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
            </button>
          </div>
        )}

        {/* Превью файла */}
        {selectedFile && (
          <div className="reply-bar">
            <div className="reply-bar-line" style={{ background: '#00acc1' }} />
            <div className="reply-bar-content">
              <div className="reply-bar-name">📎 Файл выбран</div>
              <div className="reply-bar-text">{selectedFile.name}</div>
            </div>
            <button className="reply-bar-close icon-btn" onClick={() => setSelectedFile(null)}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
            </button>
          </div>
        )}

        <div className="input-row">
          {/* Меню прикрепления */}
          <div style={{ position: 'relative' }}>
            <button
              className="input-btn"
              onClick={() => setShowAttach(!showAttach)}
              title="Прикрепить"
              style={{ color: showAttach ? 'var(--accent)' : 'var(--text-secondary)' }}
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                <path d="M16.5 6v11.5c0 2.21-1.79 4-4 4s-4-1.79-4-4V5a2.5 2.5 0 0 1 5 0v10.5c0 .55-.45 1-1 1s-1-.45-1-1V6H10v9.5a2.5 2.5 0 0 0 5 0V5c0-2.21-1.79-4-4-4S7 2.79 7 5v12.5c0 3.04 2.46 5.5 5.5 5.5s5.5-2.46 5.5-5.5V6h-1.5z"/>
              </svg>
            </button>

            {showAttach && (
              <>
                <div style={{ position: 'fixed', inset: 0, zIndex: 99 }} onClick={() => setShowAttach(false)} />
                <div className="attach-menu">
                  {/* Фото/видео */}
                  <label className="attach-item">
                    <div className="attach-icon" style={{ background: '#a29bfe' }}>
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M12 15.2A3.2 3.2 0 0 1 8.8 12 3.2 3.2 0 0 1 12 8.8a3.2 3.2 0 0 1 3.2 3.2 3.2 3.2 0 0 1-3.2 3.2M18.5 2h-13A2.5 2.5 0 0 0 3 4.5v15A2.5 2.5 0 0 0 5.5 22h13a2.5 2.5 0 0 0 2.5-2.5v-15A2.5 2.5 0 0 0 18.5 2z"/></svg>
                    </div>
                    <span>Фото или видео</span>
                    <input type="file" accept="image/*,video/*" style={{ display: 'none' }} onChange={handleFileSelect} ref={fileRef} />
                  </label>

                  {/* Файл */}
                  <label className="attach-item">
                    <div className="attach-icon" style={{ background: '#74b9ff' }}>
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M6 2c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6H6zm7 7V3.5L18.5 9H13z"/></svg>
                    </div>
                    <span>Файл</span>
                    <input type="file" style={{ display: 'none' }} onChange={handleFileSelect} />
                  </label>

                  {/* Опрос (только канал) */}
                  {chatType === 'channel' && (
                    <div className="attach-item" onClick={() => { setShowAttach(false); setShowPollModal(true); }}>
                      <div className="attach-icon" style={{ background: '#55efc4' }}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M5 9.2h3V19H5zM10.6 5h2.8v14h-2.8zm5.6 8H19v6h-2.8z"/></svg>
                      </div>
                      <span>Опрос</span>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            className="message-textarea"
            placeholder={chatType === 'channel' ? '📢 Публикация...' : 'Сообщение...'}
            value={text}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={sending}
          />

          {/* Кнопка отправки или микрофон */}
          {hasContent ? (
            <button
              className="send-btn"
              onClick={send}
              disabled={sending}
              title="Отправить (Enter)"
              style={{ background: 'var(--accent)' }}
            >
              {sending ? (
                <div style={{ width: 18, height: 18, border: '2px solid rgba(255,255,255,0.4)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                </svg>
              )}
            </button>
          ) : (
            <button
              className="send-btn"
              title="Нажмите для записи голосового"
              style={{ background: 'transparent', color: 'var(--text-secondary)' }}
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"/>
              </svg>
            </button>
          )}
        </div>
      </div>
    </>
  );
}
