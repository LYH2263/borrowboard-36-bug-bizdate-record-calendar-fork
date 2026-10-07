<template>
  <div>
    <div class="status-bar">
      <span>业务日 {{ board.business_date || '—' }}</span>
      <span>可借 {{ counts.available || 0 }}</span>
      <span>在借 {{ counts.active || 0 }}</span>
      <span>逾期 {{ counts.overdue || 0 }}</span>
    </div>
    <nav class="topnav">
      <router-link to="/">看板</router-link>
      <router-link to="/list">上架</router-link>
      <router-link to="/loans">借还记录</router-link>
      <router-link to="/owners">物主</router-link>
      <router-link to="/settings">设置</router-link>
    </nav>
    <router-view @refresh="load" />
  </div>
</template>
<script setup>
import { ref, onMounted, provide } from 'vue'
import { api } from './api'
const counts = ref({})
const bizFork = ref(false)
const recordDay = ref('')
const board = ref({ business_date: '', available: [], active: [], overdue: [] })
const loans = ref({ business_date: '', active: [], overdue: [], returned: [] })

// 改日与借出/归还可能叠单：每次“换世界”的操作取一个递增序号，
// 只有最新一次操作的快照允许落屏，旧世界迟到的响应整包丢弃。
let worldSeq = 0
function nextWorldSeq() { return ++worldSeq }

function syncDateMeta() {
  const meta = board.value.date_meta || loans.value.date_meta
  bizFork.value = !!(meta && meta.forked)
  recordDay.value = board.value.date_meta?.record_date || loans.value.record_date || ''
}

// 唯一的“换世界”入口：顶细条/分栏（board）与借还记录（loans）必须同包到达、
// 一次落屏；两边业务日不一致或属于更早的叠单，一律拒绝，杜绝各栏各算一套。
function applyWorld(snap, seq) {
  if (!snap || !snap.board || !snap.loans) return false
  if (snap.board.business_date !== snap.loans.business_date) return false
  if (seq !== undefined && seq !== worldSeq) return false
  board.value = snap.board
  counts.value = snap.board.counts || {}
  loans.value = snap.loans
  syncDateMeta()
  return true
}

async function load() {
  const seq = nextWorldSeq()
  // 一次请求取同连接、同业务日派生的两套快照，避免两个 GET 之间被改日插单。
  const snap = await api('/world')
  if (!applyWorld(snap, seq)) return
}

// 设置保存成功后，顶细条、分栏、借还记录一次换成保存结果，杜绝各栏各算一套。
// 返回该快照是否真的落屏（false = 属于更早的叠单，已触发整包重拉）。
function applySavedSnapshot(snap, seq) {
  if (applyWorld(snap, seq)) return true
  load()
  return false
}

provide('board', board)
provide('loans', loans)
provide('reloadBoard', load)
provide('nextWorldSeq', nextWorldSeq)
provide('applyWorld', applyWorld)
provide('applySavedSnapshot', applySavedSnapshot)
onMounted(load)
</script>
