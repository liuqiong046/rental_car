const { getStoredProfile, requireLogin, sendSmsCode, updatePhone } = require("../../utils/auth");
const { getNavMetrics } = require("../../utils/nav");

Page({
  data: {
    nav: getNavMetrics(),
    profile: getStoredProfile() || {},
    phone: "",
    verificationCode: "",
    codeSending: false,
    savingPhone: false
  },
  onShow() {
    if (!requireLogin("/pages/profile-phone/profile-phone")) return;
    this.setData({ profile: getStoredProfile() || {} });
  },
  goBack() {
    wx.navigateBack({
      fail: () => {
        wx.redirectTo({ url: "/pages/profile-edit/profile-edit" });
      }
    });
  },
  onPhoneInput(event) {
    this.setData({ phone: String(event.detail.value || "").slice(0, 11) });
  },
  onCodeInput(event) {
    this.setData({ verificationCode: String(event.detail.value || "").slice(0, 6) });
  },
  requestCode() {
    if (!/^1\d{10}$/.test(this.data.phone)) {
      wx.showToast({ title: "请输入新手机号", icon: "none" });
      return;
    }
    this.setData({ codeSending: true });
    sendSmsCode(this.data.phone)
      .then(() => {
        wx.showToast({ title: "验证码已发送", icon: "success" });
      })
      .catch((error) => {
        wx.showModal({ title: "发送失败", content: error.message, showCancel: false });
      })
      .finally(() => {
        this.setData({ codeSending: false });
      });
  },
  savePhone() {
    if (!/^1\d{10}$/.test(this.data.phone) || this.data.verificationCode.length < 4) {
      wx.showToast({ title: "请填写手机号和验证码", icon: "none" });
      return;
    }
    this.setData({ savingPhone: true });
    updatePhone(this.data.phone, this.data.verificationCode)
      .then((profile) => {
        this.setData({
          profile,
          phone: "",
          verificationCode: ""
        });
        wx.showToast({ title: "手机号已修改", icon: "success" });
        setTimeout(() => {
          wx.navigateBack({
            fail: () => {
              wx.redirectTo({ url: "/pages/profile-edit/profile-edit" });
            }
          });
        }, 500);
      })
      .catch((error) => {
        wx.showModal({ title: "修改失败", content: error.message, showCancel: false });
      })
      .finally(() => {
        this.setData({ savingPhone: false });
      });
  }
});
