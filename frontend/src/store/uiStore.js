import { create } from 'zustand';

// UI-стейт: что открыто, какие панели видны
const useUIStore = create((set) => ({
  // Левое меню (гамбургер)
  hamburgerOpen: false,
  setHamburgerOpen: (v) => set({ hamburgerOpen: v }),

  // Профиль/настройки (заменяет сайдбар)
  profileOpen: false,
  setProfileOpen: (v) => set({ profileOpen: v }),

  // Правая панель инфо о чате
  chatInfoOpen: false,
  setChatInfoOpen: (v) => set({ chatInfoOpen: v }),

  // Уведомления
  notifOpen: false,
  setNotifOpen: (v) => set({ notifOpen: v }),

  // Реплай (отвечаем на сообщение)
  replyTo: null,
  setReplyTo: (msg) => set({ replyTo: msg }),
  clearReplyTo: () => set({ replyTo: null }),

  // Редактирование
  editMessage: null,
  setEditMessage: (msg) => set({ editMessage: msg }),
  clearEditMessage: () => set({ editMessage: null }),

  // Полноэкранный просмотр медиа
  mediaView: null,
  setMediaView: (url) => set({ mediaView: url }),
  clearMediaView: () => set({ mediaView: null }),

  // Контекстное меню
  contextMenu: null, // { x, y, message, type }
  setContextMenu: (menu) => set({ contextMenu: menu }),
  clearContextMenu: () => set({ contextMenu: null }),

  // Вкладка сайдбара
  sidebarTab: 'all', // 'all' | 'private' | 'group' | 'channel'
  setSidebarTab: (tab) => set({ sidebarTab: tab }),

  // Поиск
  searchQuery: '',
  setSearchQuery: (q) => set({ searchQuery: q }),

  // Форвард
  forwardMessage: null,
  setForwardMessage: (msg) => set({ forwardMessage: msg }),
  clearForwardMessage: () => set({ forwardMessage: null }),
}));

export default useUIStore;
