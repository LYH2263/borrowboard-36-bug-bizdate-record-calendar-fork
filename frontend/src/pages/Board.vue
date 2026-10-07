<template>
  <div class="split">
    <section class="pane">
      <h2>可借物</h2>
      <div v-for="i in board.available" :key="i.id" class="item">
        <strong>{{ i.title }}</strong>
        <div class="muted">物主 {{ i.owner || '—' }}</div>
        <input v-model="forms[i.id].borrower" placeholder="借用人" />
        <input v-model="forms[i.id].due_date" placeholder="应还日 YYYY-MM-DD" @input="schedulePreview(i.id)" />
        <div class="muted" :style="elig[i.id] && !elig[i.id].ok ? 'color:#a33' : ''">
          资格（业务日 {{ board.business_date }}）：{{ eligText(i.id) }}
        </div>
        <button :disabled="!elig[i.id] || !elig[i.id].ok || submitErr[i.id]" @click="lend(i.id)">借出通过</button>
        <div v-if="submitErr[i.id]" class="muted" style="color:#a33;margin-top:6px">{{ submitErr[i.id] }}</div>
      </div>
    </section>
    <section class="pane">
      <h2>在借 / 逾期</h2>
      <div v-for="l in [...board.overdue, ...board.active]" :key="l.id" class="item" :class="{ overdue: l.overdue }">
        <strong>{{ l.title }}</strong> → {{ l.borrower }}
        <div class="muted">应还 {{ l.due_date }} {{ l.overdue ? '· 逾期（按业务日 ' + board.business_date + '）' : '' }}</div>
        <button @click="ret(l.id)">归还</button>
      </div>
    </section>
  </div>
</template>
<script setup>
import { inject, reactive, watch } from 'vue'
import { api } from '../api'
const board = inject('board')
const reload = inject('reloadBoard')
const applyWorld = inject('applyWorld')
const nextWorldSeq = inject('nextWorldSeq')
const forms = reactive({})
const elig = reactive({})        // id -> 服务端按当前业务日给出的预演结果
const submitErr = reactive({})
const timers = {}
const REASONS = {
  invalid_due_date: '应还日格式非法（YYYY-MM-DD）',
  due_before_business_date: '应还日早于业务日',
  item_not_available: '物品当前不可借',
  already_on_loan: '该物品已有在借记录',
}
function eligText(id) {
  const e = elig[id]
  if (!e) return '确认中…'
  return e.ok ? '可借出' : (REASONS[e.reason] || e.reason)
}
function schedulePreview(id) {
  submitErr[id] = ''
  clearTimeout(timers[id])
  timers[id] = setTimeout(() => preview(id), 300)
}
async function preview(id) {
  const due = forms[id]?.due_date || ''
  try {
    const r = await api('/items/' + id + '/lend-preview', {
      method: 'POST', body: JSON.stringify({ due_date: due }),
    })
    // 请求往返期间业务日又变了：丢弃按旧日给出的资格，按新日重算，
    // 绝不让预演资格、顶细条、可借栏各过一套。
    if (r.business_date !== board.value.business_date) return schedulePreview(id)
    elig[id] = r
  } catch (e) {
    elig[id] = { ok: false, reason: String(e.message || e) }
  }
}
watch(board, (b, old) => {
  for (const i of (b.available || [])) {
    if (!forms[i.id]) forms[i.id] = { borrower: '邻居', due_date: '2026-12-31' }
  }
  // 业务日一变，所有按旧日做的预演立即失效并按新日重检。
  if (!old || old.business_date !== b.business_date) {
    for (const k of Object.keys(elig)) delete elig[k]
    for (const i of (b.available || [])) schedulePreview(i.id)
  }
}, { immediate: true, deep: true })
async function lend(id) {
  if (!elig[id] || !elig[id].ok) return
  submitErr[id] = ''
  // 叠单防护：借出与改日并发时，只接受这一单序号对应的新世界。
  const seq = nextWorldSeq()
  let snap
  try {
    snap = await api('/items/' + id + '/lend', { method: 'POST', body: JSON.stringify(forms[id]) })
  } catch (e) {
    // 提交瞬间业务日已变导致服务端拒绝：以服务端当前世界重新拉齐后重检。
    submitErr[id] = '提交时业务日已变化，已按新业务日重新判定：' + (REASONS[e.message] || e.message)
    await reload()
    schedulePreview(id)
    return
  }
  // 顶细条、分栏逾期样式、借还记录逾期段同包落屏；响应迟到（期间又改日/借还）
  // 则整包丢弃并重新拉齐，绝不留半套世界。
  if (!applyWorld(snap, seq)) await reload()
}
async function ret(id) {
  const seq = nextWorldSeq()
  const snap = await api('/loans/' + id + '/return', { method: 'POST', body: '{}' })
  if (!applyWorld(snap, seq)) await reload()
}
</script>
