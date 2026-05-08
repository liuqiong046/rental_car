# WF-P0-06 车型库、车辆、价格日历与库存可用性

| 字段 | 值 |
| --- | --- |
| ID | WF-P0-06 |
| 阶段 | P0 / 阶段一 |
| Owner | 蔡佳 |
| 优先级 | P0 |
| 预计体量 | 1-2 天 |

> 说明：owner 负责该任务全栈闭环，不再拆前后端子任务。

## 目标

建立车型库、车辆资料、车辆审核/上下架/维保/锁车状态、价格日历和可租性计算。

## 业务闭环

PC 后台维护车辆和价格，C 端与管理端只展示审核通过、已上架、未维保、未锁车且未被占用的车辆。

## 输入文档

- PRD §5.4、§5.5、§7.4、§7.5、§9.3、§9.4

## 范围内改动

- PC 后台车型库、车辆列表、车辆详情、价格日历。
- 后端 vehicles/prices 接口。
- 车辆可用性查询基础逻辑。

## 非目标

- 不实现订单锁车和支付占用。
- 不实现批量导入和高级统计。

## 前置依赖

- `WF-P0-05`

## 交付物

- 车型与车辆 CRUD。
- 价格日历维护，含底价、C 端价、批发价。
- 可租状态接口。

## 验收动作

1. 未审核、下架、维保、锁车车辆不出现在 C 端可租列表。
2. 价格缺失时车辆不可下单或给出明确提示。
3. 车辆来源能区分运营中心自有、托管车辆、车行车辆。

## 完成定义

- 后续车辆列表、确认订单和批发调车可读取车辆供给。

## 下游 handoff

- `WF-P0-08`
- `WF-P0-09`
- `WF-P0-12`

## H5/PRD 复核标注

- 前端未完成：PC 后台已补车辆供给入口、车型库新增/编辑/删除、车辆新增/编辑/删除、图片地址维护、托管个人/车行来源资料、维保/锁车状态、单日价格和批量 90 天价格维护；仍需人工浏览器验收交互细节。C 端详情仍需继续补全 H5 价格日历体验。
- 后端未完成：vehicles/prices 仍是内存种子；缺少车型/车辆 CRUD、批量价格、时间段库存、订单占用、维保/锁车持久化、删除约束、车辆来源组织校验和按取还时间精确计算可租性的长期数据源。
- 归属说明：最小车辆供给已可支撑 C 端浏览和确认订单；车行车辆关联批发订单依赖本任务后续补足车辆来源、批发价和可用性口径。

## 当前状态

- 状态：待验收
- 说明：Codex 已完成 PC 后台车辆供给入口、车型库/车辆 CRUD、状态维护、单日价格和批量价格日历 UI；自动验证通过，待人工浏览器验收。

## 验证记录

- `python3 -m pytest tests/apps/vehicles/test_vehicle_api.py -q`（backend）：9 passed，1 个 `python_multipart` 依赖弃用 warning。
- `python3 -m pytest tests -q`（backend）：55 passed，1 个 `python_multipart` 依赖弃用 warning。
- `python3 -m ruff check app tests`、`python3 -m mypy app`：本机未安装 `ruff` / `mypy`，未执行。
- 2026-05-07 `npm.cmd run build`（admin-web）：通过；Vite 提示 chunk 超过 500 kB。
- 2026-05-07 `python.exe -m pytest tests/apps/vehicles/test_vehicle_api.py -q`（backend）：9 passed。
- 2026-05-07 `python.exe -m pytest tests -q`（backend）：55 passed。
- 2026-05-07 `python.exe -m ruff check app tests`、`python.exe -m mypy app`：可执行但未通过，暴露既有全仓 import/长行/type debt；本次未修改后端源码。
