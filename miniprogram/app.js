App({
  globalData: {
    brandName: "山海放心租",
    apiBaseUrl: "http://127.0.0.1:8000"
  },
  onLaunch(options) {
    this.captureChannelSource(options && options.query);
    this.redirectBlacklistedUser();
  },
  onShow(options) {
    this.captureChannelSource(options && options.query);
    this.redirectBlacklistedUser();
  },
  captureChannelSource(query) {
    if (!query) return;
    const channelSource = {
      channel_code: query.channel_code || query.channel || null,
      store_code: query.store_code || query.store || null,
      promoter_code: query.promoter_code || query.promoter || null
    };
    if (channelSource.channel_code || channelSource.store_code || channelSource.promoter_code) {
      wx.setStorageSync("channel_source", channelSource);
    }
  },
  redirectBlacklistedUser() {
    const profile = wx.getStorageSync("customer_profile") || null;
    if (!profile || !profile.blacklisted) return;
    const pages = typeof getCurrentPages === "function" ? getCurrentPages() : [];
    const current = pages[pages.length - 1];
    if (current && current.route === "pages/blacklist/blacklist") return;
    wx.reLaunch({ url: "/pages/blacklist/blacklist" });
  }
});
