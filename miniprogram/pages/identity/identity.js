const { fetchIdentity, prepareIdentityAsset, submitIdentity } = require("../../utils/identity");
const { requireLogin } = require("../../utils/auth");
const { getNavMetrics } = require("../../utils/nav");

const IMAGE_FIELDS = {
  id_card_front_url: "身份证人像面",
  id_card_back_url: "身份证国徽面",
  driver_license_url: "驾驶证"
};

Page({
  data: {
    nav: getNavMetrics(),
    identity: null,
    imageLabels: IMAGE_FIELDS,
    imagePreviews: {},
    form: {
      real_name: "",
      id_no: "",
      driver_license_no: "",
      id_card_front_url: "",
      id_card_back_url: "",
      driver_license_url: ""
    }
  },
  onShow() {
    if (!requireLogin("/pages/identity/identity")) return;
    fetchIdentity()
      .then((identity) => this.setData({ identity }))
      .catch(() => this.setData({ identity: null }));
  },
  onInput(event) {
    const key = event.currentTarget.dataset.key;
    this.setData({ [`form.${key}`]: event.detail.value });
  },
  chooseImage(event) {
    const key = event.currentTarget.dataset.key;
    wx.chooseImage({
      count: 1,
      sizeType: ["compressed"],
      sourceType: ["album", "camera"],
      success: (result) => {
        const path = result.tempFilePaths[0];
        const fileName = path.split("/").pop() || `${key}.jpg`;
        prepareIdentityAsset({ file_name: fileName, content_type: "image/jpeg" })
          .then((asset) => {
            this.setData({
              [`form.${key}`]: asset.asset_url,
              [`imagePreviews.${key}`]: path
            });
          })
          .catch((error) => wx.showModal({ title: "图片处理失败", content: error.message, showCancel: false }));
      }
    });
  },
  previewImage(event) {
    const key = event.currentTarget.dataset.key;
    const previewPath = this.data.imagePreviews[key] || this.data.form[key];
    if (!previewPath) return;
    wx.previewImage({ current: previewPath, urls: [previewPath] });
  },
  goBack() {
    wx.navigateBack();
  },
  submit() {
    const missingImage = Object.keys(IMAGE_FIELDS).find((key) => !this.data.form[key]);
    if (missingImage) {
      wx.showToast({ title: `请上传${IMAGE_FIELDS[missingImage]}`, icon: "none" });
      return;
    }
    submitIdentity(this.data.form)
      .then((identity) => {
        this.setData({ identity });
        wx.showToast({ title: "已提交审核", icon: "none" });
      })
      .catch((error) => wx.showModal({ title: "提交失败", content: error.message, showCancel: false }));
  }
});
