from datetime import datetime
from sqlalchemy import JSON, ForeignKey, Text, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from .config import settings

engine = create_engine(settings.database_url,
                       connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {})
SessionLocal = sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    role: Mapped[str]                  # citizen | tech | elected
    lang: Mapped[str] = mapped_column(default="English")   # language of the AI updates sent to this user
    password_hash: Mapped[str]
    created: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Ticket(Base):
    __tablename__ = "tickets"
    ref: Mapped[str] = mapped_column(primary_key=True)
    id: Mapped[int] = mapped_column(unique=True)
    title: Mapped[str]
    type: Mapped[str]
    addr: Mapped[str]
    owner: Mapped[str]                 # who owns the land: commune | department | state | epci | private | network
    reporter_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))   # the citizen who reported it
    desc: Mapped[str] = mapped_column(Text, default="")
    lat: Mapped[float | None]
    lng: Mapped[float | None]          # TODO: PostGIS geometry column when you move to PostgreSQL
    st: Mapped[int]                    # pipeline stage 0-7
    sev: Mapped[int]
    urg: Mapped[int]
    due: Mapped[int]
    cost_min: Mapped[float | None]
    cost_max: Mapped[float | None]
    created: Mapped[datetime]
    image_path: Mapped[str | None]     # the citizen photo, saved once as uploads/<ref>.jpg
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    # cons, zone, rep, ai, ch, followers (user ids), street_name, damage, after, detour, merged_into
    audit: Mapped[list["Audit"]] = relationship(cascade="all, delete-orphan", order_by="Audit.id", lazy="selectin")


class Audit(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    ref: Mapped[str] = mapped_column(ForeignKey("tickets.ref"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    d: Mapped[str]
    w: Mapped[str]
    e: Mapped[str] = mapped_column(Text)
    has_img: Mapped[bool] = mapped_column(default=False)        # shows the ticket's main photo
    image_path: Mapped[str | None]     # or its own photo: a merged report, the after-repair photo


class Notification(Base):
    __tablename__ = "notifications"    # plain-language updates for the citizens who reported or follow a ticket
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    ref: Mapped[str] = mapped_column(ForeignKey("tickets.ref"))
    text: Mapped[str] = mapped_column(Text)
    created: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    read: Mapped[bool] = mapped_column(default=False)


class Insight(Base):
    __tablename__ = "insights"         # saved AI outputs: weekly brief, hotspot forecast
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str]                  # weekly | forecast
    created: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    by: Mapped[str]
    data: Mapped[dict] = mapped_column(JSON)


class Zone(Base):
    __tablename__ = "zones"            # zones drawn by technicians / elected officials
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    level: Mapped[int]
    points: Mapped[list] = mapped_column(JSON)
    source: Mapped[str] = mapped_column(default="manual")


def add_missing_columns() -> None:
    """Stopgap until Alembic: add columns that the code has and the database lacks, keeping the data.
    Handles new columns only (no renames, no type changes)."""
    insp = inspect(engine)
    with engine.begin() as c:
        for table in Base.metadata.sorted_tables:
            if not insp.has_table(table.name):
                continue                   # create_all makes it
            have = {col["name"] for col in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name in have:
                    continue
                default = col.default.arg if col.default is not None and col.default.is_scalar else None
                sql = f'ALTER TABLE {table.name} ADD COLUMN {col.name} {col.type.compile(engine.dialect)}'
                if default is not None:
                    sql += f" DEFAULT {int(default) if isinstance(default, bool) else repr(default)}"
                c.execute(text(sql))


def get_db():
    with SessionLocal() as s:
        yield s
