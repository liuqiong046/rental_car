const { cars, categories, brands } = require("../../utils/data");
const { chooseCity, fetchEnabledCities, getStoredCity } = require("../../utils/city");
const { go, redirect, getNavMetrics } = require("../../utils/nav");
const {
  fetchAvailableVehicles,
  getStoredTrip,
  toMiniVehicle,
  updateTripDate,
  updateTripTime
} = require("../../utils/vehicles");

Page({
  data: {
    nav: getNavMetrics(),
    categories,
    brands: brands.slice(0, 4),
    cars: cars.concat(cars).map((item, index) => Object.assign({}, item, { key: `${item.id}-${index}` })),
    trip: getStoredTrip(),
    currentCity: getStoredCity(),
    activeCategory: 0,
    activeBrand: 0,
    loading: false,
    serviceInfo: {
      store: "三亚运营中心",
      hours: "09:00-21:00",
      phone: "0898-88886666"
    }
  },
  onShow() {
    fetchEnabledCities()
      .then((cities) => {
        const currentCity = getStoredCity() || cities[0] || null;
        this.setData({ currentCity });
        return this.loadVehicles();
      })
      .catch((error) => wx.showToast({ title: error.message, icon: "none" }));
  },
  go,
  redirect,
  loadVehicles() {
    const brand = this.data.activeBrand > 0 ? this.data.brands[this.data.activeBrand] : "";
    this.setData({ loading: true });
    return fetchAvailableVehicles({
      pickup_at: this.data.trip.pickup_at,
      return_at: this.data.trip.return_at,
      brand
    })
      .then((items) => {
        this.setData({ cars: items.map(toMiniVehicle), loading: false });
      })
      .catch((error) => {
        this.setData({ loading: false });
        wx.showToast({ title: error.message, icon: "none" });
      });
  },
  chooseCity() {
    chooseCity().then((city) => {
      if (!city) return;
      this.setData({ currentCity: city });
      this.loadVehicles();
    });
  },
  chooseCategory(event) {
    this.setData({ activeCategory: Number(event.currentTarget.dataset.index) });
  },
  chooseBrand(event) {
    this.setData({ activeBrand: Number(event.currentTarget.dataset.index) });
    this.loadVehicles();
  },
  changePickupDate(event) {
    this.setData({ trip: updateTripDate(this.data.trip, "pickup", event.detail.value) });
    this.loadVehicles();
  },
  changePickupTime(event) {
    this.setData({ trip: updateTripTime(this.data.trip, "pickup", event.detail.value) });
    this.loadVehicles();
  },
  changeReturnDate(event) {
    this.setData({ trip: updateTripDate(this.data.trip, "return", event.detail.value) });
    this.loadVehicles();
  },
  changeReturnTime(event) {
    this.setData({ trip: updateTripTime(this.data.trip, "return", event.detail.value) });
    this.loadVehicles();
  },
  goBrand() {
    wx.navigateTo({
      url: `/pages/cars/cars?brand=${encodeURIComponent(this.data.brands[this.data.activeBrand] || "")}`
    });
  },
  goMoreFilters() {
    wx.navigateTo({
      url: `/pages/cars/cars?brand=${encodeURIComponent(this.data.brands[this.data.activeBrand] || "")}&more=1`
    });
  }
});
