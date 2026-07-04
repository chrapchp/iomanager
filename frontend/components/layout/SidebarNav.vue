<!--*************************************************
 * Project:     IOManager
 * Author:      Peter C
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 *              2026Jul04 - Amber accent; left-border active indicator; IBM Plex type
 *              2026Jul04 - Add Tag Rules nav entry; rename Settings to Config; add separator
 *************************************************-->

<template>
  <aside class="w-52 flex flex-col bg-slate-900 border-r border-slate-800">
    <div class="px-4 py-5 flex items-baseline gap-1 border-b border-slate-800">
      <span
        class="text-amber-500 font-mono font-bold text-xl tracking-tight"
        style="text-shadow: 0 0 14px rgba(245, 158, 11, 0.45)"
      >IO</span>
      <span class="text-slate-100 font-semibold text-xl tracking-tight">Manager</span>
    </div>

    <nav class="flex-1 py-3 px-2">
      <template v-for="item in navItems" :key="item === null ? '__sep' : item.href">
        <div v-if="item === null" class="my-1.5 border-t border-slate-800/70" />
        <NuxtLink
          v-else
          :to="item.href"
          :exact="item.exact"
          class="flex items-center gap-3 pr-3 py-2.5 rounded-md text-sm transition-all"
          active-class="border-l-2 border-amber-500 bg-amber-500/5 text-amber-400 pl-2.5"
          inactive-class="border-l-2 border-transparent text-slate-400 hover:text-slate-100 hover:bg-slate-800/40 pl-3"
        >
          <component :is="item.icon" :size="16" class="shrink-0" />
          {{ item.label }}
        </NuxtLink>
      </template>
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
  ListTree,
} from 'lucide-vue-next'

type NavItem = { label: string; href: string; icon: unknown; exact: boolean } | null

const navItems: NavItem[] = [
  { label: 'Dashboard', href: '/', icon: LayoutDashboard, exact: true },
  { label: 'Import', href: '/import', icon: Upload, exact: false },
  { label: 'Generate', href: '/export', icon: Zap, exact: false },
  { label: 'Tags', href: '/tags', icon: Tag, exact: false },
  { label: 'Alarms', href: '/alarms', icon: Bell, exact: false },
  null,
  { label: 'Config', href: '/settings', icon: Settings, exact: true },
  { label: 'Tag Rules', href: '/settings/rules', icon: ListTree, exact: false },
]
</script>
