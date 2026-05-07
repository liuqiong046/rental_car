# WF-P0-02 后端工程化基线、接口规范落地与服务端基础设施

| 字段 | 值 |
| --- | --- |
| ID | WF-P0-02 |
| 阶段 | P0 / 阶段一 |
| Owner | 待定 |
| 优先级 | P0 |
| 预计体量 | 1-2 天 |

> 说明：owner 负责该任务全栈闭环，不再拆前后端子任务。

## 目标

建立 FastAPI 后端工程化基线，并把 `doc/接口规范-V1.md` 的路由、DTO、鉴权、错误和测试约定落到骨架中。

## 业务闭环

后端可以启动、暴露健康检查和 OpenAPI，具备配置、日志、测试、接口分层和后续业务模块承接能力。

## 输入文档

- `doc/技术栈方案-V1.md`
- `doc/接口规范-V1.md`
- onePet 后端 `router.py`、`schemas.py`、`service.py` 分层作为风格参考

## 范围内改动

- 配置 `pyproject.toml`、FastAPI 入口、健康检查、基础 settings、日志脱敏占位。
- 建立 `app/apps/*` 分层约定和测试目录。
- 建立 pytest + httpx.AsyncClient 的接口测试样例。

## 非目标

- 不实现具体订单、支付、车辆和权限业务。
- 不接入真实第三方密钥。

## 前置依赖

- `WF-P0-01`

## 交付物

- 可启动后端骨架。
- `/healthz` 或等价健康检查。
- 一条接口测试样例。
- 接口规范在 README 或代码注释中有链接。

## 验收动作

1. 后端依赖安装命令可执行。
2. 本地启动后可访问健康检查。
3. 测试命令能运行并通过基础接口测试。

## 完成定义

- 后续 auth、admin、order 模块可直接按接口规范新增。
- 关键目录与 `doc/接口规范-V1.md` 一致。

## H5/PRD 复核标注

- 前端待补：无独立前端交付范围。
- 后端待补：当前服务仍是工程化基线；真实数据库持久化、token 持久化、异步任务、支付/订单/车辆等业务接口不在本任务完成范围内，后续任务接入时必须替换内存占位和 demo 数据源。

## 下游 handoff

- `WF-P0-03`
- `WF-P0-05`
- `WF-P0-10`

## 当前状态

- 状态：已完成
- 说明：已落地 FastAPI 工程化基线、`/healthz`、`/api/v1/system/health`、配置、请求 ID、日志脱敏占位、README 启动说明和 pytest/httpx 接口测试；2026-05-06 复核确认本任务无独立小程序页面或 UI 原型目录，依赖解析 dry-run、Uvicorn 健康检查和 pytest 均已重新验证。

## 验证记录

- 2026-05-06：已读取 `workflow/index.md`、`workflow/tasks/P0/WF-P0-01` 至 `WF-P0-20` 全部任务包、`workflow/owners/unassigned.md`、`doc/requirements/shanhai-rental-mini-programs-requirements.md`、`doc/接口规范-V1.md` 和 `doc/技术栈方案-V1.md`。
- 2026-05-06：本任务为后端工程化基线，无 C 端或管理端小程序页面交付；未读取 lanhu 页面原型目录，且未修改任何小程序页面。
- 2026-05-06：`python3 -m pip install -e ".[dev]" --dry-run`（backend）依赖解析通过，显示可安装 `rental-car-backend-0.1.0`、`pytest-asyncio`、`ruff`、`mypy` 等开发依赖。
- 2026-05-06：`python3 -m pytest tests/apps/system/test_health_api.py -q`（backend）通过，3 passed，1 个 `python_multipart` 依赖弃用 warning。
- 2026-05-06：`python3 -m pytest tests -q`（backend）通过，55 passed，1 个 `python_multipart` 依赖弃用 warning。
- 2026-05-06：`python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8012` 临时启动成功；`curl` 访问 `/healthz` 和 `/api/v1/system/health` 均返回 200、`X-Request-ID` 和 `{"status":"ok","service":"rental-car-api","version":"0.1.0"}`。
