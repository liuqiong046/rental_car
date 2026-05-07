const { cars, order } = require("../../utils/data");
const { go, getNavMetrics } = require("../../utils/nav");
const { cancelPendingOrder, payPendingOrder } = require("../../utils/orders");
const { getStoredTrip } = require("../../utils/vehicles");

Page({
  data: {
    // TODO(WF-P0-10/WF-P0-18): 对齐 H5 订单详情全状态，补微信支付、押金/免押、
    // 接单/改派/退单、续租提前还车、售后费用、取消订单和结算费用明细。
    nav: getNavMetrics(),
    car: cars[0],
    order,
    trip: getStoredTrip(),
    pendingOrder: null,
    paying: false,
    cancelling: false,
    feeDetailOpen: false,
    steps: ["支付租车费用", "门店接单", "支付押金", "取车", "还车", "订单完成"]
  },
  onShow() {
    const pendingOrder = wx.getStorageSync("last_pending_order") || null;
    if (!pendingOrder) return;
    const car = cars.find((item) => item.id === pendingOrder.vehicle_id) || cars[0];
    this.setData({ pendingOrder, car });
  },
  go,
  toggleFeeDetail() {
    this.setData({ feeDetailOpen: !this.data.feeDetailOpen });
  },
  continuePay() {
    if (this.data.paying || !this.data.pendingOrder) return;
    this.setData({ paying: true });
    payPendingOrder(this.data.pendingOrder)
      .then((paymentResult) => {
        const paidOrder = Object.assign({}, this.data.pendingOrder, {
          payment_status: paymentResult.payment_status,
          order_status: paymentResult.order_status
        });
        wx.setStorageSync("last_pending_order", paidOrder);
        this.setData({ pendingOrder: paidOrder });
        wx.showToast({ title: "支付成功", icon: "success" });
      })
      .catch((error) => wx.showModal({ title: "支付未完成", content: error.message, showCancel: false }))
      .finally(() => this.setData({ paying: false }));
  },
  cancelOrder() {
    if (this.data.cancelling || !this.data.pendingOrder || this.data.pendingOrder.payment_status === "paid") return;
    wx.showModal({
      title: "取消订单",
      content: "待支付订单取消后将立即释放锁车名额。",
      success: ({ confirm }) => {
        if (!confirm) return;
        this.setData({ cancelling: true });
        cancelPendingOrder(this.data.pendingOrder.order_id)
          .then((cancelledOrder) => {
            wx.setStorageSync("last_pending_order", cancelledOrder);
            this.setData({ pendingOrder: cancelledOrder });
            wx.showToast({ title: "订单已取消", icon: "success" });
          })
          .catch((error) => wx.showModal({ title: "取消失败", content: error.message, showCancel: false }))
          .finally(() => this.setData({ cancelling: false }));
      }
    });
  }
});
