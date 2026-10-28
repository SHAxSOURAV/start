import { io, Socket } from "socket.io-client";

const SOCKET_URL = process.env.EXPO_PUBLIC_SOCKET_URL || "http://localhost:8000";

let socket: Socket | null = null;

export const getSocket = (token?: string): Socket => {
  if (!socket) {
    socket = io(SOCKET_URL, {
      autoConnect: false,
      transports: ["websocket"],
      auth: token ? { token } : undefined,
    });
  }
  return socket;
};

export const connectSocket = (token?: string) => {
  const s = getSocket(token);
  if (!s.connected) {
    if (token) {
      s.auth = { token };
    }
    s.connect();
  }
};

export const disconnectSocket = () => {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
};
