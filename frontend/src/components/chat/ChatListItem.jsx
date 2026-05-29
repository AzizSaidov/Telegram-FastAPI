import Avatar from '../ui/Avatar';
import { formatChatDate } from '../../hooks/useMediaUrl';
import useAuthStore from '../../store/authStore';

// Проверка прочитанности (только для личных чатов исходящих)
function Ticks({ isRead, isOut }) {
  if (!isOut) return null;
  return (
    <span className={`bubble-ticks ${isRead ? 'read' : 'unread'}`}>
      {isRead ? '✓✓' : '✓'}
    </span>
  );
}

export default function ChatListItem({ chat, isActive, onClick }) {
  const currentUser = useAuthStore((s) => s.user);
  const lastMsg = chat.last_message;
  const isMe = lastMsg?.sender?.id === currentUser?.id;

  // Превью текста
  let preview = 'Нет сообщений';
  if (lastMsg) {
    if (lastMsg.media_url && !lastMsg.text) preview = '📷 Медиафайл';
    else if (lastMsg.media_url && lastMsg.text) preview = lastMsg.text;
    else preview = lastMsg.text || '';
  }

  const time = formatChatDate(lastMsg?.created_at || chat.updated_at);

  // Для показа online только в личных
  const showOnline = chat.type === 'private' && chat.is_online;

  return (
    <div
      className={`chat-list-item${isActive ? ' active' : ''}`}
      onClick={onClick}
    >
      <div className="chat-list-avatar">
        <Avatar
          src={chat.avatar_url}
          alt={chat.title}
          size={48}
          online={showOnline}
        />
      </div>

      <div className="chat-list-body">
        <div className="chat-list-row1">
          <span className="chat-list-name">{chat.title}</span>
          <span className="chat-list-time">{time}</span>
        </div>

        <div className="chat-list-row2">
          <span className="chat-list-preview">
            {isMe && (
              <Ticks
                isOut={true}
                isRead={lastMsg?.is_read !== false}
              />
            )}{' '}
            {chat.type !== 'private' && lastMsg && !isMe && (
              <span className="sender-name">
                {lastMsg.sender?.profile?.full_name?.split(' ')[0]}:{' '}
              </span>
            )}
            {isMe && <span style={{ color: 'var(--text-secondary)' }}>Вы: </span>}
            {preview}
          </span>

          <div className="chat-list-meta">
            {chat.unread_count > 0 && (
              <span className="unread-badge">{chat.unread_count}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
