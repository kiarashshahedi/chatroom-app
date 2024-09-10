from fastapi import FastAPI, Depends
from .auth import get_current_user
from .chat import sio, router as chat_router
from .database import get_user_collection

app = FastAPI()

# Socket.IO ASGI middleware
app.mount("/ws", socketio.ASGIMiddleware(sio))

user_collection = get_user_collection()

@app.get("/me")
async def me(user=Depends(get_current_user)):
    return user

@app.post("/auto-register")
async def auto_register(user=Depends(get_current_user)):
    if not user_collection.find_one({"email": user["email"]}):
        user_collection.insert_one({
            "email": user["email"],
            "username": user["username"]
        })
    return {"message": "User auto-registered"}

# Include chat router
app.include_router(chat_router)
