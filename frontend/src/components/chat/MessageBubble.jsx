import { useState, useRef } from 'react';
import { mediaUrl, nameColor, formatTime } from '../../hooks/useMediaUrl';
import Avatar from '../ui/Avatar';
import useAuthStore from '../../store/authStore';
import useUIStore from '../../store/uiStore';
import useChatStore from '../../store/chatStore';
import PollMessage from './PollMessage';
import { addReaction, deleteMessage, pinMessage } from '../../api/chats';
import { addGroupReaction, deleteGroupMessage, pinGroupMessage } from '../../api/groups';
import { addChannelReaction, deleteChannelPost, pinChannelPost } from '../../api/channels';
import toast from 'react-hot-toast';

const EMOJI_LIST = ['👍', '❤️', '🔥', '🎉', '😂', '😮', '😢', '👎'];

function MediaContent({ url, onClick }) {
  const src = mediaUrl(url);
  if (!src) return null;
  const isVideo = url.match(/\.(mp4|webm|ogg|mov)$/i);
  return (
    <div className="bubble-media" onClick={() => onClick(src)} style={{ cursor: 'zoom-in' }}>
      {isVideo ? (
        <video src={src} controls style={{ maxHeight: 280, width: '100%', borderRadius: 8 }} onClick={e => e.stopPropagation()} />
      ) : (
        <img src={src} alt="media" style={{ maxHeight: 280, objectFit: 'cover', width: '100%', borderRadius: 8, display: 'block' }} />
      )}
    </div>
  );
}

function ReplyPreview({ replyTo, onClick }) {
  if (!replyTo) return null;
  const senderName = replyTo.sender?.profile?.full_name || 'Кто-то';
  const text = replyTo.text || (replyTo.media_url ? '📷 Медиа' : '');
  return (
    <div className="bubble-reply" onClick={onClick} style={{ cursor: onClick ? 'pointer' : 'default' }}>
      <div className="bubble-reply-line" />
      <div>
        <div className="bubble-reply-name">{senderName}</div>
        <div className="bubble-reply-text">{text}</div>
      </div>
    </div>
  );
}

function Reactions({ reactions, chatId, chatType, messageId }) {
  const { updateMessage } = useChatStore();
  if (!reactions || reactions.length === 0) return null;
  const me = useAuthStore.getState().user;

  const grouped = {};
  reactions.forEach((r) => {
    if (!grouped[r.emoji]) grouped[r.emoji] = { count: 0, isMine: false };
    grouped[r.emoji].count++;
    if (r.user?.id === me?.id) grouped[r.emoji].isMine = true;
  });

  const handleReact = async (emoji) => {
    try {
      let res;
      if (chatType === 'private') res = await addReaction(chatId, messageId, { emoji });
      else if (chatType === 'group') res = await addGroupReaction(chatId, messageId, { emoji });
      else res = await addChannelReaction(chatId, messageId, { emoji });
      updateMessage(res.data);
    } catch {}
  };

  return (
    <div className="bubble-reactions">
      {Object.entries(grouped).map(([emoji, { count, isMine }]) => (
        <button
          key={emoji}
          className={`reaction-pill${isMine ? ' own' : ''}`}
          onClick={() => handleReact(emoji)}
          title={isMine ? 'Убрать реакцию' : 'Поставить реакцию'}
        >
          <span>{emoji}</span>
          <span className="reaction-count">{count}</span>
        </button>
      ))}
    </div>
  );
}

function EmojiBar({ onPick, style }) {
  return (
    <div className="emoji-bar" style={style}>
      {EMOJI_LIST.map((e) => (
        <button
          key={e}
          className="emoji-bar-btn"
          onClick={(ev) => { ev.stopPropagation(); onPick(e); }}
        >
          {e}
        </button>
      ))}
    </div>
  );
}

export default function MessageBubble({ message, chatType, chatId, isGroup }) {
  const currentUser = useAuthStore((s) => s.user);
  const { setReplyTo, setEditMessage, setMediaView } = useUIStore();
  const { updateMessage, removeMessage } = useChatStore();
  const [showEmoji, setShowEmoji] = useState(false);
  const [ctxVisible, setCtxVisible] = useState(false);
  const [ctxPos, setCtxPos] = useState({ x: 0, y: 0 });
  const [hovering, setHovering] = useState(false);

  const isOut = message.sender?.id === currentUser?.id;
  const senderName = message.sender?.profile?.full_name || 'Unknown';
  const senderAvatar = message.sender?.profile?.avatar_url;
  const time = formatTime(message.created_at);
  const color = nameColor(message.sender?.id);

  const handleContextMenu = (e) => {
    e.preventDefault();
    // Смещаем меню чтобы не выходило за экран
    const x = Math.min(e.clientX, window.innerWidth - 200);
    const y = Math.min(e.clientY, window.innerHeight - 250);
    setCtxPos({ x, y });
    setCtxVisible(true);
  };

  const closeCtx = () => { setCtxVisible(false); setShowEmoji(false); };

  const handleDelete = async () => {
    closeCtx();
    try {
      if (chatType === 'private') await deleteMessage(chatId, message.id);
      else if (chatType === 'group') await deleteGroupMessage(chatId, message.id);
      else await deleteChannelPost(chatId, message.id);
      removeMessage(message.id);
      toast.success('Сообщение удалено');
    } catch { toast.error('Не удалось удалить'); }
  };

  const handlePin = async () => {
    closeCtx();
    try {
      let res;
      if (chatType === 'private') res = await pinMessage(chatId, message.id);
      else if (chatType === 'group') res = await pinGroupMessage(chatId, message.id);
      else res = await pinChannelPost(chatId, message.id);
      updateMessage(res.data);
      toast.success('Сообщение закреплено');
    } catch { toast.error('Не удалось закрепить'); }
  };

  const handleReact = async (emoji) => {
    closeCtx();
    try {
      let res;
      if (chatType === 'private') res = await addReaction(chatId, message.id, { emoji });
      else if (chatType === 'group') res = await addGroupReaction(chatId, message.id, { emoji });
      else res = await addChannelReaction(chatId, message.id, { emoji });
      updateMessage(res.data);
    } catch {}
  };

  const handleCopyText = () => {
    if (message.text) {
      navigator.clipboard.writeText(message.text);
      toast.success('Скопировано');
    }
    closeCtx();
  };

  return (
    <>
      {/* Overlay для закрытия контекстного меню */}
      {(ctxVisible || showEmoji) && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 998 }} onClick={closeCtx} />
      )}

      {/* Контекстное меню */}
      {ctxVisible && (
        <div className="context-menu" style={{ top: ctxPos.y, left: ctxPos.x, zIndex: 1001 }}>
          {/* Эмодзи быстрые реакции сверху */}
          <div style={{ display: 'flex', gap: 4, padding: '6px 8px', borderBottom: '1px solid var(--border)' }}>
            {EMOJI_LIST.map(e => (
              <button key={e} onClick={() => handleReact(e)} style={{ fontSize: 18, padding: '4px', borderRadius: 8, transition: 'background 0.1s' }}
                onMouseEnter={ev => ev.currentTarget.style.background = 'var(--bg-hover)'}
                onMouseLeave={ev => ev.currentTarget.style.background = 'transparent'}
              >
                {e}
              </button>
            ))}
          </div>

          <div className="context-menu-item" onClick={() => { setReplyTo(message); closeCtx(); }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M10 9V5l-7 7 7 7v-4.1c5 0 8.5 1.6 11 5.1-1-5-4-10-11-11z"/></svg>
            Ответить
          </div>

          {message.text && (
            <div className="context-menu-item" onClick={handleCopyText}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>
              Копировать
            </div>
          )}

          {isOut && !message.poll && (
            <div className="context-menu-item" onClick={() => { setEditMessage(message); closeCtx(); }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>
              Редактировать
            </div>
          )}

          <div className="context-menu-item" onClick={handlePin}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/></svg>
            Закрепить
          </div>

          <div className="context-menu-divider" />

          {isOut && (
            <div className="context-menu-item danger" onClick={handleDelete}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
              Удалить
            </div>
          )}
        </div>
      )}

      {/* Сообщение */}
      <div
        className={`message-wrapper${isOut ? ' out' : ' in'}`}
        onContextMenu={handleContextMenu}
        onMouseEnter={() => setHovering(true)}
        onMouseLeave={() => setHovering(false)}
      >
        {/* Аватар в группах/каналах (входящее) */}
        {(isGroup || chatType === 'channel') && !isOut && (
          <div className="message-group-avatar">
            <Avatar src={senderAvatar} alt={senderName} size={30} />
          </div>
        )}

        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: isOut ? 'flex-end' : 'flex-start',
          maxWidth: message.media_url && !message.text ? '280px' : '65%',
        }}>
          {/* Имя в группах */}
          {(isGroup || chatType === 'channel') && !isOut && (
            <div className="bubble-sender-name" style={{ color, paddingLeft: 4, marginBottom: 2, fontSize: 12, fontWeight: 600 }}>
              {senderName}
            </div>
          )}

          <div className={`bubble${isOut ? ' out' : ' in'}`}>
            {/* Переслано */}
            {message.forwarded_from && (
              <div className="bubble-forwarded">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 8V4l8 8-8 8v-4H4V8h8z"/></svg>
                Переслано
              </div>
            )}

            {/* Цитата */}
            <ReplyPreview replyTo={message.reply_to} />

            {/* Медиа */}
            {message.media_url && (
              <MediaContent url={message.media_url} onClick={setMediaView} />
            )}

            {/* Опрос */}
            {message.poll && (
              <PollMessage poll={message.poll} messageId={message.id} />
            )}

            {/* Текст */}
            {message.text && (
              <div className="bubble-text">{message.text}</div>
            )}

            {/* Мета */}
            <div className="bubble-meta">
              {message.is_edited && <span className="bubble-edited">изм.</span>}
              <span className="bubble-time">{time}</span>
              {isOut && chatType === 'private' && (
                <span className={`bubble-ticks${message.is_read ? ' read' : ''}`}>
                  {message.is_read ? (
                    <svg width="16" height="11" viewBox="0 0 16 11" fill="currentColor">
                      <path d="M11.071.653a.75.75 0 00-1.142-.972L4.486 6.093 2.02 3.628a.75.75 0 00-1.061 1.06l3 3a.75.75 0 001.1-.087l5.012-6.948z"/>
                      <path d="M15.071.653a.75.75 0 00-1.142-.972L8.486 6.093l-.927-.927a.75.75 0 00-1.06 1.06l1.487 1.487a.75.75 0 001.1-.087l6.985-6.973z"/>
                    </svg>
                  ) : (
                    <svg width="11" height="11" viewBox="0 0 11 11" fill="currentColor">
                      <path d="M10.071.653a.75.75 0 00-1.142-.972L3.486 6.093.98 3.588a.75.75 0 00-1.06 1.06l3 3a.75.75 0 001.1-.087L10.07.653z"/>
                    </svg>
                  )}
                </span>
              )}
            </div>
          </div>

          {/* Реакции */}
          <Reactions
            reactions={message.reactions}
            chatId={chatId}
            chatType={chatType}
            messageId={message.id}
          />
        </div>

        {/* Кнопка быстрого ответа (при ховере) */}
        {hovering && (
          <button
            className="quick-reply-btn"
            style={{ [isOut ? 'right' : 'left']: '100%', marginLeft: isOut ? 0 : 4, marginRight: isOut ? 4 : 0 }}
            onClick={() => setReplyTo(message)}
            title="Ответить"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M10 9V5l-7 7 7 7v-4.1c5 0 8.5 1.6 11 5.1-1-5-4-10-11-11z"/></svg>
          </button>
        )}
      </div>
    </>
  );
}
