const DEFAULT_BASE_URL = "http://127.0.0.1:8000";

function getApiBaseUrl() {
  const app = getApp({ allowDefault: true });
  return (app.globalData && app.globalData.apiBaseUrl) || DEFAULT_BASE_URL;
}

function request(options) {
  const token = wx.getStorageSync("customer_token");
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${getApiBaseUrl()}${options.url}`,
      method: options.method || "GET",
      data: options.data || {},
      header: Object.assign(
        { "Content-Type": "application/json" },
        token ? { Authorization: `Bearer ${token}` } : {},
        options.header || {}
      ),
      success(response) {
        if (response.statusCode >= 200 && response.statusCode < 300) {
          resolve(response.data);
          return;
        }
        const detail = response.data && response.data.detail ? response.data.detail : "请求失败";
        if (response.statusCode === 401) wx.removeStorageSync("customer_token");
        if (response.statusCode === 403 && detail.indexOf("限制") >= 0) {
          wx.removeStorageSync("customer_token");
          const profile = wx.getStorageSync("customer_profile") || {};
          wx.setStorageSync("customer_profile", Object.assign({}, profile, { blacklisted: true }));
          wx.reLaunch({ url: "/pages/blacklist/blacklist" });
          const blacklistError = new Error(detail);
          blacklistError.code = "BLACKLISTED";
          reject(blacklistError);
          return;
        }
        reject(new Error(detail));
      },
      fail() {
        reject(new Error("网络不可用，请稍后重试"));
      }
    });
  });
}

module.exports = {
  request
};
