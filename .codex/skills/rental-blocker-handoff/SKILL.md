---
name: rental-blocker-handoff
description: Use when rental_car work is blocked, scope drifts beyond the current workflow task, or another owner needs a precise handoff
---

# rental_car Blocker Handoff

## Overview

阻塞不可隐藏，交接不可模糊。发现做不下去或超出任务边界时，要写清楚卡在哪里、需要什么、谁接手。

## Trigger Conditions

- 前置依赖没有完成。
- 当前任务需要修改共享接口、状态机、公共规则或 workflow 结构。
- 工作量超出 1-2 天任务粒度。
- 需要另一个 owner 补上游或接下游。

## Blocker Record

阻塞时必须写清：

1. 卡住的具体点。
2. 已经尝试过什么。
3. 缺少什么条件才能继续。
4. 建议谁处理、处理后解锁哪个任务。

推荐格式：

```md
- 状态：阻塞
- 说明：缺少 WF-P0-06 输出的 vehicle_availability 字段，当前接口无法支撑确认订单锁车；待车辆可用性接口补齐后解锁 WF-P0-09。
```

## Handoff Rules

- 交接下游时写清接口、页面、状态或数据结构。
- 影响下游的字段和规则必须显式列出。
- 需要新增任务时，不要硬塞回当前任务。

