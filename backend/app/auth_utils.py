import base64
import hashlib
import hmac
import secrets


PBKDF2_ALGO = "sha256"
PBKDF2_ITERATIONS = 480_000
PBKDF2_SALT_BYTES = 16
PASSWORD_MIN_LENGTH = 10
PASSWORD_REQUIRED_CHARACTER_CLASSES = 3
PASSWORD_POLICY_TEXT = "密码至少10位，且需包含大写字母、小写字母、数字、符号中的至少三类"


def password_character_class_count(password: str) -> int:
    classes = [
        any(char.islower() for char in password),
        any(char.isupper() for char in password),
        any(char.isdigit() for char in password),
        any(not char.isalnum() for char in password),
    ]
    return sum(1 for matched in classes if matched)


def validate_password_strength(password: str) -> None:
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(PASSWORD_POLICY_TEXT)
    if password_character_class_count(password) < PASSWORD_REQUIRED_CHARACTER_CLASSES:
        raise ValueError(PASSWORD_POLICY_TEXT)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(PBKDF2_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        PBKDF2_ALGO,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    salt_b64 = base64.urlsafe_b64encode(salt).decode("ascii")
    hash_b64 = base64.urlsafe_b64encode(derived).decode("ascii")
    return f"pbkdf2_{PBKDF2_ALGO}${PBKDF2_ITERATIONS}${salt_b64}${hash_b64}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, iterations, salt_b64, hash_b64 = password_hash.split("$", 3)
        if scheme != f"pbkdf2_{PBKDF2_ALGO}":
            return False
        iter_count = int(iterations)
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(hash_b64.encode("ascii"))
    except Exception:
        return False

    calculated = hashlib.pbkdf2_hmac(
        PBKDF2_ALGO,
        password.encode("utf-8"),
        salt,
        iter_count,
    )
    return hmac.compare_digest(calculated, expected)


def generate_session_token() -> str:
    return secrets.token_urlsafe(48)
