<!--*************************************************
 * Project:     IOManager
 * Author:      Peter C
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 *              2026Jul04 - Amber accent; amber tag names
 *************************************************-->

<template>
  <div class="space-y-6">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h1 class="text-2xl font-semibold tracking-tight text-slate-100">Alarms</h1>
        <p class="mt-1 text-sm text-slate-500">
          {{ gen.alarms.length }} alarm{{ gen.alarms.length !== 1 ? 's' : '' }} generated
        </p>
      </div>
      <input
        v-model="search"
        type="text"
        placeholder="Filter…"
        class="px-3 py-1.5 rounded-md bg-slate-800 border border-slate-700 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-amber-500 font-mono w-52"
      />
    </div>

    <!-- Empty state -->
    <div v-if="!gen.alarms.length" class="rounded-lg bg-slate-900 border border-slate-800 p-12 text-center">
      <p class="text-slate-500 text-sm">No alarms yet.</p>
      <NuxtLink to="/export" class="mt-2 inline-block text-sm text-amber-400 hover:text-amber-300 underline underline-offset-2">
        Run generation →
      </NuxtLink>
    </div>

    <!-- Table -->
    <div v-else class="rounded-lg bg-slate-900 border border-slate-800 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-xs font-mono">
          <thead>
            <tr class="border-b border-slate-800 bg-slate-900/80">
              <th class="px-4 py-3 text-left text-slate-500 font-medium">Tag</th>
              <th class="px-4 py-3 text-left text-slate-500 font-medium">Condition</th>
              <th class="px-4 py-3 text-left text-slate-500 font-medium">Message</th>
              <th class="px-4 py-3 text-left text-slate-500 font-medium">Recipient</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="alarm in filteredAlarms"
              :key="alarm.tag_name"
              class="border-b border-slate-800/50 hover:bg-slate-800/40 transition-colors"
            >
              <td class="px-4 py-2 text-amber-300">{{ alarm.tag_name }}</td>
              <td class="px-4 py-2">
                <span
                  class="px-1.5 py-0.5 rounded text-xs"
                  :class="alarm.condition === 'POS' ? 'bg-green-950 text-green-300' : 'bg-red-950 text-red-300'"
                >
                  {{ alarm.condition }}
                </span>
              </td>
              <td class="px-4 py-2 text-slate-300 max-w-xs truncate">{{ alarm.message || '—' }}</td>
              <td class="px-4 py-2 text-slate-400">{{ alarm.recipient }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="px-4 py-2 border-t border-slate-800 text-xs text-slate-600">
        Showing {{ filteredAlarms.length }} of {{ gen.alarms.length }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const gen = useGenerationStore()
const search = ref('')

onMounted(async () => {
  if (!gen.alarms.length) await gen.fetchAlarms()
})

const filteredAlarms = computed(() => {
  if (!search.value) return gen.alarms
  const q = search.value.toLowerCase()
  return gen.alarms.filter(
    (a) =>
      a.tag_name.toLowerCase().includes(q) ||
      a.message.toLowerCase().includes(q) ||
      a.recipient.toLowerCase().includes(q)
  )
})
</script>
