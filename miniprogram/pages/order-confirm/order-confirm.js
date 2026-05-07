const { cars, order } = require("../../utils/data");
const { ensureIdentityApproved } = require("../../utils/identity");
const { go, getNavMetrics } = require("../../utils/nav");
const { requireLogin } = require("../../utils/auth");
const {
  createIdempotencyKey,
  createPendingOrder,
  estimateOrderFee,
  payPendingOrder
} = require("../../utils/orders");
const { fetchVehicleDetail, getStoredTrip, toMiniVehicle } = require("../../utils/vehicles");

Page({
  data: {
    // TODO(WF-P0-09/WF-P0-10): 对齐 H5 确认订单的地图地址选择、上门半径/超区费、
    // 创建订单成功页和支付失败/取消重试；当前只创建待支付锁车订单。
    nav: getNavMetrics(),
    car: cars[0],
    order,
    trip: getStoredTrip(),
    estimate: null,
    pickupMode: "self_pickup",
    returnMode: "self_return",
    pickupAddressSummary: "三亚运营中心",
    returnAddressSummary: "三亚运营中心",
    deliveryTip: "门店自取/自还，不收送收服务费。",
    remark: "",
    submitKey: "",
    submitting: false,
    feeDetailOpen: false,
    protections: [
      ["车损保障", "300元以下车损免收"],
      ["免折旧费", "5000元以下车损免收"],
      ["免停运费", "5000元以下车损免收"],
      ["免维修费", "5000元以下车损免收"]
    ]
  },
  onLoad(query) {
    if (!requireLogin(`/pages/order-confirm/order-confirm${query && query.id ? `?id=${query.id}` : ""}`)) return;
    const car = cars.find((item) => item.id === query.id) || cars[0];
    this.setData({ car, submitKey: createIdempotencyKey(car.id) });
    if (!query.id) {
      this.refreshEstimate();
      return;
    }
    fetchVehicleDetail(query.id)
      .then((detail) => {
        this.setData({
          car: toMiniVehicle(detail, 0),
          submitKey: createIdempotencyKey(detail.vehicle_id)
        });
        return this.refreshEstimate();
      })
      .catch((error) => wx.showToast({ title: error.message, icon: "none" }));
  },
  go,
  refreshEstimate() {
    return estimateOrderFee(this.buildOrderPayload())
      .then((estimate) => this.setData({ estimate }))
      .catch((error) => wx.showToast({ title: error.message, icon: "none" }));
  },
  buildOrderPayload() {
    return {
      vehicle_id: this.data.car.id,
      city_code: "SY",
      pickup_at: this.data.trip.pickup_at,
      return_at: this.data.trip.return_at,
      pickup_mode: this.data.pickupMode,
      return_mode: this.data.returnMode,
      pickup_address_summary: this.data.pickupAddressSummary,
      return_address_summary: this.data.returnAddressSummary,
      remark: this.data.remark || null
    };
  },
  chooseSelfService() {
    this.setData({
      pickupMode: "self_pickup",
      returnMode: "self_return",
      pickupAddressSummary: "三亚运营中心",
      returnAddressSummary: "三亚运营中心",
      deliveryTip: "门店自取/自还，不收送收服务费。"
    });
    this.refreshEstimate();
  },
  chooseDoorService() {
    this.setData({
      pickupMode: "delivery",
      returnMode: "pickup",
      pickupAddressSummary: "三亚市海棠湾附近",
      returnAddressSummary: "三亚市凤凰机场附近",
      deliveryTip: "当前城市上门送收半径 30km，超区按 9 元/km 线下补差，夜间服务费已计入预估。"
    });
    this.refreshEstimate();
  },
  changeRemark(event) {
    this.setData({ remark: event.detail.value });
  },
  toggleFeeDetail() {
    this.setData({ feeDetailOpen: !this.data.feeDetailOpen });
  },
  verifyIdentity() {
    wx.navigateTo({ url: "/pages/identity/identity" });
  },
  pay() {
    if (this.data.submitting) return;
    this.setData({ submitting: true });
    ensureIdentityApproved()
      .then(() => createPendingOrder(this.buildOrderPayload(), this.data.submitKey))
      .then((pendingOrder) => {
        wx.setStorageSync("last_pending_order", pendingOrder);
        return payPendingOrder(pendingOrder).then((paymentResult) => ({ pendingOrder, paymentResult }));
      })
      .then(({ pendingOrder, paymentResult }) => {
        wx.setStorageSync(
          "last_pending_order",
          Object.assign({}, pendingOrder, {
            payment_status: paymentResult.payment_status,
            order_status: paymentResult.order_status
          })
        );
        wx.showToast({ title: "支付成功", icon: "success" });
        wx.navigateTo({ url: "/pages/order-detail/order-detail" });
      })
      .catch((error) => wx.showModal({ title: "支付未完成", content: error.message, showCancel: false }))
      .finally(() => this.setData({ submitting: false }));
  }
});
