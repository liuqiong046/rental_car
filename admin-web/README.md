# rental_car Admin Web

PC 管理后台目录，规划使用 Vue 3 + TypeScript + Vite + Element Plus。

## 规划职责

- 工作台
- 城市、组织、账号与权限
- 车辆、价格、库存
- 客户订单、批发订单、工单
- 财务、押金、退款、结算
- 售后、投诉、通知、日志、导出

## 本地启动

```bash
cd admin-web
npm install
npm run dev
```

默认代理 `/api` 到 `http://127.0.0.1:8000`。如需指定后端地址，可设置 `VITE_API_BASE`。

## 验证账号

| 账号 | 密码 | 数据范围 |
| --- | --- | --- |
| `hq_admin` | `hq_admin123` | 全平台 |
| `ops_admin` | `ops_admin123` | 三亚城市 |
| `disabled_admin` | `disabled_admin123` | 停用账号，不可登录 |

## 已落地能力

- 登录页、登录态保存和退出。
- 未登录访问后台业务页跳转登录。
- 组织、账号、角色列表。
- 账号启用/停用操作，对应服务端权限校验和状态更新。
