const ASSET_BASE = "../../assets/lanhu_shouye";

Page({
  data: {
    // TODO(WF-P0-13): 接入管理端登录、角色入口、待办聚合、客户订单和批发订单移动处理。
    // TODO(WF-P0-14): 接入工单详情、排班、车况录入、现场费用和无网络照片提交拦截。
    // 当前数据只用于 WF-P0-01 三端骨架空跑，示例车牌和地址均保持脱敏/摘要展示。
    onlyMine: true,
    operator: {
      brand: "山海奢驾",
      center: "三亚运营中心"
    },
    entries: [
      {
        id: "today",
        title: "今日待办",
        image: `${ASSET_BASE}/entry-today.png`,
        theme: "is-today"
      },
      {
        id: "dispatch",
        title: "同行调车",
        image: `${ASSET_BASE}/entry-dispatch.png`,
        theme: "is-dispatch"
      },
      {
        id: "garage",
        title: "我家车库",
        image: `${ASSET_BASE}/entry-garage.png`,
        theme: "is-garage"
      }
    ],
    todoOrders: [
      {
        id: "todo-order-001",
        brand: "小米汽车",
        model: "SU7",
        plateMask: "湘 A **** 29",
        status: "订单待确认",
        pickupAt: "07/18 09:00",
        pickupAddress: "三亚运营中心",
        returnAt: "07/20 19:00",
        returnAddress: "三亚运营中心",
        vehicleIcon: `${ASSET_BASE}/vehicle.png`,
        route: true,
        action: "查看订单"
      },
      {
        id: "todo-order-002",
        brand: "北京现代",
        model: "",
        plateMask: "琼 A **** 51",
        status: "订单待售后",
        orderNo: "DEMO-ORDER-002",
        vehicleIcon: `${ASSET_BASE}/vehicle-small.png`,
        route: false,
        action: "查看工单"
      }
    ],
    agendaGroups: [
      {
        date: "07-18",
        month: "07",
        day: "18",
        items: [
          {
            id: "task-001",
            time: "09:05",
            stateTheme: "state-active",
            stateLabel: "进\n行\n中",
            title: "司机 A",
            type: "取借车",
            badgeTheme: "badge-green",
            place: "三亚湾交付点",
            icon: `${ASSET_BASE}/location.png`
          },
          {
            id: "task-002",
            time: "09:10",
            stateLabel: "待\n开\n始",
            stateTheme: "state-waiting",
            title: "司机 B",
            type: "送车",
            badgeTheme: "badge-green",
            place: "三亚海棠湾服务点",
            icon: `${ASSET_BASE}/location.png`
          },
          {
            id: "task-003",
            time: "09:40",
            stateLabel: "待\n排\n单",
            stateTheme: "state-queue",
            title: "保养",
            type: "其他",
            badgeTheme: "badge-mint",
            place: "琼 A **** 51",
            icon: `${ASSET_BASE}/vehicle-small.png`
          }
        ]
      }
    ],
    tabs: [
      { id: "home", label: "首页", icon: `${ASSET_BASE}/tab-home.png`, active: true },
      { id: "console", label: "控制台", icon: `${ASSET_BASE}/tab-console.png`, active: false },
      { id: "profile", label: "我的", icon: `${ASSET_BASE}/tab-profile.png`, active: false }
    ]
  },

  toggleMine() {
    this.setData({ onlyMine: !this.data.onlyMine });
  },

  openFeature(event) {
    const featureName = event.currentTarget.dataset.name || "功能";
    wx.showToast({
      title: `${featureName}建设中`,
      icon: "none"
    });
  },

  openTodo(event) {
    const actionName = event.currentTarget.dataset.name || "待办";
    wx.showToast({
      title: `${actionName}建设中`,
      icon: "none"
    });
  },

  switchTab(event) {
    const tabName = event.currentTarget.dataset.name || "页面";
    if (tabName === "首页") {
      return;
    }
    wx.showToast({
      title: `${tabName}待后续任务接入`,
      icon: "none"
    });
  }
});
