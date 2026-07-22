import pytest

from app.core.security import (
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify_roundtrip():
    hashed = hash_password("MySecretPass123")
    assert hashed != "MySecretPass123"
    assert verify_password("MySecretPass123", hashed)
    assert not verify_password("WrongPassword", hashed)


def test_access_token_roundtrip():
    token = create_access_token(user_id="abc-123", role="user")
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == "abc-123"
    assert payload["role"] == "user"


def test_refresh_token_rejected_as_access_token():
    token = create_refresh_token(user_id="abc-123")
    with pytest.raises(InvalidTokenError):
        decode_token(token, expected_type="access")


def test_invalid_token_raises():
    with pytest.raises(InvalidTokenError):
        decode_token("not-a-real-token", expected_type="access")
