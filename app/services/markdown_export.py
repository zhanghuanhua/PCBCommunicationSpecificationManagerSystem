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
    _append_direction(
        lines,
        interfaces,
        InterfaceDirection.EQP_TO_EAP,
        "EQP -> EAP 接口",
        request_examples,
        response_examples,
    )
    _append_direction(
        lines,
        interfaces,
        InterfaceDirection.EAP_TO_EQP,
        "EAP -> EQP 接口",
        request_examples,
        response_examples,
    )
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
        key = item.id or 0
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
                json.dumps(request_examples.get(key, {}), ensure_ascii=False, indent=2),
                "```",
                "",
                "#### 响应示例",
                "",
                "```json",
                json.dumps(response_examples.get(key, {}), ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )
