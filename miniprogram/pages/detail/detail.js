const { cars } = require("../../utils/data");
const { go, getNavMetrics } = require("../../utils/nav");
const { fetchVehicleDetail, getStoredTrip, toMiniVehicle } = require("../../utils/vehicles");

Page({
  data: {
    nav: getNavMetrics(),
    car: cars[0],
    trip: getStoredTrip(),
    estimateTotal: 1000,
    thumbs: [
      "/assets/detail-thumb-1.jpg",
      "/assets/detail-thumb-2.jpg",
      "/assets/detail-thumb-3.jpg",
      "/assets/detail-thumb-4.jpg",
      "/assets/detail-thumb-5.jpg"
    ],
    specs: [
      ["车牌号", "琼B2384JX"],
      ["颜色", "黄色"],
      ["座位数", "5"],
      ["燃油类型", "纯电动"],
      ["年款", "2024"],
      ["日限里程", "300km"],
      ["车辆里程", "12000km"]
    ],
    rules: [
      ["提前预定", "0.5小时"],
      ["日均限行", "200km"],
      ["超里程单价", "2.0元/公里"],
      ["租期要求", "1天起租"],
      ["油费和电费", "建议原油位/原电量还车"],
      ["续租/延迟还车", "续租服务独立按时间计算"]
    ],
    days: [],
    activeImage: 0,
    detailPhotos: [
      "/assets/detail-thumb-2.jpg",
      "/assets/detail-thumb-3.jpg",
      "/assets/detail-thumb-4.jpg",
      "/assets/detail-thumb-5.jpg"
    ]
  },
  onLoad(query) {
    const car = cars.find((item) => item.id === query.id) || cars[0];
    this.setData({ car });
    if (!query.id) return;
    fetchVehicleDetail(query.id)
      .then((detail) => {
        const nextCar = toMiniVehicle(detail, 0);
        this.setData({
          car: nextCar,
          thumbs: nextCar.previewImages,
          detailPhotos: nextCar.previewImages.slice(1),
          specs: buildSpecs(nextCar),
          rules: buildRules(nextCar),
          days: nextCar.calendar.slice(0, 14),
          estimateTotal: nextCar.detailPrice * this.data.trip.durationDays
        });
      })
      .catch((error) => wx.showToast({ title: error.message, icon: "none" }));
  },
  previewGallery(event) {
    const current = event.currentTarget.dataset.src;
    wx.previewImage({
      current,
      urls: this.data.thumbs
    });
  },
  changeHero(event) {
    const index = Number(event.currentTarget.dataset.index || 0);
    this.setData({
      activeImage: index,
      "car.hero": this.data.thumbs[index] || this.data.car.hero
    });
  },
  go
});

function buildSpecs(car) {
  return [
    ["车牌号", car.plate],
    ["颜色", car.color],
    ["座位数", `${car.seats}`],
    ["能源类型", car.energy],
    ["年款", car.modelYear],
    ["日限里程", car.dailyMileageLimit],
    ["车辆里程", car.mileage],
    ["车辆来源", car.sourceLabel]
  ];
}

function buildRules(car) {
  return [
    ["提前预定", "至少提前1小时"],
    ["日均限行", car.dailyMileageLimit],
    ["车辆押金", `${car.deposit}元，取车前线下或免押确认`],
    ["违章押金", `${car.violationDeposit}元，还车后按规则处理`],
    ["油费和电费", "建议原油位/原电量还车"],
    ["续租/延迟还车", "续租服务独立按时间计算"]
  ];
}
