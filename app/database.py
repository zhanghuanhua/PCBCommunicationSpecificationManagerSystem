from collections.abc import Generator

from datetime import UTC, datetime

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import ApiInterface, ApiParameter, SpecTemplate, SpecVersion
from app.services.examples import build_request_example, build_response_example
from app.settings import sqlite_database_url


DATABASE_URL = sqlite_database_url()
engine = create_engine(DATABASE_URL, echo=False)
_PARENT_REPAIR_DONE = False


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    _ensure_apiinterface_log_columns()
    _ensure_version_columns()
    _remove_legacy_apiinterface_code_unique()
    _ensure_default_spec_version()
    _normalize_parameter_data_types()
    _repair_cross_interface_parameter_parents()
    _repair_duplicate_interface_child_parameters()


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


def _normalize_parameter_data_types() -> None:
    with Session(engine) as session:
        parameters = session.exec(select(ApiParameter)).all()
        changed = False
        for parameter in parameters:
            if parameter.data_type.strip().lower() == "int" and parameter.data_type != "int":
                parameter.data_type = "int"
                session.add(parameter)
                changed = True
        if changed:
            session.commit()


def _repair_cross_interface_parameter_parents() -> None:
    global _PARENT_REPAIR_DONE
    if _PARENT_REPAIR_DONE:
        return
    _PARENT_REPAIR_DONE = True
    with Session(engine) as session:
        parameters = session.exec(select(ApiParameter)).all()
        interfaces = {item.id: item for item in session.exec(select(ApiInterface)).all() if item.id is not None}
        parameters_by_id = {item.id: item for item in parameters if item.id is not None}
        parameters_by_interface: dict[int, list[ApiParameter]] = {}
        for parameter in parameters:
            parameters_by_interface.setdefault(parameter.interface_id, []).append(parameter)

        changed_interface_ids: set[int] = set()
        for parameter in parameters:
            if parameter.parent_id is None:
                continue
            parent = parameters_by_id.get(parameter.parent_id)
            if not parent or parent.interface_id == parameter.interface_id:
                continue
            repaired_parent = _matching_parameter_in_interface(parent, parameters_by_interface.get(parameter.interface_id, []))
            if repaired_parent and repaired_parent.id is not None:
                parameter.parent_id = repaired_parent.id
                session.add(parameter)
                changed_interface_ids.add(parameter.interface_id)

        for interface_id in changed_interface_ids:
            interface = interfaces.get(interface_id)
            if not interface:
                continue
            interface_parameters = parameters_by_interface.get(interface_id, [])
            interface.request_log_example = _format_request_log(
                interface,
                build_request_example(interface, interface_parameters),
            )
            interface.response_log_example = _format_json_log(
                build_response_example(interface, interface_parameters),
            )
            interface.updated_at = datetime.now(UTC)
            session.add(interface)
        if changed_interface_ids:
            session.commit()


def _repair_duplicate_interface_child_parameters() -> None:
    with Session(engine) as session:
        interfaces = session.exec(select(ApiInterface)).all()
        parameters = session.exec(select(ApiParameter)).all()
        parameters_by_interface: dict[int, list[ApiParameter]] = {}
        for parameter in parameters:
            parameters_by_interface.setdefault(parameter.interface_id, []).append(parameter)
        grouped: dict[tuple[int | None, str], list[ApiInterface]] = {}
        for interface in interfaces:
            grouped.setdefault((interface.spec_version_id, interface.code), []).append(interface)

        changed_interface_ids: set[int] = set()
        for candidates in grouped.values():
            if len(candidates) < 2:
                continue
            for target in candidates:
                target_id = target.id or 0
                target_parameters = parameters_by_interface.get(target_id, [])
                for source in candidates:
                    source_id = source.id or 0
                    if source_id == target_id:
                        continue
                    if _copy_missing_child_parameters(
                        target_id,
                        target_parameters,
                        parameters_by_interface.get(source_id, []),
                        session,
                    ):
                        changed_interface_ids.add(target_id)
                        target_parameters = session.exec(
                            select(ApiParameter).where(ApiParameter.interface_id == target_id)
                        ).all()
                        parameters_by_interface[target_id] = target_parameters

        interfaces_by_id = {interface.id: interface for interface in interfaces if interface.id is not None}
        for interface_id in changed_interface_ids:
            interface = interfaces_by_id.get(interface_id)
            if not interface:
                continue
            interface_parameters = parameters_by_interface.get(interface_id, [])
            interface.request_log_example = _format_request_log(
                interface,
                build_request_example(interface, interface_parameters),
            )
            interface.response_log_example = _format_json_log(
                build_response_example(interface, interface_parameters),
            )
            interface.updated_at = datetime.now(UTC)
            session.add(interface)
        if changed_interface_ids:
            session.commit()


def _copy_missing_child_parameters(
    target_interface_id: int,
    target_parameters: list[ApiParameter],
    source_parameters: list[ApiParameter],
    session: Session,
) -> bool:
    target_parent_by_signature = {
        _parameter_signature(parameter): parameter
        for parameter in target_parameters
        if parameter.parent_id is None
    }
    target_children_by_parent: dict[int, list[ApiParameter]] = {}
    for parameter in target_parameters:
        if parameter.parent_id is not None:
            target_children_by_parent.setdefault(parameter.parent_id, []).append(parameter)
    source_children_by_parent: dict[int, list[ApiParameter]] = {}
    source_parameters_by_id = {parameter.id: parameter for parameter in source_parameters if parameter.id is not None}
    for parameter in source_parameters:
        if parameter.parent_id is not None:
            source_children_by_parent.setdefault(parameter.parent_id, []).append(parameter)

    changed = False
    for source_parent_id, source_children in source_children_by_parent.items():
        source_parent = source_parameters_by_id.get(source_parent_id)
        if not source_parent:
            continue
        target_parent = target_parent_by_signature.get(_parameter_signature(source_parent))
        if not target_parent or target_parent.id is None:
            continue
        existing_child_signatures = {
            _parameter_signature(child)
            for child in target_children_by_parent.get(target_parent.id, [])
        }
        for child in sorted(source_children, key=lambda item: (item.sort_order, item.id or 0)):
            if _parameter_signature(child) in existing_child_signatures:
                continue
            copied_child = ApiParameter(
                interface_id=target_interface_id,
                kind=child.kind,
                parent_id=target_parent.id,
                sort_order=child.sort_order,
                field_name=child.field_name,
                data_type=child.data_type,
                required=child.required,
                is_array=child.is_array,
                example_value=child.example_value,
                description=child.description,
                enum_options=child.enum_options,
            )
            session.add(copied_child)
            changed = True
    if changed:
        session.flush()
    return changed


def _parameter_signature(parameter: ApiParameter) -> tuple:
    return (parameter.kind, parameter.sort_order, parameter.field_name, parameter.data_type)


def _matching_parameter_in_interface(source_parent: ApiParameter, candidates: list[ApiParameter]) -> ApiParameter | None:
    matches = [
        item
        for item in candidates
        if item.kind == source_parent.kind
        and item.field_name == source_parent.field_name
        and item.sort_order == source_parent.sort_order
    ]
    if len(matches) == 1:
        return matches[0]
    matches = [
        item
        for item in candidates
        if item.kind == source_parent.kind
        and item.field_name == source_parent.field_name
        and item.data_type == source_parent.data_type
    ]
    if len(matches) == 1:
        return matches[0]
    matches = [
        item
        for item in candidates
        if item.kind == source_parent.kind
        and item.field_name == source_parent.field_name
    ]
    return matches[0] if len(matches) == 1 else None


def _format_request_log(interface: ApiInterface, request_example: dict) -> str:
    return f"REST:POST http://IP:Port/api/{interface.api_name}\n{_format_json_log(request_example)}"


def _format_json_log(data: dict) -> str:
    import json

    return json.dumps(data, ensure_ascii=False, indent=4)


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
    _repair_cross_interface_parameter_parents()
    _repair_duplicate_interface_child_parameters()
    with Session(engine) as session:
        yield session
