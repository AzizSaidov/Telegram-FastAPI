import { useEffect } from 'react';
import useAuthStore from '../store/authStore';
import useChatStore from '../store/chatStore';
import socketManager from '../socket/socket';

export default function useSocket() {
  const token = useAuthStore((s) => s.accessToken);
  const {
    addMessage,
    updateMessage,
    removeMessage,
    updateUnifiedChat,
    updateUserOnlineStatus,
    setTypingUser,
  } = useChatStore();

  const activeChat = useChatStore((s) => s.activeChat);

  useEffect(() => {
    if (!token) return;

    socketManager.connect(token);

    // Обработчики событий
    const onConnected = () => console.log('[WS] Connected');

    const onOnline = (data) => {
      updateUserOnlineStatus(data.user_id, true, null);
    };

    const onOffline = (data) => {
      updateUserOnlineStatus(data.user_id, false, data.last_seen);
    };

    const onMsgCreated = (data) => {
      // Добавляем только если активный чат совпадает
      if (activeChat && data.chat_id === activeChat.id) {
        addMessage(data.message || data);
      }
      // Обновляем превью в sidebar
      if (data.chat_id) {
        updateUnifiedChat(data.chat_id, 'private', {
          last_message: data.message || data,
          unread_count: activeChat?.id === data.chat_id ? 0 : undefined,
        });
      }
    };

    const onGroupMsgCreated = (data) => {
      if (activeChat && data.group_id === activeChat.id) {
        addMessage(data.message || data);
      }
      if (data.group_id) {
        updateUnifiedChat(data.group_id, 'group', {
          last_message: data.message || data,
        });
      }
    };

    const onChannelPostCreated = (data) => {
      if (activeChat && data.channel_id === activeChat.id) {
        addMessage(data.post || data);
      }
      if (data.channel_id) {
        updateUnifiedChat(data.channel_id, 'channel', {
          last_message: data.post || data,
        });
      }
    };

    const onMsgUpdated = (data) => updateMessage(data.message || data);
    const onMsgDeleted = (data) => removeMessage(data.message_id || data.id);

    const onTypingStarted = (data) => {
      setTypingUser(`${data.chat_type || 'private'}-${data.chat_id}`, data.user_id, true);
    };
    const onTypingStopped = (data) => {
      setTypingUser(`${data.chat_type || 'private'}-${data.chat_id}`, data.user_id, false);
    };

    // Регистрируем слушателей
    socketManager.on('connection_established', onConnected);
    socketManager.on('user_online', onOnline);
    socketManager.on('user_offline', onOffline);
    socketManager.on('message_created', onMsgCreated);
    socketManager.on('group_message_created', onGroupMsgCreated);
    socketManager.on('channel_post_created', onChannelPostCreated);
    socketManager.on('message_updated', onMsgUpdated);
    socketManager.on('channel_post_updated', onMsgUpdated);
    socketManager.on('message_deleted', onMsgDeleted);
    socketManager.on('channel_post_deleted', onMsgDeleted);
    socketManager.on('typing_started', onTypingStarted);
    socketManager.on('typing_stopped', onTypingStopped);

    return () => {
      socketManager.off('connection_established', onConnected);
      socketManager.off('user_online', onOnline);
      socketManager.off('user_offline', onOffline);
      socketManager.off('message_created', onMsgCreated);
      socketManager.off('group_message_created', onGroupMsgCreated);
      socketManager.off('channel_post_created', onChannelPostCreated);
      socketManager.off('message_updated', onMsgUpdated);
      socketManager.off('channel_post_updated', onMsgUpdated);
      socketManager.off('message_deleted', onMsgDeleted);
      socketManager.off('channel_post_deleted', onMsgDeleted);
      socketManager.off('typing_started', onTypingStarted);
      socketManager.off('typing_stopped', onTypingStopped);
    };
  }, [token, activeChat?.id]);
}
