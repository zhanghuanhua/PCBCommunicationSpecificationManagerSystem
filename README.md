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
