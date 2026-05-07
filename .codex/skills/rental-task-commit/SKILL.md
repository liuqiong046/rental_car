---
name: rental-task-commit
description: Use when preparing commits for rental_car after completing a workflow task or a coherent verified substep of one task
---

# rental_car Task Commit

## Overview

提交信息必须体现任务编号、类型和业务变化。当前目录若不是 Git 仓库，只输出推荐提交信息，不伪造提交。

## Commit Format

```text
WF-P0-10 feat(order): 打通支付与订单创建闭环
```

规则：

- 任务编号必须在最前面。
- 后面使用 `<type>(scope): <summary>`。
- `type` 仅用：`feat`、`fix`、`refactor`、`docs`、`test`、`chore`。
- `summary` 使用中文、动词开头、长度不超过 50 字、不加句号。

## Boundary

- 一次提交只对应一个 `WF-*` 任务，或该任务的一个可验证子步。
- 多任务混提默认禁止。
- 集成任务 `WF-P0-20`、`WF-P1-25` 可以覆盖多场景，但提交仍只写该任务编号。

## Non-Git Case

如果当前目录还不是 Git 仓库：

- 不要声称已提交。
- 给出推荐 commit message，等仓库初始化后再提交。

