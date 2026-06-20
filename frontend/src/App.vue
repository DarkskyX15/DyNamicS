<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import {
  createSlug,
  createTarget,
  createToken,
  deleteSlug,
  deleteTarget,
  getAccessToken,
  getDashboard,
  listLogs,
  listSlugs,
  listTargets,
  listTokens,
  login,
  logout,
  me,
  refresh,
  removeToken,
  toggleToken,
  updateSlug,
  updateTarget,
} from './api'

const state = reactive({
  loading: true,
  loggedIn: false,
  error: '',
  user: null,
  dashboard: null,
  targets: [],
  slugs: [],
  selectedTargetId: null,
  tokens: [],
  logs: [],
})

const loginForm = reactive({ username: 'admin', password: 'admin123' })
const targetForm = reactive({
  id: null,
  name: '',
  mode: 'dynamic_ip',
  scheme: 'https',
  host: '',
  port: null,
  base_path: '',
  default_query_text: '{}',
  full_url: '',
  enabled: true,
})
const slugForm = reactive({
  id: null,
  slug: '',
  target_id: '',
  enabled: true,
  info_public_enabled: true,
  redirect_code: 302,
  description: '',
})
const tokenForm = reactive({ label: '校园网客户端', expires_at: '' })
const plainToken = ref('')

const selectedTarget = computed(() => state.targets.find((item) => item.id === state.selectedTargetId) || null)

function setError(error) {
  state.error = error instanceof Error ? error.message : String(error || '')
}

function clearError() {
  state.error = ''
}

function parseQueryText(text) {
  if (!text?.trim()) {
    return {}
  }
  return JSON.parse(text)
}

function resetTargetForm() {
  Object.assign(targetForm, {
    id: null,
    name: '',
    mode: 'dynamic_ip',
    scheme: 'https',
    host: '',
    port: null,
    base_path: '',
    default_query_text: '{}',
    full_url: '',
    enabled: true,
  })
}

function resetSlugForm() {
  Object.assign(slugForm, {
    id: null,
    slug: '',
    target_id: state.targets[0]?.id || '',
    enabled: true,
    info_public_enabled: true,
    redirect_code: 302,
    description: '',
  })
}

async function loadProtectedData() {
  state.dashboard = await getDashboard()
  state.targets = await listTargets()
  state.slugs = await listSlugs()
  if (!slugForm.target_id && state.targets[0]) {
    slugForm.target_id = state.targets[0].id
  }
  if (!state.selectedTargetId && state.targets[0]) {
    state.selectedTargetId = state.targets[0].id
  }
  if (state.selectedTargetId) {
    state.tokens = await listTokens(state.selectedTargetId)
    state.logs = await listLogs(state.selectedTargetId)
  }
}

async function bootstrap() {
  try {
    if (getAccessToken()) {
      await me()
    } else {
      await refresh()
    }
    const user = await me()
    state.user = user
    state.loggedIn = true
    await loadProtectedData()
  } catch {
    state.loggedIn = false
  } finally {
    state.loading = false
  }
}

async function handleLogin() {
  clearError()
  try {
    const data = await login(loginForm.username, loginForm.password)
    state.user = data.user
    state.loggedIn = true
    await loadProtectedData()
  } catch (error) {
    setError(error)
  }
}

async function handleLogout() {
  await logout()
  state.loggedIn = false
  state.user = null
  state.targets = []
  state.slugs = []
  state.tokens = []
  state.logs = []
}

async function submitTarget() {
  clearError()
  try {
    const payload = {
      name: targetForm.name,
      mode: targetForm.mode,
      scheme: targetForm.mode === 'dynamic_url' ? null : targetForm.scheme,
      host: targetForm.mode === 'dynamic_url' ? null : targetForm.host || null,
      port: targetForm.port ? Number(targetForm.port) : null,
      base_path: targetForm.base_path || '',
      default_query: parseQueryText(targetForm.default_query_text),
      full_url: targetForm.mode === 'dynamic_url' ? targetForm.full_url : null,
      enabled: targetForm.enabled,
    }
    if (targetForm.id) {
      await updateTarget(targetForm.id, payload)
    } else {
      await createTarget(payload)
    }
    resetTargetForm()
    await loadProtectedData()
  } catch (error) {
    setError(error)
  }
}

function editTarget(target) {
  Object.assign(targetForm, {
    id: target.id,
    name: target.name,
    mode: target.mode,
    scheme: target.scheme || 'https',
    host: target.host || '',
    port: target.port || null,
    base_path: target.base_path || '',
    default_query_text: JSON.stringify(target.default_query || {}, null, 2),
    full_url: target.full_url || '',
    enabled: target.enabled,
  })
}

async function removeTarget(id) {
  clearError()
  try {
    await deleteTarget(id)
    if (state.selectedTargetId === id) {
      state.selectedTargetId = null
    }
    await loadProtectedData()
  } catch (error) {
    setError(error)
  }
}

async function submitSlug() {
  clearError()
  try {
    const payload = {
      slug: slugForm.slug,
      target_id: Number(slugForm.target_id),
      enabled: slugForm.enabled,
      info_public_enabled: slugForm.info_public_enabled,
      redirect_code: Number(slugForm.redirect_code),
      description: slugForm.description,
    }
    if (slugForm.id) {
      await updateSlug(slugForm.id, payload)
    } else {
      await createSlug(payload)
    }
    resetSlugForm()
    await loadProtectedData()
  } catch (error) {
    setError(error)
  }
}

function editSlug(slug) {
  Object.assign(slugForm, {
    id: slug.id,
    slug: slug.slug,
    target_id: slug.target_id,
    enabled: slug.enabled,
    info_public_enabled: slug.info_public_enabled,
    redirect_code: slug.redirect_code,
    description: slug.description,
  })
}

async function removeSlug(id) {
  clearError()
  try {
    await deleteSlug(id)
    await loadProtectedData()
  } catch (error) {
    setError(error)
  }
}

async function changeSelectedTarget(targetId) {
  state.selectedTargetId = Number(targetId)
  if (!state.selectedTargetId) {
    state.tokens = []
    state.logs = []
    return
  }
  state.tokens = await listTokens(state.selectedTargetId)
  state.logs = await listLogs(state.selectedTargetId)
}

async function submitToken() {
  if (!state.selectedTargetId) {
    return
  }
  clearError()
  try {
    const token = await createToken(state.selectedTargetId, {
      label: tokenForm.label,
      expires_at: tokenForm.expires_at || null,
    })
    plainToken.value = token.plain_token || ''
    await changeSelectedTarget(state.selectedTargetId)
  } catch (error) {
    setError(error)
  }
}

async function toggleSelectedToken(token) {
  clearError()
  try {
    await toggleToken(token.id, !token.enabled)
    await changeSelectedTarget(state.selectedTargetId)
  } catch (error) {
    setError(error)
  }
}

async function deleteSelectedToken(token) {
  clearError()
  try {
    await removeToken(token.id)
    await changeSelectedTarget(state.selectedTargetId)
  } catch (error) {
    setError(error)
  }
}

onMounted(bootstrap)
</script>

<template>
  <div class="shell">
    <header class="hero">
      <div>
        <p class="eyebrow">DyNamicS 管理台</p>
        <h1>短链网关与动态目标控制面</h1>
        <p class="subtitle">同域部署，后端通过 <code>/api</code> 提供管理 API，公开入口通过 <code>/s</code> 与 <code>/i</code> 暴露。</p>
      </div>
      <button v-if="state.loggedIn" class="ghost" @click="handleLogout">退出登录</button>
    </header>

    <p v-if="state.error" class="error">{{ state.error }}</p>

    <section v-if="state.loading" class="card">
      <p>正在加载管理台…</p>
    </section>

    <section v-else-if="!state.loggedIn" class="card login-card">
      <h2>登录</h2>
      <div class="form-grid">
        <label>
          用户名
          <input v-model="loginForm.username" placeholder="admin" />
        </label>
        <label>
          密码
          <input v-model="loginForm.password" type="password" placeholder="admin123" />
        </label>
      </div>
      <button @click="handleLogin">登录</button>
      <p class="hint">首次启动默认管理员账号为 <code>admin</code> / <code>admin123</code>。</p>
    </section>

    <main v-else class="layout">
      <section class="stats-row">
        <article class="stat card">
          <h3>{{ state.dashboard?.slug_count ?? 0 }}</h3>
          <p>slug 数量</p>
        </article>
        <article class="stat card">
          <h3>{{ state.dashboard?.target_count ?? 0 }}</h3>
          <p>target 数量</p>
        </article>
        <article class="stat card">
          <h3>{{ state.dashboard?.token_count ?? 0 }}</h3>
          <p>更新令牌数量</p>
        </article>
      </section>

      <section class="grid-two">
        <article class="card">
          <div class="section-title">
            <h2>{{ targetForm.id ? '编辑 target' : '创建 target' }}</h2>
            <button class="ghost" @click="resetTargetForm">重置</button>
          </div>
          <div class="form-grid">
            <label>
              名称
              <input v-model="targetForm.name" />
            </label>
            <label>
              模式
              <select v-model="targetForm.mode">
                <option value="static">static</option>
                <option value="dynamic_ip">dynamic_ip</option>
                <option value="dynamic_url">dynamic_url</option>
              </select>
            </label>
            <label v-if="targetForm.mode !== 'dynamic_url'">
              协议
              <select v-model="targetForm.scheme">
                <option value="http">http</option>
                <option value="https">https</option>
              </select>
            </label>
            <label v-if="targetForm.mode !== 'dynamic_url'">
              Host
              <input v-model="targetForm.host" placeholder="1.2.3.4 或 example.com" />
            </label>
            <label v-if="targetForm.mode !== 'dynamic_url'">
              端口
              <input v-model="targetForm.port" type="number" placeholder="443" />
            </label>
            <label v-if="targetForm.mode !== 'dynamic_url'">
              Base Path
              <input v-model="targetForm.base_path" placeholder="/app" />
            </label>
            <label v-if="targetForm.mode === 'dynamic_url'" class="full-width">
              完整 URL
              <input v-model="targetForm.full_url" placeholder="https://example.com/app" />
            </label>
            <label class="full-width">
              默认 Query（JSON）
              <textarea v-model="targetForm.default_query_text" rows="5"></textarea>
            </label>
            <label class="checkbox-label">
              <input v-model="targetForm.enabled" type="checkbox" />
              启用 target
            </label>
          </div>
          <button @click="submitTarget">{{ targetForm.id ? '保存 target' : '创建 target' }}</button>
        </article>

        <article class="card">
          <div class="section-title">
            <h2>{{ slugForm.id ? '编辑 slug' : '创建 slug' }}</h2>
            <button class="ghost" @click="resetSlugForm">重置</button>
          </div>
          <div class="form-grid">
            <label>
              slug
              <input v-model="slugForm.slug" placeholder="alice-home" />
            </label>
            <label>
              绑定 target
              <select v-model="slugForm.target_id">
                <option v-for="target in state.targets" :key="target.id" :value="target.id">
                  {{ target.name }} (#{{ target.id }})
                </option>
              </select>
            </label>
            <label>
              跳转状态码
              <select v-model="slugForm.redirect_code">
                <option :value="302">302</option>
                <option :value="307">307</option>
                <option :value="308">308</option>
              </select>
            </label>
            <label class="full-width">
              描述
              <textarea v-model="slugForm.description" rows="3"></textarea>
            </label>
            <label class="checkbox-label">
              <input v-model="slugForm.enabled" type="checkbox" />
              启用 slug
            </label>
            <label class="checkbox-label">
              <input v-model="slugForm.info_public_enabled" type="checkbox" />
              公开 <code>/i/&lt;slug&gt;</code>
            </label>
          </div>
          <button @click="submitSlug">{{ slugForm.id ? '保存 slug' : '创建 slug' }}</button>
        </article>
      </section>

      <section class="grid-two">
        <article class="card">
          <div class="section-title">
            <h2>Targets</h2>
            <span class="hint">点击“编辑”可回填表单</span>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>名称</th>
                  <th>模式</th>
                  <th>当前目标</th>
                  <th>Slug 数</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="target in state.targets" :key="target.id">
                  <td>{{ target.name }}</td>
                  <td>{{ target.mode }}</td>
                  <td><code>{{ target.resolved_url || '-' }}</code></td>
                  <td>{{ target.slug_count }}</td>
                  <td class="actions">
                    <button class="ghost" @click="editTarget(target)">编辑</button>
                    <button class="ghost" @click="changeSelectedTarget(target.id)">查看令牌/日志</button>
                    <button class="danger" @click="removeTarget(target.id)">删除</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        <article class="card">
          <div class="section-title">
            <h2>Slugs</h2>
            <span class="hint">公开入口：<code>/s/&lt;slug&gt;</code> 与 <code>/i/&lt;slug&gt;</code></span>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>slug</th>
                  <th>target</th>
                  <th>跳转码</th>
                  <th>公开信息</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="slug in state.slugs" :key="slug.id">
                  <td><code>{{ slug.slug }}</code></td>
                  <td>#{{ slug.target_id }}</td>
                  <td>{{ slug.redirect_code }}</td>
                  <td>{{ slug.info_public_enabled ? '是' : '否' }}</td>
                  <td class="actions">
                    <button class="ghost" @click="editSlug(slug)">编辑</button>
                    <button class="danger" @click="removeSlug(slug.id)">删除</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>
      </section>

      <section class="grid-two">
        <article class="card">
          <div class="section-title">
            <h2>更新令牌</h2>
            <select :value="state.selectedTargetId || ''" @change="changeSelectedTarget($event.target.value)">
              <option disabled value="">选择 target</option>
              <option v-for="target in state.targets" :key="target.id" :value="target.id">
                {{ target.name }} (#{{ target.id }})
              </option>
            </select>
          </div>
          <div v-if="selectedTarget" class="token-panel">
            <div class="form-grid">
              <label>
                令牌标签
                <input v-model="tokenForm.label" />
              </label>
              <label>
                过期时间（可选）
                <input v-model="tokenForm.expires_at" type="datetime-local" />
              </label>
            </div>
            <button @click="submitToken">为当前 target 创建令牌</button>
            <p v-if="plainToken" class="plain-token">明文令牌（仅展示一次）：<code>{{ plainToken }}</code></p>
            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>标签</th>
                    <th>状态</th>
                    <th>过期时间</th>
                    <th>最后使用</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="token in state.tokens" :key="token.id">
                    <td>{{ token.label }}</td>
                    <td>{{ token.enabled ? '启用' : '禁用' }}</td>
                    <td>{{ token.expires_at || '-' }}</td>
                    <td>{{ token.last_used_at || '-' }}</td>
                    <td class="actions">
                      <button class="ghost" @click="toggleSelectedToken(token)">{{ token.enabled ? '禁用' : '启用' }}</button>
                      <button class="danger" @click="deleteSelectedToken(token)">删除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <p v-else class="hint">请选择一个 target 来管理令牌。</p>
        </article>

        <article class="card">
          <div class="section-title">
            <h2>更新日志</h2>
            <span class="hint">展示当前选中 target 的审计记录</span>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>时间</th>
                  <th>来源</th>
                  <th>旧值</th>
                  <th>新值</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="log in state.logs" :key="log.id">
                  <td>{{ log.created_at }}</td>
                  <td>{{ log.source_type }}</td>
                  <td><pre>{{ JSON.stringify(log.old_snapshot, null, 2) }}</pre></td>
                  <td><pre>{{ JSON.stringify(log.new_snapshot, null, 2) }}</pre></td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>
      </section>
    </main>
  </div>
</template>
