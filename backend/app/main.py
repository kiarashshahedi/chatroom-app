from fastapi import FastAPI, Depends
import socketio
from .auth import get_current_user
from .chat import sio, router as chat_router
from .database import get_user_collection
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import timedelta
from .auth import create_access_token, verify_token

app = FastAPI()

# Token authentication

# Simulated user login
class UserLogin(BaseModel):
    username: str

@app.post("/token")
async def login_for_access_token(user_login: UserLogin):
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user_login.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# protected route
@app.get("/users/me")
async def read_users_me(token: str = Depends(verify_token)):
    return {"username": token}



# Serve static files (HTML, CSS, JS) from the "frontend" directory
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


user_collection = get_user_collection()

# return user
@app.get("/me")
async def me(user=Depends(get_current_user)):
    return user

# auto register user
@app.post("/auto-register")
async def auto_register(user=Depends(get_current_user)):
    if not user_collection.find_one({"email": user["email"]}):
        user_collection.insert_one({
            "email": user["email"],
            "username": user["username"]
        })
    return {"message": "User auto-registered"}


# Include routers
app.include_router(chat_router)
