# 山海放心租 C 端小程序

微信原生小程序工程，承接用户找车、身份认证、下单、支付、订单跟踪、售后确认和我的页面。

## 目录

```text
miniprogram/
├─ app.js
├─ app.json
├─ app.wxss
├─ pages/
├─ utils/
├─ assets/
├─ i18n/
└─ project.config.json
```

## 运行

用微信开发者工具打开 `/Users/liuqiong/workspace/rental_car/miniprogram`。

默认 API 地址在 `app.js` 的 `globalData.apiBaseUrl` 中配置为 `http://127.0.0.1:8000`。

## 登录验证

- 默认手机号：`19898766543`
- 默认验证码：`1234`
- 黑名单测试手机号：`19900000000`

订单、我的、确认订单等敏感入口会先检查本地登录态；首页和车辆详情保持公开浏览。

首页城市切换读取 `GET /api/v1/cities`，只展示后端返回的启用城市；停用城市不会出现在 C 端可选列表。

车辆列表读取 `GET /api/v1/vehicles`，只展示后端判定为可租的车辆：审核通过、已上架、非维保、非锁车、未占用且存在可租价格。

身份认证页位于 `pages/identity/identity`，默认使用 mock 图片 URL 提交；后端只返回身份证号、驾驶证号脱敏字段和授权图片 URL。

## 约束

- 页面视觉沿用当前 Figma 转换稿。
- 修改 WXML/WXSS 时遵守 `.codex/skills/rental-miniprogram-page-layout-guard/SKILL.md`。
- 不展示完整手机号、身份证、驾驶证或完整车牌号。
