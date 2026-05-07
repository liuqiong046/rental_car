---
name: rental-delivery-gate
description: Use when claiming rental_car task completion, moving a workflow item to verification or done, or handing work to another owner
---

# rental_car Delivery Gate

## Overview

任务完成不是代码写完，而是符合任务包、经过验证、状态已同步、可被下游接手。

## Completion Checklist

在把任务切到 `待验收` 或 `已完成` 前，逐项确认：

1. 改动仍在当前 `WF-*` 任务包边界内。
2. `交付物` 已全部落地。
3. 已执行对应 `验收动作`，结果可复述。
4. 接口、日志、注释、错误处理和文档同步到位。
5. `workflow/index.md`、任务包、owner 视图状态一致。
6. 下游 handoff 所需接口、页面、状态或数据结构写清楚。

## Status Decision

- `待验收`：代码完成，但缺正式验证、联调或人工检查。
- `已完成`：验收动作已通过，下游可以继续。
- `阻塞`：关键验证做不了，或缺前置条件。

## Hard Gate

任务结束必须更新开发 plan 进度。未同步 workflow 三处状态，不得声称完成。

## Never Do

- 不要未验证就标 `已完成`。
- 不要只改状态，不说明验证结果。
- 不要把“等别人看看”当成自己完成。

