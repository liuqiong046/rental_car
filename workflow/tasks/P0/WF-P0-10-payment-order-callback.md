# WF-P0-10 微信支付、订单创建与支付回调

| 字段 | 值 |
| --- | --- |
| ID | WF-P0-10 |
| 阶段 | P0 / 阶段一 |
| Owner | 蔡佳 |
| 优先级 | P0 |
| 预计体量 | 1-2 天 |

> 说明：owner 负责该任务全栈闭环，不再拆前后端子任务。

## 目标

打通微信支付预下单、C 端支付、支付回调幂等和客户订单进入待接单。

## 业务闭环

用户支付租金和服务费后，订单从待支付进入待接单，并同步 PC 后台和管理端待办数据源。

## 输入文档

- PRD §4.1、§5.8、§10、§13
- `doc/接口规范-V1.md`：payments 和幂等规则

## 范围内改动

- 支付预下单接口。
- C 端调起微信支付。
- 支付回调验签、幂等和订单状态推进。
- 支付流水记录。

## 非目标

- 不实现退款。
- 不实现押金线上支付。

## 前置依赖

- `WF-P0-02`
- `WF-P0-09`

## 交付物

- 微信支付配置和 sandbox/mock 入口。
- 支付成功订单进入待接单。
- 重复回调只生效一次。

## 验收动作

1. 未支付订单可发起支付。
2. 支付成功后订单进入待接单。
3. 重复支付回调不会重复写流水或重复推进状态。

## 完成定义

- 后续接单、批发和通知任务可监听支付后订单。

## 下游 handoff

- `WF-P0-11`
- `WF-P0-12`
- `WF-P0-19`

## 当前状态

- 状态：待验收
- 说明：已完成支付预下单、mock/sandbox 支付、支付回调幂等、支付流水内存记录、订单进入待接单以及 C 端支付/重试入口；后端自动验证与后台 build 已通过，待微信开发者工具人工预览支付页和订单详情。

## H5/PRD 复核标注

- 前端完成：C 端确认订单已接入提交并支付；订单详情支持继续支付，mock 支付成功后展示待门店接单和已支付金额，待支付未完成时可回到订单详情继续支付。
- 后端完成：`POST /api/v1/payments/prepay`、`POST /api/v1/payments/wechat/callback`、支付回调幂等、支付流水内存记录、支付金额校验、订单从 `pending_payment/unpaid` 推进到 `pending_acceptance/paid`。
- 验收提示：仍需微信开发者工具人工预览确认订单页、订单详情、支付失败/取消提示和固定底部按钮；正式微信支付验签、证书和密钥接入不在本任务范围内，当前仅提供 `wechat_mock` sandbox 入口。

## 验证记录

- `python3 -m pytest tests/apps/payments/test_payment_api.py -q`（backend）：5 passed，1 个 `python_multipart` 依赖弃用 warning。
- `python3 -m pytest tests -q`（backend）：55 passed，1 个 `python_multipart` 依赖弃用 warning。
- `find miniprogram -name '*.js' -print0 | xargs -0 -n1 node --check`：通过。
- `npm run build`（admin-web）：通过；Vite 产物构建成功，保留 chunk size warning。
