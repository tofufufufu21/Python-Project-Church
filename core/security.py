import hashlib
import os
import secrets


class SecurityManager:

    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_hex(16)
        hashed = hashlib.sha256(
            (salt + password).encode("utf-8")
        ).hexdigest()
        return "{}:{}".format(salt, hashed)

    @staticmethod
    def verify_password(plain_password: str, stored_hash: str) -> bool:
        if ":" in stored_hash:
            salt, hashed = stored_hash.split(":", 1)
            return (
                hashlib.sha256(
                    (salt + plain_password).encode("utf-8")
                ).hexdigest()
                == hashed
            )
        # Legacy support — old plain SHA256 passwords
        return (
            hashlib.sha256(
                plain_password.encode("utf-8")
            ).hexdigest()
            == stored_hash
        )

    @staticmethod
    def is_strong_password(password: str) -> bool:
        return len(password) >= 6

    @staticmethod
    def generate_session_token(username: str) -> str:
        raw = username + str(os.urandom(16))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()