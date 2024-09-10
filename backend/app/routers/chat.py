from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import List
from app.auth import verify_token
from app.database import get_email_by_sid

router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, token: str):
        sid = token  # Assuming token is used as session ID
        email = get_email_by_sid(sid)
        if email:
            await websocket.accept()
            self.active_connections.append(websocket)
            # You can use the email for further logic
        else:
            await websocket.close()

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

# Initialize the manager
manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Depends(verify_token)):
    await manager.connect(websocket, token)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_message(f"Message text was: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
