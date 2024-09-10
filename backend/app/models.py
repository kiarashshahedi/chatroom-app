from pydantic import BaseModel
from typing import List, Optional

class User(BaseModel):
    email: str
    username: str

class Message(BaseModel):
    sender: str
    content: str
    group: str
    private: bool = False

class Chat(BaseModel):
    participants: List[str]
    messages: List[Message]
