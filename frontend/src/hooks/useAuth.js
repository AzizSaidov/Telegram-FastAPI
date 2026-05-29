import useAuthStore from '../store/authStore';

export default function useAuth() {
  const { user, isAuthenticated, setAuth, clearAuth, updateUser } =
    useAuthStore();

  return { user, isAuthenticated, setAuth, clearAuth, updateUser };
}
