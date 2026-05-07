# 山海放心租

本仓库参考 `onePet` 的单仓多模块结构整理，首期包含 C 端小程序、管理端小程序、PC 管理后台、后端服务、部署配置、需求/规范文档和 workflow 任务体系。

## 目录结构

```text
rental_car/
├─ miniprogram/              # C 端微信小程序，已迁入现有页面和素材
├─ manager-miniprogram/      # 山海管家管理端小程序骨架
├─ admin-web/                # PC 管理后台骨架
├─ backend/                  # FastAPI 后端骨架
├─ deploy/                   # 本地与部署配置占位
├─ doc/                      # 技术方案、接口规范、需求文档
├─ workflow/                 # 开发任务拆分与进度真相源
└─ .codex/skills/            # 项目级开发守则 skills
```

## 当前 C 端小程序

从 Figma 文件 `l655u6JYbD0lcEdLuMJPWF` 转出的微信原生小程序工程，已整理到 `miniprogram/`。

已实现页面：

- 首页：`pages/home/home`
- 品牌选择：`pages/brand/brand`
- 选择车辆：`pages/cars/cars`
- 车辆详情：`pages/detail/detail`
- 确认订单：`pages/order-confirm/order-confirm`
- 全部订单：`pages/orders/orders`
- 订单详情：`pages/order-detail/order-detail`
- 我的：`pages/profile/profile`
- 登录注册：`pages/login/login`

设计映射：

- 主色：`#FCD41D`
- 主文本：`#2B2627`
- 页面背景：`#F8F8F7`
- 主要卡片宽度：`686rpx`，对应 Figma 343px 内容区
- 关键车辆、横幅、详情图素材位于 `miniprogram/assets/`

## 文档入口

- 需求文档：`doc/requirements/shanhai-rental-mini-programs-requirements.md`
- 技术栈方案：`doc/技术栈方案-V1.md`
- 接口规范：`doc/接口规范-V1.md`
- 开发 workflow：`workflow/index.md`

## 运行入口

- C 端小程序：用微信开发者工具打开 `/Users/liuqiong/workspace/rental_car/miniprogram`
- 管理端小程序：见 `manager-miniprogram/README.md`
- PC 管理后台：见 `admin-web/README.md`
- 后端服务：见 `backend/README.md`
- 部署配置：见 `deploy/README.md`
