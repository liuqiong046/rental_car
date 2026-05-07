const { loginByPhone, sendSmsCode } = require("../../utils/auth");
const { getNavMetrics } = require("../../utils/nav");

const COUNTDOWN_SECONDS = 60;

Page({
  data: {
    nav: getNavMetrics(),
    agree: false,
    phone: "",
    verificationCode: "",
    codeSending: false,
    loading: false,
    codeCountdown: 0,
    canSubmit: false,
    redirectUrl: "",
    showAgreementModal: false
  },
  onLoad(options) {
    const redirectUrl = options && options.redirect ? decodeURIComponent(options.redirect) : "";
    this.setData({ redirectUrl });
    this.syncSubmitState();
  },
  onUnload() {
    this.clearCountdown();
  },
  goBack() {
    wx.navigateBack({
      fail: () => {
        wx.redirectTo({ url: "/pages/home/home" });
      }
    });
  },
  toggleAgree() {
    this.setData({
      agree: !this.data.agree,
      showAgreementModal: false
    });
    this.syncSubmitState();
  },
  onPhoneInput(event) {
    this.setData({ phone: String(event.detail.value || "").slice(0, 11) });
    this.syncSubmitState();
  },
  onCodeInput(event) {
    this.setData({ verificationCode: String(event.detail.value || "").slice(0, 6) });
    this.syncSubmitState();
  },
  clearPhone() {
    this.setData({ phone: "" });
    this.syncSubmitState();
  },
  requestCode() {
    if (this.data.codeSending || this.data.codeCountdown > 0) return;
    if (!this.isPhoneValid()) {
      wx.showToast({ title: "请输入正确手机号", icon: "none" });
      return;
    }

    this.setData({ codeSending: true });
    sendSmsCode(this.data.phone)
      .then(() => {
        wx.showToast({ title: "验证码已发送", icon: "success" });
        this.startCountdown();
      })
      .catch((error) => {
        wx.showModal({ title: "发送失败", content: error.message, showCancel: false });
      })
      .finally(() => {
        this.setData({ codeSending: false });
      });
  },
  submit() {
    if (!this.data.canSubmit || this.data.loading) return;
    if (!this.data.agree) {
      this.setData({ showAgreementModal: true });
      return;
    }

    this.setData({ loading: true });
    loginByPhone(this.data.phone, this.data.verificationCode)
      .then((profile) => {
        if (profile.blacklisted) {
          wx.reLaunch({ url: "/pages/blacklist/blacklist" });
          return;
        }
        const targetUrl = this.data.redirectUrl || "/pages/profile/profile";
        wx.redirectTo({ url: targetUrl });
      })
      .catch((error) => {
        wx.showModal({ title: "登录失败", content: error.message, showCancel: false });
      })
      .finally(() => {
        this.setData({ loading: false });
      });
  },
  hideAgreementModal() {
    this.setData({ showAgreementModal: false });
  },
  isPhoneValid() {
    return /^1\d{10}$/.test(this.data.phone);
  },
  syncSubmitState() {
    const canSubmit = this.isPhoneValid() && this.data.verificationCode.length >= 4;
    this.setData({ canSubmit });
  },
  startCountdown() {
    this.clearCountdown();
    this.setData({ codeCountdown: COUNTDOWN_SECONDS });
    this.countdownTimer = setInterval(() => {
      const nextValue = this.data.codeCountdown - 1;
      if (nextValue <= 0) {
        this.clearCountdown();
        this.setData({ codeCountdown: 0 });
        return;
      }
      this.setData({ codeCountdown: nextValue });
    }, 1000);
  },
  clearCountdown() {
    if (!this.countdownTimer) return;
    clearInterval(this.countdownTimer);
    this.countdownTimer = null;
  }
});
