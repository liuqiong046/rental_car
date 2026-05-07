# rental_car Backend

FastAPI 后端目录，参考 onePet 的 `router.py`、`schemas.py`、`service.py` 单仓多模块结构。接口规范入口见 `../doc/接口规范-V1.md`。

## 目录结构

```text
backend/
├─ pyproject.toml
├─ app/
│  ├─ main.py
│  ├─ core/
│  ├─ apps/
│  │  └─ system/
│  ├─ integrations/
│  └─ tasks/
├─ alembic/
└─ tests/
```

## 本地启动

推荐使用 Python 3.12。当前基线代码兼容 Python 3.11，便于本机验证。

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

启动后访问：

- `GET /healthz`
- `GET /api/v1/system/health`
- `GET /openapi.json`

## 测试

```bash
cd backend
python -m pytest
```

## 工程约定

- 业务接口统一挂载到 `/api/v1`。
- 模块默认按 `router.py`、`schemas.py`、`service.py`、必要时 `deps.py` 分层。
- FastAPI 路由必须声明 `response_model`、`summary` 和明确状态码。
- 日志不得记录手机号、身份证、驾驶证、详细地址、token、密钥、支付配置明文。
- 请求链路统一返回 `X-Request-ID`，方便后续审计和故障定位。
