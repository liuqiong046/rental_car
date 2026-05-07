const { getStoredProfile, requireLogin, setLocalAvatar, updateProfile } = require("../../utils/auth");
const { getNavMetrics } = require("../../utils/nav");

Page({
  data: {
    nav: getNavMetrics(),
    profile: getStoredProfile() || {},
    nickname: "",
    avatarUrl: "",
    savingProfile: false,
  },
  onShow() {
    if (!requireLogin("/pages/profile-edit/profile-edit")) return;
    const profile = getStoredProfile() || {};
    this.setData({
      profile,
      nickname: profile.nickname || "",
      avatarUrl: profile.avatar_url || ""
    });
  },
  goBack() {
    wx.navigateBack({
      fail: () => {
        wx.redirectTo({ url: "/pages/profile/profile" });
      }
    });
  },
  onNicknameInput(event) {
    this.setData({ nickname: String(event.detail.value || "").slice(0, 24) });
  },
  chooseAvatar() {
    wx.chooseImage({
      count: 1,
      sizeType: ["compressed"],
      sourceType: ["album", "camera"],
      success: (result) => {
        const path = result.tempFilePaths[0];
        if (!path) return;
        this.setData({ avatarUrl: path });
      }
    });
  },
  openPhoneEdit() {
    wx.navigateTo({ url: "/pages/profile-phone/profile-phone" });
  },
  saveProfile() {
    const nickname = String(this.data.nickname || "").trim();
    if (!nickname) {
      wx.showToast({ title: "请输入昵称", icon: "none" });
      return;
    }

    this.setData({ savingProfile: true });
    updateProfile({
      nickname
    })
      .then((profile) => {
        const avatarUrl = this.data.avatarUrl || profile.avatar_url || "";
        const nextProfile = setLocalAvatar(profile.user_id, avatarUrl) || profile;
        this.setData({
          profile: nextProfile,
          nickname: nextProfile.nickname || nickname,
          avatarUrl: nextProfile.avatar_url || avatarUrl
        });
        wx.showToast({ title: "资料已保存", icon: "success" });
      })
      .catch((error) => {
        wx.showModal({ title: "保存失败", content: error.message, showCancel: false });
      })
      .finally(() => {
        this.setData({ savingProfile: false });
      });
  }
});
