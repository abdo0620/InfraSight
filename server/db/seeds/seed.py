"""Idempotent seed of reference data (departments, SLA policies, jurisdictions).
CLI: python -m db.seeds.seed [--staff-user NAME --staff-password PW]"""
import argparse
import json

from sqlalchemy import select

from config import settings
from db.database import init_db, make_engine, make_session_factory
from db.models import Department, Jurisdiction, SlaPolicy, User


def _read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def seed_reference_data(db) -> None:
    for d in _read(settings.SEEDS_DIR / 'departments.json'):
        if not db.scalar(select(Department).where(Department.name == d['name'])):
            db.add(Department(name=d['name'], categories=d['categories']))

    for f in sorted((settings.RULES_DIR / 'sla-policies').glob('*.json')):
        data = _read(f)
        for p in data['policies']:
            if not db.scalar(select(SlaPolicy).where(SlaPolicy.name == p['name'])):
                db.add(SlaPolicy(
                    name=p['name'], category_pattern=p.get('category_pattern'),
                    severity_pattern=p.get('severity_pattern'), response_days=p['response_days'],
                    is_default=p.get('is_default', False), version=data['version'],
                ))

    for f in sorted((settings.RULES_DIR / 'jurisdiction-rules').glob('*.json')):
        j = _read(f)
        if not db.scalar(select(Jurisdiction).where(Jurisdiction.code == j['code'])):
            cfg = {k: j[k] for k in ('bbox', 'utility_alert', 'version') if k in j}
            db.add(Jurisdiction(code=j['code'], name=j['name'], region=j.get('region'),
                                country=j.get('country', 'FR'), config=cfg))
    db.commit()


def create_staff_user(db, username: str, password: str) -> None:
    from services.security import hash_password
    if not db.scalar(select(User).where(User.username == username)):
        db.add(User(username=username, password_hash=hash_password(password), role='staff'))
        db.commit()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--staff-user')
    ap.add_argument('--staff-password')
    args = ap.parse_args()
    engine = make_engine()
    init_db(engine)
    with make_session_factory(engine)() as session:
        seed_reference_data(session)
        if args.staff_user and args.staff_password:
            create_staff_user(session, args.staff_user, args.staff_password)
    print('Seed complete.')
