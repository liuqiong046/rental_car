export type DataScope = {
  type: 'all' | 'city' | 'organization'
  city_code?: string | null
  organization_id?: string | null
}

export type Organization = {
  id: string
  name: string
  type: string
  parent_id?: string | null
  city_code?: string | null
  status: string
}

export type AdminRole = {
  id: string
  code: string
  name: string
  menus: string[]
  buttons: string[]
  data_scope: DataScope
}

export type AdminActor = {
  account_id: string
  username: string
  display_name: string
  organization: Organization
  role: AdminRole
  status: string
}

export type HomepageConfig = {
  banner_titles: string[]
  hot_brands: string[]
  recommended_vehicle_ids: string[]
}

export type ServiceRuleConfig = {
  unpaid_lock_minutes: number
  dealer_confirm_sla_minutes: number
  service_radius_km: number
  over_radius_fee_per_km: number
  night_service_fee: number
  deposit_amount: number
  violation_deposit_amount: number
  holiday_source: string
  early_return_refund_rule: string
  cancellation_refund_rule: string
}

export type MapFenceConfig = {
  center_latitude: number
  center_longitude: number
  radius_km: number
}

export type CityConfig = {
  city_code: string
  city_name: string
  status: 'active' | 'disabled'
  default_operation_center_id: string
  service_categories: string[]
  contact_name: string
  contact_phone_mask: string
  store_address: string
  business_hours: string
  map_fence: MapFenceConfig
  homepage: HomepageConfig
  rules: ServiceRuleConfig
  is_default: boolean
  config_version: number
  updated_at: string
}

export type VehicleModel = {
  model_id: string
  brand: string
  series: string
  model_name: string
  year: number
  vehicle_type: string
  energy_type: string
  seats: number
  gearbox: string
  min_base_price: number
  deposit_amount: number
  violation_deposit_amount: number
}

export type PriceCalendarEntry = {
  vehicle_id: string
  date: string
  base_price: number
  customer_price: number
  wholesale_price: number
  rentable: boolean
  available_periods: string[]
  updated_at: string
}

export type VehicleDetail = {
  vehicle_id: string
  city_code: string
  model: VehicleModel
  plate_mask: string
  color: string
  mileage_km: number
  daily_mileage_limit: number
  image_url: string
  source: string
  dealer_id?: string | null
  hosted_owner?: string | null
  review_status: string
  listing_status: string
  maintenance: boolean
  manually_locked: boolean
  occupied: boolean
  available: boolean
  unavailable_reason?: string | null
  today_price?: PriceCalendarEntry | null
  price_calendar: PriceCalendarEntry[]
}

export type IdentitySubmission = {
  submission_id: string
  user_id: string
  real_name: string
  id_no_mask: string
  driver_license_no_mask: string
  id_card_front_url: string
  id_card_back_url: string
  driver_license_url: string
  status: string
  reject_reason?: string | null
  updated_at: string
  version: number
}

export type IdentityAuditLog = {
  action: string
  actor_id: string
  reason: string
  created_at: string
}

export type IdentityAdminDetail = IdentitySubmission & {
  customer: {
    user_id: string
    nickname: string
    avatar_text: string
    phone_mask: string
    certification_status: string
    blacklisted: boolean
  }
  audit_logs: IdentityAuditLog[]
}

export type CustomerOrder = {
  order_id: string
  user_id: string
  vehicle_id: string
  city_code: string
  vehicle_source: string
  pickup_at: string
  return_at: string
  pickup_address_summary: string
  return_address_summary: string
  rental_days: number
  rent_fee: number
  delivery_service_fee: number
  payable_amount: number
  payment_status: string
  order_status: string
  original_vehicle_id?: string | null
  reassign_price_difference: number
  reassign_result?: string | null
  return_reason?: string | null
  operation_logs: Array<{ action: string; actor_id: string; remark: string; created_at: string }>
}

export type WholesaleOrder = {
  wholesale_order_id: string
  customer_order_id?: string | null
  city_code: string
  vehicle_id: string
  dealer_id: string
  pickup_at: string
  return_at: string
  rental_days: number
  wholesale_price: number
  status: string
  reject_reason?: string | null
  created_by: string
  created_at: string
  expires_at: string
  accepted_by?: string | null
  accepted_at?: string | null
  operation_logs: Array<{ action: string; actor_id: string; remark: string; created_at: string }>
}

type ListResponse<T> = {
  items: T[]
  total: number
}

// TODO(WF-P0-13/WF-P0-20): 补齐管理端待办、工单排班、押金/免押、续租提前还车、
// 售后投诉、财务退款/结算、消息和操作日志的后台 API client。

const API_BASE = import.meta.env.VITE_API_BASE || ''

async function request<T>(path: string, token?: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers
    }
  })
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(payload.detail || '请求失败')
  }
  if (response.status === 204) {
    return undefined as T
  }
  return response.json() as Promise<T>
}

export function login(username: string, password: string) {
  return request<{ access_token: string; actor: AdminActor }>('/api/v1/admin/auth/login', undefined, {
    method: 'POST',
    body: JSON.stringify({ username, password })
  })
}

export function fetchOrganizations(token: string) {
  return request<ListResponse<Organization>>('/api/v1/admin/organizations', token)
}

export function fetchRoles(token: string) {
  return request<ListResponse<AdminRole>>('/api/v1/admin/roles', token)
}

export function fetchAccounts(token: string) {
  return request<ListResponse<AdminActor>>('/api/v1/admin/accounts', token)
}

export function createOrganization(
  token: string,
  payload: Pick<Organization, 'name' | 'type' | 'parent_id' | 'city_code'>
) {
  return request<Organization>('/api/v1/admin/organizations', token, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export function updateOrganization(token: string, organizationId: string, payload: Partial<Organization>) {
  return request<Organization>(`/api/v1/admin/organizations/${organizationId}`, token, {
    method: 'PATCH',
    body: JSON.stringify(payload)
  })
}

export function createRole(token: string, payload: Omit<AdminRole, 'id'>) {
  return request<AdminRole>('/api/v1/admin/roles', token, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export function updateRole(token: string, roleId: string, payload: Partial<Omit<AdminRole, 'id' | 'code'>>) {
  return request<AdminRole>(`/api/v1/admin/roles/${roleId}`, token, {
    method: 'PATCH',
    body: JSON.stringify(payload)
  })
}

export function createAccount(
  token: string,
  payload: {
    username: string
    display_name: string
    password: string
    organization_id: string
    role_id: string
  }
) {
  return request<AdminActor>('/api/v1/admin/accounts', token, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export function updateAccount(
  token: string,
  accountId: string,
  payload: { display_name?: string; organization_id?: string; role_id?: string }
) {
  return request<AdminActor>(`/api/v1/admin/accounts/${accountId}`, token, {
    method: 'PATCH',
    body: JSON.stringify(payload)
  })
}

export function updateAccountStatus(token: string, accountId: string, status: string) {
  return request<AdminActor>(`/api/v1/admin/accounts/${accountId}/status`, token, {
    method: 'PATCH',
    body: JSON.stringify({ status })
  })
}

export function resetAccountPassword(token: string, accountId: string, password: string) {
  return request<void>(`/api/v1/admin/accounts/${accountId}/reset-password`, token, {
    method: 'POST',
    body: JSON.stringify({ password })
  })
}

export function fetchCityConfigs(token: string) {
  return request<ListResponse<CityConfig>>('/api/v1/cities/admin/configs', token)
}

export function createCityConfig(token: string, payload: Omit<CityConfig, 'is_default' | 'config_version' | 'updated_at'>) {
  return request<CityConfig>('/api/v1/cities/admin/configs', token, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export function updateCityConfig(token: string, cityCode: string, payload: Partial<CityConfig>) {
  return request<CityConfig>(`/api/v1/cities/admin/configs/${cityCode}`, token, {
    method: 'PATCH',
    body: JSON.stringify(payload)
  })
}

export function fetchVehicles(token: string) {
  return request<ListResponse<VehicleDetail>>('/api/v1/vehicles/admin/items', token)
}

export function fetchVehicleModels(token: string) {
  return request<ListResponse<VehicleModel>>('/api/v1/vehicles/admin/models', token)
}

export function createVehicleModel(token: string, payload: Omit<VehicleModel, 'model_id'>) {
  return request<VehicleModel>('/api/v1/vehicles/admin/models', token, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export function updateVehicleModel(token: string, modelId: string, payload: Partial<Omit<VehicleModel, 'model_id'>>) {
  return request<VehicleModel>(`/api/v1/vehicles/admin/models/${modelId}`, token, {
    method: 'PATCH',
    body: JSON.stringify(payload)
  })
}

export function deleteVehicleModel(token: string, modelId: string) {
  return request<void>(`/api/v1/vehicles/admin/models/${modelId}`, token, { method: 'DELETE' })
}

export type VehicleWritePayload = {
  city_code: string
  model_id: string
  plate_mask: string
  color: string
  mileage_km: number
  daily_mileage_limit: number
  image_url: string
  source: VehicleDetail['source']
  dealer_id?: string | null
  hosted_owner?: string | null
  review_status?: VehicleDetail['review_status']
  listing_status?: VehicleDetail['listing_status']
}

export function createVehicle(token: string, payload: VehicleWritePayload) {
  return request<VehicleDetail>('/api/v1/vehicles/admin/items', token, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export function updateVehicle(token: string, vehicleId: string, payload: Partial<VehicleWritePayload>) {
  return request<VehicleDetail>(`/api/v1/vehicles/admin/items/${vehicleId}`, token, {
    method: 'PATCH',
    body: JSON.stringify(payload)
  })
}

export function deleteVehicle(token: string, vehicleId: string) {
  return request<void>(`/api/v1/vehicles/admin/items/${vehicleId}`, token, { method: 'DELETE' })
}

export function updateVehicleStatus(
  token: string,
  vehicleId: string,
  payload: Partial<Pick<VehicleDetail, 'review_status' | 'listing_status' | 'maintenance' | 'manually_locked'>>
) {
  return request<VehicleDetail>(`/api/v1/vehicles/admin/items/${vehicleId}/status`, token, {
    method: 'PATCH',
    body: JSON.stringify(payload)
  })
}

export function fetchVehiclePrices(token: string, vehicleId: string) {
  return request<ListResponse<PriceCalendarEntry>>(`/api/v1/vehicles/admin/items/${vehicleId}/prices`, token)
}

export function upsertVehiclePrice(
  token: string,
  vehicleId: string,
  payload: Omit<PriceCalendarEntry, 'vehicle_id' | 'updated_at'>
) {
  return request<PriceCalendarEntry>(`/api/v1/vehicles/admin/items/${vehicleId}/prices`, token, {
    method: 'PUT',
    body: JSON.stringify(payload)
  })
}

export function upsertVehiclePricesBatch(
  token: string,
  vehicleId: string,
  payload: {
    start_date: string
    days: number
    base_price: number
    customer_price: number
    wholesale_price: number
    rentable: boolean
    available_periods: string[]
  }
) {
  return request<ListResponse<PriceCalendarEntry>>(`/api/v1/vehicles/admin/items/${vehicleId}/prices/batch`, token, {
    method: 'PUT',
    body: JSON.stringify(payload)
  })
}

export function fetchIdentitySubmissions(token: string) {
  return request<ListResponse<IdentitySubmission>>('/api/v1/identity/admin/submissions', token)
}

export function fetchIdentitySubmissionDetail(token: string, submissionId: string) {
  return request<IdentityAdminDetail>(`/api/v1/identity/admin/submissions/${submissionId}`, token)
}

export function authorizeIdentityPreview(token: string, submissionId: string, reason: string) {
  return request<IdentitySubmission>(`/api/v1/identity/admin/submissions/${submissionId}/authorize-preview`, token, {
    method: 'POST',
    body: JSON.stringify({ reason })
  })
}

export function reviewIdentitySubmission(
  token: string,
  submissionId: string,
  payload: { status: 'approved' | 'rejected'; reject_reason?: string }
) {
  return request<IdentitySubmission>(`/api/v1/identity/admin/submissions/${submissionId}/review`, token, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export function fetchCustomerOrders(token: string, status?: string) {
  const query = status ? `?status=${encodeURIComponent(status)}` : ''
  return request<ListResponse<CustomerOrder>>(`/api/v1/orders/admin/customer-orders${query}`, token)
}

export function acceptCustomerOrder(token: string, orderId: string, remark: string) {
  return request<CustomerOrder>(`/api/v1/orders/admin/customer-orders/${orderId}/accept`, token, {
    method: 'POST',
    headers: { 'Idempotency-Key': `admin-accept-${orderId}` },
    body: JSON.stringify({ remark })
  })
}

export function returnCustomerOrder(token: string, orderId: string, reason: string) {
  return request<CustomerOrder>(`/api/v1/orders/admin/customer-orders/${orderId}/return`, token, {
    method: 'POST',
    headers: { 'Idempotency-Key': `admin-return-${orderId}` },
    body: JSON.stringify({ reason })
  })
}

export function reassignCustomerOrder(token: string, orderId: string, targetVehicleId: string, remark: string) {
  return request<CustomerOrder>(`/api/v1/orders/admin/customer-orders/${orderId}/reassign`, token, {
    method: 'POST',
    headers: { 'Idempotency-Key': `admin-reassign-${orderId}-${targetVehicleId}` },
    body: JSON.stringify({ target_vehicle_id: targetVehicleId, remark })
  })
}

export function fetchWholesaleOrders(token: string, status?: string) {
  const query = status ? `?status=${encodeURIComponent(status)}` : ''
  return request<ListResponse<WholesaleOrder>>(`/api/v1/wholesale-orders${query}`, token)
}

export function createRelatedWholesaleOrder(token: string, customerOrderId: string, remark: string) {
  return request<WholesaleOrder>('/api/v1/wholesale-orders/admin/related', token, {
    method: 'POST',
    headers: { 'Idempotency-Key': `admin-create-wholesale-${customerOrderId}` },
    body: JSON.stringify({ customer_order_id: customerOrderId, remark })
  })
}

export function acceptWholesaleOrder(token: string, wholesaleOrderId: string, remark: string) {
  return request<WholesaleOrder>(`/api/v1/wholesale-orders/${wholesaleOrderId}/accept`, token, {
    method: 'POST',
    headers: { 'Idempotency-Key': `admin-accept-wholesale-${wholesaleOrderId}` },
    body: JSON.stringify({ remark })
  })
}

export function rejectWholesaleOrder(token: string, wholesaleOrderId: string, reason: string) {
  return request<WholesaleOrder>(`/api/v1/wholesale-orders/${wholesaleOrderId}/reject`, token, {
    method: 'POST',
    headers: { 'Idempotency-Key': `admin-reject-wholesale-${wholesaleOrderId}` },
    body: JSON.stringify({ reason })
  })
}

export function changeWholesaleOrderPrice(token: string, wholesaleOrderId: string, wholesalePrice: number, reason: string) {
  return request<WholesaleOrder>(`/api/v1/wholesale-orders/${wholesaleOrderId}/change-price`, token, {
    method: 'POST',
    headers: { 'Idempotency-Key': `admin-change-wholesale-price-${wholesaleOrderId}-${wholesalePrice}` },
    body: JSON.stringify({ wholesale_price: wholesalePrice, reason })
  })
}

export function expirePendingWholesaleOrders(token: string) {
  return request<{ expired_wholesale_order_ids: string[]; total: number }>(
    '/api/v1/wholesale-orders/admin/expire-pending?minutes_after_sla=1',
    token,
    { method: 'POST' }
  )
}
