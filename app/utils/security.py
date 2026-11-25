from pwdlib import PasswordHash
import jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
load_dotenv()


password_hash = PasswordHash.recommended()


def hashed_password(password:str) -> str:
    hash_value = password_hash.hash(password)
    return hash_value

def verify_password(password:str,stored_hash) -> bool :
    return password_hash.verify(password,stored_hash)

def create_access_token(user_id):
    expiry = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode= {"exp":expiry , "sub":str(user_id)}

    encoded_jwt = jwt.encode(to_encode, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))

    return encoded_jwt

def verify_access_token(token):
    
    return jwt.decode(token, os.getenv("SECRET_KEY"),algorithms=[os.getenv("ALGORITHM")])
