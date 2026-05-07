<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createAccount,
  createOrganization,
  createRole,
  fetchAccounts,
  fetchOrganizations,
  fetchRoles,
  resetAccountPassword,
  updateAccount,
  updateAccountStatus,
  updateOrganization,
  updateRole,
  type AdminActor,
  type AdminRole,
  type DataScope,
  type Organization
} from '../api/admin'
import AdminAccountPanel from '../components/admin-rbac/AdminAccountPanel.vue'
import AdminOrganizationPanel from '../components/admin-rbac/AdminOrganizationPanel.vue'
import AdminRolePanel from '../components/admin-rbac/AdminRolePanel.vue'
import { formatDataScope } from '../components/admin-rbac/permissionOptions'
import { useSessionStore } from '../stores/session'
type SectionKey = 'roles' | 'accounts' | 'organizations'
const router = useRouter()
const session = useSessionStore()
const activeSection = ref<SectionKey>('roles')
const loading = ref(false)
const organizations = ref<Organization[]>([])
const roles = ref<AdminRole[]>([])
const accounts = ref<AdminActor[]>([])
const scopeText = computed(() =>
  session.actor ? formatDataScope(session.actor.role.data_scope, organizations.value) : '未登录'
)
const roleAccountCounts = computed(() =>
  accounts.value.reduce<Record<string, number>>((result, item) => {
    result[item.role.id] = (result[item.role.id] || 0) + 1
    return result
  }, {})
)
const summaryCards = computed(() => [
  {
    key: 'roles' as SectionKey,
    label: '岗位权限',
    value: roles.value.length,
    description: '维护菜单、按钮与数据范围'
  },
  {
    key: 'accounts' as SectionKey,
    label: '员工账号',
    value: accounts.value.length,
    description: `启用 ${accounts.value.filter((item) => item.status === 'active').length} / 锁定 ${
      accounts.value.filter((item) => item.status === 'locked').length
    }`
  },
  {
    key: 'organizations' as SectionKey,
    label: '组织架构',
    value: organizations.value.length,
    description: '总部、运营中心、车行与岗位归属'
  }
])
const sectionTitle = computed(() => {
  if (activeSection.value === 'accounts') return '员工账号'
  if (activeSection.value === 'organizations') return '组织架构'
  return '岗位权限'
})
const sectionDescription = computed(() => {
  if (activeSection.value === 'accounts') {
    return '账号、岗位与所属组织在同一处维护，停用账号不可登录。'
  }
  if (activeSection.value === 'organizations') {
    return '组织用于承载总部、运营中心、车行和岗位的数据边界。'
  }
  return '岗位统一维护菜单、按钮和基础数据范围，供后续模块直接复用。'
})
async function loadData() {
  if (!session.token) return
  loading.value = true
  try {
    const [organizationResponse, roleResponse, accountResponse] = await Promise.all([
      fetchOrganizations(session.token),
      fetchRoles(session.token),
      fetchAccounts(session.token)
    ])
    organizations.value = organizationResponse.items
    roles.value = roleResponse.items
    accounts.value = accountResponse.items
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载后台权限数据失败')
  } finally {
    loading.value = false
  }
}
async function runAdminAction(action: () => Promise<void>, successMessage: string, reload = true) {
  try {
    await action()
    if (reload) {
      await loadData()
    }
    ElMessage.success(successMessage)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '后台权限操作失败')
    throw error
  }
}
async function handleCreateOrganization(payload: Pick<Organization, 'name' | 'type' | 'parent_id' | 'city_code'>) {
  if (!session.token) return
  await runAdminAction(async () => {
    await createOrganization(session.token, payload)
  }, '组织已新增')
}
async function handleSaveOrganization(
  payload: Pick<Organization, 'id' | 'name' | 'parent_id' | 'city_code' | 'status'>
) {
  if (!session.token) return
  await runAdminAction(async () => {
    await updateOrganization(session.token, payload.id, payload)
  }, '组织已保存')
}
async function handleCreateRole(payload: {
  code: string
  name: string
  menus: string[]
  buttons: string[]
  data_scope: DataScope
}) {
  if (!session.token) return
  await runAdminAction(async () => {
    await createRole(session.token, payload)
  }, '岗位已新增')
}
async function handleSaveRole(payload: {
  id: string
  name: string
  menus: string[]
  buttons: string[]
  data_scope: DataScope
}) {
  if (!session.token) return
  await runAdminAction(async () => {
    await updateRole(session.token, payload.id, payload)
  }, '岗位已保存')
}
async function handleCreateAccount(payload: {
  username: string
  display_name: string
  password: string
  organization_id: string
  role_id: string
}) {
  if (!session.token) return
  await runAdminAction(async () => {
    await createAccount(session.token, payload)
  }, '账号已新增')
}
async function handleSaveAccount(payload: {
  account_id: string
  display_name: string
  organization_id: string
  role_id: string
}) {
  if (!session.token) return
  await runAdminAction(async () => {
    await updateAccount(session.token, payload.account_id, payload)
  }, '账号已保存')
}
async function handleToggleAccountStatus(account: AdminActor) {
  if (!session.token) return
  const nextStatus = account.status === 'active' ? 'disabled' : 'active'
  await runAdminAction(async () => {
    await updateAccountStatus(session.token, account.account_id, nextStatus)
  }, nextStatus === 'active' ? '账号已启用' : '账号已停用')
}
async function handleLockAccount(account: AdminActor) {
  if (!session.token) return
  await runAdminAction(async () => {
    await updateAccountStatus(session.token, account.account_id, 'locked')
  }, '账号已锁定')
}
async function handleResetPassword(account: AdminActor) {
  if (!session.token) return
  const result = await ElMessageBox.prompt('请输入新密码', `重置 ${account.display_name} 的密码`, {
    inputValue: `${account.username}123456`,
    inputPattern: /^.{6,64}$/,
    inputErrorMessage: '密码长度需为 6-64 位'
  })
  await runAdminAction(async () => {
    await resetAccountPassword(session.token, account.account_id, result.value)
  }, '密码已重置', false)
}
async function logout() {
  session.clearSession()
  await router.push({ name: 'login' })
}
onMounted(() => void loadData())
</script>
<template>
  <main class="rbac-shell" v-loading="loading">
    <section class="rbac-hero">
      <div class="rbac-hero__copy">
        <p class="rbac-hero__eyebrow">WF-P0-03 · 权限中台</p>
        <h1>PC 后台登录、组织、账号与权限</h1>
        <p class="rbac-hero__summary">
          当前页面只保留组织、岗位和账号权限，不扩展到城市、车辆、订单、财务和日志模块。
        </p>
        <div class="rbac-hero__meta">
          <span>{{ session.actor?.display_name }}</span>
          <span>{{ session.actor?.organization.name }}</span>
          <span>{{ scopeText }}</span>
        </div>
      </div>
      <div class="rbac-hero__aside">
        <div class="rbac-highlight">
          <strong>服务端权限校验</strong>
          <p>未登录跳转、停用阻断与数据范围隔离以服务端结果为准。</p>
        </div>
        <el-button class="rbac-hero__logout" plain @click="logout">退出登录</el-button>
      </div>
    </section>
    <section class="rbac-summary">
      <button
        v-for="card in summaryCards"
        :key="card.key"
        class="rbac-summary__card"
        :class="{ 'is-active': activeSection === card.key }"
        type="button"
        @click="activeSection = card.key"
      >
        <span class="rbac-summary__label">{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <p>{{ card.description }}</p>
      </button>
    </section>
    <section class="rbac-guides">
      <article class="rbac-guide">
        <span>当前账号</span>
        <strong>{{ session.actor?.role.name }}</strong>
        <p>{{ scopeText }}</p>
      </article>
      <article class="rbac-guide">
        <span>原型来源</span>
        <strong>admin/pages</strong>
        <p>`lanhu_tianjiayuangong`、`lanhu_tianjiagangwei`、`lanhu_gangweiyuangong`、`staff_permission`</p>
      </article>
      <article class="rbac-guide">
        <span>任务边界</span>
        <strong>只做 WF-P0-03</strong>
        <p>后续业务模块入口将在对应 WF 任务完成后再挂回后台导航。</p>
      </article>
    </section>
    <section class="rbac-content">
      <header class="rbac-content__header">
        <div>
          <p class="rbac-content__eyebrow">页面收敛</p>
          <h2>{{ sectionTitle }}</h2>
        </div>
        <p class="rbac-content__summary">{{ sectionDescription }}</p>
      </header>
      <!-- TODO(WF-P0-05/WF-P0-07/WF-P0-11/WF-P0-12): 后续任务完成后，再把业务模块入口重新挂回后台导航。 -->
      <AdminRolePanel
        v-if="activeSection === 'roles'"
        :roles="roles"
        :organizations="organizations"
        :account-counts="roleAccountCounts"
        :on-create="handleCreateRole"
        :on-save="handleSaveRole"
      />
      <AdminAccountPanel
        v-else-if="activeSection === 'accounts'"
        :accounts="accounts"
        :organizations="organizations"
        :roles="roles"
        :on-create="handleCreateAccount"
        :on-save="handleSaveAccount"
        :on-toggle-status="handleToggleAccountStatus"
        :on-lock="handleLockAccount"
        :on-reset-password="handleResetPassword"
      />
      <AdminOrganizationPanel
        v-else
        :organizations="organizations"
        :on-create="handleCreateOrganization"
        :on-save="handleSaveOrganization"
      />
    </section>
  </main>
</template>
