import { create } from 'zustand';
import axios from 'axios';
import { reconnectSocket } from '../lib/socket';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export const useAuthStore = create((set, get) => ({
  user: JSON.parse(localStorage.getItem('auth_user') || 'null'),
  accessToken: localStorage.getItem('auth_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  authError: null,
  authLoading: false,
  pendingTwoFactorToken: null,

  isAuthenticated: () => !!get().accessToken,

  login: async (username, password) => {
    set({ authLoading: true, authError: null, pendingTwoFactorToken: null });
    try {
      const { data } = await axios.post(`${API_URL}/auth/login`, { username, password });

      if (data.requires_2fa) {
        set({ pendingTwoFactorToken: data.temp_token, authLoading: false });
        return 'requires_2fa';
      }

      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('auth_user', JSON.stringify(data.user));
      set({ user: data.user, accessToken: data.access_token, refreshToken: data.refresh_token, authLoading: false });
      reconnectSocket();
      return true;
    } catch (error) {
      set({ authError: error.response?.data?.error || 'Login failed', authLoading: false });
      return false;
    }
  },

  verifyTwoFactor: async (code) => {
    set({ authLoading: true, authError: null });
    try {
      const { data } = await axios.post(`${API_URL}/auth/2fa/login-verify`, { code }, {
        headers: { Authorization: `Bearer ${get().pendingTwoFactorToken}` },
      });
      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('auth_user', JSON.stringify(data.user));
      set({ user: data.user, accessToken: data.access_token, refreshToken: data.refresh_token, authLoading: false, pendingTwoFactorToken: null });
      reconnectSocket();
      return true;
    } catch (error) {
      set({ authError: error.response?.data?.error || 'Invalid 2FA code', authLoading: false });
      return false;
    }
  },

  register: async (username, email, password, role = 'analyst') => {
    set({ authLoading: true, authError: null });
    try {
      const { data } = await axios.post(`${API_URL}/auth/register`, { username, email, password, role });
      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('auth_user', JSON.stringify(data.user));
      set({ user: data.user, accessToken: data.access_token, refreshToken: data.refresh_token, authLoading: false });
      return true;
    } catch (error) {
      set({ authError: error.response?.data?.error || 'Registration failed', authLoading: false });
      return false;
    }
  },

  logout: async () => {
    try {
      await axios.post(`${API_URL}/auth/logout`, {}, {
        headers: { Authorization: `Bearer ${get().accessToken}` },
      });
    } catch (error) {
      // Ignore network errors on logout, still clear local session
    }
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('auth_user');
    set({ user: null, accessToken: null, refreshToken: null });
    reconnectSocket();
  },

  clearAuthError: () => set({ authError: null }),
}));

export default useAuthStore;
