import time
from datetime import timedelta
from app.auth.utils import hash_password, verify_password, create_access_token, decode_token
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES


class TestHashPassword:
    def test_hash_and_verify(self):
        hashed = hash_password("minha_senha")
        assert verify_password("minha_senha", hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("senha_correta")
        assert not verify_password("senha_errada", hashed)

    def test_different_hashes_for_same_password(self):
        h1 = hash_password("teste")
        h2 = hash_password("teste")
        assert h1 != h2


class TestJwtToken:
    def test_create_and_decode(self):
        token = create_access_token({"sub": "admin", "role": "admin"})
        payload = decode_token(token)
        assert payload["sub"] == "admin"
        assert payload["role"] == "admin"

    def test_expired_token(self):
        token = create_access_token(
            {"sub": "user"},
            expires_delta=timedelta(days=-1),
        )
        payload = decode_token(token)
        assert payload is None

    def test_invalid_token(self):
        payload = decode_token("token.invalido.aqui")
        assert payload is None

    def test_token_contains_exp(self):
        token = create_access_token({"sub": "user"})
        payload = decode_token(token)
        assert "exp" in payload
