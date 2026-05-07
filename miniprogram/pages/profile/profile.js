const { redirect, getNavMetrics } = require("../../utils/nav");
const {
  fetchProfile,
  getStoredProfile,
  logout: logoutCustomer,
  requireLogin
} = require("../../utils/auth");

const MENU_ITEMS = [
  { id: "identity", title: "身份认证", iconPath: "../../assets/profile/id-card-line.svg" },
  { id: "profile", title: "个人信息", iconPath: "../../assets/profile/user-6-line.svg" },
  { id: "channel", title: "渠道工作台", iconPath: "../../assets/profile/apps-2-ai-line.svg" },
  { id: "contact", title: "联系客服", iconPath: "../../assets/profile/customer-service-2-line.svg" }
];

// TODO(WF-P0-19): 消息中心待消息模块落地后接入“我的”页。
// TODO(WF-P2-B01): 渠道工作台首期隐藏，二期按渠道身份开放。

const CERT_STATUS_TEXT = {
  approved: "已认证",
  pending: "审核中",
  rejected: "未通过"
};

Page({
  data: {
    nav: getNavMetrics(),
    profile: getStoredProfile() || {},
    certificationText: "未认证",
    channelText: "自然访问",
    channelLabel: "渠道来源：自然访问",
    menuItems: MENU_ITEMS
  },
  onShow() {
    if (!requireLogin("/pages/profile/profile")) return;
    this.applyProfile(getStoredProfile() || {});
    fetchProfile()
      .then((profile) => {
        this.applyProfile(profile);
      })
      .catch((error) => {
        if (error && error.code === "BLACKLISTED") return;
        wx.showModal({ title: "无法进入我的", content: error.message, showCancel: false });
        wx.redirectTo({ url: "/pages/login/login?redirect=%2Fpages%2Fprofile%2Fprofile" });
      });
  },
  redirect,
  applyProfile(profile) {
    const nextProfile = profile || {};
    const certificationText = CERT_STATUS_TEXT[nextProfile.certification_status] || "未认证";
    const channelText =
      (nextProfile.channel_source && nextProfile.channel_source.channel_code) || "自然访问";
    const channelLabel = `渠道来源：${channelText}`;
    if (!nextProfile.avatarText) nextProfile.avatarText = "山";
    this.setData({ profile: nextProfile, certificationText, channelText, channelLabel });
  },
  openQuickEdit() {
    wx.navigateTo({ url: "/pages/profile-edit/profile-edit" });
  },
  openMenu(event) {
    const { id } = event.currentTarget.dataset;
    if (id === "identity") {
      wx.navigateTo({ url: "/pages/identity/identity" });
      return;
    }
    if (id === "profile") {
      wx.navigateTo({ url: "/pages/profile-edit/profile-edit" });
      return;
    }
    if (id === "contact") {
      wx.showModal({
        title: "联系客服",
        content: "请通过首页客服电话或运营通知联系人工客服。",
        showCancel: false
      });
      return;
    }
    if (id === "channel") {
      wx.showToast({ title: "渠道工作台首期隐藏", icon: "none" });
    }
  },
  logout() {
    logoutCustomer().then(() => {
      wx.reLaunch({ url: "/pages/home/home" });
    });
  }
});
