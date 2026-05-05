import hashlib
import os
import re
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
        # Legacy plain SHA-256 fallback
        return (
            hashlib.sha256(
                plain_password.encode("utf-8")
            ).hexdigest()
            == stored_hash
        )

    @staticmethod
    def validate_password_strength(password: str) -> dict:
        """
        Returns:
            valid  : bool
            score  : int  0-5
            label  : str  e.g. "Strong"
            errors : list[str]
            checks : dict  per-requirement bool flags
        """
        checks = {
            "length":    len(password) >= 12,
            "uppercase": bool(re.search(r"[A-Z]", password)),
            "lowercase": bool(re.search(r"[a-z]", password)),
            "digit":     bool(re.search(r"\d", password)),
            "special":   bool(
                re.search(r"""[!@#$%^&*()\-_=+\[\]{}|;':",./<>?`~\\]""",
                          password)
            ),
        }
        errors = []
        if not checks["length"]:
            errors.append("At least 12 characters required")
        if not checks["uppercase"]:
            errors.append("At least one uppercase letter (A–Z)")
        if not checks["lowercase"]:
            errors.append("At least one lowercase letter (a–z)")
        if not checks["digit"]:
            errors.append("At least one number (0–9)")
        if not checks["special"]:
            errors.append("At least one special character (!@#$%…)")

        score = sum(checks.values())
        labels = ["Very Weak", "Weak", "Fair", "Good", "Strong", "Very Strong"]

        return {
            "valid":  len(errors) == 0,
            "score":  score,
            "label":  labels[score],
            "errors": errors,
            "checks": checks,
        }

    @staticmethod
    def is_strong_password(password: str) -> bool:
        return SecurityManager.validate_password_strength(password)["valid"]

    @staticmethod
    def generate_otp(length: int = 6) -> str:
        return "".join(str(secrets.randbelow(10)) for _ in range(length))

    @staticmethod
    def generate_session_token(username: str) -> str:
        raw = username + str(os.urandom(16))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()