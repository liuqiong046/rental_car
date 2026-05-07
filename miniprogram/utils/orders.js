const { request } = require("./request");

function estimateOrderFee(payload) {
  return request({
    url: "/api/v1/orders/estimate",
    method: "POST",
    data: payload
  });
}

function createPendingOrder(payload, idempotencyKey) {
  return request({
    url: "/api/v1/orders",
    method: "POST",
    data: payload,
    header: { "Idempotency-Key": idempotencyKey }
  });
}

function createPaymentPrepay(orderId, idempotencyKey) {
  return request({
    url: "/api/v1/payments/prepay",
    method: "POST",
    data: { order_id: orderId },
    header: { "Idempotency-Key": idempotencyKey }
  });
}

function cancelPendingOrder(orderId, reason) {
  return request({
    url: `/api/v1/orders/${orderId}/cancel`,
    method: "POST",
    data: reason ? { reason } : {}
  });
}

function createIdempotencyKey(vehicleId) {
  return `mp-${vehicleId}-${Date.now()}`;
}

function requestOrderPayment(pendingOrder, prepay) {
  if (prepay.provider === "wechat_mock") {
    return request({
      url: "/api/v1/payments/wechat/callback",
      method: "POST",
      data: {
        order_id: pendingOrder.order_id,
        payment_id: prepay.payment_id,
        transaction_id: `mock-${prepay.payment_id}`,
        trade_state: "SUCCESS",
        paid_amount: prepay.payable_amount
      },
      header: { "Idempotency-Key": createIdempotencyKey(prepay.payment_id) }
    });
  }
  return new Promise((resolve, reject) => {
    wx.requestPayment(
      Object.assign({}, prepay.pay_params, {
        success: resolve,
        fail(error) {
          const message = error && error.errMsg && error.errMsg.indexOf("cancel") >= 0
            ? "已取消支付，可在订单详情继续支付"
            : "支付失败，请稍后重试";
          reject(new Error(message));
        }
      })
    );
  });
}

function payPendingOrder(pendingOrder) {
  const prepayKey = createIdempotencyKey(pendingOrder.order_id);
  return createPaymentPrepay(pendingOrder.order_id, prepayKey)
    .then((prepay) => requestOrderPayment(pendingOrder, prepay));
}

module.exports = {
  cancelPendingOrder,
  createIdempotencyKey,
  createPendingOrder,
  createPaymentPrepay,
  payPendingOrder,
  estimateOrderFee
};
