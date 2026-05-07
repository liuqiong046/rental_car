"""In-memory wholesale order state machine."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, status

from app.apps.admin.schemas import AdminActor
from app.apps.cities.service import city_config_service
from app.apps.orders.service import customer_order_service
from app.apps.vehicles.service import vehicle_inventory_service
from app.apps.wholesale_orders.schemas import (
    ExpireWholesaleOrdersResponse,
    WholesaleOrderChangePriceRequest,
    WholesaleOrderCreateRelatedRequest,
    WholesaleOrderDetail,
    WholesaleOrderListResponse,
)


class WholesaleOrderService:
    def __init__(self) -> None:
        # TODO(WF-P0-12): 当前批发订单、幂等和 SLA 任务为内存实现；
        # 后续需落库并接入真实调度器、车行数据范围和批发结算。
        self.orders: dict[str, WholesaleOrderDetail] = {}
        self.related_customer_index: dict[str, str] = {}
        self.idempotency_index: dict[str, WholesaleOrderDetail] = {}

    def list_orders(self, actor: AdminActor, order_status: str | None) -> WholesaleOrderListResponse:
        items = [
            order
            for order in self.orders.values()
            if _is_order_visible(actor, order) and (order_status is None or order.status == order_status)
        ]
        return WholesaleOrderListResponse(items=items, total=len(items))

    def create_related_order(
        self,
        actor: AdminActor,
        payload: WholesaleOrderCreateRelatedRequest,
        idempotency_key: str,
    ) -> WholesaleOrderDetail:
        indexed_key = f"{actor.account_id}:wholesale/create-related:{idempotency_key}"
        if indexed_key in self.idempotency_index:
            return self.idempotency_index[indexed_key]
        if payload.customer_order_id in self.related_customer_index:
            existing = self.orders[self.related_customer_index[payload.customer_order_id]]
            self.idempotency_index[indexed_key] = existing
            return existing

        customer_order = customer_order_service.get_dealer_order_for_wholesale_creation(payload.customer_order_id)
        vehicle = vehicle_inventory_service.get_vehicle_for_order_state(customer_order.vehicle_id)
        if vehicle.dealer_id is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="车辆缺少车行归属")
        _ensure_actor_can_manage_city(actor, customer_order.city_code)

        city = city_config_service.get_public_city(customer_order.city_code)
        rental_days, wholesale_price = vehicle_inventory_service.calculate_wholesale_rent_fee(
            customer_order.vehicle_id,
            customer_order.pickup_at,
            customer_order.return_at,
        )
        now = _now()
        order = WholesaleOrderDetail(
            wholesale_order_id=f"wo_{uuid4().hex[:12]}",
            customer_order_id=customer_order.order_id,
            city_code=customer_order.city_code,
            vehicle_id=customer_order.vehicle_id,
            dealer_id=vehicle.dealer_id,
            pickup_at=customer_order.pickup_at,
            return_at=customer_order.return_at,
            rental_days=rental_days,
            wholesale_price=wholesale_price,
            status="pending_dealer_acceptance",
            created_by=actor.account_id,
            created_at=now.isoformat(),
            expires_at=(now + timedelta(minutes=city.rules.dealer_confirm_sla_minutes)).isoformat(),
            operation_logs=[_log("create_related", actor.account_id, payload.remark)],
        )
        self.orders[order.wholesale_order_id] = order
        self.related_customer_index[customer_order.order_id] = order.wholesale_order_id
        self.idempotency_index[indexed_key] = order
        return order

    def accept_order(
        self,
        actor: AdminActor,
        wholesale_order_id: str,
        remark: str | None,
        idempotency_key: str,
    ) -> WholesaleOrderDetail:
        indexed_key = f"{actor.account_id}:wholesale/accept:{wholesale_order_id}:{idempotency_key}"
        if indexed_key in self.idempotency_index:
            return self.idempotency_index[indexed_key]

        order = self._get_pending_dealer_order(actor, wholesale_order_id)
        updated = order.model_copy(
            update={
                "status": "accepted",
                "accepted_by": actor.account_id,
                "accepted_at": _now().isoformat(),
                "operation_logs": [*order.operation_logs, _log("accept", actor.account_id, remark)],
            },
        )
        self.orders[wholesale_order_id] = updated
        if updated.customer_order_id is not None:
            customer_order_service.mark_dispatch_after_wholesale_accept(
                updated.customer_order_id,
                actor.account_id,
                remark,
            )
        self.idempotency_index[indexed_key] = updated
        return updated

    def reject_order(
        self,
        actor: AdminActor,
        wholesale_order_id: str,
        reason: str,
        idempotency_key: str,
    ) -> WholesaleOrderDetail:
        indexed_key = f"{actor.account_id}:wholesale/reject:{wholesale_order_id}:{idempotency_key}"
        if indexed_key in self.idempotency_index:
            return self.idempotency_index[indexed_key]
        order = self._get_pending_dealer_order(actor, wholesale_order_id)
        updated = self._reject_order(order, actor.account_id, reason, "rejected", "reject")
        self.idempotency_index[indexed_key] = updated
        return updated

    def change_price(
        self,
        actor: AdminActor,
        wholesale_order_id: str,
        payload: WholesaleOrderChangePriceRequest,
        idempotency_key: str,
    ) -> WholesaleOrderDetail:
        indexed_key = f"{actor.account_id}:wholesale/change-price:{wholesale_order_id}:{idempotency_key}"
        if indexed_key in self.idempotency_index:
            return self.idempotency_index[indexed_key]

        order = self._get_pending_dealer_order(actor, wholesale_order_id)
        updated = order.model_copy(
            update={
                "wholesale_price": payload.wholesale_price,
                "operation_logs": [*order.operation_logs, _log("change_price", actor.account_id, payload.reason)],
            },
        )
        self.orders[wholesale_order_id] = updated
        self.idempotency_index[indexed_key] = updated
        return updated

    def expire_pending_orders(
        self,
        actor: AdminActor,
        minutes_after_sla: int | None,
    ) -> ExpireWholesaleOrdersResponse:
        now = _now()
        if minutes_after_sla is not None:
            now = now + timedelta(days=1, minutes=minutes_after_sla)
        expired_ids = []
        for order in list(self.orders.values()):
            if order.status != "pending_dealer_acceptance":
                continue
            if not _is_order_visible(actor, order):
                continue
            if datetime.fromisoformat(order.expires_at) > now:
                continue
            expired = self._reject_order(order, actor.account_id, "车行确认超时", "expired_rejected", "timeout_reject")
            expired_ids.append(expired.wholesale_order_id)
        return ExpireWholesaleOrdersResponse(expired_wholesale_order_ids=expired_ids, total=len(expired_ids))

    def _reject_order(
        self,
        order: WholesaleOrderDetail,
        actor_id: str,
        reason: str,
        next_status: str,
        action: str,
    ) -> WholesaleOrderDetail:
        updated = order.model_copy(
            update={
                "status": next_status,
                "reject_reason": reason,
                "operation_logs": [*order.operation_logs, _log(action, actor_id, reason)],
            },
        )
        self.orders[order.wholesale_order_id] = updated
        if updated.customer_order_id is not None:
            customer_order_service.mark_reassign_after_wholesale_reject(updated.customer_order_id, actor_id, reason)
        return updated

    def _get_pending_dealer_order(self, actor: AdminActor, wholesale_order_id: str) -> WholesaleOrderDetail:
        order = self.orders.get(wholesale_order_id)
        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="批发订单不存在")
        if not _is_order_visible(actor, order):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
        if order.status != "pending_dealer_acceptance":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="当前批发订单状态不允许处理")
        return order


def _ensure_actor_can_manage_city(actor: AdminActor, city_code: str) -> None:
    scope = actor.role.data_scope
    if scope.type == "all":
        return
    if scope.type == "city" and scope.city_code == city_code:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")


def _is_order_visible(actor: AdminActor, order: WholesaleOrderDetail) -> bool:
    scope = actor.role.data_scope
    if scope.type == "all":
        return True
    if scope.type == "city":
        return order.city_code == scope.city_code
    return order.dealer_id == scope.organization_id


def _log(action: str, actor_id: str, remark: str | None) -> dict[str, str]:
    return {
        "action": action,
        "actor_id": actor_id,
        "remark": remark or "",
        "created_at": _now().isoformat(),
    }


def _now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


wholesale_order_service = WholesaleOrderService()
