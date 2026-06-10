from datetime import UTC, datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class InterfaceDirection(str, Enum):
    EQP_TO_EAP = "EQP_TO_EAP"
    EAP_TO_EQP = "EAP_TO_EQP"


class InterfaceStatus(str, Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    PUBLISHED = "PUBLISHED"
    DEPRECATED = "DEPRECATED"


class ParameterKind(str, Enum):
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"


class SpecVersion(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = "超毅项目 Web API 通讯规格书"
    version: str = Field(index=True)
    original_filename: str = ""
    template_path: str = ""
    status: str = "IMPORTED"
    source_version_id: int | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ApiInterface(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    spec_version_id: int | None = Field(default=None, index=True, foreign_key="specversion.id")
    code: str = Field(index=True)
    name: str
    direction: InterfaceDirection
    api_name: str = Field(index=True)
    method: str = "POST"
    content_type: str = "application/json"
    caller: str
    provider: str
    requirement: str = ""
    scenario: str = ""
    service_description: str = ""
    version: str = "4.0"
    module: str = ""
    status: InterfaceStatus = InterfaceStatus.DRAFT
    remark: str = ""
    request_log_example: str = ""
    response_log_example: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ApiParameter(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    interface_id: int = Field(index=True, foreign_key="apiinterface.id")
    kind: ParameterKind
    parent_id: int | None = Field(default=None, index=True)
    sort_order: int
    field_name: str
    data_type: str
    required: bool = True
    is_array: bool = False
    example_value: str = ""
    description: str
    enum_options: str = ""


class ExportRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    version: str
    scope: str
    formats: str
    watermark_enabled: bool = False
    watermark_text: str = ""
    output_path: str = ""
    result: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SpecTemplate(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    original_filename: str
    stored_path: str
    file_size: int = 0
    status: str = "IMPORTED"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
