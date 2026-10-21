from datetime import datetime, timedelta, timezone

import bcrypt

def get_password_hash(password : str) -> str :

    password_bytes = password.encode('utf-8')

    salt = bcrypt.gensalt()

    hashed_password_bytes = bcrypt.hashpw(password_bytes,salt)

    return hashed_password_bytes.decode('utf-8')

def verify_password(plain_password : str,hashed_password : str) -> bool :

    password_bytes = plain_password.encode('utf-8')

    hashed_password_bytes = hashed_password.encode('utf-8')

    return bcrypt.checkpw(password_bytes,hashed_password_bytes)

# def create_access_token(data : dict , expires_delta : timedelta = timedelta(minutes = 15)):
#     to_encode = data.copy()

#     expire = datetime.now(timezone.utc) + expires_delta 

#     to_encode.update({'exp':expire})

    




    


                        
