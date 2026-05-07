---
name: rental-code-quality-guard
description: Use when writing or modifying code for rental_car to enforce project rules for structure, logging, comments, errors, and verification readiness
---

# rental_car Code Quality Guard

## Overview

代码要能跑，也要方便多人和后续 AI 接手。结构、日志、注释、错误处理和验证方式必须一起交付。

## Code Rules

- 函数职责单一，避免同时处理校验、编排、持久化和格式转换。
- 命名直接表达租车业务含义，避免 `data`、`temp`、`handle2`。
- 城市、价格、订单状态、批发状态、押金和退款规则不得散落硬编码。
- 共享接口、状态枚举和金额计算变更必须同步任务包或接口规范。

## Logging Rules

- 关键流程记录进入、关键分支、失败、外部调用结果。
- 日志优先记录 `request_id`、`order_id`、`vehicle_id`、`work_order_id`、`actor_id`。
- 严禁记录手机号、身份证、驾驶证、详细地址、token、密钥、支付配置明文。

## Comment Rules

- 注释解释业务规则和为什么这样做，不翻译代码。
- 状态机、价格、退款、锁车、批发确认 SLA、支付回调幂等必须有简洁注释。
- 修改代码时删除过期注释。

## High-Risk Change Tests

下列变更必须优先补测试：

- 订单、批发订单、工单状态机
- 未支付锁车和释放
- 价格快照和费用预估
- 改派差价、退款和结算
- 支付回调、退款、接拒单、费用调整幂等
- 权限和数据范围隔离

## Completion

声称完成前转交 `rental-delivery-gate`。

