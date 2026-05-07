# WF-P0-09 确认订单、费用预估与未支付锁车

| 字段 | 值 |
| --- | --- |
| ID | WF-P0-09 |
| 阶段 | P0 / 阶段一 |
| Owner | 待定 |
| 优先级 | P0 |
| 预计体量 | 1-2 天 |

> 说明：owner 负责该任务全栈闭环，不再拆前后端子任务。

## 目标

实现确认订单、费用预估、取还车方式、地址、备注、价格快照和未支付锁车。

## 业务闭环

认证通过用户选择车辆和时间后，可提交待支付订单并短时锁车；超时未支付自动关闭并释放车辆。

## 输入文档

- PRD §4.1、§5.7、§5.8、§9.5、§13
- `doc/接口规范-V1.md`：幂等规则

## 范围内改动

- C 端确认订单页面接入接口。
- 后端费用预估和订单草稿/待支付创建。
- 未支付锁车到期时间和释放逻辑。

## 非目标

- 不发起微信支付。
- 不进入管理端待接单或生成批发订单。

## 前置依赖

- `WF-P0-05`
- `WF-P0-06`
- `WF-P0-07`
- `WF-P0-08`

## 交付物

- 费用明细：租金、上门送收服务费、优惠、应支付、押金提示。
- 待支付订单和锁车记录。
- 超时关闭任务。

## 验收动作

1. 未认证用户不能提交待支付订单。
2. 未支付订单在锁车时长内锁定车辆。
3. 超时后订单关闭且车辆释放。

## 完成定义

- 后续支付任务可基于待支付订单发起微信支付。

## 下游 handoff

- `WF-P0-10`

## 当前状态

- 状态：待验收
- 说明：已完成确认订单费用预估、待支付锁车、订单详情继续支付、待支付订单取消和锁车释放；待微信开发者工具人工预览确认订单、待支付详情和固定底部按钮。

## H5/PRD 复核标注

- 前端未完成：对照 C 端 H5 `lanhu_querendingdancduanyonghu`、`lanhu_chuangjiandingdanchenggong`、`lanhu_dingdanxiangqingdaizhifuzuchefeiyong`、`lanhu_feiyongmingxi*`、`lanhu_quxiaodingdan`，已补上门服务半径/超区费提示、待支付订单取消、费用明细展开和订单详情继续支付；仍缺地图地址选择、创建订单成功页、独立费用明细页、待支付详情全状态和微信开发者工具人工预览。
- 后端未完成：订单服务仍缺地址经纬度、服务半径计费、支付后状态推进、取消订单、订单状态流转审计和真实超时任务调度。
- 归属说明：支付相关归属 `WF-P0-10`；取消、退款前置和全状态订单中心归属 `WF-P0-11`/`WF-P0-18`。

## 验证记录

- `python3 -m pytest tests/apps/orders/test_order_confirm_api.py -q`（backend）：6 passed，1 个 `python_multipart` 依赖弃用 warning。
- `python3 -m pytest tests -q`（backend）：55 passed，1 个 `python_multipart` 依赖弃用 warning。
- `find miniprogram -name '*.js' -print0 | xargs -0 -n1 node --check`：通过。
- `python3 -m ruff check app tests`、`python3 -m mypy app`：本机未安装 `ruff` / `mypy`，未执行。
