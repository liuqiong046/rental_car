const { request } = require("./request");

function getStoredCity() {
  return wx.getStorageSync("current_city") || null;
}

function fetchEnabledCities() {
  return request({ url: "/api/v1/cities" }).then((response) => {
    const cities = response.items || [];
    wx.setStorageSync("enabled_cities", cities);
    if (!getStoredCity() && cities.length > 0) {
      wx.setStorageSync("current_city", cities[0]);
    }
    return cities;
  });
}

function chooseCity() {
  const cities = wx.getStorageSync("enabled_cities") || [];
  if (!cities.length) {
    wx.showToast({ title: "暂无可切换城市", icon: "none" });
    return Promise.resolve(null);
  }
  return new Promise((resolve) => {
    wx.showActionSheet({
      itemList: cities.map((city) => city.city_name),
      success(result) {
        const city = cities[result.tapIndex];
        wx.setStorageSync("current_city", city);
        resolve(city);
      },
      fail() {
        resolve(null);
      }
    });
  });
}

module.exports = {
  chooseCity,
  fetchEnabledCities,
  getStoredCity
};

