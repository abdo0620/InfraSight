"""Account admin. Run from backend/:
    python -m app.cli create-user <username> <citizen|tech|elected> "Display name"
    python -m app.cli set-role <username> <citizen|tech|elected>
    python -m app.cli set-password <username>
"""
import getpass, sys
from .auth import ROLES, hash_password
from .db import Base, SessionLocal, User, engine


def _password() -> str:
    pw = getpass.getpass("Password (8+ characters): ")
    if len(pw) < 8 or pw != getpass.getpass("Repeat: "):
        sys.exit("Passwords too short or do not match")
    return pw


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[0] not in ("create-user", "set-role", "set-password"):
        sys.exit(__doc__)
    Base.metadata.create_all(engine)
    cmd, username = argv[0], argv[1].lower()
    with SessionLocal() as s:
        u = s.query(User).filter_by(username=username).first()
        if cmd == "create-user":
            if u:
                sys.exit("User exists")
            if len(argv) < 3 or argv[2] not in ROLES:
                sys.exit(__doc__)
            s.add(User(username=username, name=argv[3] if len(argv) > 3 else username, role=argv[2],
                       password_hash=hash_password(_password())))
        elif not u:
            sys.exit("No such user")
        elif cmd == "set-role":
            if len(argv) < 3 or argv[2] not in ROLES:
                sys.exit(__doc__)
            u.role = argv[2]
        else:
            u.password_hash = hash_password(_password())
        s.commit()
    print("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
