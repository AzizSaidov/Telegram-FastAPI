import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import { logout as logoutRequest, searchUsers } from '../api/auth';
import { blockUser, getBlockedUsers, unblockUser } from '../api/blocks';
import {
  addChannelMember,
  addChannelReaction,
  createChannel,
  createChannelPost,
  deleteChannel,
  deleteChannelPost,
  unpinChannelPost,
  editChannelPost,
  getChannelDetail,
  getChannelPosts,
  makeChannelAdmin,
  pinChannelPost,
  removeChannelMember,
  searchChannels,
  subscribeChannel,
  unsubscribeChannel,
  updateChannel,
} from '../api/channels';
import {
  addReaction,
  createChat,
  deleteChat,
  deleteMessage,
  unpinMessage,
  editMessage,
  getChatMessages,
  getUnifiedChats,
  pinMessage,
  searchChats,
  sendMessage,
} from '../api/chats';
import { addContact, deleteContact, getContacts } from '../api/contacts';
import {
  addGroupMember,
  addGroupReaction,
  createGroup,
  deleteGroup,
  deleteGroupMessage,
  unpinGroupMessage,
  editGroupMessage,
  getGroupDetail,
  getGroupMessages,
  makeGroupAdmin,
  pinGroupMessage,
  removeGroupMember,
  sendGroupMessage,
  updateGroup,
} from '../api/groups';
import { getNotifications, markAllAsRead, markAsRead } from '../api/notifications';
import { createPoll, votePoll } from '../api/polls';
import { getMyProfile, updateMyProfile } from '../api/profiles';
import { createStory, getStories, getStoryViews, viewStory } from '../api/stories';
import { formatChatDate, formatLastSeen, formatSeparatorDate, formatTime, mediaUrl, nameColor } from '../hooks/useMediaUrl';
import socketManager from '../socket/socket';
import useAuthStore from '../store/authStore';

const TABS = [
  { key: 'all', label: 'Все' },
  { key: 'private', label: 'Личные' },
  { key: 'group', label: 'Группы' },
  { key: 'channel', label: 'Каналы' },
];

const QUICK_REACTIONS = ['👍', '❤️', '🔥', '🎉', '👀'];

const EMPTY_COMPOSE = {
  open: false,
  mode: 'private',
  query: '',
  results: [],
  loading: false,
  name: '',
  description: '',
  isPublic: true,
  avatar: null,
};

function Icon({ name, size = 22 }) {
  const paths = {
    add: 'M12 5v14M5 12h14',
    archive: 'M4 7h16v12H4z M3 5h18 M9 11h6',
    back: 'M15 18l-6-6 6-6',
    bell: 'M18 16v-5a6 6 0 0 0-12 0v5l-2 2h16l-2-2z M10 20h4',
    block: 'M7 7l10 10 M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z',
    camera: 'M4 7h3l2-3h6l2 3h3v13H4z M9 13a3 3 0 1 0 6 0 3 3 0 0 0-6 0z',
    channel: 'M4 11l16-7-5 16-3-7-8-2z',
    check: 'M5 13l4 4L19 7',
    close: 'M6 6l12 12M18 6 6 18',
    contacts: 'M16 11a4 4 0 1 0-8 0 M4 21a8 8 0 0 1 16 0',
    delete: 'M5 7h14M9 7V5h6v2M8 7l1 13h6l1-13',
    dots: 'M12 6h.01M12 12h.01M12 18h.01',
    edit: 'M4 20h4L19 9l-4-4L4 16v4z M13 7l4 4',
    forward: 'M13 6l6 6-6 6v-4H5v-4h8V6z',
    group: 'M8 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M2 21a6 6 0 0 1 12 0 M17 11a3 3 0 1 0 0-6 M15 21a5 5 0 0 1 5-5',
    image: 'M4 5h16v14H4z M8 13l2-2 3 3 2-3 3 4 M8 9h.01',
    info: 'M12 16v-4M12 8h.01 M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z',
    lock: 'M7 11V8a5 5 0 0 1 10 0v3 M6 11h12v10H6z',
    logout: 'M10 17l5-5-5-5M15 12H3M21 4v16',
    menu: 'M4 7h16M4 12h16M4 17h16',
    mic: 'M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3z M19 11a7 7 0 0 1-14 0 M12 18v3',
    moon: 'M21 12.8A8.5 8.5 0 1 1 11.2 3 7 7 0 0 0 21 12.8z',
    paperclip: 'M21 12.5l-8.5 8.5a5 5 0 0 1-7-7L15 4.5a3 3 0 0 1 4.2 4.2l-9.5 9.5a1 1 0 0 1-1.4-1.4l8.4-8.4',
    pin: 'M14 4l6 6-4 1-4 7-2-2 7-4 1-4-6-6-1 4-7 4-2-2 4-7z',
    poll: 'M5 19V9M12 19V5M19 19v-7',
    reply: 'M10 8l-5 4 5 4v-3h5a5 5 0 0 1 5 5v1',
    save: 'M5 5h12l2 2v12H5z M8 5v6h8V5 M8 19v-5h8v5',
    search: 'M11 19a8 8 0 1 1 5.7-2.3L21 21',
    send: 'M4 20l16-8L4 4v6l9 2-9 2v6z',
    settings: 'M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2 3-.2-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V21h-4v-.2a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.9.3l-.2.1-2-3 .1-.1A1.7 1.7 0 0 0 5 15a1.7 1.7 0 0 0-1.5-1H3v-4h.5A1.7 1.7 0 0 0 5 9a1.7 1.7 0 0 0-.3-1.9l-.1-.1 2-3 .2.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.5V3h4v.2a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.2-.1 2 3-.1.1A1.7 1.7 0 0 0 19 9c.3.6.9 1 1.5 1H21v4h-.5a1.7 1.7 0 0 0-1.1 1z',
    user: 'M12 12a5 5 0 1 0 0-10 5 5 0 0 0 0 10z M4 22a8 8 0 0 1 16 0',
    wallet: 'M4 7h16v12H4z M16 12h4 M6 7V5h11',
  };

  return (
    <svg className="icon" width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
      <path d={paths[name]} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function getProfile(entity) {
  return entity?.profile || entity || {};
}

function displayName(entity, fallback = 'Без имени') {
  const profile = getProfile(entity);
  return profile.full_name || profile.username || fallback;
}

function initialsFrom(text) {
  return String(text || 'TG')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase();
}

function chatTitle(chat) {
  return chat?.title || chat?.name || displayName(chat?.user, 'Telegram');
}

function chatAvatar(chat) {
  return chat?.avatar_url || chat?.user?.profile?.avatar_url || null;
}

function isVideo(url) {
  return /\.(mp4|webm|mov)$/i.test(url || '');
}

function firstPlayableStoryIndex(group) {
  const stories = group?.stories || [];
  const firstUnseen = stories.findIndex((story) => !story.is_viewed_by_me);
  return firstUnseen >= 0 ? firstUnseen : 0;
}

function Avatar({ entity, title, size = 48, className = '', style: extraStyle }) {
  const profile = getProfile(entity);
  const image = mediaUrl(profile.avatar_url || entity?.avatar_url);
  const label = title || displayName(entity);
  const color = nameColor(entity?.id || profile?.user?.id || label.length);

  return (
    <span
      className={`avatar ${className}`}
      style={{
        width: `${size}px`,
        height: `${size}px`,
        minWidth: `${size}px`,
        minHeight: `${size}px`,
        fontSize: `${Math.round(size * 0.38)}px`,
        borderRadius: '50%',
        overflow: 'hidden',
        '--avatar-color': color,
        ...extraStyle,
      }}
    >
      <span className="avatar-text">{initialsFrom(label)}</span>
      {image && (
        <img
          src={image}
          alt=""
          style={{
            width: `${size}px`,
            height: `${size}px`,
            minWidth: `${size}px`,
            borderRadius: '50%',
            objectFit: 'cover',
            display: 'block',
          }}
          onError={(e) => { e.currentTarget.style.display = 'none'; }}
        />
      )}
      {profile.is_online && <i />}
    </span>
  );
}

function Spinner() {
  return <span className="loader" aria-label="Загрузка" />;
}

function groupReactions(reactions = []) {
  const map = new Map();
  reactions.forEach((reaction) => {
    const item = map.get(reaction.emoji) || { emoji: reaction.emoji, count: 0, users: [] };
    item.count += 1;
    item.users.push(reaction.user);
    map.set(reaction.emoji, item);
  });
  return [...map.values()];
}

function messageText(message) {
  if (!message) return '';
  if (message.text) return message.text;
  if (message.media_url) return 'Медиа';
  if (message.poll) return message.poll.question;
  return '';
}

function isSameDay(a, b) {
  if (!a || !b) return false;
  return new Date(a).toDateString() === new Date(b).toDateString();
}

export default function MainPage() {
  const currentUser = useAuthStore((state) => state.user);
  const accessToken = useAuthStore((state) => state.accessToken);
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const updateAuthUser = useAuthStore((state) => state.updateUser);

  const [profile, setProfile] = useState(null);
  const [profileDraft, setProfileDraft] = useState({ full_name: '', username: '', bio: '', avatar: null });
  const [chats, setChats] = useState([]);
  const [active, setActive] = useState(null);
  const [activeDetail, setActiveDetail] = useState(null);
  const [messages, setMessages] = useState([]);
  const [stories, setStories] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [blocked, setBlocked] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [sidebarTab, setSidebarTab] = useState('all');
  const [sidebarView, setSidebarView] = useState('chats');
  const [sidebarSearch, setSidebarSearch] = useState('');
  const [chatSearch, setChatSearch] = useState('');
  const [chatSearchOpen, setChatSearchOpen] = useState(false);
  const [loadingChats, setLoadingChats] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [infoOpen, setInfoOpen] = useState(false);
  const [compose, setCompose] = useState(EMPTY_COMPOSE);
  const [storyViewer, setStoryViewer] = useState(null);
  const [storyViews, setStoryViews] = useState([]);
  const [mediaViewer, setMediaViewer] = useState(null);
  const [replyTo, setReplyTo] = useState(null);
  const [editing, setEditing] = useState(null);
  const [forwarding, setForwarding] = useState(null);
  const [focusedMessageId, setFocusedMessageId] = useState(null);
  const [inputText, setInputText] = useState('');
  const [inputFile, setInputFile] = useState(null);
  const [contactForm, setContactForm] = useState({ username: '', name: '' });
  const [contactQuery, setContactQuery] = useState('');
  const [contactResults, setContactResults] = useState([]);
  const [contactSearching, setContactSearching] = useState(false);
  const [blockForm, setBlockForm] = useState('');
  const [showMemberPicker, setShowMemberPicker] = useState(false);
  const [detailDraft, setDetailDraft] = useState({ name: '', description: '', is_public: true, avatar: null });
  const [pollDraft, setPollDraft] = useState(null);
  const [typingUsers, setTypingUsers] = useState([]);
  const [confirmDialog, setConfirmDialog] = useState(null);

  const storyInputRef = useRef(null);
  const inputFileRef = useRef(null);
  const textareaRef = useRef(null);
  const messagesEndRef = useRef(null);
  const searchTimerRef = useRef(null);

  const activeKey = active ? `${active.type}-${active.id}` : '';
  const activeRole = activeDetail?.current_user_role || active?.current_user_role || null;
  const isAdmin = activeRole === 'admin';
  const unreadNotifications = notifications.filter((item) => !item.is_read).length;
  const isOwnStoryGroup = useCallback((group) => (
    Boolean(group?.is_me || group?.user?.id === currentUser?.id)
  ), [currentUser?.id]);

  const markStoryViewedLocally = useCallback((storyId) => {
    setStories((groups) => groups.map((group) => {
      const isOwn = isOwnStoryGroup(group);
      const nextStories = (group.stories || []).map((story) => (
        story.id === storyId ? { ...story, is_viewed_by_me: true } : story
      ));

      return {
        ...group,
        stories: nextStories,
        has_unviewed: isOwn ? false : nextStories.some((story) => !story.is_viewed_by_me),
      };
    }));

    setStoryViewer((viewer) => {
      if (!viewer) return viewer;

      const isOwn = isOwnStoryGroup(viewer.group);
      const nextStories = (viewer.group.stories || []).map((story) => (
        story.id === storyId ? { ...story, is_viewed_by_me: true } : story
      ));

      return {
        ...viewer,
        group: {
          ...viewer.group,
          stories: nextStories,
          has_unviewed: isOwn ? false : nextStories.some((story) => !story.is_viewed_by_me),
        },
      };
    });
  }, [isOwnStoryGroup]);

  const loadChats = useCallback(async (query = sidebarSearch) => {
    setLoadingChats(true);
    try {
      const response = query.trim() ? await searchChats(query.trim()) : await getUnifiedChats();
      setChats(Array.isArray(response.data) ? response.data : []);
    } catch {
      toast.error('Не удалось загрузить чаты');
    } finally {
      setLoadingChats(false);
    }
  }, [sidebarSearch]);

  const loadProfile = useCallback(async () => {
    const response = await getMyProfile();
    setProfile(response.data);
    setProfileDraft({
      full_name: response.data?.full_name || '',
      username: response.data?.username || '',
      bio: response.data?.bio || '',
      avatar: null,
    });
  }, []);

  const loadStories = useCallback(async () => {
    try {
      const response = await getStories({ limit: 80, offset: 0 });
      setStories(Array.isArray(response.data) ? response.data : []);
    } catch {
      setStories([]);
    }
  }, []);

  const loadContacts = useCallback(async () => {
    try {
      const response = await getContacts();
      setContacts(Array.isArray(response.data) ? response.data : []);
    } catch {
      setContacts([]);
    }
  }, []);

  const loadBlocked = useCallback(async () => {
    try {
      const response = await getBlockedUsers();
      setBlocked(Array.isArray(response.data) ? response.data : []);
    } catch {
      setBlocked([]);
    }
  }, []);

  const loadNotifications = useCallback(async () => {
    try {
      const response = await getNotifications({ limit: 80, offset: 0 });
      setNotifications(Array.isArray(response.data) ? response.data : []);
    } catch {
      setNotifications([]);
    }
  }, []);

  const silentRefreshMessages = useCallback(async () => {
    if (!active) return;
    try {
      if (active.type === 'private') {
        const r = await getChatMessages(active.id, { limit: 100, offset: 0 });
        setMessages([...(r.data || [])].reverse());
      }
      if (active.type === 'group') {
        const r = await getGroupMessages(active.id, { limit: 100, offset: 0 });
        setMessages([...(r.data || [])].reverse());
      }
      if (active.type === 'channel') {
        const r = await getChannelPosts(active.id, { limit: 100, offset: 0 });
        setMessages([...(r.data || [])].reverse());
      }
    } catch {}
  }, [active]);

  const loadActiveData = useCallback(async () => {
    if (!active) return;

    setLoadingMessages(true);
    setMessages([]);
    setActiveDetail(null);

    try {
      if (active.type === 'private') {
        const response = await getChatMessages(active.id, { limit: 100, offset: 0 });
        setMessages([...(response.data || [])].reverse());
        setActiveDetail(active);
      }

      if (active.type === 'group') {
        const [messagesResponse, detailResponse] = await Promise.all([
          getGroupMessages(active.id, { limit: 100, offset: 0 }),
          getGroupDetail(active.id),
        ]);
        setMessages([...(messagesResponse.data || [])].reverse());
        setActiveDetail(detailResponse.data);
      }

      if (active.type === 'channel') {
        const [postsResponse, detailResponse] = await Promise.all([
          getChannelPosts(active.id, { limit: 100, offset: 0 }),
          getChannelDetail(active.id),
        ]);
        setMessages([...(postsResponse.data || [])].reverse());
        setActiveDetail(detailResponse.data);
      }
    } catch {
      toast.error('Не удалось открыть чат');
    } finally {
      setLoadingMessages(false);
    }
  }, [active]);

  useEffect(() => {
    loadProfile().catch(() => toast.error('Не удалось загрузить профиль'));
    loadChats('');
    loadStories();
    loadContacts();
    loadBlocked();
    loadNotifications();
  }, []);

  useEffect(() => {
    clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(() => loadChats(sidebarSearch), sidebarSearch.trim() ? 250 : 0);
    return () => clearTimeout(searchTimerRef.current);
  }, [sidebarSearch, loadChats]);

  useEffect(() => {
    setReplyTo(null);
    setEditing(null);
    setInputText('');
    setInputFile(null);
    setChatSearch('');
    setChatSearchOpen(false);
    loadActiveData();
  }, [activeKey, loadActiveData]);

  useEffect(() => {
    if (!active || loadingMessages || messages.length === 0) return;
    requestAnimationFrame(() => {
      messagesEndRef.current?.scrollIntoView({ block: 'end' });
    });
  }, [active, loadingMessages, messages.length]);

  useEffect(() => {
    if (!activeDetail) return;

    setDetailDraft({
      name: activeDetail.name || activeDetail.title || '',
      description: activeDetail.description || '',
      is_public: activeDetail.is_public ?? true,
      avatar: null,
    });
  }, [activeDetail]);

  useEffect(() => {
    if (!accessToken) return undefined;

    socketManager.connect(accessToken);

    const refreshActive = (data = {}) => {
      const matchesPrivate = active?.type === 'private' && data.chat_id === active.id;
      const matchesGroup = active?.type === 'group' && data.group_id === active.id;
      const matchesChannel = active?.type === 'channel' && data.channel_id === active.id;

      loadChats(sidebarSearch);
      if (matchesPrivate || matchesGroup || matchesChannel) loadActiveData();
    };

    const updateOnline = (data) => {
      setChats((items) => items.map((item) => {
        if (item.type !== 'private' || item.user?.id !== data.user_id) return item;
        return { ...item, is_online: data.is_online, last_seen: data.last_seen };
      }));
    };

    const typingStarted = (data) => {
      if (!active || data.chat_id !== active.id) return;
      setTypingUsers((items) => [...new Set([...items, data.from_user_id])]);
    };

    const typingStopped = (data) => {
      setTypingUsers((items) => items.filter((id) => id !== data.from_user_id));
    };

    socketManager.on('message_created', refreshActive);
    socketManager.on('group_message_created', refreshActive);
    socketManager.on('channel_post_created', refreshActive);
    socketManager.on('message_updated', refreshActive);
    socketManager.on('channel_post_updated', refreshActive);
    socketManager.on('message_deleted', refreshActive);
    socketManager.on('channel_post_deleted', refreshActive);
    socketManager.on('reaction_created', refreshActive);
    socketManager.on('user_online', (data) => updateOnline({ ...data, is_online: true }));
    socketManager.on('user_offline', (data) => updateOnline({ ...data, is_online: false }));
    socketManager.on('typing_started', typingStarted);
    socketManager.on('typing_stopped', typingStopped);

    return () => {
      socketManager.off('message_created', refreshActive);
      socketManager.off('group_message_created', refreshActive);
      socketManager.off('channel_post_created', refreshActive);
      socketManager.off('message_updated', refreshActive);
      socketManager.off('channel_post_updated', refreshActive);
      socketManager.off('message_deleted', refreshActive);
      socketManager.off('channel_post_deleted', refreshActive);
      socketManager.off('reaction_created', refreshActive);
      socketManager.off('typing_started', typingStarted);
      socketManager.off('typing_stopped', typingStopped);
    };
  }, [accessToken, active, loadActiveData, loadChats, sidebarSearch]);

  const filteredChats = useMemo(() => {
    if (sidebarTab === 'all') return chats;
    return chats.filter((item) => item.type === sidebarTab);
  }, [chats, sidebarTab]);

  const tabCounts = useMemo(() => ({
    all: chats.reduce((sum, item) => sum + (item.unread_count || 0), 0),
    private: chats.filter((item) => item.type === 'private' && item.unread_count > 0).length,
    group: chats.filter((item) => item.type === 'group' && item.unread_count > 0).length,
    channel: chats.filter((item) => item.type === 'channel' && item.unread_count > 0).length,
  }), [chats]);

  const visibleMessages = useMemo(() => {
    const query = chatSearch.trim().toLowerCase();
    if (!query) return messages;
    return messages.filter((message) => messageText(message).toLowerCase().includes(query));
  }, [messages, chatSearch]);

  const pinnedMessage = useMemo(() => messages.find((message) => message.is_pinned), [messages]);

  const openChat = (chat) => {
    setActive(chat);
    setSidebarView('chats');
    setMenuOpen(false);
  };

  const focusMessage = (messageId) => {
    setFocusedMessageId(messageId);
    requestAnimationFrame(() => {
      document.getElementById(`message-${messageId}`)?.scrollIntoView({ block: 'center', behavior: 'smooth' });
    });
    window.setTimeout(() => setFocusedMessageId(null), 1600);
  };

  const openCompose = (mode = 'private') => {
    setCompose({ ...EMPTY_COMPOSE, open: true, mode });
    setMenuOpen(false);
  };

  const closeCompose = () => setCompose(EMPTY_COMPOSE);

  const handleComposeSearch = async () => {
    const query = compose.query.trim();
    if (!query) return;

    setCompose((state) => ({ ...state, loading: true }));
    try {
      const response = compose.mode === 'join'
        ? await searchChannels(query)
        : await searchUsers(query);
      setCompose((state) => ({ ...state, results: Array.isArray(response.data) ? response.data : [] }));
    } finally {
      setCompose((state) => ({ ...state, loading: false }));
    }
  };

  const startPrivateChat = async (target) => {
    const payload = typeof target === 'object'
      ? { user_id: target.id }
      : { username: target };

    if (!payload.user_id && !payload.username) return;

    const response = await createChat(payload);
    await loadChats('');
    const chat = {
      ...response.data,
      type: 'private',
      title: displayName(response.data?.other_user),
      user: response.data?.other_user,
      avatar_url: response.data?.other_user?.profile?.avatar_url,
    };
    openChat(chat);
    closeCompose();
  };

  const createNewGroup = async () => {
    if (compose.name.trim().length < 2) {
      toast.error('Название группы слишком короткое');
      return;
    }

    const formData = new FormData();
    formData.append('name', compose.name.trim());
    if (compose.description.trim()) formData.append('description', compose.description.trim());
    if (compose.avatar) formData.append('avatar', compose.avatar);

    const response = await createGroup(formData);
    await loadChats('');
    openChat({ ...response.data, type: 'group', title: response.data.name });
    closeCompose();
  };

  const createNewChannel = async () => {
    if (compose.name.trim().length < 2) {
      toast.error('Название канала слишком короткое');
      return;
    }

    const formData = new FormData();
    formData.append('name', compose.name.trim());
    formData.append('is_public', String(compose.isPublic));
    if (compose.description.trim()) formData.append('description', compose.description.trim());
    if (compose.avatar) formData.append('avatar', compose.avatar);

    const response = await createChannel(formData);
    await loadChats('');
    openChat({ ...response.data, type: 'channel', title: response.data.name });
    closeCompose();
  };

  const subscribeAndOpen = async (channel) => {
    if (!channel.current_user_role) await subscribeChannel(channel.id);
    await loadChats('');
    openChat({ ...channel, type: 'channel', title: channel.name });
    closeCompose();
  };

  const saveProfile = async (event) => {
    event.preventDefault();

    const formData = new FormData();
    if (profileDraft.full_name.trim()) formData.append('full_name', profileDraft.full_name.trim());
    if (profileDraft.username.trim()) formData.append('username', profileDraft.username.trim());
    formData.append('bio', profileDraft.bio.trim());
    if (profileDraft.avatar) formData.append('avatar', profileDraft.avatar);

    const response = await updateMyProfile(formData);
    setProfile(response.data);
    setProfileDraft({
      full_name: response.data?.full_name || '',
      username: response.data?.username || '',
      bio: response.data?.bio || '',
      avatar: null,
    });
    updateAuthUser({ profile: response.data });
    toast.success('Профиль сохранён');
  };

  const logout = async () => {
    try {
      await logoutRequest();
    } catch {
      // Local logout still completes when the access token has already expired.
    }
    socketManager.disconnect();
    clearAuth();
  };

  const sendTyping = (typing) => {
    if (!active || active.type !== 'private') return;
    const toUserId = active.user?.id;
    if (!toUserId) return;
    socketManager.send(typing ? 'typing_started' : 'typing_stopped', {
      chat_id: active.id,
      chat_type: active.type,
      to_user_ids: [toUserId],
    });
  };

  const submitMessage = async (event) => {
    event.preventDefault();
    if (!active) return;

    const text = inputText.trim();
    if (!text && !inputFile && !editing) return;

    try {
      if (editing) {
        if (active.type === 'private') await editMessage(active.id, editing.id, { text });
        if (active.type === 'group') await editGroupMessage(active.id, editing.id, { text });
        if (active.type === 'channel') await editChannelPost(active.id, editing.id, { text });
        setEditing(null);
      } else {
        const formData = new FormData();
        if (text) formData.append('text', text);
        if (inputFile) formData.append('media', inputFile);
        if (replyTo && active.type !== 'channel') formData.append('reply_to_id', replyTo.id);

        if (active.type === 'private') await sendMessage(active.id, formData);
        if (active.type === 'group') await sendGroupMessage(active.id, formData);
        if (active.type === 'channel') await createChannelPost(active.id, formData);
      }

      setInputText('');
      setInputFile(null);
      setReplyTo(null);
      sendTyping(false);
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
        textareaRef.current.style.overflowY = 'hidden';
      }
      await loadActiveData();
      await loadChats(sidebarSearch);
    } catch {
      toast.error('Сообщение не отправлено');
    }
  };

  const canEditMessage = (message) => {
    if (!active || !message) return false;
    const mine = message.sender?.id === currentUser?.id || message.sender_id === currentUser?.id;
    if (active.type === 'channel') return isAdmin;
    return mine;
  };

  const canDeleteMessage = (message) => {
    if (!active || !message) return false;
    const mine = message.sender?.id === currentUser?.id || message.sender_id === currentUser?.id;
    if (active.type === 'channel') return isAdmin;
    if (active.type === 'group') return mine || isAdmin;
    return mine;
  };

  const canPinMessage = () => {
    if (!active) return false;
    if (active.type === 'private') return true;
    return isAdmin;
  };

  const reactToMessage = async (message, emoji) => {
    if (active.type === 'private') await addReaction(active.id, message.id, { emoji });
    if (active.type === 'group') await addGroupReaction(active.id, message.id, { emoji });
    if (active.type === 'channel') await addChannelReaction(active.id, message.id, { emoji });
    await silentRefreshMessages();
  };

  const removeMessage = (message) => {
    setConfirmDialog({
      message: 'Удалить сообщение?',
      onConfirm: async () => {
        setMessages((prev) => prev.filter((m) => m.id !== message.id));
        if (active.type === 'private') await deleteMessage(active.id, message.id);
        if (active.type === 'group') await deleteGroupMessage(active.id, message.id);
        if (active.type === 'channel') await deleteChannelPost(active.id, message.id);
        await silentRefreshMessages();
        await loadChats(sidebarSearch);
      },
    });
  };

  const pinActiveMessage = async (message) => {
    if (active.type === 'private') await pinMessage(active.id, message.id);
    if (active.type === 'group') await pinGroupMessage(active.id, message.id);
    if (active.type === 'channel') await pinChannelPost(active.id, message.id);
    await loadActiveData();
  };

  const unpinActiveMessage = async (messageId) => {
    if (!active) return;
    if (active.type === 'private') await unpinMessage(active.id, messageId);
    if (active.type === 'group') await unpinGroupMessage(active.id, messageId);
    if (active.type === 'channel') await unpinChannelPost(active.id, messageId);
    await loadActiveData();
  };

  const forwardToChat = async (target) => {
    if (!forwarding || !active) return;

    const formData = new FormData();
    formData.append('forwarded_from_id', forwarding.id);

    if (active.type === 'private') await sendMessage(target.id, formData);
    if (active.type === 'group') await sendGroupMessage(target.id, formData);

    setForwarding(null);
    await loadChats(sidebarSearch);
    toast.success('Сообщение переслано');
  };

  const createPollForPost = async (event) => {
    event.preventDefault();
    if (!pollDraft) return;

    const options = pollDraft.options.map((o) => o.trim()).filter(Boolean);

    if (pollDraft.question.trim().length < 2 || options.length < 2) {
      toast.error('Нужен вопрос и минимум два варианта');
      return;
    }

    try {
      let postId = pollDraft.post?.id;

      if (!postId) {
        const formData = new FormData();
        formData.append('text', pollDraft.question.trim());
        const postResponse = await createChannelPost(active.id, formData);
        postId = postResponse.data.id;
      }

      await createPoll(active.id, postId, { question: pollDraft.question.trim(), options });
      setPollDraft(null);
      await loadActiveData();
      await loadChats(sidebarSearch);
      toast.success('Опрос опубликован');
    } catch {
      toast.error('Не удалось создать опрос');
    }
  };

  const voteInPoll = async (pollId, optionId) => {
    await votePoll(pollId, { option_id: optionId });
    await loadActiveData();
  };

  const createNewStory = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;

    try {
      const formData = new FormData();
      formData.append('media', file);
      await createStory(formData);
      await loadStories();
      toast.success('История добавлена');
    } catch {
      toast.error('Не удалось добавить историю');
    }
  };

  const openStory = async (group, index = 0) => {
    const storiesInGroup = group.stories || [];
    const safeIndex = Math.max(0, Math.min(index, storiesInGroup.length - 1));
    const story = storiesInGroup[safeIndex];
    if (!story) return;
    const isOwn = isOwnStoryGroup(group);

    setStoryViewer({ group, index: safeIndex });

    try {
      if (isOwn) {
        const response = await getStoryViews(story.id);
        setStoryViews(Array.isArray(response.data) ? response.data : []);
        return;
      }

      const unviewed = (group.stories || []).filter((s) => !s.is_viewed_by_me);
      unviewed.forEach((s) => {
        markStoryViewedLocally(s.id);
        viewStory(s.id).catch(() => {});
      });

      setStoryViews([]);
    } catch {
      setStoryViews([]);
    }
  };

  const closeStoryViewer = useCallback(() => {
    setStoryViewer(null);
  }, []);

  const changeStory = (direction) => {
    if (!storyViewer) return;
    const nextIndex = storyViewer.index + direction;
    if (nextIndex < 0 || nextIndex >= storyViewer.group.stories.length) {
      closeStoryViewer();
      return;
    }
    openStory(storyViewer.group, nextIndex);
  };

  const addNewContact = async (event) => {
    event.preventDefault();
    if (!contactForm.username.trim()) return;
    await addContact({
      username: contactForm.username.trim(),
      name: contactForm.name.trim() || null,
    });
    setContactForm({ username: '', name: '' });
    await loadContacts();
  };

  const searchContacts = async (query) => {
    if (!query.trim()) { setContactResults([]); return; }
    setContactSearching(true);
    try {
      const response = await searchUsers(query.trim());
      setContactResults(Array.isArray(response.data) ? response.data : []);
    } catch {
      setContactResults([]);
    } finally {
      setContactSearching(false);
    }
  };

  const addContactFromResult = async (user) => {
    try {
      await addContact({ username: user.profile?.username, name: displayName(user) });
      setContactQuery('');
      setContactResults([]);
      await loadContacts();
      toast.success('Контакт добавлен');
    } catch {
      toast.error('Не удалось добавить контакт');
    }
  };

  const deleteContactById = async (contactId) => {
    await deleteContact(contactId);
    await loadContacts();
  };

  const blockUsername = async (username) => {
    if (!username) return;
    await blockUser({ username });
    setBlockForm('');
    await loadBlocked();
    toast.success('Пользователь заблокирован');
  };

  const unblockUsername = async (username) => {
    await unblockUser(username);
    await loadBlocked();
  };

  const saveEntityDetails = async (event) => {
    event.preventDefault();
    if (!active || !isAdmin) return;

    const formData = new FormData();
    if (detailDraft.name.trim()) formData.append('name', detailDraft.name.trim());
    formData.append('description', detailDraft.description.trim());
    if (active.type === 'channel') formData.append('is_public', String(detailDraft.is_public));
    if (detailDraft.avatar) formData.append('avatar', detailDraft.avatar);

    if (active.type === 'group') await updateGroup(active.id, formData);
    if (active.type === 'channel') await updateChannel(active.id, formData);
    await loadActiveData();
    await loadChats(sidebarSearch);
    toast.success('Информация сохранена');
  };

  const addMemberFromContacts = async (username) => {
    if (!active || !username) return;
    if (active.type === 'group') await addGroupMember(active.id, { username });
    if (active.type === 'channel') await addChannelMember(active.id, { username });
    setShowMemberPicker(false);
    await loadActiveData();
  };

  const promoteMember = (username) => {
    setConfirmDialog({
      message: `Назначить @${username} администратором?`,
      actionLabel: 'Назначить',
      onConfirm: async () => {
        if (active.type === 'group') await makeGroupAdmin(active.id, username);
        if (active.type === 'channel') await makeChannelAdmin(active.id, username);
        await loadActiveData();
        toast.success(`@${username} теперь администратор`);
      },
    });
  };

  const removeMember = (username) => {
    setConfirmDialog({
      message: `Удалить участника @${username}?`,
      onConfirm: async () => {
        if (active.type === 'group') await removeGroupMember(active.id, username);
        if (active.type === 'channel') await removeChannelMember(active.id, username);
        await loadActiveData();
      },
    });
  };

  const deleteActiveEntity = () => {
    if (!active) return;
    const labels = { private: 'чат', group: 'группу', channel: 'канал' };
    setConfirmDialog({
      message: `Удалить ${labels[active.type]}? Это действие нельзя отменить.`,
      onConfirm: async () => {
        if (active.type === 'private') await deleteChat(active.id);
        if (active.type === 'group') await deleteGroup(active.id);
        if (active.type === 'channel') await deleteChannel(active.id);
        setActive(null);
        setInfoOpen(false);
        await loadChats(sidebarSearch);
      },
    });
  };

  const toggleChannelSubscription = async () => {
    if (!active || active.type !== 'channel') return;
    if (activeRole) {
      await unsubscribeChannel(active.id);
      setActive(null);
    } else {
      await subscribeChannel(active.id);
      await loadActiveData();
    }
    await loadChats(sidebarSearch);
  };

  const markNotificationRead = async (notification) => {
    if (!notification.is_read) await markAsRead(notification.id);
    await loadNotifications();
  };

  const readAllNotifications = async () => {
    await markAllAsRead();
    await loadNotifications();
  };

  const renderMenu = () => (
    <div className="menu-popover">
      <button type="button" className="menu-profile" onClick={() => { setSidebarView('settings'); setMenuOpen(false); }}>
        <Avatar entity={profile || currentUser} size={38} style={{ flexShrink: 0 }} />
        <span>
          <strong>{displayName(profile || currentUser, 'Аккаунт')}</strong>
          <small>{profile?.username ? `@${profile.username}` : currentUser?.phone_number}</small>
        </span>
      </button>
      <button type="button" onClick={() => { setSidebarView('settings'); setMenuOpen(false); }}><Icon name="settings" />Настройки</button>
      <button type="button" onClick={() => { setSidebarView('contacts'); setMenuOpen(false); }}><Icon name="contacts" />Контакты</button>
      <button type="button" onClick={() => { setSidebarView('notifications'); setMenuOpen(false); }}><Icon name="bell" />Уведомления<span>{unreadNotifications}</span></button>
      <button type="button" onClick={() => { setSidebarView('blocked'); setMenuOpen(false); }}><Icon name="block" />Заблокированные</button>
      <div className="menu-divider" />
      <button type="button" onClick={() => openCompose('group')}><Icon name="group" />Создать группу</button>
      <button type="button" onClick={() => openCompose('channel')}><Icon name="channel" />Создать канал</button>
      <button type="button" onClick={() => openCompose('join')}><Icon name="search" />Найти канал</button>
      <div className="menu-divider" />
      <button type="button" onClick={logout}><Icon name="logout" />Выйти</button>
    </div>
  );

  const renderStories = () => {
    const myGroup = stories.find((group) => isOwnStoryGroup(group));
    const otherGroups = stories.filter((group) => group !== myGroup);

    return (
      <div className="stories-strip">
        <input ref={storyInputRef} type="file" accept="image/*,video/*" hidden onChange={createNewStory} />
        <button
          type="button"
          className={`story-item story-own ${myGroup ? 'has-story' : 'story-add'}`}
          title={myGroup ? 'Моя история' : 'Добавить историю'}
          onClick={() => (myGroup ? openStory(myGroup, firstPlayableStoryIndex(myGroup)) : storyInputRef.current?.click())}
        >
          <span className={`story-frame ${myGroup ? 'own' : 'add'}`}>
            {myGroup ? <Avatar entity={myGroup.user} size={52} /> : <Icon name="add" size={18} />}
            <i className="story-add-badge" onClick={(event) => { event.stopPropagation(); storyInputRef.current?.click(); }}>
              <Icon name="add" size={12} />
            </i>
          </span>
          <small>Моя</small>
        </button>
        {otherGroups.map((group) => (
          <button
            type="button"
            key={group.user.id}
            className={`story-item ${group.has_unviewed ? 'unviewed' : 'seen'}`}
            title={displayName(group.user)}
            onClick={() => openStory(group, firstPlayableStoryIndex(group))}
          >
            <span className={`story-frame ${group.has_unviewed ? 'unviewed' : 'seen'}`}>
              <Avatar entity={group.user} size={52} />
            </span>
            <small>{displayName(group.user)}</small>
          </button>
        ))}
      </div>
    );
  };

  const renderChatList = () => (
    <>
      <div className="sidebar-header">
        <button type="button" className="icon-button" title="Меню" onClick={() => setMenuOpen((value) => !value)}>
          <Icon name="menu" />
        </button>
        <label className="search-box">
          <Icon name="search" size={19} />
          <input value={sidebarSearch} onChange={(event) => setSidebarSearch(event.target.value)} placeholder="Поиск" />
        </label>
        <button type="button" className="icon-button accent" title="Новый чат" onClick={() => openCompose('private')}>
          <Icon name="edit" />
        </button>
        {menuOpen && renderMenu()}
      </div>

      {!storyViewer && renderStories()}

      <div className="chat-tabs">
        {TABS.map((tab) => (
          <button
            type="button"
            key={tab.key}
            className={sidebarTab === tab.key ? 'active' : ''}
            onClick={() => setSidebarTab(tab.key)}
          >
            {tab.label}
            {tabCounts[tab.key] > 0 && <span>{tabCounts[tab.key]}</span>}
          </button>
        ))}
      </div>

      <div className="chat-list">
        {loadingChats && <div className="panel-loader"><Spinner /></div>}
        {!loadingChats && filteredChats.map((chat) => (
          <button
            type="button"
            key={`${chat.type}-${chat.id}`}
            className={`chat-list-item ${activeKey === `${chat.type}-${chat.id}` ? 'active' : ''}`}
            onClick={() => openChat(chat)}
          >
            <Avatar entity={{ avatar_url: chatAvatar(chat), id: chat.id }} title={chatTitle(chat)} size={56} style={{ flexShrink: 0 }} />
            <span className="chat-list-main">
              <span className="chat-list-title">
                <strong>{chatTitle(chat)}</strong>
                <small>{formatChatDate(chat.updated_at || chat.created_at)}</small>
              </span>
              <span className="chat-list-preview">
                {chat.last_message?.sender && <b>{displayName(chat.last_message.sender)}: </b>}
                {messageText(chat.last_message)}
              </span>
            </span>
            <span className="chat-list-meta">
              {chat.type === 'channel' && <Icon name="channel" size={16} />}
              {chat.type === 'group' && <Icon name="group" size={16} />}
              {chat.unread_count > 0 && <em>{chat.unread_count}</em>}
            </span>
          </button>
        ))}
        {!loadingChats && filteredChats.length === 0 && (
          <div className="soft-empty">Ничего не найдено</div>
        )}
      </div>
    </>
  );

  const renderSettings = () => (
    <div className="side-panel">
      <div className="side-panel-header">
        <button type="button" className="icon-button" onClick={() => setSidebarView('chats')} title="Назад"><Icon name="back" /></button>
        <h2>Настройки</h2>
      </div>
      <form className="profile-editor" onSubmit={saveProfile}>
        <label className="avatar-uploader">
          <Avatar entity={profile || currentUser} size={128} />
          <input type="file" accept="image/*" hidden onChange={(event) => setProfileDraft((state) => ({ ...state, avatar: event.target.files?.[0] || null }))} />
          <span><Icon name="camera" />Фото</span>
        </label>
        <h3>{displayName(profile || currentUser, 'Профиль')}</h3>
        <small>{profile?.user?.phone_number || currentUser?.phone_number}</small>
        <label className="field">
          <span>Имя</span>
          <input value={profileDraft.full_name} onChange={(event) => setProfileDraft((state) => ({ ...state, full_name: event.target.value }))} />
        </label>
        <label className="field">
          <span>Username</span>
          <input value={profileDraft.username} onChange={(event) => setProfileDraft((state) => ({ ...state, username: event.target.value }))} placeholder="username" />
        </label>
        <label className="field">
          <span>О себе</span>
          <textarea value={profileDraft.bio} onChange={(event) => setProfileDraft((state) => ({ ...state, bio: event.target.value }))} maxLength={255} />
        </label>
        <button className="primary-button"><Icon name="save" />Сохранить</button>
      </form>
    </div>
  );

  const renderContacts = () => (
    <div className="side-panel">
      <div className="side-panel-header">
        <button type="button" className="icon-button" onClick={() => setSidebarView('chats')} title="Назад"><Icon name="back" /></button>
        <h2>Контакты</h2>
      </div>

      <div className="contact-search-box">
        <label className="search-box" style={{ margin: '10px 12px', flex: 'none' }}>
          <Icon name="search" size={18} />
          <input
            value={contactQuery}
            onChange={(e) => {
              setContactQuery(e.target.value);
              searchContacts(e.target.value);
            }}
            placeholder="Найти пользователя..."
          />
        </label>
        {contactSearching && <div className="panel-loader" style={{ padding: '8px 0' }}><Spinner /></div>}
        {contactResults.length > 0 && (
          <div className="entity-list contact-results">
            {contactResults.map((user) => {
              const alreadyAdded = contacts.some((c) => c.contact?.id === user.id);
              return (
                <div className="entity-row" key={user.id}>
                  <Avatar entity={user} size={44} />
                  <span>
                    <strong>{displayName(user)}</strong>
                    <small>{user.profile?.username ? `@${user.profile.username}` : user.phone_number}</small>
                  </span>
                  {alreadyAdded
                    ? <span style={{ fontSize: 12, color: 'var(--text-muted)', paddingRight: 8 }}>В контактах</span>
                    : <button type="button" className="icon-button accent" title="Добавить" onClick={() => addContactFromResult(user)}><Icon name="add" /></button>
                  }
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="entity-list">
        {contacts.length === 0 && !contactQuery && (
          <div className="soft-empty">Контактов нет. Найдите пользователя выше.</div>
        )}
        {contacts.map((contact) => (
          <div className="entity-row" key={contact.id}>
            <Avatar entity={contact.contact} size={44} />
            <span>
              <strong>{contact.name || displayName(contact.contact)}</strong>
              <small>{contact.contact?.profile?.username ? `@${contact.contact.profile.username}` : ''}</small>
            </span>
            {contact.contact?.profile?.username && (
              <button type="button" className="icon-button" title="Написать" onClick={() => startPrivateChat(contact.contact.profile.username)}>
                <Icon name="send" />
              </button>
            )}
            <button type="button" className="icon-button danger" title="Удалить" onClick={() => deleteContactById(contact.id)}>
              <Icon name="delete" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );

  const renderBlocked = () => (
    <div className="side-panel">
      <div className="side-panel-header">
        <button type="button" className="icon-button" onClick={() => setSidebarView('chats')} title="Назад"><Icon name="back" /></button>
        <h2>Блокировки</h2>
      </div>
      <form className="compact-form" onSubmit={(event) => { event.preventDefault(); blockUsername(blockForm.trim()); }}>
        <input value={blockForm} onChange={(event) => setBlockForm(event.target.value)} placeholder="username" />
        <button className="primary-button"><Icon name="block" />Блокировать</button>
      </form>
      <div className="entity-list">
        {blocked.map((item) => (
          <div className="entity-row" key={item.id}>
            <Avatar entity={item.blocked} size={44} />
            <span>
              <strong>{displayName(item.blocked)}</strong>
              <small>@{item.blocked?.profile?.username || 'no_username'}</small>
            </span>
            <button type="button" className="secondary-button" onClick={() => unblockUsername(item.blocked.profile.username)}>Разблокировать</button>
          </div>
        ))}
      </div>
    </div>
  );

  const renderNotifications = () => (
    <div className="side-panel">
      <div className="side-panel-header">
        <button type="button" className="icon-button" onClick={() => setSidebarView('chats')} title="Назад"><Icon name="back" /></button>
        <h2>Уведомления</h2>
        <button type="button" className="icon-button" title="Прочитать все" onClick={readAllNotifications}><Icon name="check" /></button>
      </div>
      <div className="entity-list">
        {notifications.map((notification) => (
          <button
            type="button"
            className={`notification-row ${notification.is_read ? '' : 'unread'}`}
            key={notification.id}
            onClick={() => markNotificationRead(notification)}
          >
            <Avatar entity={notification.from_user} size={42} />
            <span>
              <strong>{displayName(notification.from_user)}</strong>
              <small>{notification.type} · {notification.entity_type} · {formatChatDate(notification.created_at)}</small>
            </span>
          </button>
        ))}
        {notifications.length === 0 && <div className="soft-empty">Уведомлений нет</div>}
      </div>
    </div>
  );

  const renderSidebar = () => {
    if (sidebarView === 'settings') return renderSettings();
    if (sidebarView === 'contacts') return renderContacts();
    if (sidebarView === 'blocked') return renderBlocked();
    if (sidebarView === 'notifications') return renderNotifications();
    return renderChatList();
  };

  const renderChatStatus = () => {
    if (!active) return '';
    if (active.type === 'private') {
      return active.is_online ? 'в сети' : formatLastSeen(active.last_seen || active.user?.profile?.last_seen);
    }
    if (active.type === 'group') return `${activeDetail?.members_count || active.members_count || 0} участников`;
    if (active.type === 'channel') return `${activeDetail?.members_count || active.members_count || 0} подписчиков`;
    return '';
  };

  const renderMessageMedia = (message) => {
    const url = mediaUrl(message.media_url);
    if (!url) return null;
    if (isVideo(url)) {
      return <video className="message-media" src={url} controls onClick={() => setMediaViewer(url)} />;
    }
    return <img className="message-media" src={url} alt="" onClick={() => setMediaViewer(url)} />;
  };

  const renderPoll = (poll) => {
    if (!poll) return null;
    return (
      <div className="poll-card">
        <strong>{poll.question}</strong>
        {poll.options.map((option) => (
          <button
            type="button"
            className={`poll-option ${option.is_voted_by_me ? 'selected' : ''}`}
            key={option.id}
            onClick={() => voteInPoll(poll.id, option.id)}
            disabled={poll.is_voted_by_me}
          >
            <span>{option.text}</span>
            <b>{option.percent}%</b>
            <i style={{ width: `${option.percent}%` }} />
          </button>
        ))}
        <small>{poll.total_votes} голосов</small>
      </div>
    );
  };

  const renderMessage = (message, index) => {
    const mine = message.sender?.id === currentUser?.id || message.sender_id === currentUser?.id;
    const previous = visibleMessages[index - 1];
    const showDate = !previous || !isSameDay(previous.created_at, message.created_at);
    const reactions = groupReactions(message.reactions);
    const sender = message.sender;
    const showSender = !mine && active?.type !== 'private';

    return (
      <div key={message.id}>
        {showDate && <div className="date-chip">{formatSeparatorDate(message.created_at)}</div>}
        <div
          id={`message-${message.id}`}
          className={`message-row ${mine ? 'own' : ''} ${focusedMessageId === message.id ? 'focused' : ''}`}
        >
          {!mine && active?.type === 'group' && <Avatar entity={sender} size={32} />}
          <div className="message-bubble">
            {showSender && (
              <b className="sender-name" style={{ color: nameColor(sender?.id) }}>
                {displayName(sender)}
              </b>
            )}
            {message.reply_to && (
              <button type="button" className="reply-preview" onClick={() => focusMessage(message.reply_to.id)}>
                <b>{displayName(message.reply_to.sender)}</b>
                <span>{messageText(message.reply_to)}</span>
              </button>
            )}
            {message.forwarded_from && (
              <div className="forward-preview">
                <Icon name="forward" size={15} />
                <span>{displayName(message.forwarded_from.sender)}</span>
              </div>
            )}
            {renderMessageMedia(message)}
            {message.text && <p>{message.text}</p>}
            {renderPoll(message.poll)}
            <div className="message-meta">
              {message.is_edited && <span>изменено</span>}
              {message.is_pinned && <Icon name="pin" size={14} />}
              <time>{formatTime(message.created_at)}</time>
              {mine && active?.type === 'private' && <span className="ticks">{message.is_read ? '✓✓' : '✓'}</span>}
            </div>
            {reactions.length > 0 && (
              <div className="reaction-row">
                {reactions.map((reaction) => (
                  <button type="button" key={reaction.emoji} onClick={() => reactToMessage(message, reaction.emoji)}>
                    {reaction.emoji} <span>{reaction.count}</span>
                  </button>
                ))}
              </div>
            )}
            <div className="message-actions">
              {active?.type !== 'channel' && (
                <button type="button" title="Ответить" onClick={() => setReplyTo(message)}><Icon name="reply" size={16} /></button>
              )}
              {canEditMessage(message) && (
                <button type="button" title="Изменить" onClick={() => { setEditing(message); setInputText(message.text || ''); }}><Icon name="edit" size={16} /></button>
              )}
              {canDeleteMessage(message) && (
                <button type="button" title="Удалить" onClick={() => removeMessage(message)}><Icon name="delete" size={16} /></button>
              )}
              {canPinMessage(message) && (
                <button type="button" title="Закрепить" onClick={() => pinActiveMessage(message)}><Icon name="pin" size={16} /></button>
              )}
              {active?.type !== 'channel' && (
                <button type="button" title="Переслать" onClick={() => setForwarding(message)}><Icon name="forward" size={16} /></button>
              )}
              {active?.type === 'channel' && isAdmin && !message.poll && (
                <button type="button" title="Опрос" onClick={() => setPollDraft({ post: message, question: '', options: ['', ''] })}><Icon name="poll" size={16} /></button>
              )}
              {QUICK_REACTIONS.map((emoji) => (
                <button type="button" key={emoji} title={emoji} onClick={() => reactToMessage(message, emoji)}>{emoji}</button>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderInput = () => {
    if (!active) return null;

    if (active.type === 'channel' && !activeRole) {
      return (
        <div className="input-locked">
          <button type="button" className="primary-button" onClick={toggleChannelSubscription}>Подписаться</button>
        </div>
      );
    }

    if (active.type === 'channel' && !isAdmin) {
      return (
        <div className="input-locked">
          <span>Только администраторы могут публиковать посты</span>
          <button type="button" className="secondary-button" onClick={toggleChannelSubscription}>Отписаться</button>
        </div>
      );
    }

    return (
      <form className="chat-input" onSubmit={submitMessage}>
        {(replyTo || editing || inputFile) && (
          <div className="input-context">
            <span>
              <b>{editing ? 'Редактирование' : replyTo ? `Ответ: ${displayName(replyTo.sender)}` : 'Файл'}</b>
              <small>{editing ? messageText(editing) : replyTo ? messageText(replyTo) : inputFile?.name}</small>
            </span>
            <button type="button" className="icon-button" onClick={() => { setReplyTo(null); setEditing(null); setInputFile(null); setInputText(''); }}>
              <Icon name="close" size={18} />
            </button>
          </div>
        )}
        <input ref={inputFileRef} type="file" accept="image/*,video/*" hidden onChange={(event) => setInputFile(event.target.files?.[0] || null)} />
        <button type="button" className="icon-button" title="Медиа" onClick={() => inputFileRef.current?.click()}><Icon name="paperclip" /></button>
        {active.type === 'channel' && isAdmin && (
          <button type="button" className="icon-button" title="Опрос" onClick={() => setPollDraft({ post: null, question: '', options: ['', ''] })}><Icon name="poll" /></button>
        )}
        <textarea
          ref={textareaRef}
          value={inputText}
          onChange={(event) => {
            setInputText(event.target.value);
            const el = event.target;
            el.style.height = 'auto';
            el.style.height = `${el.scrollHeight}px`;
            el.style.overflowY = el.scrollHeight > 150 ? 'auto' : 'hidden';
          }}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault();
              submitMessage(event);
            }
          }}
          onFocus={() => sendTyping(true)}
          onBlur={() => sendTyping(false)}
          placeholder={active.type === 'channel' ? 'Пост' : 'Сообщение'}
          rows={1}
        />
        <button type="submit" className="send-button" title={editing ? 'Сохранить' : 'Отправить'}>
          <Icon name={inputText.trim() || inputFile || editing ? 'send' : 'mic'} />
        </button>
      </form>
    );
  };

  const renderChat = () => (
    <main className={`chat-pane ${active ? 'open' : ''}`}>
      {!active && (
        <div className="empty-chat">
          <div className="telegram-orb"><Icon name="send" size={46} /></div>
          <span>Выберите чат</span>
        </div>
      )}

      {active && (
        <>
          <header className="chat-header">
            <button type="button" className="icon-button mobile-back" onClick={() => setActive(null)} title="Назад"><Icon name="back" /></button>
            <Avatar entity={{ avatar_url: chatAvatar(active), id: active.id }} title={chatTitle(active)} size={52} style={{ flexShrink: 0 }} />
            <button type="button" className="chat-title" onClick={() => setInfoOpen(true)}>
              <strong>{chatTitle(active)}</strong>
              <span>{renderChatStatus()}</span>
            </button>
            {chatSearchOpen && (
              <label className="chat-search">
                <Icon name="search" size={18} />
                <input value={chatSearch} onChange={(event) => setChatSearch(event.target.value)} autoFocus placeholder="Поиск" />
              </label>
            )}
            <button type="button" className="icon-button" title="Поиск" onClick={() => setChatSearchOpen((value) => !value)}><Icon name="search" /></button>
            <button type="button" className="icon-button" title="Информация" onClick={() => setInfoOpen((value) => !value)}><Icon name="info" /></button>
          </header>

          {pinnedMessage && (
            <div className="pinned-bar">
              <button type="button" className="pinned-bar-content" onClick={() => focusMessage(pinnedMessage.id)}>
                <Icon name="pin" size={18} />
                <span><b>Закреплённое сообщение</b><small>{messageText(pinnedMessage)}</small></span>
              </button>
              <button type="button" className="icon-button" title="Открепить" onClick={() => unpinActiveMessage(pinnedMessage.id)}>
                <Icon name="close" size={16} />
              </button>
            </div>
          )}

          <section className="messages">
            {loadingMessages && <div className="panel-loader"><Spinner /></div>}
            {!loadingMessages && visibleMessages.map(renderMessage)}
            {!loadingMessages && visibleMessages.length === 0 && <div className="soft-empty">Сообщений нет</div>}
            {typingUsers.length > 0 && (
              <div className="typing">
                <span className="typing-dots">
                  <span /><span /><span />
                </span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </section>

          {renderInput()}
        </>
      )}
    </main>
  );

  const renderInfoPanel = () => {
    if (!active || !infoOpen) return null;

    const isPrivate = active.type === 'private';
    const entityTitle = isPrivate ? chatTitle(active) : activeDetail?.name || activeDetail?.title || chatTitle(active);
    const entityAvatar = isPrivate ? active.user : { avatar_url: activeDetail?.avatar_url || active.avatar_url, id: active.id };
    const members = activeDetail?.members || [];
    const username = active.user?.profile?.username;
    const isContact = contacts.some((contact) => contact.contact?.profile?.username === username);
    const isBlocked = blocked.some((item) => item.blocked?.profile?.username === username);
    const isOwner = !isPrivate && (activeDetail?.owner?.id === currentUser?.id);

    return (
      <aside className="info-panel">
        <div className="side-panel-header">
          <button type="button" className="icon-button" onClick={() => setInfoOpen(false)} title="Закрыть"><Icon name="close" /></button>
          <h2>Информация</h2>
        </div>
        <div className="info-hero">
          <Avatar entity={entityAvatar} title={entityTitle} size={96} style={{ flexShrink: 0 }} />
          <h3>{entityTitle}</h3>
          <span>{isPrivate ? renderChatStatus() : renderChatStatus()}</span>
        </div>

        {isPrivate && (
          <div className="info-actions">
            {username && !isContact && <button type="button" className="secondary-button" onClick={() => { setContactForm({ username, name: entityTitle }); addContact({ username, name: entityTitle }).then(loadContacts); }}><Icon name="contacts" />В контакты</button>}
            {username && isContact && <button type="button" className="secondary-button" onClick={() => setSidebarView('contacts')}><Icon name="contacts" />Контакты</button>}
            {username && !isBlocked && <button type="button" className="secondary-button danger" onClick={() => blockUsername(username)}><Icon name="block" />Блокировать</button>}
            {username && isBlocked && <button type="button" className="secondary-button" onClick={() => unblockUsername(username)}><Icon name="check" />Разблокировать</button>}
          </div>
        )}

        {!isPrivate && (
          <>
            {active.type === 'channel' && activeDetail?.is_public && (
              <button type="button" className="secondary-button wide" onClick={toggleChannelSubscription}>
                {activeRole ? 'Отписаться' : 'Подписаться'}
              </button>
            )}

            {isAdmin && (
              <form className="entity-editor" onSubmit={saveEntityDetails}>
                <label className="field">
                  <span>Название</span>
                  <input value={detailDraft.name} onChange={(event) => setDetailDraft((state) => ({ ...state, name: event.target.value }))} />
                </label>
                <label className="field">
                  <span>Описание</span>
                  <textarea value={detailDraft.description} onChange={(event) => setDetailDraft((state) => ({ ...state, description: event.target.value }))} />
                </label>
                {active.type === 'channel' && (
                  <label className="switch-row">
                    <input type="checkbox" checked={detailDraft.is_public} onChange={(event) => setDetailDraft((state) => ({ ...state, is_public: event.target.checked }))} />
                    <span>Публичный канал</span>
                  </label>
                )}
                <label className="file-line">
                  <Icon name="camera" />
                  <span>{detailDraft.avatar?.name || 'Обновить фото'}</span>
                  <input type="file" accept="image/*" hidden onChange={(event) => setDetailDraft((state) => ({ ...state, avatar: event.target.files?.[0] || null }))} />
                </label>
                <button className="primary-button"><Icon name="save" />Сохранить</button>
              </form>
            )}

            {isAdmin && (
              <div className="member-picker-wrap">
                <button
                  type="button"
                  className="primary-button wide"
                  onClick={() => setShowMemberPicker((v) => !v)}
                >
                  <Icon name="add" />Добавить участника
                </button>
                {showMemberPicker && (
                  <div className="member-picker-list">
                    {contacts.filter((c) => {
                      const username = c.contact?.profile?.username;
                      return username && !members.some((m) => m.user?.profile?.username === username);
                    }).length === 0 && (
                      <div className="soft-empty" style={{ padding: '12px 14px', fontSize: 13 }}>Все контакты уже в группе</div>
                    )}
                    {contacts
                      .filter((c) => {
                        const username = c.contact?.profile?.username;
                        return username && !members.some((m) => m.user?.profile?.username === username);
                      })
                      .map((c) => (
                        <button
                          type="button"
                          key={c.id}
                          className="entity-row"
                          onClick={() => addMemberFromContacts(c.contact.profile.username)}
                        >
                          <Avatar entity={c.contact} size={38} />
                          <span>
                            <strong>{c.name || displayName(c.contact)}</strong>
                            <small>@{c.contact.profile.username}</small>
                          </span>
                        </button>
                      ))}
                  </div>
                )}
              </div>
            )}

            <div className="members-list">
              {members.map((member) => {
                const memberUsernameValue = member.user?.profile?.username;
                return (
                  <div className="entity-row" key={member.id}>
                    <Avatar entity={member.user} size={42} style={{ flexShrink: 0 }} />
                    <span>
                      <strong>{displayName(member.user)}</strong>
                      <small>{member.role} · @{memberUsernameValue || 'no_username'}</small>
                    </span>
                    {isAdmin && member.role !== 'admin' && memberUsernameValue && (
                      <button type="button" className="icon-button" title="Сделать админом" onClick={() => promoteMember(memberUsernameValue)}>
                        <Icon name="settings" />
                      </button>
                    )}
                    {isAdmin && memberUsernameValue && member.user?.id !== currentUser?.id && (
                      <button type="button" className="icon-button danger" title="Удалить" onClick={() => removeMember(memberUsernameValue)}>
                        <Icon name="delete" />
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </>
        )}

        {(isPrivate || isOwner) && (
          <div className="info-actions" style={{ marginTop: 'auto', paddingTop: 12 }}>
            <button type="button" className="secondary-button danger wide" onClick={deleteActiveEntity}>
              <Icon name="delete" />
              {isPrivate ? 'Удалить чат' : active.type === 'group' ? 'Удалить группу' : 'Удалить канал'}
            </button>
          </div>
        )}
      </aside>
    );
  };

  const renderComposeModal = () => {
    if (!compose.open) return null;

    return (
      <div className="modal-backdrop" onMouseDown={closeCompose}>
        <section className="modal" onMouseDown={(event) => event.stopPropagation()}>
          <header>
            <h2>Новое действие</h2>
            <button type="button" className="icon-button" onClick={closeCompose}><Icon name="close" /></button>
          </header>
          <div className="segmented">
            <button type="button" className={compose.mode === 'private' ? 'active' : ''} onClick={() => setCompose((state) => ({ ...state, mode: 'private', results: [] }))}>Чат</button>
            <button type="button" className={compose.mode === 'group' ? 'active' : ''} onClick={() => setCompose((state) => ({ ...state, mode: 'group', results: [] }))}>Группа</button>
            <button type="button" className={compose.mode === 'channel' ? 'active' : ''} onClick={() => setCompose((state) => ({ ...state, mode: 'channel', results: [] }))}>Канал</button>
            <button type="button" className={compose.mode === 'join' ? 'active' : ''} onClick={() => setCompose((state) => ({ ...state, mode: 'join', results: [] }))}>Найти</button>
          </div>

          {(compose.mode === 'private' || compose.mode === 'join') && (
            <>
              <form className="modal-search" onSubmit={(event) => { event.preventDefault(); handleComposeSearch(); }}>
                <input value={compose.query} onChange={(event) => setCompose((state) => ({ ...state, query: event.target.value }))} placeholder={compose.mode === 'join' ? 'Поиск каналов' : 'Поиск пользователей'} />
                <button className="primary-button">{compose.loading ? <Spinner /> : <Icon name="search" />}Искать</button>
              </form>
              <div className="entity-list modal-list">
                {compose.results.map((item) => (
                  <button
                    type="button"
                    key={item.id}
                    className="entity-row"
                    onClick={() => compose.mode === 'join' ? subscribeAndOpen({ ...item, type: 'channel', title: item.name }) : startPrivateChat(item)}
                    disabled={compose.mode === 'private' && !item.id}
                  >
                    <Avatar entity={compose.mode === 'join' ? { avatar_url: item.avatar_url, id: item.id } : item} size={44} />
                    <span>
                      <strong>{compose.mode === 'join' ? item.name : displayName(item)}</strong>
                      <small>{compose.mode === 'join' ? `${item.members_count || 0} подписчиков` : item.profile?.username ? `@${item.profile.username}` : item.phone_number}</small>
                    </span>
                  </button>
                ))}
              </div>
            </>
          )}

          {(compose.mode === 'group' || compose.mode === 'channel') && (
            <form className="modal-form" onSubmit={(event) => { event.preventDefault(); compose.mode === 'group' ? createNewGroup() : createNewChannel(); }}>
              <label className="field">
                <span>Название</span>
                <input value={compose.name} onChange={(event) => setCompose((state) => ({ ...state, name: event.target.value }))} autoFocus />
              </label>
              <label className="field">
                <span>Описание</span>
                <textarea value={compose.description} onChange={(event) => setCompose((state) => ({ ...state, description: event.target.value }))} />
              </label>
              {compose.mode === 'channel' && (
                <label className="switch-row">
                  <input type="checkbox" checked={compose.isPublic} onChange={(event) => setCompose((state) => ({ ...state, isPublic: event.target.checked }))} />
                  <span>Публичный канал</span>
                </label>
              )}
              <label className="file-line">
                <Icon name="camera" />
                <span>{compose.avatar?.name || 'Фото'}</span>
                <input type="file" accept="image/*" hidden onChange={(event) => setCompose((state) => ({ ...state, avatar: event.target.files?.[0] || null }))} />
              </label>
              <button className="primary-button"><Icon name="add" />Создать</button>
            </form>
          )}
        </section>
      </div>
    );
  };

  const renderStoryViewer = () => {
    if (!storyViewer) return null;
    const story = storyViewer.group.stories[storyViewer.index];
    if (!story) return null;
    const url = mediaUrl(story.media_url);
    const isOwn = isOwnStoryGroup(storyViewer.group);
    const viewsCount = isOwn ? (storyViews.length || story.views_count || 0) : (story.views_count || 0);
    const meta = isOwn
      ? `${viewsCount} просмотров`
      : story.is_viewed_by_me ? 'просмотрено' : 'новая история';

    return (
      <div className="story-viewer" onMouseDown={closeStoryViewer}>
        <section className="story-stage" onMouseDown={(event) => event.stopPropagation()}>
          <div className="story-progress">
            {storyViewer.group.stories.map((item, itemIndex) => (
              <span key={item.id} className={itemIndex <= storyViewer.index ? 'active' : ''}>
                <i />
              </span>
            ))}
          </div>
          <header>
            <Avatar entity={storyViewer.group.user} size={42} />
            <span>
              <strong>{isOwn ? 'Моя история' : displayName(storyViewer.group.user)}</strong>
              <small>{formatChatDate(story.created_at)} · {meta}</small>
            </span>
            <button type="button" className="icon-button" onClick={closeStoryViewer}><Icon name="close" /></button>
          </header>
          <button
            type="button"
            className="story-nav left"
            onClick={() => changeStory(-1)}
            disabled={storyViewer.index === 0}
            title="Предыдущая история"
          >
            <Icon name="back" />
          </button>
          <div className="story-media">
            {isVideo(url) ? <video src={url} controls autoPlay /> : <img src={url} alt="" />}
          </div>
          <button
            type="button"
            className="story-nav right"
            onClick={() => changeStory(1)}
            title="Следующая история"
          >
            <Icon name="back" />
          </button>
        </section>
      </div>
    );
  };

  const renderForwardModal = () => {
    if (!forwarding || !active || active.type === 'channel') return null;
    const targets = chats.filter((chat) => chat.type === active.type && chat.id !== active.id);

    return (
      <div className="modal-backdrop" onMouseDown={() => setForwarding(null)}>
        <section className="modal small" onMouseDown={(event) => event.stopPropagation()}>
          <header>
            <h2>Переслать</h2>
            <button type="button" className="icon-button" onClick={() => setForwarding(null)}><Icon name="close" /></button>
          </header>
          <div className="entity-list modal-list">
            {targets.map((target) => (
              <button type="button" className="entity-row" key={`${target.type}-${target.id}`} onClick={() => forwardToChat(target)}>
                <Avatar entity={{ avatar_url: chatAvatar(target), id: target.id }} title={chatTitle(target)} size={44} />
                <span><strong>{chatTitle(target)}</strong><small>{target.type === 'private' ? 'личный чат' : 'группа'}</small></span>
              </button>
            ))}
            {targets.length === 0 && <div className="soft-empty">Нет подходящих чатов</div>}
          </div>
        </section>
      </div>
    );
  };

  const renderPollModal = () => {
    if (!pollDraft) return null;

    return (
      <div className="modal-backdrop" onMouseDown={() => setPollDraft(null)}>
        <section className="modal small" onMouseDown={(event) => event.stopPropagation()}>
          <header>
            <h2>Опрос</h2>
            <button type="button" className="icon-button" onClick={() => setPollDraft(null)}><Icon name="close" /></button>
          </header>
          <form className="modal-form" onSubmit={createPollForPost}>
            <label className="field">
              <span>Вопрос</span>
              <input value={pollDraft.question} onChange={(event) => setPollDraft((state) => ({ ...state, question: event.target.value }))} autoFocus />
            </label>
            {pollDraft.options.map((option, index) => (
              <label className="field" key={index}>
                <span>Вариант {index + 1}</span>
                <input
                  value={option}
                  onChange={(event) => setPollDraft((state) => ({
                    ...state,
                    options: state.options.map((item, itemIndex) => itemIndex === index ? event.target.value : item),
                  }))}
                />
              </label>
            ))}
            <button type="button" className="secondary-button" onClick={() => setPollDraft((state) => ({ ...state, options: [...state.options, ''] }))} disabled={pollDraft.options.length >= 10}>
              <Icon name="add" />Вариант
            </button>
            <button className="primary-button"><Icon name="poll" />Создать</button>
          </form>
        </section>
      </div>
    );
  };

  const renderConfirmDialog = () => {
    if (!confirmDialog) return null;

    const handleConfirm = () => {
      const { onConfirm } = confirmDialog;
      setConfirmDialog(null);
      onConfirm().catch(() => toast.error('Не удалось выполнить действие'));
    };

    return (
      <div className="modal-backdrop" onMouseDown={() => setConfirmDialog(null)}>
        <section className="modal confirm-modal" onMouseDown={(e) => e.stopPropagation()}>
          <p>{confirmDialog.message}</p>
          <div className="confirm-actions">
            <button type="button" className="ghost-button" onClick={() => setConfirmDialog(null)}>Отмена</button>
            <button
              type="button"
              className={confirmDialog.actionLabel ? 'primary-button' : 'danger-button'}
              onClick={handleConfirm}
            >
              {confirmDialog.actionLabel || 'Удалить'}
            </button>
          </div>
        </section>
      </div>
    );
  };

  return (
    <div className="telegram-shell">
      <aside className={`telegram-sidebar ${active ? 'chat-selected' : ''}`}>
        {renderSidebar()}
      </aside>

      {renderChat()}
      {renderInfoPanel()}
      {renderComposeModal()}
      {renderStoryViewer()}
      {renderForwardModal()}
      {renderPollModal()}
      {renderConfirmDialog()}

      {mediaViewer && (
        <div className="media-viewer" onClick={() => setMediaViewer(null)}>
          <button type="button" className="icon-button" onClick={() => setMediaViewer(null)}><Icon name="close" /></button>
          {isVideo(mediaViewer) ? <video src={mediaViewer} controls autoPlay /> : <img src={mediaViewer} alt="" />}
        </div>
      )}
    </div>
  );
}
