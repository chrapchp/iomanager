<!--*************************************************
 * Project:     IOManager
 * Author:      Peter Chrapchynski
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 *              2026Jun24 - Guard template on draft as well as store.config to avoid null render
 *************************************************-->

<template>
  <div class="max-w-3xl space-y-8">
    <div>
      <h1 class="text-2xl font-semibold tracking-tight text-slate-100">Settings</h1>
      <p class="mt-1 text-sm text-slate-500">View and edit the application configuration.</p>
    </div>

    <!-- Loading -->
    <div v-if="store.loading" class="text-sm text-slate-500 animate-pulse">Loading config…</div>

    <template v-else-if="store.config && draft">
      <!-- Target system -->
      <div class="rounded-lg bg-slate-900 border border-slate-800 p-5 space-y-3">
        <h2 class="text-sm font-semibold text-slate-300">Target System</h2>
        <select
          v-model="draft.target_system"
          class="px-3 py-1.5 rounded-md bg-slate-800 border border-slate-700 text-sm text-slate-200 focus:outline-none focus:border-cyan-600 font-mono"
        >
          <option value="twinsoft">twinsoft</option>
        </select>
      </div>

      <!-- Alarm defaults -->
      <div class="rounded-lg bg-slate-900 border border-slate-800 p-5 space-y-4">
        <h2 class="text-sm font-semibold text-slate-300">Alarm Defaults</h2>

        <div class="grid grid-cols-2 gap-4 text-sm">
          <div class="space-y-1">
            <label class="text-xs text-slate-500">Condition</label>
            <select
              v-model="draft.alarm_defaults.condition"
              class="w-full px-3 py-1.5 rounded-md bg-slate-800 border border-slate-700 text-slate-200 focus:outline-none focus:border-cyan-600 font-mono text-xs"
            >
              <option value="POS">POS (rising edge)</option>
              <option value="NEG">NEG (falling edge)</option>
            </select>
          </div>

          <div class="space-y-1">
            <label class="text-xs text-slate-500">Recipient</label>
            <input
              v-model="draft.alarm_defaults.recipient"
              type="text"
              class="w-full px-3 py-1.5 rounded-md bg-slate-800 border border-slate-700 text-slate-200 focus:outline-none focus:border-cyan-600 font-mono text-xs"
            />
          </div>

          <div class="space-y-1">
            <label class="text-xs text-slate-500">Handling</label>
            <select
              v-model="draft.alarm_defaults.options.handling"
              class="w-full px-3 py-1.5 rounded-md bg-slate-800 border border-slate-700 text-slate-200 focus:outline-none focus:border-cyan-600 font-mono text-xs"
            >
              <option value="ENABLED">ENABLED</option>
              <option value="DISABLED">DISABLED</option>
            </select>
          </div>

          <div class="space-y-1 flex flex-col">
            <label class="text-xs text-slate-500">Options</label>
            <div class="flex flex-col gap-1 mt-1">
              <label class="flex items-center gap-2 text-xs text-slate-400">
                <input v-model="draft.alarm_defaults.options.notify_end_of_alarm" type="checkbox" class="accent-cyan-500" />
                Notify end of alarm
              </label>
              <label class="flex items-center gap-2 text-xs text-slate-400">
                <input v-model="draft.alarm_defaults.call_all_recipients" type="checkbox" class="accent-cyan-500" />
                Call all recipients
              </label>
              <label class="flex items-center gap-2 text-xs text-slate-400">
                <input v-model="draft.alarm_defaults.is_report" type="checkbox" class="accent-cyan-500" />
                Is report
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Rules (read-only summary) -->
      <div class="rounded-lg bg-slate-900 border border-slate-800 overflow-hidden">
        <div class="px-4 py-3 border-b border-slate-800">
          <h2 class="text-sm font-semibold text-slate-300">
            Rules
            <span class="ml-2 text-xs text-slate-600 font-normal">({{ store.config.rules.length }} defined — edit config JSON to modify)</span>
          </h2>
        </div>
        <table class="w-full text-xs font-mono">
          <thead>
            <tr class="border-b border-slate-800">
              <th class="px-4 py-2 text-left text-slate-500 font-medium">Name</th>
              <th class="px-4 py-2 text-left text-slate-500 font-medium">Entries</th>
              <th class="px-4 py-2 text-left text-slate-500 font-medium">Condition</th>
              <th class="px-4 py-2 text-left text-slate-500 font-medium">FB</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="rule in store.config.rules"
              :key="rule.name"
              class="border-b border-slate-800/50 hover:bg-slate-800/30"
            >
              <td class="px-4 py-2 text-cyan-300">{{ rule.name }}</td>
              <td class="px-4 py-2 text-slate-400">{{ rule.entries.map((e) => e.role).join(', ') }}</td>
              <td class="px-4 py-2 text-slate-500">{{ rule.condition_code ?? '—' }}</td>
              <td class="px-4 py-2 text-slate-600 truncate max-w-xs">{{ rule.function_block ?? '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Templates (read-only) -->
      <div class="rounded-lg bg-slate-900 border border-slate-800 overflow-hidden">
        <div class="px-4 py-3 border-b border-slate-800">
          <h2 class="text-sm font-semibold text-slate-300">
            Templates
            <span class="ml-2 text-xs text-slate-600 font-normal">({{ store.config.templates.length }} defined)</span>
          </h2>
        </div>
        <table class="w-full text-xs font-mono">
          <thead>
            <tr class="border-b border-slate-800">
              <th class="px-4 py-2 text-left text-slate-500 font-medium">Template</th>
              <th class="px-4 py-2 text-left text-slate-500 font-medium">Rules</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="t in store.config.templates"
              :key="t.template"
              class="border-b border-slate-800/50 hover:bg-slate-800/30"
            >
              <td class="px-4 py-2 text-amber-300">{{ t.template }}</td>
              <td class="px-4 py-2 text-slate-400">{{ t.rules.join(', ') }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Save / status -->
      <div class="flex items-center gap-4">
        <button
          :disabled="store.saving"
          class="px-5 py-2 rounded-md bg-cyan-500 hover:bg-cyan-400 disabled:opacity-40 disabled:cursor-not-allowed text-sm font-semibold text-slate-950 transition-colors"
          @click="save"
        >
          {{ store.saving ? 'Saving…' : 'Save' }}
        </button>
        <span v-if="saved" class="text-sm text-green-400">Saved.</span>
        <span v-if="store.error" class="text-sm text-red-400">{{ store.error }}</span>
      </div>
    </template>

    <div v-else class="text-sm text-red-400">{{ store.error }}</div>
  </div>
</template>

<script setup lang="ts">
import type { AppConfig } from '~/types/api'

const store = useConfigStore()
const saved = ref(false)
const draft = ref<AppConfig | null>(null)

onMounted(async () => {
  await store.fetchConfig()
  if (store.config) draft.value = JSON.parse(JSON.stringify(store.config))
})

async function save() {
  if (!draft.value) return
  saved.value = false
  try {
    await store.saveConfig(draft.value)
    saved.value = true
    setTimeout(() => { saved.value = false }, 3000)
  } catch {}
}
</script>
