import { create } from 'zustand';
import { authApi } from '@/api/auth';
import { configureAuthBridge } from '@/api/client';
import type { LoginRequest, User } from '@/types';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  /** True until the initial bootstrap (refresh + me) settles. */
  initializing: boolean;
  login: (credentials: LoginRequest) => Promise<User>;
  logout: () => Promise<void>;
  bootstrap: () => Promise<void>;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: null,
  initializing: true,

  login: async (credentials) => {
    const res = await authApi.login(credentials);
    set({ accessToken: res.access_token, user: res.user });
    return res.user;
  },

  logout: async () => {
    try {
      await authApi.logout();
    } catch {
      // Logout is best-effort; clear local state regardless.
    }
    set({ accessToken: null, user: null });
  },

  /**
   * On app start, try to recover a session from the refresh cookie:
   * refresh -> set access token -> fetch the current user.
   */
  bootstrap: async () => {
    try {
      const { access_token } = await authApi.refresh();
      set({ accessToken: access_token });
      const user = await authApi.me();
      set({ user });
    } catch {
      set({ accessToken: null, user: null });
    } finally {
      set({ initializing: false });
    }
  },

  setUser: (user) => set({ user }),
}));

// Wire the API client to read/update the token held in this store. Done once at
// module load so the interceptors never need to import the store directly.
configureAuthBridge({
  getAccessToken: () => useAuthStore.getState().accessToken,
  onTokenRefreshed: (token) => useAuthStore.setState({ accessToken: token }),
  onAuthFailure: () => useAuthStore.setState({ accessToken: null, user: null }),
});

export const selectIsAuthenticated = (s: AuthState): boolean => Boolean(s.user);
