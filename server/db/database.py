from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from config import settings
from db.base import Base


def make_engine(url: str | None = None):
    url = url or settings.database_url()
    kwargs = {}
    if url.startswith('sqlite'):
        kwargs['connect_args'] = {'check_same_thread': False}
        if url == 'sqlite://' or ':memory:' in url:
            kwargs['poolclass'] = StaticPool
    return create_engine(url, **kwargs)


def make_session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)


def init_db(engine) -> None:
    from db import models  # noqa: F401  (registers all tables)
    Base.metadata.create_all(engine)
