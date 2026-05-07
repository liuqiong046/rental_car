<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Organization } from '../../api/admin'
import { ORGANIZATION_TYPE_OPTIONS } from './permissionOptions'

const props = defineProps<{
  organizations: Organization[]
  onCreate: (payload: Pick<Organization, 'name' | 'type' | 'parent_id' | 'city_code'>) => Promise<void>
  onSave: (payload: Pick<Organization, 'id' | 'name' | 'parent_id' | 'city_code' | 'status'>) => Promise<void>
}>()

const draft = ref({
  name: '',
  type: 'operation_center',
  parent_id: '',
  city_code: 'SY'
})
const items = ref<Organization[]>([])

watch(
  () => props.organizations,
  (value) => {
    items.value = value.map((item) => ({ ...item }))
  },
  { immediate: true }
)

const parentOptions = computed(() =>
  items.value.map((item) => ({
    label: `${item.name} (${item.id})`,
    value: item.id
  }))
)
const typeLabelMap = Object.fromEntries(ORGANIZATION_TYPE_OPTIONS.map((item) => [item.value, item.label]))

async function submit() {
  await props.onCreate({
    name: draft.value.name.trim(),
    type: draft.value.type,
    parent_id: draft.value.parent_id || null,
    city_code: draft.value.city_code.trim() || null
  })
  draft.value = {
    name: '',
    type: 'operation_center',
    parent_id: '',
    city_code: draft.value.city_code
  }
}

async function save(item: Organization) {
  await props.onSave({
    id: item.id,
    name: item.name.trim(),
    parent_id: item.parent_id || null,
    city_code: item.city_code?.trim() || null,
    status: item.status
  })
}
</script>

<template>
  <section class="admin-panel-stack">
    <article class="admin-panel-card">
      <div class="admin-panel-card__header">
        <div>
          <h3>新增组织</h3>
          <p>组织用于承载总部、运营中心、车行和岗位的归属与数据边界。</p>
        </div>
      </div>
      <div class="admin-form-grid">
        <el-input v-model="draft.name" placeholder="组织名称" />
        <el-select v-model="draft.type" placeholder="组织类型">
          <el-option
            v-for="option in ORGANIZATION_TYPE_OPTIONS"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
        <el-select v-model="draft.parent_id" clearable filterable placeholder="上级组织">
          <el-option v-for="option in parentOptions" :key="option.value" :label="option.label" :value="option.value" />
        </el-select>
        <el-input v-model="draft.city_code" placeholder="城市编码，例如 SY" />
      </div>
      <div class="admin-panel-card__footer">
        <el-button type="primary" @click="submit">新增组织</el-button>
      </div>
    </article>

    <div class="admin-entity-grid">
      <article v-for="item in items" :key="item.id" class="admin-entity-card">
        <div class="admin-entity-card__header">
          <div>
            <strong>{{ item.name }}</strong>
            <p class="admin-entity-card__meta">{{ typeLabelMap[item.type] || item.type }} · {{ item.id }}</p>
          </div>
          <el-tag :type="item.status === 'active' ? 'success' : 'info'">
            {{ item.status === 'active' ? '启用' : '停用' }}
          </el-tag>
        </div>
        <div class="admin-form-grid admin-form-grid--compact">
          <el-input v-model="item.name" placeholder="组织名称" />
          <el-select v-model="item.type" placeholder="组织类型">
            <el-option
              v-for="option in ORGANIZATION_TYPE_OPTIONS"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <el-select v-model="item.parent_id" clearable filterable placeholder="上级组织">
            <el-option v-for="option in parentOptions" :key="option.value" :label="option.label" :value="option.value" />
          </el-select>
          <el-input v-model="item.city_code" placeholder="城市编码" />
          <el-select v-model="item.status" placeholder="状态">
            <el-option label="启用" value="active" />
            <el-option label="停用" value="disabled" />
          </el-select>
        </div>
        <div class="admin-panel-card__footer">
          <el-button @click="save(item)">保存组织</el-button>
        </div>
      </article>
    </div>
  </section>
</template>
