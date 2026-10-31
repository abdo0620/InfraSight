from services.security import create_token, hash_password, read_token, verify_password


def test_password_hash_roundtrip():
    h = hash_password('secret')
    assert verify_password('secret', h) and not verify_password('wrong', h)
    assert h != hash_password('secret')           # salted


def test_token_roundtrip_and_expiry():
    assert read_token(create_token('u1', 'staff'))['role'] == 'staff'
    assert read_token(create_token('u1', 'staff', ttl_s=-1)) is None
    assert read_token('garbage') is None


def test_tampered_token_is_rejected():
    body, sig = create_token('u1', 'citizen').split('.')
    assert read_token(f'{body}.{"0" * len(sig)}') is None
