<template>
  <div style="padding:16px;max-width:480px">
    <h1>设置 · 邻里互借</h1>
    <label class="muted">业务日（YYYY-MM-DD），在借与逾期都按它划分</label>
    <input v-model="businessDate" placeholder="YYYY-MM-DD" />
    <div style="display:flex;gap:8px;align-items:center">
      <button @click="save">保存业务日</button>
      <span class="muted" v-if="msg" :style="err ? 'color:#a33' : ''">{{ msg }}</span>
    </div>
    <hr />
    <pre>{{ s }}</pre>
  </div>
</template>
<script setup>
import { ref, onMounted, inject } from 'vue'
import { api } from '../api'
const s = ref('')
const businessDate = ref('')
const savedDate = ref('')
const msg = ref('')
const err = ref(false)
const applySavedSnapshot = inject('applySavedSnapshot')
const nextWorldSeq = inject('nextWorldSeq')

async function load() {
  const settings = await api('/settings')
  s.value = JSON.stringify(settings, null, 2)
  businessDate.value = settings.business_date || ''
  savedDate.value = businessDate.value
}
onMounted(load)

async function save() {
  msg.value = ''; err.value = false
  const before = savedDate.value
  // 叠单防护：序号在发请求前取好，保存往返期间若有借出/归还/另一次改日先落屏，
  // 本单响应整包丢弃并重新拉齐，只留最新的一个逾期世界。
  const seq = nextWorldSeq()
  let snap
  try {
    snap = await api('/settings', {
      method: 'POST', body: JSON.stringify({ business_date: businessDate.value }),
    })
  } catch (e) {
    // 非法日期：服务端整单失败、未落库，本地输入与展示都回到改前的业务日。
    businessDate.value = before
    err = true
    msg.value = '业务日非法，已回到改前值（' + before + '）：' + e.message
    return
  }
  // 顶细条、分栏、借还记录一次跟保存结果（同一服务端快照）；
  // 迟到（叠单）时该快照不落屏，App 已按服务端现况整包重拉；
  // 本页设置区也重新拉取权威值，不拿被拒旧包里的日期当“最新”。
  if (!applySavedSnapshot(snap, seq)) {
    const fresh = await api('/settings')
    s.value = JSON.stringify(fresh, null, 2)
    savedDate.value = fresh.business_date
    businessDate.value = savedDate.value
    msg.value = '保存期间发生了更新的借还/改日操作，已按最新业务日 ' + savedDate.value + ' 重新拉齐'
    return
  }
  s.value = JSON.stringify(snap.settings, null, 2)
  savedDate.value = snap.settings.business_date
  businessDate.value = savedDate.value
  msg.value = '已保存，业务日 ' + savedDate.value + ' 已写入'
  if (snap.loans?.date_meta) msg.value += ' · 逾期判定日 ' + (snap.loans.date_meta.record_date || '')
}
</script>
