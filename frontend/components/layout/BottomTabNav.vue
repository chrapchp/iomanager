<!--*************************************************
 * Project:     IOManager
 * Author:      Peter C
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 *              2026Jul04 - Amber active accent
 *              2026Jul04 - Add Tag Rules entry; rename Settings to Config
 *              2026Jul07 - Add Virtual Tags entry
 *************************************************-->

<template>
  <nav class="fixed bottom-0 inset-x-0 bg-slate-900 border-t border-slate-800 flex">
    <NuxtLink
      v-for="item in navItems"
      :key="item.href"
      :to="item.href"
      :exact="item.exact"
      class="flex-1 flex flex-col items-center justify-center py-2 gap-0.5 text-xs transition-colors"
      active-class="text-amber-400"
      inactive-class="text-slate-500 hover:text-slate-300"
    >
      <component :is="item.icon" :size="20" class="shrink-0" />
      <span>{{ item.label }}</span>
    </NuxtLink>
  </nav>
</template>

<script setup lang="ts">
import {
  LayoutDashboard,
  Upload,
  Zap,
  Tag,
  Tags,
  Bell,
  Settings,
  ListTree,
} from 'lucide-vue-next'

const navItems = [
  { label: 'Home', href: '/', icon: LayoutDashboard, exact: true },
  { label: 'Import', href: '/import', icon: Upload, exact: false },
  { label: 'Generate', href: '/export', icon: Zap, exact: false },
  { label: 'Tags', href: '/tags', icon: Tag, exact: false },
  { label: 'Virtual', href: '/virtual-tags', icon: Tags, exact: false },
  { label: 'Alarms', href: '/alarms', icon: Bell, exact: false },
  { label: 'Config', href: '/settings', icon: Settings, exact: true },
  { label: 'Tag Rules', href: '/settings/rules', icon: ListTree, exact: false },
]
</script>
