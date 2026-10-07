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
const board = ref({ business_date: '', available: [], active: [], overdue: [] })
const loans = ref({ business_date: '', active: [], overdue: [], returned: [] })
// 初始加载、设置保存、借出、归还都落到这同一个入口：响应里服务端已按
// 同一业务日派生好顶细条、分栏、借还记录，一次换齐，只允许一种逾期世界。
function applySnapshot(snap) {
  if (!snap) return
  if (snap.board) {
    board.value = snap.board
    counts.value = snap.board.counts || {}
  }
  if (snap.loans) loans.value = snap.loans
}
async function load() {
  applySnapshot(await api('/snapshot'))
}
async function loadLoans() {
  loans.value = await api('/loans')
}
provide('board', board)
provide('loans', loans)
provide('reloadBoard', load)
provide('reloadLoans', loadLoans)
provide('applySnapshot', applySnapshot)
onMounted(load)
</script>
