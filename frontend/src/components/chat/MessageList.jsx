import { useEffect, useRef } from 'react';
import useChatStore from '../../store/chatStore';
import useAuthStore from '../../store/authStore';
import MessageBubble from './MessageBubble';
import DateSeparator from './DateSeparator';
import TypingIndicator from './TypingIndicator';
import Spinner from '../ui/Spinner';

function isSameDay(a, b) {
  const da = new Date(a), db = new Date(b);
  return da.getFullYear() === db.getFullYear() &&
    da.getMonth() === db.getMonth() &&
    da.getDate() === db.getDate();
}

export default function MessageList({ chatId, chatType, loading }) {
  const messages = useChatStore((s) => s.messages);
  const typingUsers = useChatStore((s) => s.typingUsers);
  const bottomRef = useRef(null);
  const isGroup = chatType === 'group';

  // Авто-скролл вниз при новом сообщении
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  // Типающие пользователи для этого чата
  const chatKey = `${chatType}-${chatId}`;
  const typingSet = typingUsers[chatKey];
  const typingNames = typingSet ? [...typingSet].map((id) => `User ${id}`) : [];

  if (loading) {
    return (
      <div className="message-list flex-center">
        <Spinner size={36} />
      </div>
    );
  }

  return (
    <div className="message-list">
      {messages.map((msg, i) => {
        const prev = messages[i - 1];
        const showDate = !prev || !isSameDay(prev.created_at, msg.created_at);
        return (
          <div key={msg.id}>
            {showDate && <DateSeparator date={msg.created_at} />}
            <MessageBubble
              message={msg}
              chatType={chatType}
              chatId={chatId}
              isGroup={isGroup}
            />
          </div>
        );
      })}

      {typingNames.length > 0 && <TypingIndicator names={typingNames} />}

      <div ref={bottomRef} />
    </div>
  );
}
