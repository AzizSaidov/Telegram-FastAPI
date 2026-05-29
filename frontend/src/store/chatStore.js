import { create } from 'zustand';

const useChatStore = create((set, get) => ({
  unifiedChats: [],
  activeChat: null,
  activeChatType: null,
  messages: [],
  typingUsers: {},

  setUnifiedChats: (chats) => set({ unifiedChats: chats }),

  setActiveChat: (chat, type) =>
    set({ activeChat: chat, activeChatType: type, messages: [] }),

  clearActiveChat: () =>
    set({ activeChat: null, activeChatType: null, messages: [] }),

  setMessages: (messages) => set({ messages }),

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  updateMessage: (updatedMsg) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === updatedMsg.id ? updatedMsg : m
      ),
    })),

  removeMessage: (messageId) =>
    set((state) => ({
      messages: state.messages.filter((m) => m.id !== messageId),
    })),

  updateUnifiedChat: (chatId, chatType, updates) =>
    set((state) => ({
      unifiedChats: state.unifiedChats.map((c) =>
        c.id === chatId && c.type === chatType ? { ...c, ...updates } : c
      ),
    })),

  setTypingUser: (chatKey, userId, isTyping) =>
    set((state) => {
      const current = { ...state.typingUsers };

      if (isTyping) {
        if (!current[chatKey]) current[chatKey] = new Set();
        current[chatKey] = new Set([...current[chatKey], userId]);
      } else {
        if (current[chatKey]) {
          current[chatKey] = new Set(
            [...current[chatKey]].filter((id) => id !== userId)
          );
          if (current[chatKey].size === 0) delete current[chatKey];
        }
      }

      return { typingUsers: current };
    }),

  updateUserOnlineStatus: (userId, isOnline, lastSeen) =>
    set((state) => ({
      unifiedChats: state.unifiedChats.map((c) => {
        if (c.type === 'private' && c.user?.id === userId) {
          return { ...c, is_online: isOnline, last_seen: lastSeen };
        }
        return c;
      }),
    })),
}));

export default useChatStore;
