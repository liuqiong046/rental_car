"""In-memory customer order confirmation service."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, status

from app.apps.cities.service import city_config_service
from app.apps.orders.schemas import (
    CustomerOrderDetail,
    CustomerOrderListResponse,
    ExpireUnpaidOrdersResponse,
    FeeEstimate,
    OrderAcceptRequest,
    OrderCancelRequest,
    OrderConfirmRequest,
    OrderReassignRequest,
    OrderReturnRequest,
)
from app.apps.users.schemas import CustomerProfile
from app.apps.vehicles.service import vehicle_inventory_service


class CustomerOrderService:
    def __init__(self) -> None:
        # TODO(WF-P0-09/WF-P0-10): 当前订单、幂等和锁车记录为内存实现；
        # 后续需落库并接入支付流水、超时任务调度和操作日志。
        # TODO(WF-P0-10/WF-P0-11): 支付成功后需幂等推进为待接单，并为 PC/管理端
        # 客户订单接单、改派和退单提供状态机数据源。
        # TODO(WF-P0-12/WF-P0-18): 后续补关联批发订单、工单、押金、续租提前还车、
        # 售后费用、退款、结算和完整操作审计，当前只覆盖下单到待排车的最小状态。
        self.orders: dict[str, CustomerOrderDetail] = {}
        self.idempotency_index: dict[str, str] = {}
        self.operation_idempotency_index: dict[str, CustomerOrderDetail] = {}

    def estimate(self, payload: OrderConfirmRequest) -> FeeEstimate:
        city = city_config_service.get_public_city(payload.city_code)
        vehicle = vehicle_inventory_service.get_available_for_order(
            payload.vehicle_id,
            payload.pickup_at,
            payload.return_at,
        )
        rental_days, rent_fee = vehicle_inventory_service.calculate_customer_rent_fee(
            payload.vehicle_id,
            payload.pickup_at,
            payload.return_at,
        )
        delivery_service_fee = _delivery_service_fee(payload, city.rules.night_service_fee)
        return FeeEstimate(
            vehicle_id=payload.vehicle_id,
            city_code=payload.city_code.upper(),
            rental_days=rental_days,
            rent_fee=rent_fee,
            delivery_service_fee=delivery_service_fee,
            discount_amount=0,
            payable_amount=rent_fee + delivery_service_fee,
            vehicle_deposit_amount=vehicle.model.deposit_amount,
            violation_deposit_amount=vehicle.model.violation_deposit_amount,
            price_snapshot=_price_snapshot(vehicle.price_calendar, payload.pickup_at, payload.return_at),
            lock_minutes=city.rules.unpaid_lock_minutes,
        )

    def create_pending_payment_order(
        self,
        customer: CustomerProfile,
        payload: OrderConfirmRequest,
        idempotency_key: str,
    ) -> CustomerOrderDetail:
        if customer.certification_status != "approved":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="身份认证通过后才能提交订单")

        indexed_key = f"{customer.user_id}:{idempotency_key}"
        if indexed_key in self.idempotency_index:
            return self.orders[self.idempotency_index[indexed_key]]

        estimate = self.estimate(payload)
        vehicle = vehicle_inventory_service.get_available_for_order(
            payload.vehicle_id,
            payload.pickup_at,
            payload.return_at,
        )
        city = city_config_service.get_public_city(payload.city_code)
        now = _now()
        lock_expires_at = now + timedelta(minutes=city.rules.unpaid_lock_minutes)
        order = CustomerOrderDetail(
            order_id=f"ord_{uuid4().hex[:12]}",
            user_id=customer.user_id,
            vehicle_id=payload.vehicle_id,
            city_code=payload.city_code.upper(),
            vehicle_source=vehicle.source,
            pickup_at=payload.pickup_at,
            return_at=payload.return_at,
            pickup_mode=payload.pickup_mode,
            return_mode=payload.return_mode,
            pickup_address_summary=payload.pickup_address_summary,
            return_address_summary=payload.return_address_summary,
            remark=payload.remark,
            rental_days=estimate.rental_days,
            rent_fee=estimate.rent_fee,
            delivery_service_fee=estimate.delivery_service_fee,
            discount_amount=estimate.discount_amount,
            payable_amount=estimate.payable_amount,
            vehicle_deposit_amount=estimate.vehicle_deposit_amount,
            violation_deposit_amount=estimate.violation_deposit_amount,
            payment_status="unpaid",
            order_status="pending_payment",
            lock_expires_at=lock_expires_at.isoformat(),
            created_at=now.isoformat(),
            price_snapshot=estimate.price_snapshot,
        )
        vehicle_inventory_service.lock_for_unpaid_order(
            order.vehicle_id,
            order.pickup_at,
            order.return_at,
            order.order_id,
        )
        self.orders[order.order_id] = order
        self.idempotency_index[indexed_key] = order.order_id
        return order

    def expire_unpaid_orders(self, minutes_after_lock: int | None = None) -> ExpireUnpaidOrdersResponse:
        now = _now()
        if minutes_after_lock is not None:
            now = now + timedelta(days=1, minutes=minutes_after_lock)
        expired_order_ids = []
        for order in list(self.orders.values()):
            if order.order_status != "pending_payment":
                continue
            if datetime.fromisoformat(order.lock_expires_at) > now:
                continue
            expired_order_ids.append(order.order_id)
            self.orders[order.order_id] = order.model_copy(update={"order_status": "closed"})
            if not self._has_active_vehicle_order(order.vehicle_id, order.order_id):
                vehicle_inventory_service.release_unpaid_order_lock(order.vehicle_id, order.order_id)
        return ExpireUnpaidOrdersResponse(expired_order_ids=expired_order_ids, total=len(expired_order_ids))

    def get_order_for_payment(self, order_id: str, user_id: str) -> CustomerOrderDetail:
        order = self._get_order(order_id)
        if order.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能支付本人订单")
        if order.order_status != "pending_payment" or order.payment_status != "unpaid":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="当前订单状态不允许支付")
        return order

    def cancel_pending_payment_order(
        self,
        user_id: str,
        order_id: str,
        payload: OrderCancelRequest,
    ) -> CustomerOrderDetail:
        order = self._get_order(order_id)
        if order.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能取消本人订单")
        if order.order_status != "pending_payment" or order.payment_status != "unpaid":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="当前订单状态不允许取消")
        updated = order.model_copy(
            update={
                "order_status": "closed",
                "return_reason": payload.reason,
                "operation_logs": _append_log(order, "cancel", user_id, payload.reason),
            }
        )
        self.orders[order_id] = updated
        if not self._has_active_vehicle_order(order.vehicle_id, order.order_id):
            vehicle_inventory_service.release_unpaid_order_lock(order.vehicle_id, order.order_id)
        return updated

    def get_order_for_payment_callback(self, order_id: str) -> CustomerOrderDetail:
        return self._get_order(order_id)

    def mark_paid_after_callback(self, order_id: str) -> CustomerOrderDetail:
        order = self._get_order(order_id)
        if order.payment_status == "paid":
            return order
        if order.order_status != "pending_payment":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="当前订单状态不允许支付")
        # 支付成功后车辆占用继续保留，后续 WF-P0-11 从待接单进入履约。
        updated = order.model_copy(
            update={"payment_status": "paid", "order_status": "pending_acceptance"},
        )
        self.orders[order_id] = updated
        return updated

    def list_admin_customer_orders(
        self,
        actor_id: str,
        order_status: str | None,
    ) -> CustomerOrderListResponse:
        _ = actor_id
        items = [
            order
            for order in self.orders.values()
            if order.payment_status == "paid" and (order_status is None or order.order_status == order_status)
        ]
        return CustomerOrderListResponse(items=items, total=len(items))

    def get_admin_customer_order(self, actor_id: str, order_id: str) -> CustomerOrderDetail:
        _ = actor_id
        return self._get_order(order_id)

    def accept_customer_order(
        self,
        actor_id: str,
        order_id: str,
        payload: OrderAcceptRequest,
        idempotency_key: str,
    ) -> CustomerOrderDetail:
        indexed_key = f"{actor_id}:orders/accept:{order_id}:{idempotency_key}"
        if indexed_key in self.operation_idempotency_index:
            return self.operation_idempotency_index[indexed_key]

        order = self._get_dispatchable_order(order_id)
        if order.vehicle_source == "dealer":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="车行车辆需创建关联批发订单")
        updated = order.model_copy(
            update={
                "order_status": "pending_dispatch",
                "accepted_by": actor_id,
                "accepted_at": _now().isoformat(),
                "operation_logs": _append_log(order, "accept", actor_id, payload.remark),
            },
        )
        self.orders[order_id] = updated
        self.operation_idempotency_index[indexed_key] = updated
        return updated

    def return_customer_order(
        self,
        actor_id: str,
        order_id: str,
        payload: OrderReturnRequest,
        idempotency_key: str,
    ) -> CustomerOrderDetail:
        indexed_key = f"{actor_id}:orders/return:{order_id}:{idempotency_key}"
        if indexed_key in self.operation_idempotency_index:
            return self.operation_idempotency_index[indexed_key]

        order = self._get_dispatchable_order(order_id)
        updated = order.model_copy(
            update={
                "order_status": "pending_return",
                "return_reason": payload.reason,
                "operation_logs": _append_log(order, "return", actor_id, payload.reason),
            },
        )
        self.orders[order_id] = updated
        self.operation_idempotency_index[indexed_key] = updated
        return updated

    def reassign_customer_order(
        self,
        actor_id: str,
        order_id: str,
        payload: OrderReassignRequest,
        idempotency_key: str,
    ) -> CustomerOrderDetail:
        indexed_key = f"{actor_id}:orders/reassign:{order_id}:{idempotency_key}"
        if indexed_key in self.operation_idempotency_index:
            return self.operation_idempotency_index[indexed_key]

        order = self._get_dispatchable_order(order_id)
        target_vehicle = vehicle_inventory_service.get_available_for_order(
            payload.target_vehicle_id,
            order.pickup_at,
            order.return_at,
        )
        current_vehicle = vehicle_inventory_service.get_vehicle_for_order_state(order.vehicle_id)
        if target_vehicle.model.model_id != current_vehicle.model.model_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="只能改派同车型车辆")

        _, target_rent_fee = vehicle_inventory_service.calculate_customer_rent_fee(
            payload.target_vehicle_id,
            order.pickup_at,
            order.return_at,
        )
        target_total = target_rent_fee + order.delivery_service_fee - order.discount_amount
        price_difference = target_total - order.payable_amount
        vehicle_inventory_service.release_unpaid_order_lock(order.vehicle_id, order.order_id)
        vehicle_inventory_service.lock_for_unpaid_order(
            payload.target_vehicle_id,
            order.pickup_at,
            order.return_at,
            order.order_id,
        )
        updated = order.model_copy(
            update={
                "vehicle_id": payload.target_vehicle_id,
                "original_vehicle_id": order.original_vehicle_id or order.vehicle_id,
                "order_status": "pending_dispatch",
                "reassign_price_difference": price_difference,
                "reassign_result": _reassign_result(price_difference),
                "operation_logs": _append_log(order, "reassign", actor_id, payload.remark),
            },
        )
        self.orders[order_id] = updated
        self.operation_idempotency_index[indexed_key] = updated
        return updated

    def get_dealer_order_for_wholesale_creation(self, order_id: str) -> CustomerOrderDetail:
        order = self._get_dispatchable_order(order_id)
        if order.vehicle_source != "dealer":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="只有车行车辆需要创建关联批发订单")
        return order

    def mark_dispatch_after_wholesale_accept(
        self,
        order_id: str,
        actor_id: str,
        remark: str | None,
    ) -> CustomerOrderDetail:
        order = self._get_dispatchable_order(order_id)
        updated = order.model_copy(
            update={
                "order_status": "pending_dispatch",
                "accepted_by": actor_id,
                "accepted_at": _now().isoformat(),
                "operation_logs": _append_log(order, "wholesale_accept", actor_id, remark),
            },
        )
        self.orders[order_id] = updated
        return updated

    def mark_reassign_after_wholesale_reject(
        self,
        order_id: str,
        actor_id: str,
        reason: str,
    ) -> CustomerOrderDetail:
        order = self._get_order(order_id)
        if order.payment_status != "paid" or order.order_status != "pending_acceptance":
            return order
        updated = order.model_copy(
            update={
                "order_status": "pending_reassign",
                "return_reason": f"批发订单已拒绝：{reason}",
                "operation_logs": _append_log(order, "wholesale_reject", actor_id, reason),
            },
        )
        self.orders[order_id] = updated
        return updated

    def _get_order(self, order_id: str) -> CustomerOrderDetail:
        order = self.orders.get(order_id)
        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
        return order

    def _get_dispatchable_order(self, order_id: str) -> CustomerOrderDetail:
        order = self._get_order(order_id)
        if order.payment_status != "paid" or order.order_status != "pending_acceptance":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="当前订单状态不允许处理")
        return order

    def _has_active_vehicle_order(self, vehicle_id: str, ignored_order_id: str) -> bool:
        return any(
            order.order_id != ignored_order_id
            and order.vehicle_id == vehicle_id
            and order.order_status != "closed"
            for order in self.orders.values()
        )


def _delivery_service_fee(payload: OrderConfirmRequest, night_service_fee: int) -> int:
    fee = 0
    if payload.pickup_mode == "delivery":
        fee += night_service_fee
    if payload.return_mode == "pickup":
        fee += night_service_fee
    return fee


def _price_snapshot(calendar: list[object], pickup_at: str, return_at: str) -> list[dict[str, int | str]]:
    pickup_date = datetime.fromisoformat(pickup_at).date()
    return_date = datetime.fromisoformat(return_at).date()
    needed_dates = {
        (pickup_date + timedelta(days=offset)).isoformat()
        for offset in range((return_date - pickup_date).days + 1)
    }
    return [
        {"date": entry.date, "customer_price": entry.customer_price}
        for entry in calendar
        if entry.date in needed_dates
    ]


def _now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _append_log(
    order: CustomerOrderDetail,
    action: str,
    actor_id: str,
    remark: str | None,
) -> list[dict[str, str]]:
    log = {
        "action": action,
        "actor_id": actor_id,
        "remark": remark or "",
        "created_at": _now().isoformat(),
    }
    return [*order.operation_logs, log]


def _reassign_result(price_difference: int) -> str:
    if price_difference > 0:
        return "运营中心承担差价"
    if price_difference < 0:
        return "待结算退差"
    return "无差价"


customer_order_service = CustomerOrderService()
