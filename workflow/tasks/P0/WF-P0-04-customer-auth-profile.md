# WF-P0-04 C 端登录、用户资料与黑名单拦截

| 字段 | 值 |
| --- | --- |
| ID | WF-P0-04 |
| 阶段 | P0 / 阶段一 |
| Owner | 刘琼 |
| 优先级 | P0 |
| 预计体量 | 1-2 天 |

> 说明：owner 负责该任务全栈闭环，不再拆前后端子任务。

## 目标

打通 C 端微信手机号登录、用户资料维护、渠道来源记录和黑名单拦截。

## 业务闭环

用户可浏览公开页面，执行认证、下单、订单和我的等敏感动作前必须登录；黑名单用户被拦截。

## 输入文档

- PRD §5.1、§5.12、§12.1、§13
- 当前 C 端 `pages/login`、`pages/profile`

## 范围内改动

- C 端登录、资料展示与退出。
- 后端 auth/users 接口。
- 渠道、门店或推广参数记录。
- 黑名单状态读取和进入小程序拦截提示。

## 非目标

- 不实现身份认证材料提交。
- 不实现渠道工作台、渠道收益或渠道价格助手。

## 前置依赖

- `WF-P0-01`
- `WF-P0-02`

## 交付物

- 登录态持久化与请求头注入。
- 用户资料读取和更新。
- 黑名单拦截提示。

## 验收动作

1. 未登录用户可浏览首页和车辆详情。
2. 未登录用户进入订单或我的敏感动作会进入登录。
3. 黑名单用户无法继续使用小程序。

## 完成定义

- 后续身份认证、车辆浏览和订单任务可稳定读取当前用户。

## H5/PRD 复核标注

- 已补前端：C 端登录页已接验证码发送流程；新增个人信息编辑页和修改手机号入口；`我的` 页面展示认证状态与渠道来源，并隐藏首期不应展示的渠道工作台/托管入口；新增黑名单拦截页。
- 已补后端：已新增验证码发送、验证码校验、手机号变更接口；用户资料更新、渠道来源记录和黑名单敏感入口拦截已覆盖。
- 剩余非目标：真实微信 openid/unionid 换取、短信供应商、用户资料持久化和黑名单数据持久化仍待后续基础设施接入。
- H5 对照：`/Users/liuqiong/Downloads/山海放心租c端-h5/lanhu_denglumimadenglu`、`lanhu_wode`、`lanhu_gerenxinxi`、`lanhu_shenfenyanzhengweirenzheng` 展示了本任务和下游身份认证任务需要衔接的页面状态。

## 接口契约补充

- `POST /api/v1/auth/sms-code`
- `PATCH /api/v1/users/me/phone`

## 下游 handoff

- `WF-P0-07`
- `WF-P0-08`
- `WF-P0-09`

## 当前状态

- 状态：待验收
- 说明：登录页已按最新 UI 稿返修完成，并通过定向静态检查与微信开发者工具 CLI preview；仍待人工核对默认态、已填写态和未勾选协议弹层。

## 验证记录

- 2026-05-06：已读取 `workflow/index.md`、`workflow/tasks/P0/WF-P0-01` 至 `WF-P0-20` 全部任务包、`workflow/owners/unassigned.md`、`doc/requirements/shanhai-rental-mini-programs-requirements.md`、`doc/接口规范-V1.md`、`doc/技术栈方案-V1.md`。
- 2026-05-06：已读取 C 端原型目录 `小程序页面/C 端小程序/pages/lanhu_denglumimadenglu`、`lanhu_wode`、`lanhu_gerenxinxi`、`lanhu_shenfenyanzhengweirenzheng` 的 `component.wxml|wxss|js|json`；黑名单拦截页按任务包与 PRD 落地。
- 2026-05-06：`node --check miniprogram/app.js miniprogram/utils/auth.js miniprogram/utils/request.js miniprogram/pages/login/login.js miniprogram/pages/profile/profile.js miniprogram/pages/profile-edit/profile-edit.js miniprogram/pages/blacklist/blacklist.js miniprogram/pages/orders/orders.js miniprogram/pages/order-confirm/order-confirm.js miniprogram/pages/identity/identity.js` 通过。
- 2026-05-06：`rg -n "19898766543|460200199001011234|460200199001019999|3301234123412345677" miniprogram/pages miniprogram/utils miniprogram/app.js` 未命中，确认本次修改未继续暴露完整手机号、身份证或驾驶证示例值。
- 2026-05-06：`/Applications/wechatwebdevtools.app/Contents/MacOS/cli preview --project /Users/liuqiong/workspace/rental_car/miniprogram --qr-format image --qr-output /tmp/rental-customer-preview/qr.png --info-output /tmp/rental-customer-preview/info.json --disable-gpu` 通过，成功生成 C 端小程序预览二维码，总包大小 1.1 MB / 1101542 bytes。
- 2026-05-06：已读取最新登录页 UI 稿 `/Users/liuqiong/Downloads/注册-1.png`、`/Users/liuqiong/Downloads/注册-2.png`、`/Users/liuqiong/Downloads/注册-3.png`，并继续对照原型目录 `小程序页面/C 端小程序/pages/lanhu_denglumimadenglu` 返修 `pages/login`。
- 2026-05-06：`node --check miniprogram/pages/login/login.js` 通过。
- 2026-05-06：`node -e "JSON.parse(require('fs').readFileSync('miniprogram/pages/login/login.json', 'utf8')); console.log('login.json ok')"` 通过。
- 2026-05-06：`rg -n "1[0-9]{10}|[0-9]{15,18}" miniprogram/pages/login miniprogram/assets/login` 未命中，确认登录页与新增资源未写入完整手机号、身份证或驾驶证号码。
- 2026-05-06：`/Applications/wechatwebdevtools.app/Contents/MacOS/cli preview --project /Users/liuqiong/workspace/rental_car/miniprogram --qr-format image --qr-output /tmp/rental-customer-preview/qr.png --info-output /tmp/rental-customer-preview/info.json --disable-gpu` 通过，成功生成 C 端小程序预览二维码，总包大小 1.1 MB / 1111590 bytes。
