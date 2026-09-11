import { create } from 'zustand';
import { getSocket } from '../lib/socket';

let listenerAttached = false;

export const useNotificationStore = create((set, get) => ({
  notifications: [],
  unreadCount: 0,

  init: () => {
    if (listenerAttached) return;
    listenerAttached = true;

    const socket = getSocket();
    socket.on('risk_alert', (payload) => {
      // Only surface HIGH risk signals as notifications to avoid noise
      if (payload.risk_level !== 'HIGH') return;
      set((state) => ({
        notifications: [{ ...payload, id: `${payload.customer_id}-${payload.timestamp}` }, ...state.notifications].slice(0, 50),
        unreadCount: state.unreadCount + 1,
      }));
    });
  },

  markAllRead: () => set({ unreadCount: 0 }),

  clear: () => set({ notifications: [], unreadCount: 0 }),
}));

export default useNotificationStore;
