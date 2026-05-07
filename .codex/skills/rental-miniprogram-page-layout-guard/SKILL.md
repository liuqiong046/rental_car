---
name: rental-miniprogram-page-layout-guard
description: Use when modifying or implementing rental_car customer or manager miniprogram pages, UI-converted page code, WXML, WXSS, navigation, status bars, capsule buttons, safe areas, or layout behavior
---

# rental_car Miniprogram Page Layout Guard

## Overview

小程序页面必须以微信真实运行环境为准。当前 C 端已有 Figma 转换页面，后续修改要保持视觉一致和布局稳定。

## Requirement-First Rules

开发时以需求文档和当前任务包为主，UI 转换原型代码只作为辅助参考。

- 先读取当前任务对应的 `workflow/tasks/P0|P1|P2/WF-*.md`，重点看 `范围内改动`、`交付物` 和 `验收动作`。
- 需求基线优先参考 `doc/requirements/shanhai-rental-mini-programs-requirements.md`。
- `workflow/index.md`、任务包和需求文档定义了做什么；UI 转换原型代码主要辅助确认页面结构、布局、视觉层级和交互摆放。
- 不要因为原型里出现了某个按钮、文案、状态或流程，就覆盖任务包和需求文档已经定义的业务逻辑。
- 若检查到需求文档、任务包和 UI 转换原型代码之间存在业务逻辑不一致，必须先询问用户确认，不能自行按原型或按猜测实现。

## Prototype Source Gate

实现 C 端或管理端小程序页面前，必须先读取对应 UI 转换原型代码，不能只凭记忆或现有页面猜测。

- C 端原型目录：`/Users/liuqiong/workspace/rental_car/小程序页面/C 端小程序/pages/<对应原型目录>/component.wxml|wxss|js|json`
- 管理端原型目录：`/Users/liuqiong/workspace/rental_car/小程序页面/管理端小程序页面/pages/<对应原型目录>/component.wxml|wxss|js|json`
- 页面匹配优先使用 `lanhu_*` 目录名；不确定时用页面标题、业务名、路由名和原型目录搜索。
- 若无法唯一匹配原型目录，先询问用户确认，不要自行选择相近页面。

## Implementation Mapping Rules

- C 端实际实现目录为 `miniprogram/pages/**`。
- 管理端实际实现目录为 `manager-miniprogram/pages/**`。
- 原型代码只作为视觉、层级、间距和文案参考；实现时要转成当前项目可维护的 WXML、WXSS 和 JS 结构。
- 不要直接整页复制 UI 转换代码，尤其不要复制无语义 class、固定屏幕高度和不可维护的绝对堆叠。
- 原型里的假状态栏、假时间、电量、信号和蓝湖胶囊图形不得照搬到真实页面。

## Navigation and Safe Area Rules

- C 端自定义导航优先复用 `miniprogram/utils/nav.js` 的 `getNavMetrics()` 和现有全局导航样式。
- 管理端若继续使用原生导航，不能额外绘制假状态栏。
- 管理端若页面需要自定义头部，按 C 端同类方式计算 `statusBarHeight`、胶囊按钮位置和 `navHeight`。
- 自定义导航必须处理状态栏高度、胶囊避让、标题和返回按钮位置。
- 顶部业务内容不得被胶囊按钮、状态栏或导航标题遮挡。
- 固定底部按钮、工具栏和弹层底部操作区必须避让 `env(safe-area-inset-bottom)`。

## Customer Miniprogram Rules

- 沿用当前主色 `#FCD41D`、背景 `#F8F8F7`、主文本 `#2B2627`。
- 保持 `686rpx` 主要卡片内容宽度风格。
- 不绘制底部黑色 Home Indicator；只做安全区避让。
- 车辆图片、价格、按钮和订单状态不得遮挡或溢出。

## Manager Miniprogram Rules

- 管理端是高频履约工具，优先信息密度、状态清晰和操作效率。
- 工单、待办、订单和费用页面要稳定展示状态、时间、车辆、执行人和下一步动作。
- 无网络时车况照片不得离线提交，必须给出恢复网络后再提交的提示。

## Verification

- 交付页面实现时说明读取了哪个原型目录。
- 页面改动后用微信开发者工具或等价预览检查关键页面。
- 检查窄屏、长文本、金额、车牌脱敏、状态标签、顶部导航、胶囊避让和固定底部按钮。

## Never Do

- 不要只按 H5 预览判断小程序可用。
- 不要跳过原型目录读取直接实现页面。
- 不要用前端隐藏按钮代替权限控制。
- C端小程序不要展示完整车牌号、手机号、身份证或驾驶证敏感信息。
