from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine


DATABASE_URL = "sqlite:///data/interface_manager.db"
engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
