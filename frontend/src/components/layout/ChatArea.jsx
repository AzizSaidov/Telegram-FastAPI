import { useEffect, useState, useCallback } from 'react';
import TopBar from './TopBar';
import MessageList from '../chat/MessageList';
import InputPanel from '../input/InputPanel';
import useChatStore from '../../store/chatStore';
import useAuthStore from '../../store/authStore';
import { getChatMessages } from '../../api/chats';
import { getGroupMessages, getGroupDetail } from '../../api/groups';
import { getChannelPosts, getChannelDetail } from '../../api/channels';

export default function ChatArea() {
  const activeChat = useChatStore((s) => s.activeChat);
  const { setMessages } = useChatStore();
  const currentUser = useAuthStore((s) => s.user);
  const [loading, setLoading] = useState(false);
  const [currentUserRole, setCurrentUserRole] = useState('member');

  const chatId = activeChat?.id;
  const chatType = activeChat?.type;

  const loadMessages = useCallback(async () => {
    if (!chatId || !chatType) return;
    setLoading(true);
    try {
      let res;
      if (chatType === 'private') {
        res = await getChatMessages(chatId, { limit: 50, offset: 0 });
      } else if (chatType === 'group') {
        res = await getGroupMessages(chatId, { limit: 50, offset: 0 });
        // Узнаём роль
        try {
          const detail = await getGroupDetail(chatId);
          const me = detail.data.members?.find(m => m.user?.id === currentUser?.id);
          if (me) setCurrentUserRole(me.role || 'member');
        } catch {}
      } else if (chatType === 'channel') {
        res = await getChannelPosts(chatId, { limit: 50, offset: 0 });
        // Узнаём роль в канале
        try {
          const detail = await getChannelDetail(chatId);
          const me = detail.data.members?.find(m => m.user?.id === currentUser?.id);
          if (me) setCurrentUserRole(me.role || 'subscriber');
        } catch {}
      }
      // API отдаёт newest first → разворачиваем
      const msgs = res?.data || [];
      setMessages([...msgs].reverse());
    } finally {
      setLoading(false);
    }
  }, [chatId, chatType]);

  useEffect(() => {
    setMessages([]);
    loadMessages();
  }, [chatId, chatType]);

  if (!activeChat) return null;

  return (
    <>
      <TopBar />
      <MessageList chatId={chatId} chatType={chatType} loading={loading} />
      <InputPanel chatId={chatId} chatType={chatType} currentUserRole={currentUserRole} />
    </>
  );
}
