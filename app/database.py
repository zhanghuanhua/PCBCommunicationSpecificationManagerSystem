from collections.abc import Generator

from datetime import UTC, datetime

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import ApiInterface, SpecTemplate, SpecVersion


DATABASE_URL = "sqlite:///data/interface_manager.db"
engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    _ensure_apiinterface_log_columns()
    _ensure_version_columns()
    _remove_legacy_apiinterface_code_unique()
    _ensure_default_spec_version()


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


def _ensure_version_columns() -> None:
    inspector = inspect(engine)
    if "apiinterface" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("apiinterface")}
    with engine.begin() as connection:
        if "spec_version_id" not in columns:
            connection.execute(text("ALTER TABLE apiinterface ADD COLUMN spec_version_id INTEGER"))


def _remove_legacy_apiinterface_code_unique() -> None:
    inspector = inspect(engine)
    if "apiinterface" not in inspector.get_table_names():
        return
    with engine.begin() as connection:
        indexes = connection.execute(text("PRAGMA index_list('apiinterface')")).fetchall()
        has_code_unique = False
        for index in indexes:
            index_name = index[1]
            is_unique = bool(index[2])
            if not is_unique:
                continue
            columns = connection.execute(text(f"PRAGMA index_info('{index_name}')")).fetchall()
            if [column[2] for column in columns] == ["code"]:
                has_code_unique = True
                break
        if not has_code_unique:
            return
        connection.execute(text("PRAGMA foreign_keys=OFF"))
        connection.execute(
            text(
                """
                CREATE TABLE apiinterface_new (
                    id INTEGER PRIMARY KEY,
                    spec_version_id INTEGER,
                    code VARCHAR NOT NULL,
                    name VARCHAR NOT NULL,
                    direction VARCHAR NOT NULL,
                    api_name VARCHAR NOT NULL,
                    method VARCHAR NOT NULL DEFAULT 'POST',
                    content_type VARCHAR NOT NULL DEFAULT 'application/json',
                    caller VARCHAR NOT NULL,
                    provider VARCHAR NOT NULL,
                    requirement VARCHAR NOT NULL DEFAULT '',
                    scenario VARCHAR NOT NULL DEFAULT '',
                    service_description VARCHAR NOT NULL DEFAULT '',
                    version VARCHAR NOT NULL DEFAULT '4.0',
                    module VARCHAR NOT NULL DEFAULT '',
                    status VARCHAR NOT NULL DEFAULT 'DRAFT',
                    remark VARCHAR NOT NULL DEFAULT '',
                    request_log_example TEXT DEFAULT '',
                    response_log_example TEXT DEFAULT '',
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )
        current_columns = {column["name"] for column in inspector.get_columns("apiinterface")}
        desired_columns = [
            "id",
            "spec_version_id",
            "code",
            "name",
            "direction",
            "api_name",
            "method",
            "content_type",
            "caller",
            "provider",
            "requirement",
            "scenario",
            "service_description",
            "version",
            "module",
            "status",
            "remark",
            "request_log_example",
            "response_log_example",
            "created_at",
            "updated_at",
        ]
        copied_columns = [column for column in desired_columns if column in current_columns]
        columns_sql = ", ".join(copied_columns)
        connection.execute(
            text(f"INSERT INTO apiinterface_new ({columns_sql}) SELECT {columns_sql} FROM apiinterface")
        )
        connection.execute(text("DROP TABLE apiinterface"))
        connection.execute(text("ALTER TABLE apiinterface_new RENAME TO apiinterface"))
        connection.execute(text("CREATE INDEX ix_apiinterface_code ON apiinterface (code)"))
        connection.execute(text("CREATE INDEX ix_apiinterface_api_name ON apiinterface (api_name)"))
        connection.execute(text("CREATE INDEX ix_apiinterface_spec_version_id ON apiinterface (spec_version_id)"))
        connection.execute(text("PRAGMA foreign_keys=ON"))


def _ensure_default_spec_version() -> None:
    with Session(engine) as session:
        existing_version = session.exec(select(SpecVersion)).first()
        unassigned = session.exec(
            select(ApiInterface).where(ApiInterface.spec_version_id.is_(None))
        ).all()
        if not unassigned:
            return
        if existing_version is None:
            template = session.exec(select(SpecTemplate).order_by(SpecTemplate.created_at.desc())).first()
            existing_version = SpecVersion(
                name=_guess_spec_name(template.original_filename if template else ""),
                version=_guess_version(template.original_filename if template else "4.0"),
                original_filename=template.original_filename if template else "",
                template_path=template.stored_path if template else "",
                status=template.status if template else "IMPORTED",
                updated_at=datetime.now(UTC),
            )
            session.add(existing_version)
            session.commit()
            session.refresh(existing_version)
        for item in unassigned:
            item.spec_version_id = existing_version.id
            if not item.version:
                item.version = existing_version.version
            session.add(item)
        session.commit()


def _guess_version(filename: str) -> str:
    import re

    match = re.search(r"v?\s*(\d+(?:\.\d+)*)", filename, flags=re.IGNORECASE)
    return match.group(1) if match else "4.0"


def _guess_spec_name(filename: str) -> str:
    if not filename:
        return "超毅项目 Web API 通讯规格书"
    clean = filename.rsplit(".", 1)[0]
    import re

    return re.sub(r"\s*v?\d+(?:\.\d+)*\s*$", "", clean, flags=re.IGNORECASE).strip() or clean


def get_session() -> Generator[Session, None, None]:
    SQLModel.metadata.create_all(engine)
    _ensure_apiinterface_log_columns()
    _ensure_version_columns()
    _remove_legacy_apiinterface_code_unique()
    _ensure_default_spec_version()
    with Session(engine) as session:
        yield session
