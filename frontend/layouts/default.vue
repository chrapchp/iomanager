<!--*************************************************
 * Project:     IOManager
 * Author:      Peter Chrapchynski
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 *************************************************-->

<template>
  <div class="flex h-screen bg-slate-950 text-slate-100 overflow-hidden">
    <SidebarNav class="hidden lg:flex shrink-0" />

    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
      <main class="flex-1 overflow-y-auto p-6 pb-20 lg:pb-6">
        <slot />
      </main>
    </div>

    <BottomTabNav class="lg:hidden" />
  </div>
</template>

<script setup lang="ts">
</script>
