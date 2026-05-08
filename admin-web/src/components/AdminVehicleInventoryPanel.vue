<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  createVehicle,
  createVehicleModel,
  deleteVehicle,
  deleteVehicleModel,
  fetchVehicleModels,
  fetchVehiclePrices,
  fetchVehicles,
  updateVehicle,
  updateVehicleModel,
  updateVehicleStatus,
  upsertVehiclePrice,
  upsertVehiclePricesBatch,
  type PriceCalendarEntry,
  type VehicleDetail,
  type VehicleModel,
  type VehicleWritePayload
} from '../api/admin'

const props = defineProps<{
  token: string
}>()

type VehicleSource = VehicleDetail['source']

type ModelForm = Omit<VehicleModel, 'model_id'>
type VehicleForm = VehicleWritePayload
type PriceForm = Omit<PriceCalendarEntry, 'vehicle_id' | 'updated_at'>
type BatchPriceForm = PriceForm & {
  start_date: string
  days: number
}

const modelDefaults: ModelForm = {
  brand: '小米',
  series: 'SU7',
  model_name: '小米汽车 SU7',
  year: new Date().getFullYear(),
  vehicle_type: '轿车',
  energy_type: '纯电动',
  seats: 5,
  gearbox: '自动挡',
  min_base_price: 160,
  deposit_amount: 8000,
  violation_deposit_amount: 3000
}

const vehicleDefaults: VehicleForm = {
  city_code: 'SY',
  model_id: '',
  plate_mask: '琼 B •••• 00',
  color: '海湾蓝',
  mileage_km: 0,
  daily_mileage_limit: 300,
  image_url: '/assets/car-blue.jpg',
  source: 'operation_owned',
  dealer_id: null,
  hosted_owner: null,
  review_status: 'pending',
  listing_status: 'unlisted'
}

const today = new Date().toISOString().slice(0, 10)

const priceDefaults: PriceForm = {
  date: today,
  base_price: 180,
  customer_price: 198,
  wholesale_price: 150,
  rentable: true,
  available_periods: ['00:00-24:00']
}

const batchDefaults: BatchPriceForm = {
  ...priceDefaults,
  start_date: today,
  days: 30
}

const loading = ref(false)
const models = ref<VehicleModel[]>([])
const vehicles = ref<VehicleDetail[]>([])
const prices = ref<PriceCalendarEntry[]>([])
const activeVehicleId = ref('')
const editingModelId = ref('')
const editingVehicleId = ref('')
const modelForm = reactive<ModelForm>({ ...modelDefaults })
const vehicleForm = reactive<VehicleForm>({ ...vehicleDefaults })
const priceForm = reactive<PriceForm>({ ...priceDefaults })
const batchForm = reactive<BatchPriceForm>({ ...batchDefaults })

const activeVehicle = computed(() => vehicles.value.find((item) => item.vehicle_id === activeVehicleId.value) || null)
const vehicleSourceOptions: Array<{ label: string; value: VehicleSource }> = [
  { label: '运营中心自有', value: 'operation_owned' },
  { label: '托管车辆', value: 'hosted' },
  { label: '车行车辆', value: 'dealer' }
]
const availabilitySummary = computed(() => {
  const available = vehicles.value.filter((item) => item.available).length
  const blocked = vehicles.value.length - available
  const noPrice = vehicles.value.filter((item) => item.unavailable_reason === '当前日期缺少可租价格').length
  return { available, blocked, noPrice }
})

function sourceLabel(source: VehicleSource) {
  return vehicleSourceOptions.find((item) => item.value === source)?.label || source
}

function resetModelForm() {
  editingModelId.value = ''
  Object.assign(modelForm, modelDefaults)
}

function resetVehicleForm() {
  editingVehicleId.value = ''
  Object.assign(vehicleForm, { ...vehicleDefaults, model_id: models.value[0]?.model_id || '' })
}

function resetPriceForms() {
  Object.assign(priceForm, priceDefaults)
  Object.assign(batchForm, batchDefaults)
}

function normalizeVehiclePayload(payload: VehicleForm): VehicleForm {
  return {
    ...payload,
    city_code: payload.city_code.toUpperCase(),
    dealer_id: payload.source === 'dealer' ? payload.dealer_id || null : null,
    hosted_owner: payload.source === 'hosted' ? payload.hosted_owner || null : null
  }
}

async function loadInventory() {
  loading.value = true
  try {
    const [modelResponse, vehicleResponse] = await Promise.all([
      fetchVehicleModels(props.token),
      fetchVehicles(props.token)
    ])
    models.value = modelResponse.items
    vehicles.value = vehicleResponse.items
    if (!vehicleForm.model_id && models.value[0]) {
      vehicleForm.model_id = models.value[0].model_id
    }
    if (!activeVehicleId.value && vehicles.value[0]) {
      activeVehicleId.value = vehicles.value[0].vehicle_id
    }
    await loadPrices()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载车辆库存失败')
  } finally {
    loading.value = false
  }
}

async function loadPrices() {
  if (!activeVehicleId.value) {
    prices.value = []
    return
  }
  const response = await fetchVehiclePrices(props.token, activeVehicleId.value)
  prices.value = response.items.sort((left, right) => left.date.localeCompare(right.date))
}

async function saveModel() {
  try {
    if (editingModelId.value) {
      await updateVehicleModel(props.token, editingModelId.value, { ...modelForm })
      ElMessage.success('车型已保存')
    } else {
      await createVehicleModel(props.token, { ...modelForm })
      ElMessage.success('车型已新增')
    }
    resetModelForm()
    await loadInventory()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '车型保存失败')
  }
}

function editModel(model: VehicleModel) {
  editingModelId.value = model.model_id
  Object.assign(modelForm, model)
}

async function removeModel(model: VehicleModel) {
  try {
    await ElMessageBox.confirm(`确认删除车型 ${model.model_name}？`, '删除车型', { type: 'warning' })
    await deleteVehicleModel(props.token, model.model_id)
    ElMessage.success('车型已删除')
    await loadInventory()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error instanceof Error ? error.message : '车型删除失败')
    }
  }
}

async function saveVehicle() {
  try {
    const payload = normalizeVehiclePayload(vehicleForm)
    if (editingVehicleId.value) {
      await updateVehicle(props.token, editingVehicleId.value, payload)
      ElMessage.success('车辆已保存')
    } else {
      await createVehicle(props.token, payload)
      ElMessage.success('车辆已新增')
    }
    resetVehicleForm()
    await loadInventory()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '车辆保存失败')
  }
}

function editVehicle(vehicle: VehicleDetail) {
  editingVehicleId.value = vehicle.vehicle_id
  Object.assign(vehicleForm, {
    city_code: vehicle.city_code,
    model_id: vehicle.model.model_id,
    plate_mask: vehicle.plate_mask,
    color: vehicle.color,
    mileage_km: vehicle.mileage_km,
    daily_mileage_limit: vehicle.daily_mileage_limit,
    image_url: vehicle.image_url,
    source: vehicle.source,
    dealer_id: vehicle.dealer_id || null,
    hosted_owner: vehicle.hosted_owner || null,
    review_status: vehicle.review_status,
    listing_status: vehicle.listing_status
  })
}

async function removeVehicle(vehicle: VehicleDetail) {
  try {
    await ElMessageBox.confirm(`确认删除车辆 ${vehicle.plate_mask}？`, '删除车辆', { type: 'warning' })
    await deleteVehicle(props.token, vehicle.vehicle_id)
    ElMessage.success('车辆已删除')
    if (activeVehicleId.value === vehicle.vehicle_id) {
      activeVehicleId.value = ''
    }
    await loadInventory()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error instanceof Error ? error.message : '车辆删除失败')
    }
  }
}

async function toggleVehicleStatus(vehicle: VehicleDetail, key: 'maintenance' | 'manually_locked') {
  try {
    await updateVehicleStatus(props.token, vehicle.vehicle_id, { [key]: !vehicle[key] })
    ElMessage.success(key === 'maintenance' ? '维保状态已更新' : '锁车状态已更新')
    await loadInventory()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '车辆状态更新失败')
  }
}

async function saveSinglePrice() {
  if (!activeVehicleId.value) return
  try {
    await upsertVehiclePrice(props.token, activeVehicleId.value, { ...priceForm })
    ElMessage.success('单日价格已保存')
    await loadInventory()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '价格保存失败')
  }
}

async function saveBatchPrices() {
  if (!activeVehicleId.value) return
  try {
    await upsertVehiclePricesBatch(props.token, activeVehicleId.value, { ...batchForm })
    ElMessage.success('批量价格已保存')
    await loadInventory()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '批量价格保存失败')
  }
}

async function selectVehicle(vehicleId: string) {
  activeVehicleId.value = vehicleId
  await loadPrices()
}

onMounted(() => void loadInventory())
</script>

<template>
  <div class="admin-panel-stack vehicle-workbench" v-loading="loading">
    <section class="vehicle-kpi-row">
      <article class="vehicle-kpi">
        <span>可租车辆</span>
        <strong>{{ availabilitySummary.available }}</strong>
        <p>审核通过、已上架、无维保锁车且价格有效</p>
      </article>
      <article class="vehicle-kpi">
        <span>不可租车辆</span>
        <strong>{{ availabilitySummary.blocked }}</strong>
        <p>下架、未审核、维保、锁车、占用或缺价</p>
      </article>
      <article class="vehicle-kpi">
        <span>缺价车辆</span>
        <strong>{{ availabilitySummary.noPrice }}</strong>
        <p>下单前必须补齐取还日期价格</p>
      </article>
    </section>

    <section class="admin-panel-card">
      <header class="admin-panel-card__header">
        <div>
          <h3>车型库</h3>
          <p>维护品牌、车系、车型、押金和最低底价，车辆价格不能低于车型底价。</p>
        </div>
        <el-button plain @click="resetModelForm">清空</el-button>
      </header>
      <el-form label-position="top" class="admin-form-grid">
        <el-form-item label="品牌">
          <el-input v-model="modelForm.brand" />
        </el-form-item>
        <el-form-item label="车系">
          <el-input v-model="modelForm.series" />
        </el-form-item>
        <el-form-item label="车型名称">
          <el-input v-model="modelForm.model_name" />
        </el-form-item>
        <el-form-item label="年份">
          <el-input-number v-model="modelForm.year" :min="2000" :max="2100" />
        </el-form-item>
        <el-form-item label="车辆类型">
          <el-input v-model="modelForm.vehicle_type" />
        </el-form-item>
        <el-form-item label="能源类型">
          <el-input v-model="modelForm.energy_type" />
        </el-form-item>
        <el-form-item label="座位数">
          <el-input-number v-model="modelForm.seats" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="变速箱">
          <el-input v-model="modelForm.gearbox" />
        </el-form-item>
        <el-form-item label="最低底价">
          <el-input-number v-model="modelForm.min_base_price" :min="0" />
        </el-form-item>
        <el-form-item label="车辆押金">
          <el-input-number v-model="modelForm.deposit_amount" :min="0" />
        </el-form-item>
        <el-form-item label="违章押金">
          <el-input-number v-model="modelForm.violation_deposit_amount" :min="0" />
        </el-form-item>
      </el-form>
      <footer class="admin-panel-card__footer">
        <el-button type="primary" @click="saveModel">{{ editingModelId ? '保存车型' : '新增车型' }}</el-button>
      </footer>
      <el-table :data="models" class="vehicle-table">
        <el-table-column prop="brand" label="品牌" min-width="96" />
        <el-table-column prop="series" label="车系" min-width="96" />
        <el-table-column prop="model_name" label="车型" min-width="150" />
        <el-table-column prop="min_base_price" label="最低底价" width="104" />
        <el-table-column label="押金" width="150">
          <template #default="{ row }: { row: VehicleModel }">
            {{ row.deposit_amount }} / {{ row.violation_deposit_amount }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }: { row: VehicleModel }">
            <el-button text type="primary" @click="editModel(row)">编辑</el-button>
            <el-button text type="danger" @click="removeModel(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="admin-panel-card">
      <header class="admin-panel-card__header">
        <div>
          <h3>车辆资料</h3>
          <p>车辆来源区分运营中心自有、托管车辆和车行车辆，状态会直接影响 C 端可租列表。</p>
        </div>
        <el-button plain @click="resetVehicleForm">清空</el-button>
      </header>
      <el-form label-position="top" class="admin-form-grid">
        <el-form-item label="城市代码">
          <el-input v-model="vehicleForm.city_code" />
        </el-form-item>
        <el-form-item label="车型">
          <el-select v-model="vehicleForm.model_id" filterable>
            <el-option
              v-for="model in models"
              :key="model.model_id"
              :label="`${model.brand} ${model.series} ${model.model_name}`"
              :value="model.model_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="脱敏车牌">
          <el-input v-model="vehicleForm.plate_mask" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-input v-model="vehicleForm.color" />
        </el-form-item>
        <el-form-item label="里程">
          <el-input-number v-model="vehicleForm.mileage_km" :min="0" />
        </el-form-item>
        <el-form-item label="日里程限制">
          <el-input-number v-model="vehicleForm.daily_mileage_limit" :min="0" />
        </el-form-item>
        <el-form-item label="车辆图片">
          <el-input v-model="vehicleForm.image_url" />
        </el-form-item>
        <el-form-item label="车辆来源">
          <el-select v-model="vehicleForm.source">
            <el-option v-for="item in vehicleSourceOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="vehicleForm.source === 'dealer'" label="车行组织 ID">
          <el-input v-model="vehicleForm.dealer_id" />
        </el-form-item>
        <el-form-item v-if="vehicleForm.source === 'hosted'" label="托管车主">
          <el-input v-model="vehicleForm.hosted_owner" />
        </el-form-item>
        <el-form-item label="审核状态">
          <el-select v-model="vehicleForm.review_status">
            <el-option label="待审核" value="pending" />
            <el-option label="通过" value="approved" />
            <el-option label="拒绝" value="rejected" />
          </el-select>
        </el-form-item>
        <el-form-item label="上下架">
          <el-select v-model="vehicleForm.listing_status">
            <el-option label="上架" value="listed" />
            <el-option label="下架" value="unlisted" />
          </el-select>
        </el-form-item>
      </el-form>
      <footer class="admin-panel-card__footer">
        <el-button type="primary" @click="saveVehicle">{{ editingVehicleId ? '保存车辆' : '新增车辆' }}</el-button>
      </footer>
      <el-table :data="vehicles" class="vehicle-table" row-key="vehicle_id">
        <el-table-column label="车辆" min-width="220">
          <template #default="{ row }: { row: VehicleDetail }">
            <strong>{{ row.model.brand }} {{ row.model.series }}</strong>
            <p class="vehicle-table__muted">{{ row.plate_mask }} · {{ row.color }} · {{ sourceLabel(row.source) }}</p>
          </template>
        </el-table-column>
        <el-table-column label="状态" min-width="210">
          <template #default="{ row }: { row: VehicleDetail }">
            <div class="vehicle-status-tags">
              <el-tag :type="row.available ? 'success' : 'warning'">{{ row.available ? '可租' : '不可租' }}</el-tag>
              <el-tag>{{ row.review_status }}</el-tag>
              <el-tag>{{ row.listing_status }}</el-tag>
            </div>
            <p v-if="row.unavailable_reason" class="vehicle-table__muted">{{ row.unavailable_reason }}</p>
          </template>
        </el-table-column>
        <el-table-column label="今日价格" width="130">
          <template #default="{ row }: { row: VehicleDetail }">
            {{ row.today_price ? `¥${row.today_price.customer_price}` : '缺价' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="310" fixed="right">
          <template #default="{ row }: { row: VehicleDetail }">
            <el-button text type="primary" @click="editVehicle(row)">编辑</el-button>
            <el-button text @click="selectVehicle(row.vehicle_id)">价格</el-button>
            <el-button text @click="toggleVehicleStatus(row, 'maintenance')">
              {{ row.maintenance ? '结束维保' : '维保' }}
            </el-button>
            <el-button text @click="toggleVehicleStatus(row, 'manually_locked')">
              {{ row.manually_locked ? '解锁' : '锁车' }}
            </el-button>
            <el-button text type="danger" @click="removeVehicle(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="admin-panel-card">
      <header class="admin-panel-card__header">
        <div>
          <h3>价格日历</h3>
          <p>{{ activeVehicle ? `${activeVehicle.plate_mask} · ${activeVehicle.model.model_name}` : '请选择车辆维护价格' }}</p>
        </div>
        <el-select v-model="activeVehicleId" filterable placeholder="选择车辆" @change="selectVehicle">
          <el-option
            v-for="vehicle in vehicles"
            :key="vehicle.vehicle_id"
            :label="`${vehicle.plate_mask} · ${vehicle.model.model_name}`"
            :value="vehicle.vehicle_id"
          />
        </el-select>
      </header>
      <div class="price-editor-grid">
        <div>
          <h4>单日价格</h4>
          <el-form label-position="top" class="admin-form-grid admin-form-grid--compact">
            <el-form-item label="日期">
              <el-date-picker v-model="priceForm.date" value-format="YYYY-MM-DD" type="date" />
            </el-form-item>
            <el-form-item label="底价">
              <el-input-number v-model="priceForm.base_price" :min="0" />
            </el-form-item>
            <el-form-item label="C 端价">
              <el-input-number v-model="priceForm.customer_price" :min="0" />
            </el-form-item>
            <el-form-item label="批发价">
              <el-input-number v-model="priceForm.wholesale_price" :min="0" />
            </el-form-item>
            <el-form-item label="可租">
              <el-switch v-model="priceForm.rentable" />
            </el-form-item>
          </el-form>
          <el-button type="primary" :disabled="!activeVehicleId" @click="saveSinglePrice">保存单日</el-button>
        </div>
        <div>
          <h4>批量 90 天内价格</h4>
          <el-form label-position="top" class="admin-form-grid admin-form-grid--compact">
            <el-form-item label="开始日期">
              <el-date-picker v-model="batchForm.start_date" value-format="YYYY-MM-DD" type="date" />
            </el-form-item>
            <el-form-item label="天数">
              <el-input-number v-model="batchForm.days" :min="1" :max="90" />
            </el-form-item>
            <el-form-item label="底价">
              <el-input-number v-model="batchForm.base_price" :min="0" />
            </el-form-item>
            <el-form-item label="C 端价">
              <el-input-number v-model="batchForm.customer_price" :min="0" />
            </el-form-item>
            <el-form-item label="批发价">
              <el-input-number v-model="batchForm.wholesale_price" :min="0" />
            </el-form-item>
            <el-form-item label="可租">
              <el-switch v-model="batchForm.rentable" />
            </el-form-item>
          </el-form>
          <el-button type="primary" :disabled="!activeVehicleId" @click="saveBatchPrices">批量保存</el-button>
        </div>
      </div>
      <el-table :data="prices" class="vehicle-table">
        <el-table-column prop="date" label="日期" width="130" />
        <el-table-column prop="base_price" label="底价" width="100" />
        <el-table-column prop="customer_price" label="C 端价" width="100" />
        <el-table-column prop="wholesale_price" label="批发价" width="100" />
        <el-table-column label="可租" width="90">
          <template #default="{ row }: { row: PriceCalendarEntry }">
            <el-tag :type="row.rentable ? 'success' : 'info'">{{ row.rentable ? '可租' : '停售' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时段" min-width="180">
          <template #default="{ row }: { row: PriceCalendarEntry }">
            {{ row.available_periods.join('、') }}
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>
