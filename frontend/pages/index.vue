<!--*************************************************
 * Project:     IOManager
 * Author:      Peter Chrapchynski
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 *************************************************-->

<template>
  <div class="max-w-4xl space-y-8">
    <div>
      <h1 class="text-2xl font-semibold tracking-tight text-slate-100">Dashboard</h1>
      <p class="mt-1 text-sm text-slate-500">Twinsoft PLC tag &amp; alarm import generator</p>
    </div>

    <!-- Status cards -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <!-- Address map -->
      <div class="rounded-lg bg-slate-900 border border-slate-800 p-5 space-y-3">
        <div class="flex items-center justify-between">
          <span class="text-xs font-medium text-slate-500 uppercase tracking-wider">Address Map</span>
          <StatusBadge
            :status="imports.status.twinsoft_loaded ? 'success' : 'idle'"
            :label="imports.status.twinsoft_loaded ? 'Loaded' : 'Not loaded'"
          />
        </div>
        <div v-if="imports.status.twinsoft_loaded" class="space-y-1 font-mono text-xs text-slate-400">
          <div class="flex justify-between">
            <span>Coil</span>
            <span class="text-slate-200">{{ imports.status.coil_occupied }}</span>
          </div>
          <div class="flex justify-between">
            <span>Register</span>
            <span class="text-slate-200">{{ imports.status.register_occupied }}</span>
          </div>
        </div>
        <p v-else class="text-xs text-slate-600">Upload Twinsoft export XML to pre-occupy addresses.</p>
      </div>

      <!-- IO Index -->
      <div class="rounded-lg bg-slate-900 border border-slate-800 p-5 space-y-3">
        <div class="flex items-center justify-between">
          <span class="text-xs font-medium text-slate-500 uppercase tracking-wider">I/O Index</span>
          <StatusBadge
            :status="imports.status.io_index_loaded ? 'success' : 'warning'"
            :label="imports.status.io_index_loaded ? 'Loaded' : 'Required'"
          />
        </div>
        <div v-if="imports.status.io_index_loaded" class="space-y-1 font-mono text-xs text-slate-400">
          <div class="flex justify-between">
            <span>Rows</span>
            <span class="text-slate-200">{{ imports.status.row_count }}</span>
          </div>
        </div>
        <p v-else class="text-xs text-slate-600">Upload the IO Dist Excel file to begin.</p>
      </div>

      <!-- Last generation -->
      <div class="rounded-lg bg-slate-900 border border-slate-800 p-5 space-y-3">
        <div class="flex items-center justify-between">
          <span class="text-xs font-medium text-slate-500 uppercase tracking-wider">Generation</span>
          <StatusBadge
            :status="gen.result ? (gen.result.error_count > 0 ? 'warning' : 'success') : 'idle'"
            :label="gen.result ? (gen.result.error_count > 0 ? `${gen.result.error_count} errors` : 'OK') : 'Pending'"
          />
        </div>
        <div v-if="gen.result" class="space-y-1 font-mono text-xs text-slate-400">
          <div class="flex justify-between">
            <span>Tags</span>
            <span class="text-slate-200">{{ gen.result.tag_count }}</span>
          </div>
          <div class="flex justify-between">
            <span>Alarms</span>
            <span class="text-slate-200">{{ gen.result.alarm_count }}</span>
          </div>
        </div>
        <p v-else class="text-xs text-slate-600">Run generation after loading the I/O index.</p>
      </div>
    </div>

    <!-- Quick actions -->
    <div class="flex flex-wrap gap-3">
      <NuxtLink
        to="/import"
        class="px-4 py-2 rounded-md bg-slate-800 hover:bg-slate-700 text-sm text-slate-200 transition-colors"
      >
        Go to Import →
      </NuxtLink>
      <NuxtLink
        to="/export"
        class="px-4 py-2 rounded-md bg-cyan-500 hover:bg-cyan-400 text-sm font-medium text-slate-950 transition-colors"
      >
        Go to Generate →
      </NuxtLink>
    </div>

    <!-- Recent errors -->
    <div v-if="gen.result && gen.result.error_count > 0" class="rounded-lg bg-slate-900 border border-slate-800 overflow-hidden">
      <div class="px-4 py-3 border-b border-slate-800">
        <h2 class="text-sm font-medium text-red-400">Generation Errors ({{ gen.result.error_count }})</h2>
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
</template>

<script setup lang="ts">
const imports = useImportsStore()
const gen = useGenerationStore()

onMounted(() => imports.refreshStatus())
</script>
