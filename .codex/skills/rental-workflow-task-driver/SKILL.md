---
name: rental-workflow-task-driver
description: Use when starting or resuming implementation work in rental_car that should map to a workflow task under workflow/tasks
---

# rental_car Workflow Task Driver

## Overview

在 rental_car 中，开发必须先锚定一个 `WF-*` 任务包，再写代码。任务包是范围、依赖、接口契约和验收的唯一合同。

## Required Flow

1. 先定位唯一任务 ID，例如 `WF-P0-10`。
2. 读取三处内容：
   - `workflow/tasks/P0|P1|P2/<task>.md`
   - `workflow/index.md`
   - `workflow/owners/<owner>.md`，当前待定任务读取 `workflow/owners/unassigned.md`
3. 确认 `depends_on` 已完成；未解锁时不得直接开工。
4. 只做任务包 `范围内改动`；超出边界不要顺手吸收。
5. 真正开始改代码前，把状态切到 `开发中`，并同步使用 `rental-workflow-status-sync`。

## Scope Rules

- 一次只推进一个 workflow 小任务。
- `交付物` 和 `验收动作` 决定做到哪里算完成。
- 新增或修改接口时，同时使用 `rental-api-contract-guard`。
- 涉及敏感信息、支付、退款、导出、密钥时，同时使用 `rental-secrets-and-pii-guard`。

## Hard Gate

任务结束必须更新开发 plan 进度。未同步 `workflow/index.md`、任务包、owner 视图，不得声称任务完成。

## Never Do

- 不允许脱离 `WF-*` 编号直接开发。
- 不允许依赖未完成时假设上游稍后补上。
- 不允许一个提交混入多个无关任务。

