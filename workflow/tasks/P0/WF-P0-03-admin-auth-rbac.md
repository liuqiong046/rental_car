# WF-P0-03 PC 后台登录、组织、账号与权限

| 字段 | 值 |
| --- | --- |
| ID | WF-P0-03 |
| 阶段 | P0 / 阶段一 |
| Owner | 待定 |
| 优先级 | P0 |
| 预计体量 | 1-2 天 |

> 说明：owner 负责该任务全栈闭环，不再拆前后端子任务。

## 目标

建立 PC 后台登录、组织、账号、角色、菜单和基础数据范围能力。

## 业务闭环

总部、运营中心、车行和岗位账号能登录后台，并按角色看到基础菜单和授权数据范围。

## 输入文档

- PRD §3.3、§3.4、§7.3、§11.2
- `doc/接口规范-V1.md`：鉴权、权限与数据范围

## 范围内改动

- 后台登录页、会话保存、退出。
- 后端账号、角色、组织和权限基础接口。
- PC 后台组织账号和角色管理基础页面。

## 非目标

- 不实现完整字段权限、复杂审批流和高级数据权限。
- 不实现业务模块的细粒度按钮全集。

## 前置依赖

- `WF-P0-01`
- `WF-P0-02`

## 交付物

- 后台可登录。
- 可创建或维护组织、账号、角色。
- 权限依赖可供后续配置、审核、财务模块复用。

## 验收动作

1. 未登录访问后台业务页会跳转登录。
2. 不同角色看到的数据范围不同。
3. 停用账号不可登录。

## 完成定义

- 后续 PC 配置、审核、财务、日志任务可挂载到权限体系。

## H5/PRD 复核标注

- 已补前端：PC 后台已支持组织新增/编辑/停用、角色新增/维护、账号新增/编辑、重置密码、停用/启用和锁定；菜单/按钮权限可在角色表中维护。
- 已补后端：已新增组织维护、角色维护、账号编辑、重置密码和锁定/解锁接口；密码哈希不再按用户名固定推导，新建/重置账号使用独立哈希。
- 剩余非目标：账号、角色、组织、token 仍为内存数据源；完整字段权限、复杂审批流、审计日志查看与持久化归属后续基础设施或 `WF-P0-19`。

## 接口契约补充

- `POST /api/v1/admin/organizations`
- `PATCH /api/v1/admin/organizations/{organization_id}`
- `POST /api/v1/admin/roles`
- `PATCH /api/v1/admin/roles/{role_id}`
- `PATCH /api/v1/admin/accounts/{account_id}`
- `POST /api/v1/admin/accounts/{account_id}/reset-password`

## 下游 handoff

- `WF-P0-05`
- `WF-P0-07`
- `WF-P0-18`
- `WF-P0-19`

## 当前状态

- 状态：已完成
- 说明：已按 `/Users/liuqiong/Downloads/admin/pages/lanhu_tianjiayuangong`、`lanhu_tianjiagangwei`、`lanhu_gangweiyuangong`、`staff_permission` 收敛后台登录、组织、账号、角色和权限页面，并移出 `AdminShell` 中超出 `WF-P0-03` 范围的城市、车辆、身份审核、客户订单和批发订单内容；2026-05-06 已完成 API 与页面双验收。

## 验证记录

- 2026-05-06：已读取 `workflow/index.md`、`workflow/tasks/P0/WF-P0-01` 至 `WF-P0-20`、`workflow/owners/unassigned.md`、`doc/requirements/shanhai-rental-mini-programs-requirements.md`、`doc/接口规范-V1.md`、`doc/技术栈方案-V1.md`。
- 2026-05-06：已读取 PC admin 原型源码目录 `/Users/liuqiong/Downloads/admin/pages/lanhu_tianjiayuangong`、`/Users/liuqiong/Downloads/admin/pages/lanhu_tianjiagangwei`、`/Users/liuqiong/Downloads/admin/pages/lanhu_gangweiyuangong`、`/Users/liuqiong/Downloads/admin/pages/staff_permission`；辅助读取 `/Users/liuqiong/Downloads/admin/pages/lanhu_kongzhitai` 确认后续业务入口归属。
- 2026-05-06：`rg -n "fetchCityConfigs|fetchVehicles|fetchIdentity|fetchCustomerOrders|fetchWholesaleOrders|customerOrders|wholesaleOrders|cities|vehicles|identities" admin-web/src/views/AdminShell.vue admin-web/src/components/admin-rbac admin-web/src/views/LoginView.vue` 未命中，确认当前后台壳页未再混入后续 WF 页面数据加载逻辑。
- 2026-05-06：`cd admin-web && npm run build` 通过；Vite 仍提示构建产物 chunk 大于 500 kB，但不影响 `WF-P0-03` 本次页面返修交付。
- 2026-05-06：`cd backend && python3 -m pytest tests/apps/admin/test_admin_api.py` 通过，`7 passed`；已覆盖未登录访问后台接口返回 `401 请先登录`、`ops_admin` 账号只看到其城市范围账号、`disabled_admin` 登录返回 `403 账号不可用`。
- 2026-05-06：本机 `browser-use` 的 `iab` backend 不可用，改用独立 Chromium + Playwright 页面验收；`curl -i http://127.0.0.1:8000/healthz` 返回 `200`，`curl -i -X POST http://127.0.0.1:8000/api/v1/admin/auth/login ...` 返回 `200`，确认后台服务可用。
- 2026-05-06：`cd admin-web && npx playwright test .codex-acceptance/wf-p0-03-acceptance.spec.js --reporter=line` 通过，`1 passed (4.3s)`；已实测 `http://127.0.0.1:5175` 未登录访问 `/` 自动跳转 `/login`、`hq_admin` 登录后显示 `全平台`、`ops_admin` 登录后显示 `城市 SY`、`disabled_admin` 登录停留在 `/login` 且提示 `账号不可用`。
