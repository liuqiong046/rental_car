const { cars } = require("../../utils/data");
const { go, getNavMetrics } = require("../../utils/nav");
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
    brand: "",
    showMoreFilters: false,
    trip: getStoredTrip(),
    cars: cars.concat(cars).map((item, index) => Object.assign({}, item, { key: `${item.id}-${index}` })),
    filters: [
      { label: "综合排序", type: "sort" },
      { label: "价格", type: "price" },
      { label: "颜色", type: "color" },
      { label: "能源", type: "energy_type" },
      { label: "座位", type: "seats" },
      { label: "变速箱", type: "gearbox" }
    ],
    selectedFilters: {},
    filterText: "全部条件",
    moreFilterDraft: {}
  },
  onLoad(query) {
    const nextData = {};
    if (query.brand) nextData.brand = decodeURIComponent(query.brand);
    if (query.more) nextData.showMoreFilters = true;
    this.setData(nextData);
  },
  onShow() {
    this.loadVehicles();
  },
  loadVehicles() {
    const selected = this.data.selectedFilters;
    const price = selected.price || {};
    fetchAvailableVehicles({
      pickup_at: this.data.trip.pickup_at,
      return_at: this.data.trip.return_at,
      brand: this.data.brand,
      price_min: price.min,
      price_max: price.max,
      color: selected.color,
      energy_type: selected.energy_type,
      seats: selected.seats,
      gearbox: selected.gearbox
    })
      .then((items) => {
        const vehicles = items.map(toMiniVehicle);
        this.setData({ cars: vehicles, filterText: buildFilterText(this.data.brand, selected) });
      })
      .catch((error) => wx.showToast({ title: error.message, icon: "none" }));
  },
  chooseFilter(event) {
    const type = event.currentTarget.dataset.type;
    if (type === "sort") {
      this.toggleMoreFilters();
      return;
    }
    const options = filterOptions(type);
    if (!options.length) return;
    wx.showActionSheet({
      itemList: options.map((item) => item.label),
      success: (result) => {
        const option = options[result.tapIndex];
        const selectedFilters = Object.assign({}, this.data.selectedFilters, {
          [type]: option.value
        });
        if (option.value === "") delete selectedFilters[type];
        this.setData({ selectedFilters });
        this.loadVehicles();
      }
    });
  },
  toggleMoreFilters() {
    this.setData({
      showMoreFilters: !this.data.showMoreFilters,
      moreFilterDraft: Object.assign({}, this.data.selectedFilters)
    });
  },
  closeMoreFilters() {
    this.setData({ showMoreFilters: false });
  },
  chooseMoreFilter(event) {
    const type = event.currentTarget.dataset.type;
    const value = event.currentTarget.dataset.value;
    const nextDraft = Object.assign({}, this.data.moreFilterDraft, {
      [type]: parseFilterValue(type, value)
    });
    if (value === "") delete nextDraft[type];
    this.setData({ moreFilterDraft: nextDraft });
  },
  applyMoreFilters() {
    this.setData({
      selectedFilters: Object.assign({}, this.data.moreFilterDraft),
      showMoreFilters: false
    });
    this.loadVehicles();
  },
  resetMoreFilters() {
    this.setData({ moreFilterDraft: {} });
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
  noop() {},
  go,
  goBrand() {
    wx.navigateTo({ url: "/pages/brand/brand" });
  }
});

function filterOptions(type) {
  const options = {
    price: [
      { label: "全部价格", value: "" },
      { label: "200元以下", value: { max: 200 } },
      { label: "200-300元", value: { min: 200, max: 300 } }
    ],
    color: [
      { label: "全部颜色", value: "" },
      { label: "海湾蓝", value: "海湾蓝" },
      { label: "珍珠白", value: "珍珠白" }
    ],
    energy_type: [
      { label: "全部能源", value: "" },
      { label: "纯电动", value: "纯电动" }
    ],
    seats: [
      { label: "全部座位", value: "" },
      { label: "5座", value: 5 }
    ],
    gearbox: [
      { label: "全部变速箱", value: "" },
      { label: "自动挡", value: "自动挡" }
    ]
  };
  return options[type] || [];
}

function buildFilterText(brand, selected) {
  const parts = [brand || "全部车型"];
  if (selected.price) parts.push("价格筛选");
  ["color", "energy_type", "seats", "gearbox"].forEach((key) => {
    if (selected[key]) parts.push(`${selected[key]}${key === "seats" ? "座" : ""}`);
  });
  return parts.join("｜");
}

function parseFilterValue(type, value) {
  if (type === "seats") return value ? Number(value) : "";
  if (type === "price") {
    if (value === "under200") return { max: 200 };
    if (value === "200-300") return { min: 200, max: 300 };
    if (value === "300plus") return { min: 300 };
    return "";
  }
  return value;
}
