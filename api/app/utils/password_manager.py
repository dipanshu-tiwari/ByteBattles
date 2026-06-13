from pwdlib import PasswordHash
hash_password = PasswordHash.recommended()

def hash(password: str):
    return hash_password.hash(password)

def verify(given_password: str, hashed_password: str):
    return hash_password.verify(given_password, hashed_password)