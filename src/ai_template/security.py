from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from ai_template.config import settings


def get_password_hash(password : str) -> str :

    password_bytes = password.encode('utf-8')

    salt = bcrypt.gensalt()

    hashed_password_bytes = bcrypt.hashpw(password_bytes,salt)

    return hashed_password_bytes.decode('utf-8')

def verify_password(plain_password : str,hashed_password : str) -> bool :

    password_bytes = plain_password.encode('utf-8')

    hashed_password_bytes = hashed_password.encode('utf-8')

    return bcrypt.checkpw(password_bytes,hashed_password_bytes)

def create_access_token(data : dict) -> str :
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes = settings.access_token_expire_minutes)

    to_encode.update({"exp":expire})

    return jwt.encode(to_encode,settings.secret_key,algorithm = settings.algorithm)
    




    


                        
