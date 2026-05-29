from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        connections = self.active_connections.get(user_id)

        if not connections:
            return

        if websocket in connections:
            connections.remove(websocket)

        if not connections:
            self.active_connections.pop(user_id, None)

    def is_user_connected(self, user_id: int):
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0

    async def send_to_user(self, user_id: int, data: dict):
        connections = self.active_connections.get(user_id, [])

        for websocket in connections.copy():
            try:
                await websocket.send_json(data)
            except (RuntimeError, WebSocketDisconnect):
                self.disconnect(user_id, websocket)

    async def broadcast_to_users(self, user_ids: list[int], data: dict):
        for user_id in set(user_ids):
            await self.send_to_user(user_id, data)

    async def broadcast(self, data: dict):
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, data)


manager = ConnectionManager()
