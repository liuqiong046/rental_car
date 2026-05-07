---
name: rental-api-contract-guard
description: Use when adding or changing rental_car backend APIs, request or response DTOs, OpenAPI behavior, authentication, errors, or idempotent endpoints
---

# rental_car API Contract Guard

## Overview

接口是三端协作合同。新增或修改 API 时，必须保持路径、DTO、鉴权、错误、幂等和测试一致。

## Required Rules

- 路由统一使用 `/api/v1`。
- 模块按 `router.py`、`schemas.py`、`service.py`、必要时 `deps.py` 分层。
- FastAPI 路由必须声明 `response_model`、`summary` 和明确状态码。
- DTO 使用 Pydantic v2；列表响应统一 `{ items, total? }`。
- 鉴权、角色和数据范围必须服务端校验。
- 错误返回至少包含稳定 `detail`，后续扩展错误码不得破坏 `detail`。

## Idempotency Required

以下接口必须要求 `Idempotency-Key`：

- 下单、支付预下单、支付回调
- 退款发起
- 客户订单接单、退单、改派
- 批发订单接单、拒绝、改价
- 工单完成、现场费用新增
- 押金/免押确认、结算完成

## Documentation Sync

修改接口必须同步：

- `doc/接口规范-V1.md`，或
- 当前 `workflow/tasks/*` 中的接口契约说明。

## Test Rules

- 接口测试使用 `pytest` + `httpx.AsyncClient`。
- 覆盖状态码、响应字段、鉴权失败、数据范围隔离、非法状态、幂等重复提交。
- 不只断言 200。

## Never Do

- 不要让前端靠猜测响应字段接入。
- 不要在列表接口返回敏感明文。
- 不要只在前端隐藏按钮代替权限校验。

