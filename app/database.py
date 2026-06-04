from collections.abc import Generator

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine


DATABASE_URL = "sqlite:///data/interface_manager.db"
engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    _ensure_apiinterface_log_columns()


def _ensure_apiinterface_log_columns() -> None:
    inspector = inspect(engine)
    if "apiinterface" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("apiinterface")}
    with engine.begin() as connection:
        if "request_log_example" not in columns:
            connection.execute(text("ALTER TABLE apiinterface ADD COLUMN request_log_example TEXT DEFAULT ''"))
        if "response_log_example" not in columns:
            connection.execute(text("ALTER TABLE apiinterface ADD COLUMN response_log_example TEXT DEFAULT ''"))


def get_session() -> Generator[Session, None, None]:
    _ensure_apiinterface_log_columns()
    with Session(engine) as session:
        yield session
