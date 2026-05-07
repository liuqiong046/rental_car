const { getStoredProfile, logout } = require("../../utils/auth");
const { getNavMetrics } = require("../../utils/nav");

Page({
  data: {
    nav: getNavMetrics(),
    profile: getStoredProfile() || {}
  },
  onShow() {
    this.setData({ profile: getStoredProfile() || {} });
  },
  contactService() {
    wx.showModal({
      title: "联系客服",
      content: "请通过首页客服电话或运营通知联系人工客服核实处理结果。",
      showCancel: false
    });
  },
  switchAccount() {
    logout().then(() => {
      wx.reLaunch({ url: "/pages/login/login" });
    });
  }
});
