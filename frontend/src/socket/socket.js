class SocketManager {
  constructor() {
    this.ws = null;
    this.handlers = {};
    this.reconnectTimer = null;
    this.isConnecting = false;
    this.reconnectDelay = 2000;
    this.maxReconnectDelay = 30000;
    this.stopped = false;
    this.token = null;
  }

  connect(token) {
    if (!token) return;

    if (this.ws && this.token === token) return;
    if (this.ws && this.token !== token) this.disconnect();
    if (this.isConnecting) return;

    this.token = token;
    this.stopped = false;
    this.isConnecting = true;

    const wsBase = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
    this.ws = new WebSocket(`${wsBase}/ws?token=${encodeURIComponent(token)}`);

    this.ws.onopen = () => {
      this.isConnecting = false;
      this.reconnectDelay = 2000;
    };

    this.ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        const listeners = this.handlers[payload.type] || [];
        listeners.forEach((handler) => handler(payload.data || {}));
      } catch {
        const listeners = this.handlers.error || [];
        listeners.forEach((handler) => handler({ detail: 'Invalid socket message' }));
      }
    };

    this.ws.onclose = (event) => {
      this.ws = null;
      this.isConnecting = false;

      if (this.stopped || event.code === 1000 || event.code === 1008) return;

      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = setTimeout(() => {
        const savedToken = localStorage.getItem('access_token');
        if (savedToken) this.connect(savedToken);
      }, this.reconnectDelay);

      this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, this.maxReconnectDelay);
    };

    this.ws.onerror = () => {};
  }

  disconnect() {
    this.stopped = true;
    this.token = null;
    clearTimeout(this.reconnectTimer);
    this.reconnectTimer = null;
    if (this.ws) {
      this.ws.close(1000);
      this.ws = null;
    }
    this.isConnecting = false;
  }

  send(type, data = {}) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, data }));
    }
  }

  on(type, handler) {
    if (!this.handlers[type]) this.handlers[type] = [];
    if (!this.handlers[type].includes(handler)) {
      this.handlers[type].push(handler);
    }
  }

  off(type, handler) {
    if (!this.handlers[type]) return;
    this.handlers[type] = this.handlers[type].filter((item) => item !== handler);
  }

  isConnected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

const socketManager = new SocketManager();

export default socketManager;
