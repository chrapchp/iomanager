<!--*************************************************
 * Project:     IOManager
 * Author:      Peter C
 * Date:        2026Jul04
 * History:     2026Jul04 - Initial creation; extracted from settings page
 *************************************************-->

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-semibold tracking-tight text-slate-100">Tag Rules</h1>
      <p class="mt-1 text-sm text-slate-500">Rule entries that drive tag and alarm generation.</p>
    </div>

    <!-- Sub-nav -->
    <div class="flex gap-0 border-b border-slate-800">
      <NuxtLink
        to="/settings"
        class="px-4 py-2 text-sm border-b-2 -mb-px transition-colors"
        active-class="border-amber-500 text-amber-400"
        inactive-class="border-transparent text-slate-500 hover:text-slate-300"
      >Config</NuxtLink>
      <NuxtLink
        to="/settings/rules"
        class="px-4 py-2 text-sm border-b-2 -mb-px transition-colors"
        active-class="border-amber-500 text-amber-400"
        inactive-class="border-transparent text-slate-500 hover:text-slate-300"
      >Tag Rules</NuxtLink>
    </div>

    <!-- Loading -->
    <div v-if="store.loading" class="text-sm text-slate-500 animate-pulse">Loading config…</div>

    <template v-else-if="store.config && draft">
      <!-- Rules table -->
      <div class="rounded-lg bg-slate-900 border border-slate-800 overflow-hidden">
        <div class="px-4 py-3 border-b border-slate-800">
          <h2 class="text-sm font-semibold text-slate-300">
            Rules
            <span class="ml-2 text-xs text-slate-600 font-normal">({{ draft.rules.length }} defined)</span>
          </h2>
        </div>
        <div class="overflow-x-auto">
          <table class="text-xs font-mono whitespace-nowrap">
            <thead>
              <tr class="border-b border-slate-800 bg-slate-800/40">
                <th class="px-3 py-2 text-left text-slate-500 font-medium">Role</th>
                <th class="px-3 py-2 text-left text-slate-500 font-medium">Addr</th>
                <th class="px-3 py-2 text-left text-slate-500 font-medium">Tag Suffix</th>
                <th class="px-3 py-2 text-left text-slate-500 font-medium">Class</th>
                <th class="px-3 py-2 text-left text-slate-500 font-medium">Desc Delim</th>
                <th class="px-3 py-2 text-left text-slate-500 font-medium">Desc Suffix</th>
                <th class="px-3 py-2 text-left text-slate-500 font-medium">Folder</th>
                <th class="px-3 py-2 text-center text-slate-500 font-medium">Write</th>
                <th class="px-3 py-2 text-left text-slate-500 font-medium">Write Min</th>
                <th class="px-3 py-2 text-left text-slate-500 font-medium">Write Max</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="(rule, ri) in draft.rules" :key="rule.name">
                <!-- Rule header row -->
                <tr class="border-b border-slate-700 bg-slate-800/20">
                  <td colspan="10" class="px-3 py-1.5">
                    <div class="flex items-center gap-4">
                      <span class="text-amber-400 font-semibold tracking-wide">{{ rule.name }}</span>
                      <div class="flex items-center gap-1.5">
                        <span class="text-slate-600">condition:</span>
                        <input
                          v-model="draft.rules[ri].condition_code"
                          type="text"
                          placeholder="none"
                          class="w-36 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 placeholder-slate-700 focus:outline-none focus:border-amber-500"
                        />
                      </div>
                      <div class="flex items-center gap-1.5">
                        <span class="text-slate-600">function block:</span>
                        <input
                          v-model="draft.rules[ri].function_block"
                          type="text"
                          placeholder="none"
                          class="w-72 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 placeholder-slate-700 focus:outline-none focus:border-amber-500"
                        />
                      </div>
                    </div>
                  </td>
                </tr>
                <!-- Entry rows -->
                <tr
                  v-for="(entry, ei) in rule.entries"
                  :key="entry.role"
                  class="border-b border-slate-800/50 hover:bg-slate-800/20"
                >
                  <td class="px-3 py-1">
                    <input
                      v-model="draft.rules[ri].entries[ei].role"
                      type="text"
                      class="w-20 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 focus:outline-none focus:border-amber-500"
                    />
                  </td>
                  <td class="px-3 py-1">
                    <input
                      v-model.number="draft.rules[ri].entries[ei].addr"
                      type="number"
                      min="0"
                      class="w-20 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-amber-300 focus:outline-none focus:border-amber-500"
                    />
                  </td>
                  <td class="px-3 py-1">
                    <input
                      v-model="draft.rules[ri].entries[ei].tag_suffix"
                      type="text"
                      class="w-20 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 focus:outline-none focus:border-amber-500"
                    />
                  </td>
                  <td class="px-3 py-1">
                    <select
                      v-model="draft.rules[ri].entries[ei].data_class"
                      class="w-24 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 focus:outline-none focus:border-amber-500"
                    >
                      <option v-for="dt in DATA_TYPES" :key="dt" :value="dt">{{ dt }}</option>
                    </select>
                  </td>
                  <td class="px-3 py-1">
                    <input
                      v-model="draft.rules[ri].entries[ei].desc_delimiter"
                      type="text"
                      class="w-14 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 focus:outline-none focus:border-amber-500"
                    />
                  </td>
                  <td class="px-3 py-1">
                    <input
                      v-model="draft.rules[ri].entries[ei].desc_suffix"
                      type="text"
                      class="w-36 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 focus:outline-none focus:border-amber-500"
                    />
                  </td>
                  <td class="px-3 py-1">
                    <input
                      v-model="draft.rules[ri].entries[ei].folder"
                      type="text"
                      class="w-72 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 focus:outline-none focus:border-amber-500"
                    />
                  </td>
                  <td class="px-3 py-1 text-center">
                    <input
                      v-model="draft.rules[ri].entries[ei].write_allowed"
                      type="checkbox"
                      class="accent-amber-500"
                    />
                  </td>
                  <td class="px-3 py-1">
                    <input
                      v-model="draft.rules[ri].entries[ei].write_allowed_min"
                      type="text"
                      class="w-16 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 focus:outline-none focus:border-amber-500"
                    />
                  </td>
                  <td class="px-3 py-1">
                    <input
                      v-model="draft.rules[ri].entries[ei].write_allowed_max"
                      type="text"
                      class="w-16 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 focus:outline-none focus:border-amber-500"
                    />
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Save -->
      <div class="flex items-center gap-4">
        <button
          :disabled="store.saving"
          class="px-5 py-2 rounded-md bg-amber-500 hover:bg-amber-400 disabled:opacity-40 disabled:cursor-not-allowed text-sm font-semibold text-slate-950 transition-colors"
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

const DATA_TYPES = ['BOOL', 'INT16', 'UINT16', 'INT32', 'UINT32', 'FLOAT', 'TEXT'] as const

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
