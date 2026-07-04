<!--*************************************************
 * Project:     IOManager
 * Author:      Peter Chrapchynski
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 *              2026Jul04 - Amber drag-active state
 *************************************************-->

<template>
  <div
    class="relative flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-8 transition-colors cursor-pointer"
    :class="[
      dragging ? 'border-amber-400 bg-amber-400/5' : 'border-slate-700 bg-slate-900 hover:border-slate-500',
      loading ? 'pointer-events-none opacity-60' : '',
    ]"
    @dragover.prevent="dragging = true"
    @dragleave="dragging = false"
    @drop.prevent="onDrop"
    @click="fileInput?.click()"
  >
    <input
      ref="fileInput"
      type="file"
      class="sr-only"
      :accept="accept"
      @change="onInputChange"
    />

    <Upload :size="28" class="text-slate-500" />

    <div class="text-center">
      <p class="text-sm font-medium text-slate-300">{{ label }}</p>
      <p v-if="selectedFile" class="mt-1 text-xs text-amber-400 font-mono truncate max-w-56">
        {{ selectedFile.name }}
      </p>
      <p v-else class="mt-1 text-xs text-slate-500">
        Drag & drop or click to select · {{ accept }}
      </p>
    </div>

    <div v-if="loading" class="absolute inset-0 flex items-center justify-center rounded-lg bg-slate-900/70">
      <span class="text-xs text-slate-400 animate-pulse">Uploading…</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Upload } from 'lucide-vue-next'

const props = defineProps<{
  label: string
  accept: string
  loading?: boolean
}>()

const emit = defineEmits<{
  change: [file: File]
}>()

const dragging = ref(false)
const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

function onDrop(e: DragEvent) {
  dragging.value = false
  const file = e.dataTransfer?.files[0]
  if (file) handleFile(file)
}

function onInputChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) handleFile(file)
}

function handleFile(file: File) {
  selectedFile.value = file
  emit('change', file)
}
</script>
