<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { AdminActor, AdminRole, Organization } from '../../api/admin'

const props = defineProps<{
  accounts: AdminActor[]
  organizations: Organization[]
  roles: AdminRole[]
  onCreate: (payload: {
    username: string
    display_name: string
    password: string
    organization_id: string
    role_id: string
  }) => Promise<void>
  onSave: (payload: {
    account_id: string
    display_name: string
    organization_id: string
    role_id: string
  }) => Promise<void>
  onToggleStatus: (account: AdminActor) => Promise<void>
  onLock: (account: AdminActor) => Promise<void>
  onResetPassword: (account: AdminActor) => Promise<void>
}>()

const draft = ref({
  username: '',
  display_name: '',
  password: '',
  organization_id: '',
  role_id: ''
})
const keyword = ref('')
const items = ref<AdminActor[]>([])

watch(
  () => props.accounts,
  (value) => {
    items.value = value.map((item) => ({
      ...item,
      organization: { ...item.organization },
      role: {
        ...item.role,
        menus: [...item.role.menus],
        buttons: [...item.role.buttons],
        data_scope: { ...item.role.data_scope }
      }
    }))
  },
  { immediate: true }
)

const organizationOptions = computed(() =>
  props.organizations.map((item) => ({
    label: item.name,
    value: item.id
  }))
)
const roleOptions = computed(() =>
  props.roles.map((item) => ({
    label: item.name,
    value: item.id
  }))
)
const filteredAccounts = computed(() => {
  const value = keyword.value.trim().toLowerCase()
  if (!value) return items.value
  return items.value.filter((item) => {
    const target = [
      item.username,
      item.display_name,
      item.organization.name,
      item.role.name
    ]
      .join(' ')
      .toLowerCase()
    return target.includes(value)
  })
})

async function submit() {
  await props.onCreate({
    username: draft.value.username.trim(),
    display_name: draft.value.display_name.trim(),
    password: draft.value.password,
    organization_id: draft.value.organization_id,
    role_id: draft.value.role_id
  })
  draft.value = {
    username: '',
    display_name: '',
    password: '',
    organization_id: draft.value.organization_id,
    role_id: draft.value.role_id
  }
}

async function save(item: AdminActor) {
  await props.onSave({
    account_id: item.account_id,
    display_name: item.display_name.trim(),
    organization_id: item.organization.id,
    role_id: item.role.id
  })
}
</script>

<template>
  <section class="admin-panel-stack">
    <article class="admin-panel-card">
      <div class="admin-panel-card__header">
        <div>
          <h3>新增账号</h3>
          <p>账号、所属组织和岗位绑定后即可登录后台。</p>
        </div>
        <el-tag type="warning">停用账号不可登录</el-tag>
      </div>
      <div class="admin-form-grid">
        <el-input v-model="draft.display_name" placeholder="员工姓名" />
        <el-input v-model="draft.username" placeholder="登录账号" />
        <el-input v-model="draft.password" placeholder="初始密码" show-password />
        <el-select v-model="draft.organization_id" placeholder="所属组织">
          <el-option v-for="option in organizationOptions" :key="option.value" :label="option.label" :value="option.value" />
        </el-select>
        <el-select v-model="draft.role_id" placeholder="岗位">
          <el-option v-for="option in roleOptions" :key="option.value" :label="option.label" :value="option.value" />
        </el-select>
      </div>
      <p class="admin-note">
        当前后台接口按账号密码登录落地，原型中的手机号默认密码提示只作为版式参考，不覆盖现有契约。
      </p>
      <div class="admin-panel-card__footer">
        <el-button type="primary" @click="submit">新增账号</el-button>
      </div>
    </article>

    <article class="admin-panel-card">
      <div class="admin-panel-card__header">
        <div>
          <h3>账号列表</h3>
          <p>可按姓名、账号、组织或岗位搜索并直接保存。</p>
        </div>
        <el-input v-model="keyword" clearable placeholder="搜索账号 / 姓名 / 组织 / 岗位" />
      </div>
      <div class="admin-entity-grid">
        <article v-for="item in filteredAccounts" :key="item.account_id" class="admin-entity-card">
          <div class="admin-entity-card__header">
            <div>
              <strong>{{ item.display_name }}</strong>
              <p class="admin-entity-card__meta">{{ item.username }}</p>
            </div>
            <el-tag :type="item.status === 'active' ? 'success' : item.status === 'locked' ? 'warning' : 'info'">
              {{ item.status === 'active' ? '启用' : item.status === 'locked' ? '锁定' : '停用' }}
            </el-tag>
          </div>
          <div class="admin-form-grid admin-form-grid--compact">
            <el-input v-model="item.display_name" placeholder="员工姓名" />
            <el-select v-model="item.organization.id" placeholder="所属组织">
              <el-option v-for="option in organizationOptions" :key="option.value" :label="option.label" :value="option.value" />
            </el-select>
            <el-select v-model="item.role.id" placeholder="岗位">
              <el-option v-for="option in roleOptions" :key="option.value" :label="option.label" :value="option.value" />
            </el-select>
          </div>
          <div class="admin-inline-actions">
            <el-button @click="save(item)">保存账号</el-button>
            <el-button @click="props.onToggleStatus(item)">
              {{ item.status === 'active' ? '停用账号' : '启用账号' }}
            </el-button>
            <el-button :disabled="item.status === 'locked'" @click="props.onLock(item)">锁定账号</el-button>
            <el-button @click="props.onResetPassword(item)">重置密码</el-button>
          </div>
        </article>
      </div>
    </article>
  </section>
</template>
