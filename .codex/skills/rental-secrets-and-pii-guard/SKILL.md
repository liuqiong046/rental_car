---
name: rental-secrets-and-pii-guard
description: Use when rental_car code touches secrets, third-party credentials, payments, refunds, exports, audit logs, or sensitive PII fields
---

# rental_car Secrets and PII Guard

## Overview

密钥、支付配置和敏感信息是上线硬门禁。任何相关改动必须先满足本 skill。

## Secrets Rules

- 微信支付、对象存储、地图、短信、JWT、加密主密钥只允许从配置和环境变量读取。
- 密钥不得入库、不得入日志、不得提交到源码或示例配置。
- 第三方能力统一封装在 `app/integrations/<provider>/`。

## PII Rules

| 字段 | 落库 | 展示 |
| --- | --- | --- |
| 手机号 | 密文或受控字段 + `phone_mask` | 默认只返回 mask |
| 身份证号 | 密文 + `id_no_mask` | 默认只返回 mask |
| 驾驶证号/照片 | 受控存储 | 默认脱敏或授权 URL |
| 详细地址 | 密文或受控字段 | 按角色返回 summary 或审计后明文 |
| 支付配置 | 配置系统 | 不返回前端 |

## Audit Required

下列动作必须记录审计或操作日志：

- 查看完整证件、详细地址或导出敏感数据
- 支付、退款、押金确认、结算、金额调整
- 权限变更、账号停用、车辆删除或强制下架
- 价格规则、城市规则和确认 SLA 修改

## Logging Rules

- 不要打印整份请求体或用户对象。
- 错误日志记录业务 ID、错误码和影响，不记录敏感原文。

## Never Do

- 不要把密钥、token、证件号、手机号、详细地址写进日志或文档。
- 不要让导出绕过数据范围。
- 不要让支付、退款、结算缺少审计。

