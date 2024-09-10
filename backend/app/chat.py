from typing import Optional
import socketio
from fastapi import APIRouter, Depends
from .auth import decode_token, get_current_user
from .database import get_chat_collection, get_user_collection, get_email_by_sid
from .models import Message
from fastapi import HTTPException
from .database import get_online_users_collection
from datetime import datetime
from fastapi import File, UploadFile, HTTPException
import os
from fastapi.responses import FileResponse
from uuid import uuid4
from fastapi.middleware.wsgi import WSGIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI




sio = socketio.AsyncServer()
app = FastAPI()

# Mount the Socket.IO ASGI app into FastAPI
app.add_middleware(BaseHTTPMiddleware, dispatch=sio)

router = APIRouter()

chat_collection = get_chat_collection()
user_collection = get_user_collection()

# Track Users When They Connect or Disconnect
online_users_collection = get_online_users_collection()

@sio.event
async def connect(sid, environ):
    token = environ['HTTP_AUTHORIZATION'].replace("Bearer ", "")
    user = decode_token(token)

    # Mark user as online
    online_users_collection.update_one(
        {"email": user["email"]},
        {"$set": {"email": user["email"], "last_seen": None, "online": True}},
        upsert=True
    )

    # Join room for private chats (user's email acts as room ID)
    await sio.enter_room(sid, user["email"])

    # Optionally join group rooms if the user is in any groups
    user_groups = chat_collection.find({"participants": user["email"]})
    for group in user_groups:
        await sio.enter_room(sid, group["group"])

    print(f"User {user['email']} connected")
    await sio.emit('online_users', await get_online_users(), room=sid)

@sio.event
async def disconnect(sid):
    # Handle disconnection
    user_email = await get_email_by_sid(sid)
    if user_email:
        # Mark user as offline and update last seen time
        online_users_collection.update_one(
            {"email": user_email},
            {"$set": {"online": False, "last_seen": datetime.utcnow()}}
        )
        print(f"User {user_email} disconnected")
        await sio.emit('online_users', await get_online_users())
        
@sio.event
async def disconnect(sid):
    print('Client disconnected:', sid)

# Send Messages in Private or Group Chats
@sio.event
async def send_message(sid, data):
    sender = data['sender']
    content = data.get('content', '')  # Text message content
    media_url = data.get('media_url', None)  # Media URL if available
    private = data.get('private', False)
    group = data.get('group', None)
    receiver = data.get('receiver', None)
    
    message = {
        "sender": sender,
        "content": content,
        "media_url": media_url,  # Include the media URL
        "group": group,
        "private": private
    }

    if private and receiver:
        # Send private message
        chat_collection.update_one(
            {"participants": {"$all": [sender, receiver]}},
            {"$push": {"messages": message}},
            upsert=True
        )
        await sio.emit('receive_message', message, room=receiver)
    elif group:
        # Send group message
        chat_collection.update_one(
            {"group": group},
            {"$push": {"messages": message}},
            upsert=True
        )
        await sio.emit('receive_message', message, room=group)

# get chat history 
@router.get("/chat-history")
async def get_chat_history(group: Optional[str] = None, receiver: Optional[str] = None, user=Depends(get_current_user)):
    if group:
        chats = chat_collection.find_one({"group": group})
    elif receiver:
        chats = chat_collection.find_one({"participants": {"$all": [user["email"], receiver]}, "private": True})
    else:
        raise HTTPException(status_code=400, detail="Either group or receiver must be provided")
    
    if not chats:
        return []
    
    return chats.get("messages", [])

#Add Endpoint to Create Groups
@router.post("/create-group")
async def create_group(group_name: str, user=Depends(get_current_user)):
    # Check if group exists
    group = chat_collection.find_one({"group": group_name})
    if group:
        raise HTTPException(status_code=400, detail="Group already exists")
    
    # Create new group
    chat_collection.insert_one({
        "group": group_name,
        "participants": [user["email"]],
        "messages": []
    })
    return {"message": f"Group '{group_name}' created"}

# Add Users to Group
@router.post("/add-to-group")
async def add_to_group(group_name: str, new_user: str, user=Depends(get_current_user)):
    
    group = chat_collection.find_one({"group": group_name})
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if user["email"] not in group["participants"]:
        raise HTTPException(status_code=403, detail="Not authorized to add users to this group")
    
    chat_collection.update_one(
        {"group": group_name},
        {"$addToSet": {"participants": new_user}}
    )
    return {"message": f"Added {new_user} to group '{group_name}'"}

# Start Private Chat
@router.post("/start-private-chat")
async def start_private_chat(receiver_email: str, user=Depends(get_current_user)):
    existing_chat = chat_collection.find_one({
        "participants": {"$all": [user["email"], receiver_email]},
        "private": True
    })
    if existing_chat:
        return {"message": "Private chat already exists"}

    # Create a new private chat
    chat_collection.insert_one({
        "participants": [user["email"], receiver_email],
        "private": True,
        "messages": []
    })
    return {"message": f"Private chat with {receiver_email} started"}

# Getting Online Users
async def get_online_users():
    
    # Fetch online users
    online_users = online_users_collection.find({"online": True}, {"_id": 0, "email": 1})
    
    # Emit updated online users to all clients
    await sio.emit('online_users', await get_online_users())  
      
    return [user['email'] for user in online_users]

# Add API Endpoint to Fetch Online Users
@router.get("/online-users")
async def fetch_online_users():
    return await get_online_users()

# Medias

# Define the folder to store uploaded files
UPLOAD_DIRECTORY = "uploaded_files"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

@router.post("/upload-media/")
async def upload_media(file: UploadFile = File(...), user=Depends(get_current_user)):
    # Generate a unique filename
    file_extension = file.filename.split(".")[-1]
    file_name = f"{uuid4()}.{file_extension}"

    # Save the uploaded file
    file_path = os.path.join(UPLOAD_DIRECTORY, file_name)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    file_url = f"/media/{file_name}"
    return {"file_url": file_url}

# Serve the uploaded files
@router.get("/media/{file_name}")
async def get_media(file_name: str):
    file_path = os.path.join(UPLOAD_DIRECTORY, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)