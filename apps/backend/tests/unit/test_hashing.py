from auth.hashing import hash_password, verify_password


class TestPasswordHashing:
    def test_hash_returns_different_from_plain(self):
        hashed = hash_password("secret123")
        assert hashed != "secret123"
        assert hashed.startswith("$2")

    def test_verify_correct_password(self):
        hashed = hash_password("secret123")
        assert verify_password("secret123", hashed) is True

    def test_verify_incorrect_password(self):
        hashed = hash_password("secret123")
        assert verify_password("wrong", hashed) is False

    def test_hash_is_stable_for_same_input(self):
        hashed = hash_password("secret123")
        assert verify_password("secret123", hashed) is True
        assert verify_password("secret123", hashed) is True

    def test_different_salts_produce_different_hashes(self):
        h1 = hash_password("secret123")
        h2 = hash_password("secret123")
        assert h1 != h2
