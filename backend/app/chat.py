import socketio
from fastapi import APIRouter, Depends
from .auth import get_current_user
from .database import get_chat_collection, get_user_collection
from .models import Message

sio = socketio.AsyncServer(async_mode='asgi')
router = APIRouter()

chat_collection = get_chat_collection()
user_collection = get_user_collection()

@sio.event
async def connect(sid, environ):
    print('Client connected:', sid)

@sio.event
async def disconnect(sid):
    print('Client disconnected:', sid)

@sio.event
async def send_message(sid, data):
    sender = data['sender']
    content = data['content']
    group = data['group']
    private = data.get('private', False)
    
    message = Message(sender=sender, content=content, group=group, private=private)
    
    chat_collection.update_one(
        {"participants": {"$all": [sender]} if private else {"$in": [group]}},
        {"$push": {"messages": message.dict()}},
        upsert=True
    )
    await sio.emit('receive_message', message.dict(), room=group)

@router.get("/chat-history/{group}")
async def get_chat_history(group: str, user=Depends(get_current_user)):
    chats = chat_collection.find_one({"participants": {"$in": [group]}})
    if not chats:
        return []
    return chats.get("messages", [])
