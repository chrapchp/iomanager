<!--*************************************************
 * Project:     IOManager
 * Author:      Peter C
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 *              2026Jun24 - Add IO index download link after generation
 *              2026Jul04 - Amber accent
 *************************************************-->

<template>
  <div class="max-w-3xl space-y-8">
    <div>
      <h1 class="text-2xl font-semibold tracking-tight text-slate-100">Generate</h1>
      <p class="mt-1 text-sm text-slate-500">Run the ETL pipeline and download output files.</p>
    </div>

    <!-- Prerequisite warning -->
    <div
      v-if="!imports.status.io_index_loaded"
      class="rounded-lg bg-amber-950/50 border border-amber-800/60 px-4 py-3 text-sm text-amber-300"
    >
      I/O Index not loaded.
      <NuxtLink to="/import" class="underline underline-offset-2 hover:text-amber-200">Go to Import →</NuxtLink>
    </div>

    <!-- Generate button -->
    <button
      :disabled="!imports.status.io_index_loaded || gen.generating"
      class="px-6 py-3 rounded-md font-semibold text-slate-950 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      :class="gen.generating ? 'bg-amber-600 animate-pulse' : 'bg-amber-500 hover:bg-amber-400'"
      @click="runGenerate"
    >
      {{ gen.generating ? 'Generating…' : 'Generate' }}
    </button>

    <!-- Error banner -->
    <div v-if="gen.error" class="rounded-md bg-red-950 border border-red-800 px-4 py-3 text-sm text-red-300 font-mono">
      {{ gen.error }}
    </div>

    <!-- Results -->
    <div v-if="gen.result" class="space-y-6">
      <!-- Summary counts -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div
          v-for="stat in summaryStats"
          :key="stat.label"
          class="rounded-lg bg-slate-900 border border-slate-800 p-4 text-center"
        >
          <div class="text-2xl font-mono font-semibold" :class="stat.color">{{ stat.value }}</div>
          <div class="mt-1 text-xs text-slate-500">{{ stat.label }}</div>
        </div>
      </div>

      <!-- Download links -->
      <div class="rounded-lg bg-slate-900 border border-slate-800 overflow-hidden">
        <div class="px-4 py-3 border-b border-slate-800">
          <h2 class="text-sm font-medium text-slate-300">Output Files</h2>
        </div>
        <div class="divide-y divide-slate-800">
          <a
            v-for="file in outputFiles"
            :key="file.name"
            :href="gen.downloadUrl(file.name)"
            :download="file.name"
            class="flex items-center justify-between px-4 py-3 hover:bg-slate-800/50 transition-colors"
          >
            <div>
              <span class="text-sm font-mono text-slate-200">{{ file.name }}</span>
              <span class="ml-3 text-xs text-slate-500">{{ file.description }}</span>
            </div>
            <Download :size="14" class="text-slate-500 shrink-0" />
          </a>
        </div>
      </div>

      <!-- IO index download (Log column written back) -->
      <div class="rounded-lg bg-slate-900 border border-slate-800 overflow-hidden">
        <div class="px-4 py-3 border-b border-slate-800">
          <h2 class="text-sm font-medium text-slate-300">Updated I/O Index</h2>
          <p class="text-xs text-slate-500 mt-0.5">Log column and red highlights written back to the source file.</p>
        </div>
        <div class="px-4 py-3">
          <a
            :href="gen.downloadUrl('io-index')"
            download
            class="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-slate-800 hover:bg-slate-700 text-sm text-slate-200 transition-colors"
          >
            <Download :size="14" />
            Download IO Index (with Log)
          </a>
        </div>
      </div>

      <!-- Row errors -->
      <div v-if="gen.result.error_count > 0" class="rounded-lg bg-slate-900 border border-slate-800 overflow-hidden">
        <div class="px-4 py-3 border-b border-slate-800 flex items-center gap-2">
          <h2 class="text-sm font-medium text-red-400">Row Errors</h2>
          <span class="text-xs text-slate-500">(written to Log column in Excel)</span>
        </div>
        <table class="w-full text-xs font-mono">
          <thead>
            <tr class="border-b border-slate-800">
              <th class="px-4 py-2 text-left text-slate-500 font-medium w-12">Row</th>
              <th class="px-4 py-2 text-left text-slate-500 font-medium">Tag</th>
              <th class="px-4 py-2 text-left text-slate-500 font-medium">Template</th>
              <th class="px-4 py-2 text-left text-slate-500 font-medium">Message</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="err in gen.result.errors"
              :key="`${err.row_number}-${err.tag_name}`"
              class="border-b border-slate-800/50 hover:bg-slate-800/40"
            >
              <td class="px-4 py-2 text-slate-500">{{ err.row_number }}</td>
              <td class="px-4 py-2 text-slate-300">{{ err.tag_name }}</td>
              <td class="px-4 py-2 text-slate-400">{{ err.template }}</td>
              <td class="px-4 py-2 text-red-400">{{ err.message }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Download } from 'lucide-vue-next'

const imports = useImportsStore()
const gen = useGenerationStore()

onMounted(() => imports.refreshStatus())

async function runGenerate() {
  await gen.generate().catch(() => {})
}

const summaryStats = computed(() => {
  const r = gen.result
  if (!r) return []
  return [
    { label: 'Tags', value: r.tag_count, color: 'text-amber-400' },
    { label: 'Alarms', value: r.alarm_count, color: 'text-blue-400' },
    { label: 'Cond. lines', value: r.conditioning_count, color: 'text-slate-300' },
    { label: 'Errors', value: r.error_count, color: r.error_count > 0 ? 'text-red-400' : 'text-green-400' },
  ]
})

const outputFiles = [
  { name: 'tags.xml', description: 'Twinsoft tag import' },
  { name: 'alarms.xml', description: 'Twinsoft alarm import' },
  { name: 'conditioning.txt', description: 'PLC conditioning assignments' },
  { name: 'function_blocks.txt', description: 'PLC function block calls' },
]
</script>
