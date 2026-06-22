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

## Windows 服务器部署

建议在服务器上准备以下目录：

```text
D:\EAPSystem\
D:\EAPSystem\data\
D:\EAPSystem\exports\
D:\EAPSystem\uploads\
```

服务器部署时，系统会使用这些目录：

- `D:\EAPSystem\data\interface_manager.db`：共享数据库文件。
- `D:\EAPSystem\exports`：Word、PDF、Markdown 导出文件。
- `D:\EAPSystem\uploads`：导入的原始规格书模板。

第一次部署：

```powershell
cd D:\EAPSystem\app
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

手动启动：

```powershell
.\scripts\start-server.ps1
```

浏览器访问：

```text
http://服务器IP:8000
```

如果需要开机自动启动，请用管理员身份打开 PowerShell 后执行：

```powershell
.\scripts\install-windows-service.ps1
```

如服务器防火墙未放行 8000 端口，可用管理员身份执行：

```powershell
New-NetFirewallRule -DisplayName "EAP Spec Manager 8000" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000
```

日常备份重点备份：

```text
D:\EAPSystem\data\interface_manager.db
D:\EAPSystem\uploads\
D:\EAPSystem\exports\
```
