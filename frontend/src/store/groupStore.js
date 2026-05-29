import { create } from 'zustand';

const useGroupStore = create((set) => ({
  groupDetail: null,
  members: [],

  setGroupDetail: (detail) => set({ groupDetail: detail }),

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

  clearGroup: () => set({ groupDetail: null, members: [] }),
}));

export default useGroupStore;
