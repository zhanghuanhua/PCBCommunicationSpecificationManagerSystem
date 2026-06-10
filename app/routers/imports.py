from datetime import UTC, datetime
import json
from pathlib import Path
import re
from uuid import uuid4
from zipfile import BadZipFile

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, delete, select
from starlette.status import HTTP_400_BAD_REQUEST

from app.database import get_session
from app.models import ApiInterface, ApiParameter, InterfaceStatus, SpecTemplate, SpecVersion
from app.services.spec_parser import ParsedInterface, ParsedParameter, parse_interface_basics_from_docx

router = APIRouter(prefix="/imports")
templates = Jinja2Templates(directory="app/templates")

TEMPLATE_DIR = Path("data/templates")


@router.post("/spec")
async def upload_spec_template(
    request: Request,
    spec_file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    filename = spec_file.filename or ""
    if not filename.lower().endswith(".docx"):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="只支持上传 .docx Word 文件",
        )

    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    stored_path = TEMPLATE_DIR / f"{uuid4().hex}.docx"
    content = await spec_file.read()
    stored_path.write_bytes(content)

    template = SpecTemplate(
        original_filename=filename,
        stored_path=str(stored_path),
        file_size=len(content),
    )
    session.add(template)
    session.commit()
    session.refresh(template)
    spec_version = _create_or_update_spec_version(template, session)
    import_result = _save_parsed_interfaces(stored_path, spec_version, session)

    return templates.TemplateResponse(
        request,
        "import_spec.html",
        {
            "title": "导入原规格书",
            "template": template,
            "spec_version": spec_version,
            "message": "导入成功",
            "import_result": import_result,
        },
    )


def _create_or_update_spec_version(template: SpecTemplate, session: Session) -> SpecVersion:
    version = _guess_version(template.original_filename)
    existing = session.exec(select(SpecVersion).where(SpecVersion.version == version)).first()
    if existing:
        existing.name = _guess_spec_name(template.original_filename)
        existing.original_filename = template.original_filename
        existing.template_path = template.stored_path
        existing.status = "IMPORTED"
        existing.updated_at = datetime.now(UTC)
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    spec_version = SpecVersion(
        name=_guess_spec_name(template.original_filename),
        version=version,
        original_filename=template.original_filename,
        template_path=template.stored_path,
        status="IMPORTED",
    )
    session.add(spec_version)
    session.commit()
    session.refresh(spec_version)
    return spec_version


def _save_parsed_interfaces(docx_path: Path, spec_version: SpecVersion, session: Session) -> dict:
    try:
        parsed = parse_interface_basics_from_docx(docx_path)
    except (BadZipFile, ValueError):
        parsed = []
    created: list[ParsedInterface] = []
    updated: list[ParsedInterface] = []

    for item in parsed:
        exists = session.exec(
            select(ApiInterface).where(
                ApiInterface.spec_version_id == spec_version.id,
                ApiInterface.code == item.code,
            )
        ).first()
        if exists:
            exists.spec_version_id = spec_version.id
            exists.name = item.name
            exists.direction = item.direction
            exists.api_name = item.api_name
            exists.caller = item.caller
            exists.provider = item.provider
            exists.requirement = item.requirement
            exists.scenario = item.scenario
            exists.service_description = item.service_description
            exists.version = spec_version.version
            exists.status = InterfaceStatus.PUBLISHED
            exists.request_log_example = item.request_log_example
            exists.response_log_example = item.response_log_example
            exists.updated_at = datetime.now(UTC)
            session.add(exists)
            session.flush()
            _replace_parameters(exists.id or 0, item.parameters, session)
            updated.append(item)
            continue
        interface = ApiInterface(
            spec_version_id=spec_version.id,
            code=item.code,
            name=item.name,
            direction=item.direction,
            api_name=item.api_name,
            caller=item.caller,
            provider=item.provider,
            requirement=item.requirement,
            scenario=item.scenario,
            service_description=item.service_description,
            version=spec_version.version,
            status=InterfaceStatus.PUBLISHED,
            request_log_example=item.request_log_example,
            response_log_example=item.response_log_example,
        )
        session.add(interface)
        session.flush()
        _replace_parameters(interface.id or 0, item.parameters, session)
        created.append(item)

    spec_version.status = "IMPORTED"
    spec_version.updated_at = datetime.now(UTC)
    session.add(spec_version)
    session.commit()
    return {
        "parsed_total": len(parsed),
        "created_total": len(created),
        "updated_total": len(updated),
        "parameter_total": sum(len(item.parameters) for item in parsed),
        "eqp_to_eap_total": sum(1 for item in parsed if item.code.startswith("EQP-EAP-")),
        "eap_to_eqp_total": sum(1 for item in parsed if item.code.startswith("EAP-EQP-")),
        "created": created,
        "updated": updated,
    }


def _guess_version(filename: str) -> str:
    match = re.search(r"v?\s*(\d+(?:\.\d+)*)", filename, flags=re.IGNORECASE)
    return match.group(1) if match else "4.0"


def _guess_spec_name(filename: str) -> str:
    clean = filename.rsplit(".", 1)[0]
    return re.sub(r"\s*v?\d+(?:\.\d+)*\s*$", "", clean, flags=re.IGNORECASE).strip() or clean


def _replace_parameters(
    interface_id: int, parsed_parameters: list[ParsedParameter], session: Session
) -> None:
    session.exec(delete(ApiParameter).where(ApiParameter.interface_id == interface_id))
    sequence_to_parameter: dict[str, ApiParameter] = {}
    pending_parent_links: list[tuple[ApiParameter, str]] = []
    for index, item in enumerate(parsed_parameters, start=1):
        parameter = ApiParameter(
            interface_id=interface_id,
            kind=item.kind,
            sort_order=index,
            field_name=item.field_name,
            data_type=item.data_type,
            required=item.required,
            example_value=item.example_value,
            description=item.description,
            enum_options=_parameter_metadata(item),
        )
        session.add(parameter)
        session.flush()
        if item.sequence:
            sequence_to_parameter[item.sequence] = parameter
        if item.parent_sequence:
            pending_parent_links.append((parameter, item.parent_sequence))
    for parameter, parent_sequence in pending_parent_links:
        parent = sequence_to_parameter.get(parent_sequence)
        if parent is not None:
            parameter.parent_id = parent.id
            session.add(parameter)


def _parameter_metadata(item: ParsedParameter) -> str:
    return json.dumps(
        {
            "sequence": item.sequence,
            "parent_sequence": item.parent_sequence,
            "is_group": item.is_group,
        },
        ensure_ascii=False,
    )
