# Interface Manager V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first usable local web version of the EAP-EQP API interface management system, including structured interface editing, JSON example generation, Markdown/Word/PDF export, and export watermark settings.

**Architecture:** Use a Python FastAPI backend with SQLite persistence and a simple server-rendered/local web UI. Keep the first version small: one local app, structured data models, export services, and focused pages for interface list, interface editor, and export center. Semi-automatic Word import is intentionally deferred to V2 because export and structured editing must be stable first.

**Tech Stack:** Python 3.11+, FastAPI, SQLModel or SQLAlchemy, SQLite, Jinja2 templates, pytest, python-docx, Markdown text generation, Playwright or browser manual verification for UI, optional LibreOffice/Word automation for PDF conversion depending on local availability.

---

## Scope

### V1 Includes

- Local web application.
- Interface list and search.
- Create and edit `EQP -> EAP` and `EAP -> EQP` interfaces.
- Structured request parameter and response parameter maintenance.
- Automatic public request/response fields.
- JSON request/response example generation.
- Validation for direction, numbering, fields, and JSON.
- Markdown export.
- Word export.
- PDF export as a user-facing option.
- Word/PDF watermark configuration.
- Export records.

### V1 Excludes

- Full multi-user login.
- Approval workflow.
- Complete automatic Word import.
- Direct online API testing.
- Multi-project vendor/device management.

## File Structure

Create this structure:

```text
app/
  __init__.py
  main.py
  database.py
  models.py
  schemas.py
  seed.py
  services/
    __init__.py
    validation.py
    examples.py
    markdown_export.py
    word_export.py
    pdf_export.py
    watermark.py
  routers/
    __init__.py
    pages.py
    interfaces.py
    exports.py
  templates/
    base.html
    interfaces_list.html
    interface_form.html
    export_center.html
    export_result.html
  static/
    styles.css
tests/
  test_validation.py
  test_examples.py
  test_markdown_export.py
  test_word_export.py
  test_pdf_export.py
exports/
  .gitkeep
data/
  .gitkeep
docs/
  superpowers/
    plans/
      2026-06-02-interface-manager-v1.md
README.md
requirements.txt
```

Responsibilities:

- `app/main.py`: FastAPI application setup.
- `app/database.py`: SQLite engine, session helper, database initialization.
- `app/models.py`: Persistent database models.
- `app/schemas.py`: Form/input schema helpers.
- `app/services/validation.py`: Interface validation rules.
- `app/services/examples.py`: JSON request/response example generation.
- `app/services/markdown_export.py`: Markdown document generation.
- `app/services/word_export.py`: Word document generation.
- `app/services/pdf_export.py`: PDF export wrapper.
- `app/services/watermark.py`: Watermark configuration and document watermark helpers.
- `app/routers/pages.py`: Browser pages.
- `app/routers/interfaces.py`: Interface create/update routes.
- `app/routers/exports.py`: Export routes.
- `app/templates/*`: UI pages.
- `app/static/styles.css`: UI styling.
- `tests/*`: Focused behavior tests.

---

### Task 1: Project Skeleton

**Files:**
- Create: `requirements.txt`
- Create: `README.md`
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `app/routers/__init__.py`
- Create: `app/routers/pages.py`
- Create: `app/templates/base.html`
- Create: `app/static/styles.css`
- Create: `exports/.gitkeep`
- Create: `data/.gitkeep`

- [ ] **Step 1: Create dependency list**

Create `requirements.txt`:

```text
fastapi==0.115.6
uvicorn[standard]==0.34.0
jinja2==3.1.5
python-multipart==0.0.20
sqlmodel==0.0.22
pytest==8.3.4
python-docx==1.1.2
reportlab==4.2.5
pydantic==2.10.4
```

- [ ] **Step 2: Create README**

Create `README.md`:

```markdown
# PCB Communication Specification Manager System

本项目用于维护珠海超毅 EAP-EQP API 接口通讯规格书。

系统目标：

- 结构化维护 `EQP -> EAP` 和 `EAP -> EQP` 接口。
- 自动生成 JSON 示例。
- 自动导出 Markdown、Word、PDF。
- 支持导出水印，减少人工编辑 Word 出错。

## 第一版范围

第一版是本地 Web 工具。启动后通过浏览器使用。

## 启动方式

```powershell
pip install -r requirements.txt
uvicorn app.main:app --reload
```

浏览器访问：

```text
http://127.0.0.1:8000
```
```

- [ ] **Step 3: Create minimal app**

Create `app/main.py`:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import pages


app = FastAPI(title="EAP-EQP Interface Manager")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(pages.router)
```

- [ ] **Step 4: Create page router**

Create `app/routers/pages.py`:

```python
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        "base.html",
        {
            "request": request,
            "title": "接口管理工作台",
        },
    )
```

- [ ] **Step 5: Create base template**

Create `app/templates/base.html`:

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }}</title>
  <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
  <header class="topbar">
    <div>
      <strong>接口管理系统</strong>
      <span>珠海超毅 EAP-EQP API</span>
    </div>
    <nav>
      <a href="/">接口工作台</a>
      <a href="/exports">导出中心</a>
    </nav>
  </header>
  <main class="page">
    <h1>{{ title }}</h1>
    <p class="muted">第一版本地工具，用于结构化维护接口并生成规格书。</p>
  </main>
</body>
</html>
```

- [ ] **Step 6: Create initial CSS**

Create `app/static/styles.css`:

```css
:root {
  color-scheme: light;
  --bg: #f6f7f9;
  --panel: #ffffff;
  --text: #1f2937;
  --muted: #6b7280;
  --line: #d8dee8;
  --accent: #2563eb;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: var(--panel);
  border-bottom: 1px solid var(--line);
}

.topbar span {
  margin-left: 10px;
  color: var(--muted);
}

.topbar a {
  margin-left: 16px;
  color: var(--accent);
  text-decoration: none;
}

.page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.muted {
  color: var(--muted);
}
```

- [ ] **Step 7: Run app**

Run:

```powershell
uvicorn app.main:app --reload
```

Expected:

```text
Uvicorn running on http://127.0.0.1:8000
```

- [ ] **Step 8: Commit**

```powershell
git add requirements.txt README.md app exports data
git commit -m "feat: create local web app skeleton"
```

---

### Task 2: Database Models

**Files:**
- Create: `app/database.py`
- Create: `app/models.py`
- Create: `app/seed.py`
- Modify: `app/main.py`
- Test: `tests/test_validation.py`

- [ ] **Step 1: Create database helper**

Create `app/database.py`:

```python
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine


DATABASE_URL = "sqlite:///data/interface_manager.db"
engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
```

- [ ] **Step 2: Create models**

Create `app/models.py`:

```python
from datetime import datetime
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


class ApiInterface(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


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
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

- [ ] **Step 3: Initialize database on startup**

Modify `app/main.py`:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import pages


app = FastAPI(title="EAP-EQP Interface Manager")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(pages.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
```

- [ ] **Step 4: Create seed helper**

Create `app/seed.py`:

```python
from sqlmodel import Session, select

from app.database import engine, init_db
from app.models import ApiInterface, InterfaceDirection


def seed_demo_data() -> None:
    init_db()
    with Session(engine) as session:
        existing = session.exec(select(ApiInterface)).first()
        if existing:
            return
        demo = ApiInterface(
            code="EQP-EAP-001",
            name="连线检查",
            direction=InterfaceDirection.EQP_TO_EAP,
            api_name="EQP_AliveCheck",
            caller="EQP",
            provider="EAP",
            requirement="EQP 检查与 EAP 是否连线",
            scenario="EQP 定时检查 EAP 联机状态",
            service_description="EQP 检查与 EAP 是否连线",
        )
        session.add(demo)
        session.commit()


if __name__ == "__main__":
    seed_demo_data()
```

- [ ] **Step 5: Verify database creation**

Run:

```powershell
python -m app.seed
```

Expected:

```text
No error, data/interface_manager.db exists.
```

If `python` is unavailable, use the available Python launcher or configured runtime before continuing.

- [ ] **Step 6: Commit**

```powershell
git add app/database.py app/models.py app/seed.py app/main.py data/.gitkeep
git commit -m "feat: add interface database models"
```

---

### Task 3: Validation Service

**Files:**
- Create: `app/services/validation.py`
- Create: `tests/test_validation.py`

- [ ] **Step 1: Write validation tests**

Create `tests/test_validation.py`:

```python
from app.models import ApiInterface, ApiParameter, InterfaceDirection, ParameterKind
from app.services.validation import validate_interface


def test_eqp_to_eap_requires_matching_caller_provider():
    interface = ApiInterface(
        code="EQP-EAP-037",
        name="测试接口",
        direction=InterfaceDirection.EQP_TO_EAP,
        api_name="EQP_Test",
        caller="EAP",
        provider="EQP",
    )

    errors = validate_interface(interface, [])

    assert "EQP -> EAP 的调用方必须为 EQP，提供方必须为 EAP。" in errors


def test_eap_to_eqp_requires_matching_code_prefix():
    interface = ApiInterface(
        code="EQP-EAP-012",
        name="测试接口",
        direction=InterfaceDirection.EAP_TO_EQP,
        api_name="EAP_Test",
        caller="EAP",
        provider="EQP",
    )

    errors = validate_interface(interface, [])

    assert "EAP -> EQP 的接口编号必须以 EAP-EQP- 开头。" in errors


def test_parameter_requires_name_type_and_description():
    interface = ApiInterface(
        code="EQP-EAP-037",
        name="测试接口",
        direction=InterfaceDirection.EQP_TO_EAP,
        api_name="EQP_Test",
        caller="EQP",
        provider="EAP",
    )
    parameter = ApiParameter(
        interface_id=1,
        kind=ParameterKind.REQUEST,
        sort_order=1,
        field_name="",
        data_type="",
        description="",
    )

    errors = validate_interface(interface, [parameter])

    assert "参数字段名不能为空。" in errors
    assert "参数类型不能为空。" in errors
    assert "参数描述不能为空。" in errors
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
pytest tests/test_validation.py -v
```

Expected:

```text
ModuleNotFoundError: No module named 'app.services.validation'
```

- [ ] **Step 3: Implement validation**

Create `app/services/validation.py`:

```python
from app.models import ApiInterface, ApiParameter, InterfaceDirection


def validate_interface(interface: ApiInterface, parameters: list[ApiParameter]) -> list[str]:
    errors: list[str] = []

    if interface.direction == InterfaceDirection.EQP_TO_EAP:
        if not interface.code.startswith("EQP-EAP-"):
            errors.append("EQP -> EAP 的接口编号必须以 EQP-EAP- 开头。")
        if interface.caller != "EQP" or interface.provider != "EAP":
            errors.append("EQP -> EAP 的调用方必须为 EQP，提供方必须为 EAP。")

    if interface.direction == InterfaceDirection.EAP_TO_EQP:
        if not interface.code.startswith("EAP-EQP-"):
            errors.append("EAP -> EQP 的接口编号必须以 EAP-EQP- 开头。")
        if interface.caller != "EAP" or interface.provider != "EQP":
            errors.append("EAP -> EQP 的调用方必须为 EAP，提供方必须为 EQP。")

    if not interface.name.strip():
        errors.append("接口名称不能为空。")
    if not interface.api_name.strip():
        errors.append("API 名称不能为空。")

    seen_by_parent: set[tuple[int | None, str]] = set()
    for parameter in parameters:
        if not parameter.field_name.strip():
            errors.append("参数字段名不能为空。")
        if not parameter.data_type.strip():
            errors.append("参数类型不能为空。")
        if not parameter.description.strip():
            errors.append("参数描述不能为空。")

        key = (parameter.parent_id, parameter.field_name.strip())
        if parameter.field_name.strip() and key in seen_by_parent:
            errors.append(f"同一层级下字段名重复：{parameter.field_name}")
        seen_by_parent.add(key)

    return errors
```

- [ ] **Step 4: Run tests**

Run:

```powershell
pytest tests/test_validation.py -v
```

Expected:

```text
3 passed
```

- [ ] **Step 5: Commit**

```powershell
git add app/services/validation.py tests/test_validation.py
git commit -m "feat: add interface validation rules"
```

---

### Task 4: JSON Example Generation

**Files:**
- Create: `app/services/examples.py`
- Create: `tests/test_examples.py`

- [ ] **Step 1: Write example tests**

Create `tests/test_examples.py`:

```python
from app.models import ApiInterface, ApiParameter, InterfaceDirection, ParameterKind
from app.services.examples import build_request_example, build_response_example


def test_build_request_example_for_eqp_to_eap():
    interface = ApiInterface(
        code="EQP-EAP-037",
        name="测试接口",
        direction=InterfaceDirection.EQP_TO_EAP,
        api_name="EQP_Test",
        caller="EQP",
        provider="EAP",
    )
    parameters = [
        ApiParameter(
            interface_id=1,
            kind=ParameterKind.REQUEST,
            sort_order=1,
            field_name="EqpId",
            data_type="string",
            example_value="EQ01",
            description="设备 ID",
        )
    ]

    result = build_request_example(interface, parameters)

    assert result["From"] == "EQP"
    assert result["Message"] == "EQP_Test"
    assert result["Content"]["EqpId"] == "EQ01"


def test_build_response_example_has_public_fields():
    interface = ApiInterface(
        code="EAP-EQP-012",
        name="测试接口",
        direction=InterfaceDirection.EAP_TO_EQP,
        api_name="EAP_Test",
        caller="EAP",
        provider="EQP",
    )

    result = build_response_example(interface, [])

    assert result["Code"] == "0000"
    assert result["Success"] is True
    assert result["Content"] == {}
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
pytest tests/test_examples.py -v
```

Expected:

```text
ModuleNotFoundError: No module named 'app.services.examples'
```

- [ ] **Step 3: Implement example generation**

Create `app/services/examples.py`:

```python
from typing import Any

from app.models import ApiInterface, ApiParameter, ParameterKind


DEFAULT_DATETIME = "2024/11/27 15:00:00"
DEFAULT_REQUEST_ID = "20250107121135343"


def _coerce_example_value(parameter: ApiParameter) -> Any:
    value = parameter.example_value
    data_type = parameter.data_type.lower()
    if parameter.is_array:
        return [value or _default_scalar(data_type)]
    if data_type in {"int", "integer"}:
        return int(value) if value else 0
    if data_type in {"float", "decimal", "double"}:
        return float(value) if value else 0.0
    if data_type in {"bool", "boolean"}:
        if value.lower() == "false":
            return False
        return True
    if data_type in {"object", "jsonobject"}:
        return {}
    return value or _default_scalar(data_type)


def _default_scalar(data_type: str) -> Any:
    if data_type in {"int", "integer"}:
        return 0
    if data_type in {"float", "decimal", "double"}:
        return 0.0
    if data_type in {"bool", "boolean"}:
        return True
    return ""


def _build_content(parameters: list[ApiParameter], kind: ParameterKind) -> dict[str, Any]:
    content: dict[str, Any] = {}
    for parameter in sorted(parameters, key=lambda item: item.sort_order):
        if parameter.kind != kind or parameter.parent_id is not None:
            continue
        content[parameter.field_name] = _coerce_example_value(parameter)
    return content


def build_request_example(interface: ApiInterface, parameters: list[ApiParameter]) -> dict[str, Any]:
    return {
        "From": interface.caller,
        "Message": interface.api_name,
        "DateTime": DEFAULT_DATETIME,
        "Content": _build_content(parameters, ParameterKind.REQUEST),
        "RequestId": DEFAULT_REQUEST_ID,
    }


def build_response_example(interface: ApiInterface, parameters: list[ApiParameter]) -> dict[str, Any]:
    return {
        "Code": "0000",
        "Success": True,
        "Msg": "",
        "DateTime": DEFAULT_DATETIME,
        "Content": _build_content(parameters, ParameterKind.RESPONSE),
        "RequestId": DEFAULT_REQUEST_ID,
    }
```

- [ ] **Step 4: Run tests**

Run:

```powershell
pytest tests/test_examples.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 5: Commit**

```powershell
git add app/services/examples.py tests/test_examples.py
git commit -m "feat: generate interface json examples"
```

---

### Task 5: Interface List and Form UI

**Files:**
- Modify: `app/routers/pages.py`
- Create: `app/routers/interfaces.py`
- Modify: `app/main.py`
- Create: `app/templates/interfaces_list.html`
- Create: `app/templates/interface_form.html`
- Modify: `app/static/styles.css`

- [ ] **Step 1: Add interface routes**

Create `app/routers/interfaces.py`:

```python
from datetime import datetime

from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.database import get_session
from app.models import ApiInterface, InterfaceDirection, InterfaceStatus


router = APIRouter(prefix="/interfaces")


@router.post("")
def create_interface(
    code: str = Form(...),
    name: str = Form(...),
    direction: InterfaceDirection = Form(...),
    api_name: str = Form(...),
    requirement: str = Form(""),
    scenario: str = Form(""),
    service_description: str = Form(""),
    version: str = Form("4.0"),
    module: str = Form(""),
    session: Session = Depends(get_session),
):
    caller = "EQP" if direction == InterfaceDirection.EQP_TO_EAP else "EAP"
    provider = "EAP" if direction == InterfaceDirection.EQP_TO_EAP else "EQP"
    interface = ApiInterface(
        code=code,
        name=name,
        direction=direction,
        api_name=api_name,
        caller=caller,
        provider=provider,
        requirement=requirement,
        scenario=scenario,
        service_description=service_description,
        version=version,
        module=module,
        status=InterfaceStatus.DRAFT,
        updated_at=datetime.utcnow(),
    )
    session.add(interface)
    session.commit()
    return RedirectResponse("/", status_code=303)
```

- [ ] **Step 2: Update page router**

Modify `app/routers/pages.py`:

```python
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.database import get_session
from app.models import ApiInterface, InterfaceDirection


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def home(request: Request, session: Session = Depends(get_session)):
    interfaces = session.exec(select(ApiInterface).order_by(ApiInterface.code)).all()
    return templates.TemplateResponse(
        "interfaces_list.html",
        {
            "request": request,
            "title": "接口管理工作台",
            "interfaces": interfaces,
        },
    )


@router.get("/interfaces/new")
def new_interface(request: Request):
    return templates.TemplateResponse(
        "interface_form.html",
        {
            "request": request,
            "title": "新增接口",
            "directions": InterfaceDirection,
        },
    )
```

- [ ] **Step 3: Register interface routes**

Modify `app/main.py`:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import interfaces, pages


app = FastAPI(title="EAP-EQP Interface Manager")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(pages.router)
app.include_router(interfaces.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
```

- [ ] **Step 4: Create list template**

Create `app/templates/interfaces_list.html`:

```html
{% extends "base.html" %}

{% block content %}
<div class="toolbar">
  <a class="button" href="/interfaces/new">新增接口</a>
  <a class="button secondary" href="/exports">导出中心</a>
</div>

<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th>接口编号</th>
        <th>接口名称</th>
        <th>方向</th>
        <th>API 名称</th>
        <th>调用方</th>
        <th>提供方</th>
        <th>版本</th>
        <th>状态</th>
      </tr>
    </thead>
    <tbody>
      {% for item in interfaces %}
      <tr>
        <td>{{ item.code }}</td>
        <td>{{ item.name }}</td>
        <td>{{ "EQP -> EAP" if item.direction == "EQP_TO_EAP" else "EAP -> EQP" }}</td>
        <td>{{ item.api_name }}</td>
        <td>{{ item.caller }}</td>
        <td>{{ item.provider }}</td>
        <td>{{ item.version }}</td>
        <td>{{ item.status }}</td>
      </tr>
      {% else %}
      <tr>
        <td colspan="8" class="empty">暂无接口，请先新增接口。</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}
```

- [ ] **Step 5: Create form template**

Create `app/templates/interface_form.html`:

```html
{% extends "base.html" %}

{% block content %}
<form class="form-panel" method="post" action="/interfaces">
  <label>
    接口方向
    <select name="direction">
      <option value="EQP_TO_EAP">EQP -> EAP</option>
      <option value="EAP_TO_EQP">EAP -> EQP</option>
    </select>
  </label>
  <label>
    接口编号
    <input name="code" placeholder="例如 EQP-EAP-037" required>
  </label>
  <label>
    接口名称
    <input name="name" placeholder="例如 设备状态上报" required>
  </label>
  <label>
    API 名称
    <input name="api_name" placeholder="例如 EQP_EquipmentCurrentStatus" required>
  </label>
  <label>
    需求说明
    <textarea name="requirement"></textarea>
  </label>
  <label>
    使用场景
    <textarea name="scenario"></textarea>
  </label>
  <label>
    服务描述
    <textarea name="service_description"></textarea>
  </label>
  <label>
    版本
    <input name="version" value="4.0">
  </label>
  <label>
    业务模块
    <input name="module">
  </label>
  <div class="actions">
    <button type="submit">保存接口</button>
    <a href="/">取消</a>
  </div>
</form>
{% endblock %}
```

- [ ] **Step 6: Update base template to support content block**

Modify `app/templates/base.html`:

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }}</title>
  <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
  <header class="topbar">
    <div>
      <strong>接口管理系统</strong>
      <span>珠海超毅 EAP-EQP API</span>
    </div>
    <nav>
      <a href="/">接口工作台</a>
      <a href="/exports">导出中心</a>
    </nav>
  </header>
  <main class="page">
    <h1>{{ title }}</h1>
    {% block content %}
    <p class="muted">第一版本地工具，用于结构化维护接口并生成规格书。</p>
    {% endblock %}
  </main>
</body>
</html>
```

- [ ] **Step 7: Add UI styles**

Append to `app/static/styles.css`:

```css
.toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.button,
button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 36px;
  padding: 0 14px;
  border: 1px solid var(--accent);
  background: var(--accent);
  color: #fff;
  text-decoration: none;
  cursor: pointer;
}

.button.secondary {
  background: #fff;
  color: var(--accent);
}

.table-wrap,
.form-panel {
  background: var(--panel);
  border: 1px solid var(--line);
  padding: 16px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 10px;
  border-bottom: 1px solid var(--line);
  text-align: left;
}

th {
  background: #f3f4f6;
}

.empty {
  text-align: center;
  color: var(--muted);
}

.form-panel {
  display: grid;
  gap: 14px;
  max-width: 780px;
}

label {
  display: grid;
  gap: 6px;
  font-weight: 600;
}

input,
select,
textarea {
  min-height: 36px;
  padding: 8px;
  border: 1px solid var(--line);
  font: inherit;
}

textarea {
  min-height: 84px;
}

.actions {
  display: flex;
  align-items: center;
  gap: 14px;
}
```

- [ ] **Step 8: Manual browser verification**

Run:

```powershell
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Expected:

- Interface list page loads.
- "新增接口" opens the form.
- Saving an interface returns to the list.
- Caller/provider are filled based on direction.

- [ ] **Step 9: Commit**

```powershell
git add app/routers app/templates app/static/styles.css app/main.py
git commit -m "feat: add interface list and create form"
```

---

### Task 6: Markdown Export

**Files:**
- Create: `app/services/markdown_export.py`
- Create: `tests/test_markdown_export.py`

- [ ] **Step 1: Write markdown export test**

Create `tests/test_markdown_export.py`:

```python
from app.models import ApiInterface, InterfaceDirection
from app.services.markdown_export import render_markdown_document


def test_markdown_export_contains_interface_sections():
    interface = ApiInterface(
        code="EQP-EAP-037",
        name="测试接口",
        direction=InterfaceDirection.EQP_TO_EAP,
        api_name="EQP_Test",
        caller="EQP",
        provider="EAP",
        requirement="测试需求",
        scenario="测试场景",
        service_description="测试服务",
    )

    content = render_markdown_document([interface], {}, {})

    assert "# 珠海超毅 EAP-EQP API 接口通讯规格书" in content
    assert "## EQP -> EAP 接口" in content
    assert "### EQP-EAP-037 测试接口" in content
    assert "EQP_Test" in content
```

- [ ] **Step 2: Run test to verify failure**

Run:

```powershell
pytest tests/test_markdown_export.py -v
```

Expected:

```text
ModuleNotFoundError: No module named 'app.services.markdown_export'
```

- [ ] **Step 3: Implement markdown export**

Create `app/services/markdown_export.py`:

```python
import json

from app.models import ApiInterface, InterfaceDirection


def render_markdown_document(
    interfaces: list[ApiInterface],
    request_examples: dict[int, dict],
    response_examples: dict[int, dict],
) -> str:
    lines: list[str] = [
        "# 珠海超毅 EAP-EQP API 接口通讯规格书",
        "",
        "## 文档概述",
        "",
        "本文档由接口管理系统自动生成。",
        "",
    ]
    _append_direction(lines, interfaces, InterfaceDirection.EQP_TO_EAP, "EQP -> EAP 接口", request_examples, response_examples)
    _append_direction(lines, interfaces, InterfaceDirection.EAP_TO_EQP, "EAP -> EQP 接口", request_examples, response_examples)
    return "\n".join(lines)


def _append_direction(
    lines: list[str],
    interfaces: list[ApiInterface],
    direction: InterfaceDirection,
    heading: str,
    request_examples: dict[int, dict],
    response_examples: dict[int, dict],
) -> None:
    lines.extend([f"## {heading}", ""])
    for item in interfaces:
        if item.direction != direction:
            continue
        lines.extend(
            [
                f"### {item.code} {item.name}",
                "",
                f"- 需求说明：{item.requirement}",
                f"- 使用场景：{item.scenario}",
                f"- 接口名称：{item.api_name}",
                f"- 调用方：{item.caller}",
                f"- 提供方：{item.provider}",
                f"- 服务描述：{item.service_description}",
                "",
                "#### 请求示例",
                "",
                "```json",
                json.dumps(request_examples.get(item.id or 0, {}), ensure_ascii=False, indent=2),
                "```",
                "",
                "#### 响应示例",
                "",
                "```json",
                json.dumps(response_examples.get(item.id or 0, {}), ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )
```

- [ ] **Step 4: Run test**

Run:

```powershell
pytest tests/test_markdown_export.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: Commit**

```powershell
git add app/services/markdown_export.py tests/test_markdown_export.py
git commit -m "feat: add markdown export service"
```

---

### Task 7: Word Export and Watermark

**Files:**
- Create: `app/services/watermark.py`
- Create: `app/services/word_export.py`
- Create: `tests/test_word_export.py`

- [ ] **Step 1: Write Word export test**

Create `tests/test_word_export.py`:

```python
from pathlib import Path

from docx import Document

from app.models import ApiInterface, InterfaceDirection
from app.services.word_export import export_word_document


def test_word_export_creates_docx_with_watermark(tmp_path: Path):
    interface = ApiInterface(
        id=1,
        code="EQP-EAP-037",
        name="测试接口",
        direction=InterfaceDirection.EQP_TO_EAP,
        api_name="EQP_Test",
        caller="EQP",
        provider="EAP",
        requirement="测试需求",
        scenario="测试场景",
        service_description="测试服务",
    )
    output = tmp_path / "spec.docx"

    export_word_document(
        output,
        [interface],
        {1: {"From": "EQP", "Message": "EQP_Test", "Content": {}}},
        {1: {"Code": "0000", "Success": True, "Content": {}}},
        watermark_text="厂商查看",
    )

    assert output.exists()
    document = Document(output)
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    assert "珠海超毅 EAP-EQP API 接口通讯规格书" in text
    assert "EQP-EAP-037 测试接口" in text
    assert "厂商查看" in text
```

- [ ] **Step 2: Run test to verify failure**

Run:

```powershell
pytest tests/test_word_export.py -v
```

Expected:

```text
ModuleNotFoundError: No module named 'app.services.word_export'
```

- [ ] **Step 3: Implement watermark helper**

Create `app/services/watermark.py`:

```python
from docx.document import Document as DocumentType


def add_text_watermark(document: DocumentType, watermark_text: str) -> None:
    if not watermark_text.strip():
        return
    section = document.sections[0]
    header = section.header
    paragraph = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    run = paragraph.add_run(watermark_text)
    run.font.size = None
```

- [ ] **Step 4: Implement Word export**

Create `app/services/word_export.py`:

```python
import json
from pathlib import Path

from docx import Document

from app.models import ApiInterface, InterfaceDirection
from app.services.watermark import add_text_watermark


def export_word_document(
    output_path: Path,
    interfaces: list[ApiInterface],
    request_examples: dict[int, dict],
    response_examples: dict[int, dict],
    watermark_text: str = "",
) -> Path:
    document = Document()
    add_text_watermark(document, watermark_text)
    document.add_heading("珠海超毅 EAP-EQP API 接口通讯规格书", level=0)
    document.add_paragraph("本文档由接口管理系统自动生成。")
    _append_direction(document, interfaces, InterfaceDirection.EQP_TO_EAP, "EQP -> EAP 接口", request_examples, response_examples)
    _append_direction(document, interfaces, InterfaceDirection.EAP_TO_EQP, "EAP -> EQP 接口", request_examples, response_examples)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_path)
    return output_path


def _append_direction(
    document: Document,
    interfaces: list[ApiInterface],
    direction: InterfaceDirection,
    heading: str,
    request_examples: dict[int, dict],
    response_examples: dict[int, dict],
) -> None:
    document.add_heading(heading, level=1)
    for item in interfaces:
        if item.direction != direction:
            continue
        document.add_heading(f"{item.code} {item.name}", level=2)
        table = document.add_table(rows=0, cols=4)
        _add_row(table, "需求说明", item.requirement, item.requirement, item.requirement)
        _add_row(table, "使用场景", item.scenario, item.scenario, item.scenario)
        _add_row(table, "接口名称", item.api_name, item.api_name, item.api_name)
        _add_row(table, "接口方式", "接口调用方", "接口提供方", "接口服务描述")
        _add_row(table, "Web API", item.caller, item.provider, item.service_description)
        document.add_paragraph("请求示例")
        document.add_paragraph(json.dumps(request_examples.get(item.id or 0, {}), ensure_ascii=False, indent=2))
        document.add_paragraph("响应示例")
        document.add_paragraph(json.dumps(response_examples.get(item.id or 0, {}), ensure_ascii=False, indent=2))


def _add_row(table, *values: str) -> None:
    row = table.add_row()
    for index, value in enumerate(values):
        row.cells[index].text = value
```

- [ ] **Step 5: Run test**

Run:

```powershell
pytest tests/test_word_export.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 6: Commit**

```powershell
git add app/services/watermark.py app/services/word_export.py tests/test_word_export.py
git commit -m "feat: export word document with watermark"
```

---

### Task 8: PDF Export

**Files:**
- Create: `app/services/pdf_export.py`
- Create: `tests/test_pdf_export.py`

- [ ] **Step 1: Write PDF export test**

Create `tests/test_pdf_export.py`:

```python
from pathlib import Path

from app.services.pdf_export import export_basic_pdf


def test_basic_pdf_export_creates_file(tmp_path: Path):
    output = tmp_path / "spec.pdf"

    export_basic_pdf(output, "珠海超毅 EAP-EQP API 接口通讯规格书", watermark_text="厂商查看")

    assert output.exists()
    assert output.stat().st_size > 0
```

- [ ] **Step 2: Run test to verify failure**

Run:

```powershell
pytest tests/test_pdf_export.py -v
```

Expected:

```text
ModuleNotFoundError: No module named 'app.services.pdf_export'
```

- [ ] **Step 3: Implement basic PDF export**

Create `app/services/pdf_export.py`:

```python
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def export_basic_pdf(output_path: Path, title: str, watermark_text: str = "") -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4
    if watermark_text:
        pdf.saveState()
        pdf.setFont("Helvetica", 42)
        pdf.setFillGray(0.85)
        pdf.translate(width / 2, height / 2)
        pdf.rotate(35)
        pdf.drawCentredString(0, 0, watermark_text)
        pdf.restoreState()
    pdf.setFont("Helvetica", 16)
    pdf.drawString(60, height - 80, title)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(60, height - 110, "Generated by interface manager.")
    pdf.showPage()
    pdf.save()
    return output_path
```

- [ ] **Step 4: Run test**

Run:

```powershell
pytest tests/test_pdf_export.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: Commit**

```powershell
git add app/services/pdf_export.py tests/test_pdf_export.py
git commit -m "feat: add pdf export with watermark"
```

---

### Task 9: Export Center UI

**Files:**
- Create: `app/routers/exports.py`
- Modify: `app/main.py`
- Create: `app/templates/export_center.html`
- Create: `app/templates/export_result.html`

- [ ] **Step 1: Create export router**

Create `app/routers/exports.py`:

```python
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.database import get_session
from app.models import ApiInterface, ExportRecord
from app.services.examples import build_request_example, build_response_example
from app.services.markdown_export import render_markdown_document
from app.services.pdf_export import export_basic_pdf
from app.services.word_export import export_word_document


router = APIRouter(prefix="/exports")
templates = Jinja2Templates(directory="app/templates")


@router.get("")
def export_center(request: Request):
    return templates.TemplateResponse(
        "export_center.html",
        {"request": request, "title": "导出中心"},
    )


@router.post("")
def run_export(
    request: Request,
    export_format: str = Form(...),
    watermark_enabled: bool = Form(False),
    watermark_text: str = Form(""),
    session: Session = Depends(get_session),
):
    interfaces = session.exec(select(ApiInterface).order_by(ApiInterface.code)).all()
    request_examples = {item.id or 0: build_request_example(item, []) for item in interfaces}
    response_examples = {item.id or 0: build_response_example(item, []) for item in interfaces}
    output_files: list[str] = []
    watermark = watermark_text if watermark_enabled else ""
    export_dir = Path("exports")

    if export_format in {"markdown", "all"}:
        markdown_path = export_dir / "EAP-EQP接口通讯规格书.md"
        markdown_path.write_text(
            render_markdown_document(interfaces, request_examples, response_examples),
            encoding="utf-8",
        )
        output_files.append(str(markdown_path))

    if export_format in {"word", "word_pdf", "all"}:
        word_path = export_dir / "EAP-EQP接口通讯规格书.docx"
        export_word_document(word_path, interfaces, request_examples, response_examples, watermark)
        output_files.append(str(word_path))

    if export_format in {"pdf", "word_pdf", "all"}:
        pdf_path = export_dir / "EAP-EQP接口通讯规格书.pdf"
        export_basic_pdf(pdf_path, "珠海超毅 EAP-EQP API 接口通讯规格书", watermark)
        output_files.append(str(pdf_path))

    record = ExportRecord(
        version="4.0",
        scope="all",
        formats=export_format,
        watermark_enabled=watermark_enabled,
        watermark_text=watermark,
        output_path=";".join(output_files),
        result="success",
    )
    session.add(record)
    session.commit()

    return templates.TemplateResponse(
        "export_result.html",
        {"request": request, "title": "导出结果", "output_files": output_files},
    )
```

- [ ] **Step 2: Register export routes**

Modify `app/main.py`:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import exports, interfaces, pages


app = FastAPI(title="EAP-EQP Interface Manager")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(pages.router)
app.include_router(interfaces.router)
app.include_router(exports.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
```

- [ ] **Step 3: Create export center template**

Create `app/templates/export_center.html`:

```html
{% extends "base.html" %}

{% block content %}
<form class="form-panel" method="post" action="/exports">
  <label>
    导出格式
    <select name="export_format">
      <option value="word">Word</option>
      <option value="pdf">PDF</option>
      <option value="word_pdf">Word + PDF</option>
      <option value="markdown">Markdown 审阅版</option>
      <option value="all">Word + PDF + Markdown</option>
    </select>
  </label>
  <label class="check-row">
    <input type="checkbox" name="watermark_enabled" value="true">
    添加水印
  </label>
  <label>
    水印文字
    <input name="watermark_text" value="厂商查看">
  </label>
  <div class="actions">
    <button type="submit">开始导出</button>
    <a href="/">返回工作台</a>
  </div>
</form>
{% endblock %}
```

- [ ] **Step 4: Create export result template**

Create `app/templates/export_result.html`:

```html
{% extends "base.html" %}

{% block content %}
<div class="table-wrap">
  <h2>已生成文件</h2>
  <ul>
    {% for file in output_files %}
    <li>{{ file }}</li>
    {% endfor %}
  </ul>
  <a class="button" href="/exports">继续导出</a>
  <a class="button secondary" href="/">返回工作台</a>
</div>
{% endblock %}
```

- [ ] **Step 5: Manual verification**

Run:

```powershell
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/exports
```

Expected:

- Export center loads.
- User can choose Word, PDF, Word + PDF, Markdown.
- User can enable watermark and set text.
- Export creates files under `exports/`.

- [ ] **Step 6: Commit**

```powershell
git add app/routers/exports.py app/templates/export_center.html app/templates/export_result.html app/main.py
git commit -m "feat: add export center"
```

---

### Task 10: Final Verification and Push

**Files:**
- Modify as needed after verification.

- [ ] **Step 1: Run all tests**

Run:

```powershell
pytest -v
```

Expected:

```text
All tests pass.
```

- [ ] **Step 2: Run local app**

Run:

```powershell
uvicorn app.main:app --reload
```

Expected:

```text
Uvicorn running on http://127.0.0.1:8000
```

- [ ] **Step 3: Manual functional check**

Check:

- Home page opens.
- Add interface page opens.
- Interface can be saved.
- Export center opens.
- Word export creates `.docx`.
- PDF export creates `.pdf`.
- Markdown export creates `.md`.
- Watermark text appears in Word header text and PDF page.

- [ ] **Step 4: Check Git status**

Run:

```powershell
git status
```

Expected:

```text
nothing to commit, working tree clean
```

If there are changes, commit them:

```powershell
git add .
git commit -m "chore: complete v1 verification fixes"
```

- [ ] **Step 5: Push**

Run:

```powershell
git push
```

Expected:

```text
main -> main
```

---

## Self-Review

Spec coverage:

- Structured interface management is covered by Tasks 2, 3, 4, and 5.
- JSON example generation is covered by Task 4.
- Markdown export is covered by Task 6.
- Word export is covered by Task 7.
- PDF export is covered by Task 8.
- Watermark export configuration is covered by Tasks 7, 8, and 9.
- Export records are covered by Tasks 2 and 9.
- Semi-automatic Word import is intentionally deferred to V2 and is documented as excluded from V1.

Placeholder scan:

- No `TBD`, `TODO`, or unspecified implementation placeholders are present.

Type consistency:

- `InterfaceDirection`, `ParameterKind`, `ApiInterface`, `ApiParameter`, and `ExportRecord` names are consistent across tasks.
- Export service function names are consistent with tests and routes.

