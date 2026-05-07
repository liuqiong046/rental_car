# WF-P0-01 基建骨架与三端空跑

| 字段 | 值 |
| --- | --- |
| ID | WF-P0-01 |
| 阶段 | P0 / 阶段一 |
| Owner | 待定 |
| 优先级 | P0 |
| 预计体量 | 1-2 天 |

> 说明：owner 负责该任务全栈闭环，不再拆前后端子任务。

## 目标

建立 `backend/`、`admin-web/`、`manager-miniprogram/`、`deploy/` 的最小骨架，并把现有 C 端小程序整理到 `miniprogram/`。

## 业务闭环

从当前只有 C 端页面和需求文档的状态出发，按 onePet 风格补齐工程目录、三端入口、启动说明和部署占位，让后续任务都能基于统一目录推进。

## 输入文档

- `doc/requirements/shanhai-rental-mini-programs-requirements.md`：§1、§2、§12
- `doc/技术栈方案-V1.md`：§1、§5、§7

## 范围内改动

- 初始化后端、PC 后台、管理端小程序和部署目录。
- 将当前 C 端微信小程序文件整理到 `miniprogram/`。
- 增加根级 README 或分目录 README 的最小启动说明。

## 非目标

- 不实现业务接口、登录、订单、支付、权限或数据库模型。
- 不做 C 端 TypeScript 迁移或业务重构。

## 前置依赖

- 无

## 交付物

- `backend/`、`admin-web/`、`manager-miniprogram/`、`deploy/` 骨架。
- `miniprogram/` 下的 C 端小程序目录。
- 三端最小启动说明。
- 后端健康检查占位或等价启动反馈。

## 验收动作

1. C 端可用微信开发者工具打开 `miniprogram/`。
2. 后端、后台、管理端小程序目录存在并有最小入口说明。
3. `deploy/` 存在可继续扩展的 compose/nginx 占位。

## 完成定义

- 后续 `WF-P0-02`、`WF-P0-03`、`WF-P0-04` 可在该骨架上继续开发。
- 所有新增入口都有说明，避免后续 owner 二次猜测。

## H5/PRD 复核标注

- 前端待补：管理端小程序空跑首页已按 `小程序页面/管理端小程序页面/pages/lanhu_shouye` 对齐运营中心信息、今日待办/同行调车/我家车库入口、待办工单卡片、时间线和底部入口；控制台、真实今日待办、调车、批发订单、工单详情、车况登记等页面不属于本任务交付完成范围，后续应在 `WF-P0-13`、`WF-P0-14` 落地。
- 后端待补：本任务只要求骨架和健康检查占位；真实业务 API、数据库和任务队列按 `WF-P0-02` 及后续业务任务推进。

## 下游 handoff

- `WF-P0-02`
- `WF-P0-03`
- `WF-P0-04`

## 当前状态

- 状态：已完成
- 说明：2026-05-06 已根据微信开发者工具截图继续修正管理端首页筛选区和时间线样式，范围仍限 `WF-P0-01` 骨架入口；自动语法、敏感字段定向检查和微信开发者工具 CLI preview 均已通过。

## 验证记录

- 2026-05-06：已读取 `小程序页面/管理端小程序页面/pages/lanhu_shouye/component.wxml|wxss|js|json`；辅助抽查 `lanhu_shouyeyoubanner`、`lanhu_kongzhitai`、`lanhu_jinridaiban1`、`lanhu_jinridaibanzanwudaibanshixiang` 确认后续页面归属。
- 2026-05-06：`node --check manager-miniprogram/pages/home/home.js && node --check manager-miniprogram/app.js` 通过。
- 2026-05-06：`rg` 定向检查管理端首页未展示完整手机号、身份证、驾驶证、完整车牌号、详细地址或密钥；仅保留脱敏车牌和地址摘要。
- 2026-05-06：首次尝试运行 `/Applications/wechatwebdevtools.app/Contents/MacOS/cli preview --project /Users/liuqiong/workspace/rental_car/manager-miniprogram` 时，微信开发者工具提示 IDE Service Port 未开启且需要交互确认；用户开启后重新运行成功。
- 2026-05-06：`/Applications/wechatwebdevtools.app/Contents/MacOS/cli preview --project /Users/liuqiong/workspace/rental_car/manager-miniprogram --qr-format image --qr-output /tmp/rental-manager-preview/qr.png --info-output /tmp/rental-manager-preview/info.json --disable-gpu` 通过，输出总包大小 13.0 KB / 13350 bytes，并生成预览二维码。
- 2026-05-06：再次按 `lanhu_shouye` 返修首页视觉，使用真实原型图片资产但未复制假状态栏、假胶囊和 Home indicator；`node --check`、JSON 解析、敏感字段/假状态栏扫描和微信开发者工具 CLI preview 通过，输出总包大小 123.4 KB / 126371 bytes。
- 2026-05-06：根据截图修正顶部样式，移除误用的整张头部截图背景，改为 CSS 渐变头部并修复车辆标题换行；`node --check`、JSON 解析、敏感字段/假状态栏扫描和微信开发者工具 CLI preview 通过，输出总包大小 54.4 KB / 55718 bytes。
- 2026-05-06：根据截图继续修正样式，将会受微信原生 `button` 默认布局影响的 `operator-switch`、入口卡、筛选、待办卡和底部 tab 改成 `view` 容器，修复右上角异常白胶囊与尺寸漂移；`node --check`、JSON 解析和微信开发者工具 CLI preview 通过，输出总包大小 54.4 KB / 55704 bytes。
- 2026-05-06：根据截图继续核对 UI 稿，修正“只看我的任务”筛选区与时间线为原稿的紧凑横卡结构，补齐状态竖条、标题行和地点浅灰底条；`node --check`、JSON 解析和微信开发者工具 CLI preview 通过，输出总包大小 55.3 KB / 56658 bytes。
