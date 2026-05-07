const { cars, order } = require("../../utils/data");
const { go, redirect, getNavMetrics } = require("../../utils/nav");
const { requireLogin } = require("../../utils/auth");

Page({
  data: {
    nav: getNavMetrics(),
    // TODO(WF-P0-11/WF-P0-18): 后续接入服务端订单列表和 H5 全状态分组，补改派/退单、
    // 押金、续租提前还车、车况、售后费用、退款状态、结算进度和本地隐藏删除。
    tabs: ["全部", "待支付", "待接单", "待取车", "待还车", "已完成"],
    activeTab: 0,
    orders: [
      Object.assign({}, order, { key: "order-1" }),
      Object.assign({}, order, { key: "order-2", status: "待取车" })
    ],
    car: cars[0]
  },
  onShow() {
    if (!requireLogin("/pages/orders/orders")) return;
    this.refreshLocalOrders();
  },
  go,
  redirect,
  switchTab(event) {
    this.setData({ activeTab: Number(event.currentTarget.dataset.index) });
  },
  refreshLocalOrders() {
    const pendingOrder = wx.getStorageSync("last_pending_order") || null;
    if (!pendingOrder) return;
    const statusText = statusTextByOrder(pendingOrder);
    const paidOrder = Object.assign({}, order, {
      key: pendingOrder.order_id,
      no: pendingOrder.order_id,
      status: statusText,
      renter: "本人用车",
      phone: "已登录",
      pickupDate: pendingOrder.pickup_at,
      returnDate: pendingOrder.return_at,
      duration: `${pendingOrder.rental_days || 1} 天`,
      pickupAddress: pendingOrder.pickup_address_summary,
      returnAddress: pendingOrder.return_address_summary,
      rentFee: pendingOrder.rent_fee,
      serviceFee: pendingOrder.delivery_service_fee,
      total: pendingOrder.payable_amount
    });
    this.setData({ orders: [paidOrder] });
  }
});

function statusTextByOrder(orderItem) {
  if (orderItem.order_status === "pending_acceptance") return "待接单";
  if (orderItem.order_status === "pending_dispatch") return "待取车";
  if (orderItem.order_status === "pending_return") return "待退单";
  if (orderItem.order_status === "pending_reassign") return "待改派";
  return orderItem.payment_status === "paid" ? "待接单" : "待支付";
}
