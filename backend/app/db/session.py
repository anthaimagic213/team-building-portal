"""
Database Session Management

Quản lý kết nối database và khởi tạo tables.
"""

from typing import Generator
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Create SQLite engine with proper configuration
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.

    Usage in FastAPI endpoints:
        def my_endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.db.base import Base

    # Import toàn bộ models để SQLAlchemy nhận diện table
    from app.db.models import (
        Event,
        Team,
        User,
        RefreshToken,
        Flight,
        Vehicle,
        Registration,
        GalaSeat,
        GalaConfig,
        GalaTeamTurn,
        Hotel,
        HotelRoom,
        AuditLog,
        EventRepresentative,
    )

    Base.metadata.create_all(bind=engine)

    # Keep existing data while upgrading registrations for event-scoped teams.
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("registrations")}
    if "team_id" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE registrations ADD COLUMN team_id VARCHAR"))
        print("Added registrations.team_id")

    gala_seat_columns = {column["name"] for column in inspector.get_columns("gala_seats")}
    if "locked_by_user_id" not in gala_seat_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE gala_seats ADD COLUMN locked_by_user_id VARCHAR"))
        print("Added gala_seats.locked_by_user_id")

    registration_columns = {column["name"] for column in inspector.get_columns("registrations")}
    with engine.begin() as connection:
        for column_name in ("assigned_outbound_flight_id", "assigned_return_flight_id"):
            if column_name not in registration_columns:
                connection.execute(text(f"ALTER TABLE registrations ADD COLUMN {column_name} VARCHAR"))
                print(f"Added registrations.{column_name}")

    gala_columns = {column["name"] for column in inspector.get_columns("gala_configs")}
    with engine.begin() as connection:
        if "rows" not in gala_columns:
            connection.execute(text("ALTER TABLE gala_configs ADD COLUMN rows INTEGER NOT NULL DEFAULT 0"))
        if "columns" not in gala_columns:
            connection.execute(text("ALTER TABLE gala_configs ADD COLUMN columns INTEGER NOT NULL DEFAULT 0"))

    # Older databases may have been created with a one-registration-per-user
    # unique index.  Rebuild only that table when necessary so one user can
    # register for multiple events without losing existing rows.
    if engine.url.get_backend_name() == "sqlite":
        with engine.begin() as connection:
            indexes = connection.execute(text("PRAGMA index_list(registrations)")).fetchall()
            has_user_unique = False
            for index in indexes:
                index_name = str(index[1]).replace('"', '""')
                if not bool(index[2]):
                    continue
                index_columns = connection.execute(
                    text(f'PRAGMA index_info("{index_name}")')
                ).fetchall()
                if [row[2] for row in index_columns] == ["user_id"]:
                    has_user_unique = True
                    break

            if has_user_unique:
                table = Base.metadata.tables["registrations"]
                old_columns = [row[1] for row in connection.execute(text("PRAGMA table_info(registrations)"))]
                new_columns = [column.name for column in table.columns if column.name in old_columns]
                quoted_columns = ", ".join(f'"{name}"' for name in new_columns)
                connection.execute(text("ALTER TABLE registrations RENAME TO registrations_legacy"))
                table.create(bind=connection)
                connection.execute(text(
                    f'INSERT INTO registrations ({quoted_columns}) '
                    f'SELECT {quoted_columns} FROM registrations_legacy'
                ))
                connection.execute(text("DROP TABLE registrations_legacy"))
                print("Removed legacy registrations.user_id unique constraint")

    print("Database tables created successfully")

    from app.db.seed import seed_admin_user

    db = SessionLocal()

    try:
        seed_admin_user(db)
    finally:
        db.close()

