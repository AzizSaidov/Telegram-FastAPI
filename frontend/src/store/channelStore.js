import { create } from 'zustand';

const useChannelStore = create((set) => ({
  channelDetail: null,
  members: [],

  setChannelDetail: (detail) => set({ channelDetail: detail }),

  setMembers: (members) => set({ members }),

  addMember: (member) =>
    set((state) => ({ members: [...state.members, member] })),

  removeMember: (username) =>
    set((state) => ({
      members: state.members.filter(
        (m) => m.user.profile.username !== username
      ),
    })),

  updateMemberRole: (username, role) =>
    set((state) => ({
      members: state.members.map((m) =>
        m.user.profile.username === username ? { ...m, role } : m
      ),
    })),

  clearChannel: () => set({ channelDetail: null, members: [] }),
}));

export default useChannelStore;
