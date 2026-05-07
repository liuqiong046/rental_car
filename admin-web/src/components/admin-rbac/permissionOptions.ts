import type { DataScope, Organization } from '../../api/admin'

export const ORGANIZATION_TYPE_OPTIONS = [
  { label: '总部', value: 'headquarters' },
  { label: '运营中心', value: 'operation_center' },
  { label: '车行', value: 'dealer' },
  { label: '部门', value: 'department' },
  { label: '岗位', value: 'position' }
]

export const ROLE_MENU_OPTIONS = [
  { label: '工作台', value: 'dashboard' },
  { label: '组织管理', value: 'organizations' },
  { label: '员工账号', value: 'accounts' },
  { label: '岗位权限', value: 'roles' }
]

export const ROLE_BUTTON_OPTIONS = [
  { label: '新增组织', value: 'organization:create' },
  { label: '编辑组织', value: 'organization:update' },
  { label: '新增岗位', value: 'role:create' },
  { label: '编辑岗位', value: 'role:update' },
  { label: '新增账号', value: 'account:create' },
  { label: '编辑账号', value: 'account:update' },
  { label: '启停与锁定账号', value: 'account:status' },
  { label: '重置密码', value: 'account:reset-password' }
]

export function cloneDataScope(scope: DataScope): DataScope {
  return {
    type: scope.type,
    city_code: scope.city_code ?? null,
    organization_id: scope.organization_id ?? null
  }
}

export function uniqueValues(values: string[]) {
  return Array.from(new Set(values.filter(Boolean)))
}

export function getOrganizationName(organizations: Organization[], organizationId?: string | null) {
  if (!organizationId) return '未绑定组织'
  return organizations.find((item) => item.id === organizationId)?.name || organizationId
}

export function formatDataScope(scope: DataScope, organizations: Organization[]) {
  if (scope.type === 'all') return '全平台'
  if (scope.type === 'city') return `城市 ${scope.city_code || '-'}`
  return `组织 ${getOrganizationName(organizations, scope.organization_id)}`
}
