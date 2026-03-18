import hashlib
import os


class SecurityManager:

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return SecurityManager.hash_password(plain_password) == hashed_password

    @staticmethod
    def is_strong_password(password: str) -> bool:
        if len(password) < 6:
            return False
        return True

    @staticmethod
    def generate_session_token(username: str) -> str:
        raw = username + str(os.urandom(16))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()