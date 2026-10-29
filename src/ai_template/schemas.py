from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    email : EmailStr
    password : str

class ChatRequest(BaseModel):
    prompt : str

class ChatResponse(BaseModel):
    response : str 
    model : str 

class Token(BaseModel):
    access_token : str 
    token_type : str

class ChatHistoryResponse(BaseModel):
    id : int
    prompt : str
    response : str
    model : str
    created_at : datetime

    model_config = ConfigDict(from_attributes=True)
    
        

    