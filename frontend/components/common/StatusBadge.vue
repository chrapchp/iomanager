<!--*************************************************
 * Project:     IOManager
 * Author:      Peter Chrapchynski
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 *************************************************-->

<template>
  <span class="inline-flex items-center gap-1.5 text-xs font-medium">
    <span class="inline-block w-1.5 h-1.5 rounded-full" :class="dotClass" />
    <span :class="textClass">{{ label }}</span>
  </span>
</template>

<script setup lang="ts">
const props = defineProps<{
  status: 'success' | 'warning' | 'error' | 'idle'
  label: string
}>()

const dotClass = computed(() => ({
  'bg-green-400': props.status === 'success',
  'bg-amber-400': props.status === 'warning',
  'bg-red-400': props.status === 'error',
  'bg-slate-600': props.status === 'idle',
}))

const textClass = computed(() => ({
  'text-green-400': props.status === 'success',
  'text-amber-400': props.status === 'warning',
  'text-red-400': props.status === 'error',
  'text-slate-500': props.status === 'idle',
}))
</script>
