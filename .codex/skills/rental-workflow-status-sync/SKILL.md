---
name: rental-workflow-status-sync
description: Use when rental_car workflow task status changes, including start, pause, blocker, handoff, verification, or completion
---

# rental_car Workflow Status Sync

## Overview

在 rental_car 中，状态不同步等于没有协作。任何开始、阻塞、待验收、完成都必须回写 workflow 文件。

## Update Targets

每次状态变化至少同步三处：

1. `workflow/index.md`
2. 当前任务包 `workflow/tasks/P0|P1|P2/<task>.md`
3. 对应 owner 视图；owner 为 `待定` 时同步 `workflow/owners/unassigned.md`

## Allowed Status

- `待开始`
- `可领取`
- `开发中`
- `待验收`
- `已完成`
- `阻塞`
- `待规划`：仅用于 P2 backlog

## Update Rules

- 开始编码前：切到 `开发中`
- 代码完成但待人工或联调验收：切到 `待验收`
- 验收动作已执行并通过：切到 `已完成`
- 依赖缺失、需求冲突、外部条件不足：切到 `阻塞`
- 上游完成后才把下游从 `待开始` 切到 `可领取`

## Task File Rule

任务包 `当前状态` 至少包含：

```md
- 状态：开发中
- 说明：正在实现支付回调与订单状态推进
```

## Never Do

- 不要代码已经开始写了，状态还停在 `待开始`。
- 不要只更新一个文件。
- 不要任务已完成但 owner 视图仍显示阻塞或待开始。

