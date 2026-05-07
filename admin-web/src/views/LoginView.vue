<script setup lang="ts">
import { Lock, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { login } from '../api/admin'
import { useSessionStore } from '../stores/session'

const router = useRouter()
const session = useSessionStore()
const loading = ref(false)
const form = reactive({
  username: 'hq_admin',
  password: 'hq_admin123'
})

async function submit() {
  loading.value = true
  try {
    const response = await login(form.username, form.password)
    session.setSession(response.access_token, response.actor)
    await router.push({ name: 'admin' })
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-shell">
      <div class="login-hero">
        <p class="login-hero__eyebrow">WF-P0-03 · 权限中台</p>
        <h1>山海放心租 PC 管理后台</h1>
        <p class="login-hero__summary">
          总部、运营中心和车行账号从这里进入后台。未登录访问业务页会自动跳转登录，停用账号不可进入系统。
        </p>
        <div class="login-hero__chips">
          <span>组织架构</span>
          <span>员工账号</span>
          <span>岗位权限</span>
        </div>
      </div>

      <section class="login-panel">
        <header class="login-panel__header">
          <div>
            <p class="login-panel__eyebrow">账号登录</p>
            <h2>进入权限工作台</h2>
          </div>
          <span class="login-panel__badge">服务端校验</span>
        </header>

        <el-form label-position="top" @submit.prevent="submit">
          <el-form-item label="账号">
            <el-input v-model="form.username" :prefix-icon="User" autocomplete="username" placeholder="请输入账号" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input
              v-model="form.password"
              :prefix-icon="Lock"
              autocomplete="current-password"
              placeholder="请输入密码"
              show-password
              type="password"
            />
          </el-form-item>
          <el-button :loading="loading" native-type="submit" type="primary">登录后台</el-button>
        </el-form>

        <p class="login-panel__note">
          当前页面沿用原型的浅灰底、绿色渐变头部和白卡片风格；示例账号和密码仍按现有接口契约保留。
        </p>
      </section>
    </section>
  </main>
</template>

<style scoped>
.login-page {
  display: grid;
  min-height: 100vh;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at top left, rgb(96 209 134 / 0.16), transparent 24%),
    var(--admin-bg);
}

.login-shell {
  display: grid;
  grid-template-columns: minmax(320px, 1.1fr) minmax(360px, 420px);
  gap: 24px;
  width: min(1100px, 100%);
  align-items: stretch;
}

.login-hero,
.login-panel {
  padding: 32px;
  border-radius: 32px;
  border: 1px solid var(--admin-border);
  box-shadow: 0 24px 56px rgb(36 45 42 / 0.08);
}

.login-hero {
  background: linear-gradient(140deg, var(--admin-hero-start), var(--admin-hero-end));
}

.login-hero__eyebrow,
.login-panel__eyebrow {
  margin: 0 0 12px;
  color: var(--admin-muted);
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.login-hero h1,
.login-panel h2 {
  margin: 0;
  color: var(--admin-text);
  font-size: 36px;
  line-height: 1.12;
}

.login-hero__summary,
.login-panel__note {
  margin: 16px 0 0;
  color: var(--admin-subtle);
  line-height: 1.7;
}

.login-hero__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 24px;
}

.login-hero__chips span,
.login-panel__badge {
  display: inline-flex;
  align-items: center;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgb(255 255 255 / 0.78);
  color: var(--admin-text);
  font-size: 13px;
}

.login-panel {
  background: rgb(255 255 255 / 0.92);
}

.login-panel__header {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.login-panel :deep(.el-button) {
  width: 100%;
  min-height: 44px;
  border-color: transparent;
  background: var(--admin-accent);
  box-shadow: 0 14px 24px rgb(255 107 0 / 0.18);
}

.login-panel :deep(.el-button:hover) {
  background: var(--admin-accent-strong);
}

@media (max-width: 900px) {
  .login-shell {
    grid-template-columns: 1fr;
  }

  .login-hero,
  .login-panel {
    padding: 24px;
    border-radius: 24px;
  }

  .login-hero h1,
  .login-panel h2 {
    font-size: 30px;
  }
}
</style>
