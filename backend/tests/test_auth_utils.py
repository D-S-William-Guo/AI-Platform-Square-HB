"""Unit tests for auth_utils.py — password hashing, strength validation, tokens."""

import pytest
from app.auth_utils import (
    generate_session_token,
    hash_password,
    password_character_class_count,
    validate_password_strength,
    verify_password,
    PASSWORD_POLICY_TEXT,
)


class TestPasswordCharacterClassCount:
    def test_all_lowercase(self):
        assert password_character_class_count("abcdefghij") == 1

    def test_lowercase_and_uppercase(self):
        assert password_character_class_count("Abcdefghij") == 2

    def test_lowercase_uppercase_and_digit(self):
        assert password_character_class_count("Abcdefgh1j") == 3

    def test_all_four_classes(self):
        assert password_character_class_count("Abcdefg1!j") == 4

    def test_empty_string(self):
        assert password_character_class_count("") == 0

    def test_only_symbols(self):
        assert password_character_class_count("!@#$%^&*()") == 1

    def test_only_digits(self):
        assert password_character_class_count("1234567890") == 1

    def test_unicode_chars(self):
        # Unicode letters are not ASCII uppercase/lowercase
        assert password_character_class_count("中文测试abcdef") == 1


class TestValidatePasswordStrength:
    def test_too_short_raises(self):
        with pytest.raises(ValueError, match=PASSWORD_POLICY_TEXT):
            validate_password_strength("Ab1!")

    def test_missing_classes_raises(self):
        with pytest.raises(ValueError, match=PASSWORD_POLICY_TEXT):
            validate_password_strength("abcdefghijkl")  # only lowercase

    def test_compliant_password_passes(self):
        # 10 chars, 3 classes (lower+upper+digit)
        validate_password_strength("Abcdefgh1j")

    def test_exactly_three_classes_passes(self):
        validate_password_strength("TestPass1!@#")

    def test_all_four_classes_passes(self):
        validate_password_strength("MyP@ssw0rd!")

    def test_minimum_length_exactly(self):
        validate_password_strength("Ab1cdefgh2")  # exactly 10 chars


class TestHashPassword:
    def test_returns_string_with_expected_format(self):
        result = hash_password("testpassword123")
        assert result.startswith("pbkdf2_sha256$")
        parts = result.split("$")
        assert len(parts) == 4
        assert parts[0] == "pbkdf2_sha256"
        assert parts[1] == "480000"  # iterations

    def test_same_password_produces_different_hash(self):
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2  # different salts

    def test_different_passwords_produce_different_hashes(self):
        h1 = hash_password("password1!")
        h2 = hash_password("password2!")
        assert h1 != h2


class TestVerifyPassword:
    def test_roundtrip(self):
        password = "MyTestP@ss1"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_wrong_password(self):
        hashed = hash_password("correct_password1")
        assert verify_password("wrong_password1", hashed) is False

    def test_malformed_hash_returns_false(self):
        assert verify_password("anything", "not_a_valid_hash") is False

    def test_wrong_scheme_returns_false(self):
        assert verify_password("anything", "pbkdf2_sha1$1000$abc$def") is False

    def test_empty_string_password(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True

    def test_none_iterations_returns_false(self):
        assert verify_password("anything", "pbkdf2_sha256$notanumber$abc$def") is False


class TestGenerateSessionToken:
    def test_returns_non_empty_string(self):
        token = generate_session_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_returns_url_safe_string(self):
        token = generate_session_token()
        # URL-safe base64 should not contain +, /, or =
        assert "+" not in token
        assert "/" not in token

    def test_returns_64_characters(self):
        # 48 bytes in url-safe base64 = 64 characters
        token = generate_session_token()
        assert len(token) == 64

    def test_unique_on_successive_calls(self):
        tokens = [generate_session_token() for _ in range(10)]
        assert len(set(tokens)) == 10
