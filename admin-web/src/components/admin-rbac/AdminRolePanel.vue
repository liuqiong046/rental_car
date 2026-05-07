<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { AdminRole, DataScope, Organization } from '../../api/admin'
import {
  ROLE_BUTTON_OPTIONS,
  ROLE_MENU_OPTIONS,
  cloneDataScope,
  formatDataScope,
  uniqueValues
} from './permissionOptions'

type RoleEditor = {
  code: string
  name: string
  menus: string[]
  buttons: string[]
  extraMenus: string[]
  extraButtons: string[]
  dataScope: DataScope
}

const props = defineProps<{
  roles: AdminRole[]
  organizations: Organization[]
  accountCounts: Record<string, number>
  onCreate: (payload: {
    code: string
    name: string
    menus: string[]
    buttons: string[]
    data_scope: DataScope
  }) => Promise<void>
  onSave: (payload: {
    id: string
    name: string
    menus: string[]
    buttons: string[]
    data_scope: DataScope
  }) => Promise<void>
}>()

const selectedRoleId = ref('')
const items = ref<AdminRole[]>([])
const permissionLabels = new Map(
  [...ROLE_MENU_OPTIONS, ...ROLE_BUTTON_OPTIONS].map((item) => [item.value, item.label])
)
const draft = ref(createEmptyRole())

watch(
  () => props.roles,
  (value) => {
    items.value = value.map(cloneRole)
    if (selectedRoleId.value) {
      const current = items.value.find((item) => item.id === selectedRoleId.value)
      if (current) {
        draft.value = toRoleEditor(current)
        return
      }
    }
    if (items.value[0]) {
      selectRole(items.value[0].id)
    } else {
      startCreate()
    }
  },
  { immediate: true }
)

const isCreateMode = computed(() => !selectedRoleId.value)
const roleCards = computed(() =>
  items.value.map((item) => ({
    ...item,
    count: props.accountCounts[item.id] || 0,
    preview: [...item.menus, ...item.buttons].slice(0, 4).map((permission) => permissionLabels.get(permission) || permission)
  }))
)

function createEmptyRole(): RoleEditor {
  return {
    code: '',
    name: '',
    menus: [],
    buttons: [],
    extraMenus: [],
    extraButtons: [],
    dataScope: {
      type: 'organization',
      organization_id: props.organizations[0]?.id || null
    }
  }
}

function cloneRole(role: AdminRole): AdminRole {
  return {
    ...role,
    menus: [...role.menus],
    buttons: [...role.buttons],
    data_scope: cloneDataScope(role.data_scope)
  }
}

function toRoleEditor(role: AdminRole): RoleEditor {
  const knownMenus = new Set(ROLE_MENU_OPTIONS.map((item) => item.value))
  const knownButtons = new Set(ROLE_BUTTON_OPTIONS.map((item) => item.value))
  return {
    code: role.code,
    name: role.name,
    menus: role.menus.filter((item) => knownMenus.has(item)),
    buttons: role.buttons.filter((item) => knownButtons.has(item)),
    extraMenus: role.menus.filter((item) => !knownMenus.has(item)),
    extraButtons: role.buttons.filter((item) => !knownButtons.has(item)),
    dataScope: cloneDataScope(role.data_scope)
  }
}

function selectRole(roleId: string) {
  const target = items.value.find((item) => item.id === roleId)
  if (!target) return
  selectedRoleId.value = roleId
  draft.value = toRoleEditor(target)
}

function startCreate() {
  selectedRoleId.value = ''
  draft.value = createEmptyRole()
}

function normalizeDataScope(scope: DataScope): DataScope {
  if (scope.type === 'all') return { type: 'all' }
  if (scope.type === 'city') {
    return { type: 'city', city_code: scope.city_code?.trim() || '' }
  }
  return {
    type: 'organization',
    organization_id: scope.organization_id || props.organizations[0]?.id || null
  }
}

async function submit() {
  if (!draft.value.code.trim() && isCreateMode.value) {
    ElMessage.warning('请先填写岗位编码')
    return
  }
  if (!draft.value.name.trim()) {
    ElMessage.warning('请先填写岗位名称')
    return
  }
  const dataScope = normalizeDataScope(draft.value.dataScope)
  const payload = {
    code: draft.value.code.trim(),
    name: draft.value.name.trim(),
    menus: uniqueValues([...draft.value.menus, ...draft.value.extraMenus]),
    buttons: uniqueValues([...draft.value.buttons, ...draft.value.extraButtons]),
    data_scope: dataScope
  }
  if (selectedRoleId.value) {
    await props.onSave({ ...payload, id: selectedRoleId.value })
    return
  }
  await props.onCreate(payload)
  startCreate()
}
</script>

<template>
  <section class="role-layout">
    <article class="admin-panel-card role-panel">
      <div class="admin-panel-card__header">
        <div>
          <h3>岗位列表</h3>
          <p>从员工权限原型收敛为可维护的岗位卡片，点击卡片切换编辑对象。</p>
        </div>
        <el-button plain @click="startCreate">新建岗位</el-button>
      </div>
      <div class="role-list">
        <button
          v-for="item in roleCards"
          :key="item.id"
          class="role-tile"
          :class="{ 'is-active': selectedRoleId === item.id }"
          type="button"
          @click="selectRole(item.id)"
        >
          <div class="role-tile__header">
            <strong>{{ item.name }}</strong>
            <span>{{ item.count }} 人</span>
          </div>
          <p>{{ item.code }}</p>
          <p>{{ formatDataScope(item.data_scope, props.organizations) }}</p>
          <div class="admin-preview-tags">
            <span v-for="tag in item.preview" :key="tag" class="admin-preview-tag">{{ tag }}</span>
          </div>
        </button>
      </div>
    </article>

    <article class="admin-panel-card role-panel">
      <div class="admin-panel-card__header">
        <div>
          <h3>{{ isCreateMode ? '新增岗位' : '编辑岗位' }}</h3>
          <p>保留 `WF-P0-03` 范围内的菜单、按钮和基础数据范围。</p>
        </div>
        <el-tag :type="isCreateMode ? 'warning' : 'success'">
          {{ isCreateMode ? '新增模式' : '编辑模式' }}
        </el-tag>
      </div>

      <div class="admin-form-grid">
        <el-input v-model="draft.code" :disabled="!isCreateMode" placeholder="岗位编码，例如 ops_admin" />
        <el-input v-model="draft.name" placeholder="岗位名称" />
        <el-select v-model="draft.dataScope.type" placeholder="数据范围">
          <el-option label="全平台" value="all" />
          <el-option label="城市" value="city" />
          <el-option label="组织" value="organization" />
        </el-select>
        <el-input
          v-if="draft.dataScope.type === 'city'"
          v-model="draft.dataScope.city_code"
          placeholder="城市编码，例如 SY"
        />
        <el-select
          v-else-if="draft.dataScope.type === 'organization'"
          v-model="draft.dataScope.organization_id"
          filterable
          placeholder="选择组织"
        >
          <el-option v-for="item in props.organizations" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </div>

      <div class="role-permission-grid">
        <section class="role-permission-group">
          <h4>菜单权限</h4>
          <el-checkbox-group v-model="draft.menus" class="role-checkbox-list">
            <el-checkbox v-for="item in ROLE_MENU_OPTIONS" :key="item.value" :label="item.value">
              {{ item.label }}
            </el-checkbox>
          </el-checkbox-group>
        </section>
        <section class="role-permission-group">
          <h4>按钮权限</h4>
          <el-checkbox-group v-model="draft.buttons" class="role-checkbox-list">
            <el-checkbox v-for="item in ROLE_BUTTON_OPTIONS" :key="item.value" :label="item.value">
              {{ item.label }}
            </el-checkbox>
          </el-checkbox-group>
        </section>
      </div>

      <div v-if="draft.extraMenus.length || draft.extraButtons.length" class="admin-note">
        为避免丢失其他任务已写入的权限，未在 `WF-P0-03` 预设列表中的权限会按原值保留：
        {{ [...draft.extraMenus, ...draft.extraButtons].join('、') }}
      </div>

      <div class="admin-panel-card__footer">
        <el-button @click="startCreate">清空表单</el-button>
        <el-button type="primary" @click="submit">{{ isCreateMode ? '新增岗位' : '保存岗位' }}</el-button>
      </div>
    </article>
  </section>
</template>
