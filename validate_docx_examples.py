from __future__ import annotations

import json
import re
from pathlib import Path


import sys


TEXT_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("review_output/docx_extract.txt")


def line_no(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def normalize_quotes(s: str) -> str:
    return s.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")


def collect_balanced_json(text: str):
    items = []
    stack = 0
    start = None
    in_string = False
    escape = False
    for i, ch in enumerate(text):
        if start is None:
            if ch == "{":
                start = i
                stack = 1
                in_string = False
                escape = False
            continue
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            stack += 1
        elif ch == "}":
            stack -= 1
            if stack == 0:
                items.append((start, i + 1, text[start : i + 1]))
                start = None
    if start is not None:
        items.append((start, len(text), text[start:]))
    return items


def nearest_title(lines, n):
    title = ""
    for i in range(n - 1, max(-1, n - 80), -1):
        m = re.match(r"^(EQP-EAP|EAP-EQP)-\d{3}\s+(.+)$", lines[i].strip())
        if m:
            title = lines[i].strip()
            break
    return title


def nearest_endpoint(lines, n):
    for i in range(n - 1, max(-1, n - 30), -1):
        m = re.search(r"REST:POST\s+(\S+)", lines[i])
        if m:
            return m.group(1)
    return ""


def flatten_keys(obj, prefix=""):
    keys = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else k
            keys.add(p)
            keys |= flatten_keys(v, p)
    elif isinstance(obj, list):
        for v in obj:
            keys |= flatten_keys(v, prefix + "[]")
    return keys


def main():
    text = TEXT_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()
    examples = []
    for start, end, raw in collect_balanced_json(text):
        ln = line_no(text, start)
        title = nearest_title(lines, ln)
        endpoint = nearest_endpoint(lines, ln)
        normal = normalize_quotes(raw)
        parsed = None
        err = ""
        try:
            parsed = json.loads(normal)
        except Exception as exc:
            err = str(exc)
        examples.append(
            {
                "line": ln,
                "title": title,
                "endpoint": endpoint,
                "valid_after_quote_normalize": parsed is not None,
                "has_smart_quotes": raw != normal,
                "error": err,
                "message": parsed.get("Message") if isinstance(parsed, dict) else "",
                "request_id": parsed.get("RequestId") if isinstance(parsed, dict) else "",
                "keys": sorted(flatten_keys(parsed)) if parsed is not None else [],
                "snippet": raw[:400].replace("\n", "\\n"),
            }
        )
    invalid = [e for e in examples if not e["valid_after_quote_normalize"] or e["has_smart_quotes"]]
    endpoint_mismatch = []
    for e in examples:
        msg = e.get("message") or ""
        ep = e.get("endpoint") or ""
        if msg and ep and not ep.endswith("/" + msg):
            endpoint_mismatch.append(e)
    reqid_mismatch = []
    by_title = {}
    for e in examples:
        by_title.setdefault(e["title"], []).append(e)
    for title, arr in by_title.items():
        if not title:
            continue
        ids = {e["request_id"] for e in arr if e["request_id"]}
        if len(ids) > 1:
            reqid_mismatch.append({"title": title, "ids": sorted(ids), "lines": [e["line"] for e in arr]})

    output = {
        "example_count": len(examples),
        "invalid_or_smart_quote": invalid,
        "endpoint_mismatch": endpoint_mismatch,
        "request_id_mismatch_by_interface": reqid_mismatch,
    }
    Path("review_output/example_validation.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in output.items()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
