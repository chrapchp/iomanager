<!--*************************************************
 * Project:     IOManager
 * Author:      Peter Chrapchynski
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 *************************************************-->

<template>
  <aside class="w-52 flex flex-col bg-slate-900 border-r border-slate-800">
    <div class="px-4 py-5 flex items-baseline gap-1 border-b border-slate-800">
      <span class="text-cyan-400 font-mono font-bold text-xl tracking-tight">IO</span>
      <span class="text-slate-100 font-semibold text-xl tracking-tight">Manager</span>
    </div>

    <nav class="flex-1 py-3 space-y-0.5 px-2">
      <NuxtLink
        v-for="item in navItems"
        :key="item.href"
        :to="item.href"
        :exact="item.exact"
        class="flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors"
        active-class="bg-slate-800 text-cyan-400"
        inactive-class="text-slate-400 hover:text-slate-100 hover:bg-slate-800/60"
      >
        <component :is="item.icon" :size="16" class="shrink-0" />
        {{ item.label }}
      </NuxtLink>
    </nav>

    <div class="px-4 py-3 border-t border-slate-800">
      <p class="text-xs text-slate-600 font-mono">Twinsoft · PLC ETL</p>
    </div>
  </aside>
</template>

<script setup lang="ts">
import {
  LayoutDashboard,
  Upload,
  Zap,
  Tag,
  Bell,
  Settings,
} from 'lucide-vue-next'

const navItems = [
  { label: 'Dashboard', href: '/', icon: LayoutDashboard, exact: true },
  { label: 'Import', href: '/import', icon: Upload, exact: false },
  { label: 'Generate', href: '/export', icon: Zap, exact: false },
  { label: 'Tags', href: '/tags', icon: Tag, exact: false },
  { label: 'Alarms', href: '/alarms', icon: Bell, exact: false },
  { label: 'Settings', href: '/settings', icon: Settings, exact: false },
]
</script>
