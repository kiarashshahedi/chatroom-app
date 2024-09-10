from pymongo import MongoClient
from .config import settings
from typing import Optional
import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment variable
MONGO_URI = os.getenv("MONGO_URI")

# Initialize MongoDB client
client = MongoClient(MONGO_URI)

db = client['messenger_db']
users_collection = db["users"]

def get_user_collection():
    return db['users']

def get_chat_collection():
    return db['chats']

# showing online users
def get_online_users_collection():
    return db['online_users']

# getting email 
def get_email_by_sid(sid: str) -> Optional[str]:
    user = users_collection.find_one({"session_id": sid})
    if user:
        return user.get("email")
    return None