import { io } from 'socket.io-client';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

let socket = null;

// Shared Socket.IO connection so multiple components (live feed, notification
// bell, etc.) don't each open their own duplicate WebSocket. The auth
// callback re-reads the token on every (re)connect so switching users or
// activating a different dataset is picked up without recreating the socket.
export const getSocket = () => {
  if (!socket) {
    socket = io(API_URL, {
      transports: ['websocket', 'polling'],
      auth: (cb) => cb({ token: localStorage.getItem('auth_token') }),
    });
  }
  return socket;
};

// Forces the socket to re-handshake (and re-join the correct dataset room)
// after a login, logout, or dataset activation changes the active token/dataset.
export const reconnectSocket = () => {
  if (socket) {
    socket.disconnect();
    socket.connect();
  }
};

export default getSocket;
