<!--*************************************************
 * Project:     IOManager
 * Author:      Peter C
 * Date:        2026Jul04
 * History:     2026Jul04 - Initial creation; extracted from settings page
 *              2026Jul04 - Add rule delete, entry delete, create rule modal
 *              2026Jul04 - Fix: keep inline confirm open on delete error
 *              2026Jul04 - Redesign: card-per-rule, click-to-edit, Write Min/Max conditional
 *              2026Jul04 - Widen fb field to ~60 chars (w-96 input, max-w-sm read-only)
 *              2026Jul07 - Add inline rename flow with template-reference warning
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

    <div v-if="store.loading" class="text-sm text-slate-500 animate-pulse">Loading config…</div>

    <template v-else-if="store.config && draft">
      <!-- Top bar -->
      <div class="flex items-center justify-between">
        <p class="text-xs text-slate-600 font-mono">{{ draft.rules.length }} rules defined</p>
        <button
          class="px-3 py-1 rounded text-xs font-semibold bg-amber-500/10 border border-amber-500/30 text-amber-400 hover:bg-amber-500/20 transition-colors"
          @click="openCreateModal"
        >+ New Rule</button>
      </div>

      <!-- Rule cards -->
      <div class="space-y-4">
        <div
          v-for="(rule, ri) in draft.rules"
          :key="rule.name"
          class="rounded-lg border border-slate-800 bg-slate-900 overflow-hidden"
        >
          <!-- Card header -->
          <div class="flex items-center gap-4 px-4 py-3 border-b border-slate-800 bg-slate-800/30 border-l-2 border-l-amber-500/60">
            <!-- Rule name (always visible) -->
            <span class="font-mono font-bold text-amber-400 text-sm tracking-wide min-w-max">{{ rule.name }}</span>

            <!-- ── Rename mode ── -->
            <template v-if="renameTarget === rule.name">
              <!-- Step 1: input new name -->
              <template v-if="renameStep === 'input'">
                <span class="text-xs text-slate-500">→</span>
                <input
                  v-model="renameNewName"
                  type="text"
                  class="w-32 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-amber-300 focus:outline-none focus:border-amber-500 text-xs font-mono"
                  @keydown.enter="requestRename(rule.name)"
                  @keydown.esc="cancelRename"
                />
                <span v-if="renameError" class="text-red-400 text-xs">{{ renameError }}</span>
                <div class="ml-auto flex items-center gap-2 shrink-0">
                  <button
                    :disabled="busy"
                    class="px-3 py-1 rounded text-xs font-semibold bg-amber-500/10 border border-amber-500/30 text-amber-400 hover:bg-amber-500/20 disabled:opacity-40 transition-colors"
                    @click="requestRename(rule.name)"
                  >{{ busy ? 'Renaming…' : 'Rename' }}</button>
                  <button
                    class="text-xs text-slate-500 hover:text-slate-300 transition-colors"
                    @click="cancelRename"
                  >Cancel</button>
                </div>
              </template>
              <!-- Step 2: confirm cascade -->
              <template v-else>
                <span class="text-xs text-amber-300/80">
                  Referenced in templates:
                  <span class="font-semibold">{{ renameRefs.join(', ') }}</span>
                  — those references will also be renamed.
                </span>
                <div class="ml-auto flex items-center gap-2 shrink-0">
                  <button
                    class="text-xs text-slate-500 hover:text-slate-300 transition-colors"
                    @click="cancelRename"
                  >Cancel</button>
                  <button
                    :disabled="busy"
                    class="px-3 py-1 rounded text-xs font-semibold bg-amber-500 hover:bg-amber-400 disabled:opacity-40 text-slate-950 transition-colors"
                    @click="executeRename(rule.name)"
                  >{{ busy ? 'Renaming…' : 'Proceed' }}</button>
                </div>
              </template>
            </template>

            <!-- ── Normal / edit / delete mode ── -->
            <template v-else>
              <!-- Metadata: edit mode shows inputs, read-only shows values -->
              <template v-if="editingRule === rule.name">
                <div class="flex items-center gap-1.5">
                  <span class="text-xs text-slate-600">cond:</span>
                  <input
                    v-model="draft.rules[ri].condition_code"
                    type="text"
                    placeholder="none"
                    class="w-36 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 placeholder-slate-700 focus:outline-none focus:border-amber-500 text-xs font-mono"
                  />
                </div>
                <div class="flex items-center gap-1.5">
                  <span class="text-xs text-slate-600">fb:</span>
                  <input
                    v-model="draft.rules[ri].function_block"
                    type="text"
                    placeholder="none"
                    class="w-96 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 placeholder-slate-700 focus:outline-none focus:border-amber-500 text-xs font-mono"
                  />
                </div>
              </template>
              <template v-else>
                <span class="text-xs">
                  <span class="text-slate-600">cond: </span>
                  <span class="text-slate-300 font-mono">{{ rule.condition_code || '—' }}</span>
                </span>
                <span class="text-xs max-w-sm truncate">
                  <span class="text-slate-600">fb: </span>
                  <span class="text-slate-400 font-mono">{{ rule.function_block || '—' }}</span>
                </span>
              </template>

              <!-- Actions -->
              <div class="ml-auto flex items-center gap-2 shrink-0">
                <span v-if="editingRule === rule.name && saveError" class="text-red-400 text-xs max-w-xs truncate">{{ saveError }}</span>

                <!-- Edit / Done / Cancel -->
                <template v-if="editingRule === rule.name">
                  <button
                    :disabled="busy"
                    class="px-3 py-1 rounded text-xs font-semibold bg-amber-500 hover:bg-amber-400 disabled:opacity-40 text-slate-950 transition-colors"
                    @click="doneEdit(rule.name)"
                  >{{ busy ? 'Saving…' : 'Done' }}</button>
                  <button
                    class="px-3 py-1 rounded text-xs border border-slate-700 text-slate-400 hover:text-slate-200 transition-colors"
                    @click="cancelEdit(rule.name)"
                  >Cancel</button>
                </template>
                <button
                  v-else
                  class="px-3 py-1 rounded text-xs border border-slate-700 text-slate-400 hover:text-slate-200 transition-colors"
                  @click="enterEdit(rule.name)"
                >Edit</button>

                <!-- Rename -->
                <button
                  v-if="editingRule !== rule.name && deleteRuleTarget !== rule.name"
                  class="px-3 py-1 rounded text-xs border border-slate-700 text-slate-400 hover:text-slate-200 transition-colors"
                  @click="startRename(rule.name)"
                >Rename</button>

                <!-- Delete rule (inline confirm) -->
                <template v-if="deleteRuleTarget === rule.name">
                  <span class="text-red-400 text-xs">Delete <span class="font-semibold">{{ rule.name }}</span>?</span>
                  <button class="text-xs text-slate-500 hover:text-slate-300 transition-colors" @click="deleteRuleTarget = null">Cancel</button>
                  <button
                    :disabled="busy"
                    class="text-xs text-red-400 hover:text-red-300 disabled:opacity-40 transition-colors"
                    @click="confirmDeleteRule(rule.name)"
                  >Yes, delete</button>
                  <span v-if="ruleError" class="text-red-400 text-xs max-w-xs truncate">{{ ruleError }}</span>
                </template>
                <button
                  v-else-if="editingRule !== rule.name"
                  class="text-xs text-slate-600 hover:text-red-400 transition-colors"
                  @click="startDelete(rule.name)"
                >Delete</button>
              </div>
            </template>
          </div>

          <!-- Entries table -->
          <div class="overflow-x-auto">
            <table class="text-xs font-mono whitespace-nowrap w-full">
              <thead>
                <tr class="border-b border-slate-800/60 bg-slate-800/10">
                  <th class="px-3 py-2 text-left text-slate-600 font-medium">Role</th>
                  <th class="px-3 py-2 text-left text-slate-600 font-medium">Addr</th>
                  <th class="px-3 py-2 text-left text-slate-600 font-medium">Suffix</th>
                  <th class="px-3 py-2 text-left text-slate-600 font-medium">Class</th>
                  <th class="px-3 py-2 text-left text-slate-600 font-medium">Delim</th>
                  <th class="px-3 py-2 text-left text-slate-600 font-medium">Desc Suffix</th>
                  <th class="px-3 py-2 text-left text-slate-600 font-medium">Folder</th>
                  <th class="px-3 py-2 text-left text-slate-600 font-medium">Write</th>
                  <!-- Delete col header only in edit mode -->
                  <th v-if="editingRule === rule.name" class="px-3 py-2 w-6"></th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(entry, ei) in rule.entries"
                  :key="ei"
                  class="border-b border-slate-800/40 last:border-0"
                  :class="editingRule === rule.name ? 'bg-slate-800/10' : 'hover:bg-slate-800/10'"
                >
                  <!-- ── Edit mode ── -->
                  <template v-if="editingRule === rule.name">
                    <td class="px-2 py-1.5">
                      <input
                        v-model="draft.rules[ri].entries[ei].role"
                        type="text"
                        class="w-20 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 focus:outline-none focus:border-amber-500"
                      />
                    </td>
                    <td class="px-2 py-1.5">
                      <input
                        v-model.number="draft.rules[ri].entries[ei].addr"
                        type="number"
                        min="0"
                        class="w-20 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-amber-300 focus:outline-none focus:border-amber-500"
                      />
                    </td>
                    <td class="px-2 py-1.5">
                      <input
                        v-model="draft.rules[ri].entries[ei].tag_suffix"
                        type="text"
                        class="w-16 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 focus:outline-none focus:border-amber-500"
                      />
                    </td>
                    <td class="px-2 py-1.5">
                      <select
                        v-model="draft.rules[ri].entries[ei].data_class"
                        class="w-24 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 focus:outline-none focus:border-amber-500"
                      >
                        <option v-for="dt in DATA_TYPES" :key="dt" :value="dt">{{ dt }}</option>
                      </select>
                    </td>
                    <td class="px-2 py-1.5">
                      <input
                        v-model="draft.rules[ri].entries[ei].desc_delimiter"
                        type="text"
                        class="w-14 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 focus:outline-none focus:border-amber-500"
                      />
                    </td>
                    <td class="px-2 py-1.5">
                      <input
                        v-model="draft.rules[ri].entries[ei].desc_suffix"
                        type="text"
                        class="w-32 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 focus:outline-none focus:border-amber-500"
                      />
                    </td>
                    <td class="px-2 py-1.5">
                      <input
                        v-model="draft.rules[ri].entries[ei].folder"
                        type="text"
                        class="w-64 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 focus:outline-none focus:border-amber-500"
                      />
                    </td>
                    <td class="px-2 py-1.5">
                      <div class="flex flex-col gap-1">
                        <input
                          v-model="draft.rules[ri].entries[ei].write_allowed"
                          type="checkbox"
                          class="accent-amber-500"
                        />
                        <template v-if="draft.rules[ri].entries[ei].write_allowed">
                          <div class="flex items-center gap-1 mt-0.5">
                            <span class="text-slate-600">min</span>
                            <input
                              v-model="draft.rules[ri].entries[ei].write_allowed_min"
                              type="text"
                              class="w-14 px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 focus:outline-none focus:border-amber-500"
                            />
                          </div>
                          <div class="flex items-center gap-1">
                            <span class="text-slate-600">max</span>
                            <input
                              v-model="draft.rules[ri].entries[ei].write_allowed_max"
                              type="text"
                              class="w-14 px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 focus:outline-none focus:border-amber-500"
                            />
                          </div>
                        </template>
                      </div>
                    </td>
                    <td class="px-2 py-1.5 text-center align-top">
                      <button
                        :disabled="rule.entries.length === 1"
                        :title="rule.entries.length === 1 ? 'Rule must have at least one entry' : 'Delete entry'"
                        class="text-slate-600 hover:text-red-400 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                        @click="removeEntry(ri, ei)"
                      >×</button>
                    </td>
                  </template>

                  <!-- ── Read-only ── -->
                  <template v-else>
                    <td class="px-3 py-2 text-slate-300">{{ entry.role }}</td>
                    <td class="px-3 py-2 text-amber-300/80">{{ entry.addr }}</td>
                    <td class="px-3 py-2 text-slate-500">{{ entry.tag_suffix || '—' }}</td>
                    <td class="px-3 py-2 text-slate-300">{{ entry.data_class }}</td>
                    <td class="px-3 py-2 text-slate-500">{{ entry.desc_delimiter || '—' }}</td>
                    <td class="px-3 py-2 text-slate-400">{{ entry.desc_suffix || '—' }}</td>
                    <td class="px-3 py-2 text-slate-400 max-w-xs truncate">{{ entry.folder || '—' }}</td>
                    <td class="px-3 py-2">
                      <span :class="entry.write_allowed ? 'text-amber-400' : 'text-slate-700'">
                        {{ entry.write_allowed ? '✓' : '—' }}
                      </span>
                      <div v-if="entry.write_allowed" class="text-slate-500 text-xs mt-0.5">
                        {{ entry.write_allowed_min || '?' }}…{{ entry.write_allowed_max || '?' }}
                      </div>
                    </td>
                  </template>
                </tr>
              </tbody>

              <!-- Add entry row — edit mode only -->
              <tfoot v-if="editingRule === rule.name">
                <tr class="border-t border-slate-800/60">
                  <td :colspan="9" class="px-3 py-2">
                    <button
                      class="text-xs text-amber-400/70 hover:text-amber-400 transition-colors"
                      @click="addEntry(ri)"
                    >+ Add entry</button>
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </div>
    </template>

    <div v-else-if="store.error" class="text-sm text-red-400">{{ store.error }}</div>

    <!-- Create rule modal -->
    <Teleport to="body">
      <div
        v-if="modal.open"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/70"
        @click.self="closeModal"
      >
        <div class="bg-slate-900 border border-slate-700 rounded-lg p-6 w-full max-w-2xl space-y-5 shadow-2xl max-h-[90vh] overflow-y-auto">
          <h3 class="text-sm font-semibold text-slate-200">New Rule</h3>

          <div class="space-y-1">
            <label class="text-xs text-slate-500">Rule Name <span class="text-slate-600">(e.g. _TC)</span></label>
            <input
              v-model="modal.name"
              type="text"
              placeholder="_RULE"
              class="w-full px-3 py-1.5 rounded-md bg-slate-800 border border-slate-700 text-slate-200 focus:outline-none focus:border-amber-500 font-mono text-xs"
            />
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-1">
              <label class="text-xs text-slate-500">Condition Code</label>
              <input
                v-model="modal.condition_code"
                type="text"
                placeholder="none"
                class="w-full px-3 py-1.5 rounded-md bg-slate-800 border border-slate-700 text-slate-200 focus:outline-none focus:border-amber-500 font-mono text-xs"
              />
            </div>
            <div class="space-y-1">
              <label class="text-xs text-slate-500">Function Block</label>
              <input
                v-model="modal.function_block"
                type="text"
                placeholder="none"
                class="w-full px-3 py-1.5 rounded-md bg-slate-800 border border-slate-700 text-slate-200 focus:outline-none focus:border-amber-500 font-mono text-xs"
              />
            </div>
          </div>

          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <label class="text-xs text-slate-500">Entries <span class="text-slate-600">(at least one required)</span></label>
              <button
                class="text-xs text-amber-400 hover:text-amber-300 transition-colors"
                @click="addModalEntry"
              >+ Add entry</button>
            </div>
            <div class="overflow-x-auto rounded border border-slate-800">
              <table class="text-xs font-mono whitespace-nowrap">
                <thead>
                  <tr class="border-b border-slate-800 bg-slate-800/40">
                    <th class="px-2 py-1.5 text-left text-slate-500">Role</th>
                    <th class="px-2 py-1.5 text-left text-slate-500">Addr</th>
                    <th class="px-2 py-1.5 text-left text-slate-500">Suffix</th>
                    <th class="px-2 py-1.5 text-left text-slate-500">Class</th>
                    <th class="px-2 py-1.5 text-left text-slate-500">Folder</th>
                    <th class="px-2 py-1.5 text-center text-slate-500">Write</th>
                    <th class="px-2 py-1.5 w-6"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(entry, i) in modal.entries"
                    :key="i"
                    class="border-b border-slate-800/50"
                  >
                    <td class="px-2 py-1">
                      <input v-model="entry.role" type="text" placeholder="io"
                        class="w-16 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 focus:outline-none focus:border-amber-500" />
                    </td>
                    <td class="px-2 py-1">
                      <input v-model.number="entry.addr" type="number" min="0"
                        class="w-20 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-amber-300 focus:outline-none focus:border-amber-500" />
                    </td>
                    <td class="px-2 py-1">
                      <input v-model="entry.tag_suffix" type="text"
                        class="w-16 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 focus:outline-none focus:border-amber-500" />
                    </td>
                    <td class="px-2 py-1">
                      <select v-model="entry.data_class"
                        class="w-20 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 focus:outline-none focus:border-amber-500">
                        <option v-for="dt in DATA_TYPES" :key="dt" :value="dt">{{ dt }}</option>
                      </select>
                    </td>
                    <td class="px-2 py-1">
                      <input v-model="entry.folder" type="text" placeholder="IO\\..."
                        class="w-44 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 focus:outline-none focus:border-amber-500" />
                    </td>
                    <td class="px-2 py-1 text-center">
                      <input v-model="entry.write_allowed" type="checkbox" class="accent-amber-500" />
                    </td>
                    <td class="px-2 py-1 text-center">
                      <button
                        :disabled="modal.entries.length === 1"
                        class="text-slate-600 hover:text-red-400 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                        @click="modal.entries.splice(i, 1)"
                      >×</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <p v-if="modal.error" class="text-xs text-red-400">{{ modal.error }}</p>

          <div class="flex gap-3 pt-1">
            <button
              :disabled="busy"
              class="px-4 py-1.5 rounded-md bg-amber-500 hover:bg-amber-400 disabled:opacity-40 disabled:cursor-not-allowed text-xs font-semibold text-slate-950 transition-colors"
              @click="submitCreate"
            >{{ busy ? 'Creating…' : 'Create' }}</button>
            <button
              class="px-4 py-1.5 rounded-md border border-slate-700 text-xs text-slate-400 hover:text-slate-200 transition-colors"
              @click="closeModal"
            >Cancel</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import type { AppConfig, RuleEntry } from '~/types/api'

const DATA_TYPES = ['BOOL', 'INT16', 'UINT16', 'INT32', 'UINT32', 'FLOAT', 'TEXT'] as const

const store = useConfigStore()
const busy = ref(false)
const draft = ref<AppConfig | null>(null)

// Per-card edit state
const editingRule = ref<string | null>(null)
const saveError = ref<string | null>(null)

// Delete rule state
const deleteRuleTarget = ref<string | null>(null)
const ruleError = ref<string | null>(null)

// Rename rule state
const renameTarget = ref<string | null>(null)
const renameNewName = ref('')
const renameStep = ref<'input' | 'confirm'>('input')
const renameRefs = ref<string[]>([])
const renameError = ref<string | null>(null)

function blankEntry(): RuleEntry {
  return {
    role: '', addr: 0, tag_suffix: '', data_class: 'BOOL',
    desc_delimiter: '', desc_suffix: '', folder: '',
    write_allowed: false, write_allowed_min: '', write_allowed_max: '',
  }
}

onMounted(async () => {
  await store.fetchConfig()
  if (store.config) draft.value = JSON.parse(JSON.stringify(store.config))
})

// ── Edit mode ─────────────────────────────────────────────────────────────────

function startDelete(ruleName: string) {
  editingRule.value = null
  renameTarget.value = null
  renameError.value = null
  saveError.value = null
  ruleError.value = null
  deleteRuleTarget.value = ruleName
}

function startRename(ruleName: string) {
  editingRule.value = null
  deleteRuleTarget.value = null
  ruleError.value = null
  saveError.value = null
  renameTarget.value = ruleName
  renameNewName.value = ruleName
  renameStep.value = 'input'
  renameRefs.value = []
  renameError.value = null
}

function cancelRename() {
  renameTarget.value = null
  renameStep.value = 'input'
  renameError.value = null
}

function requestRename(ruleName: string) {
  const newName = renameNewName.value.trim()
  if (!newName) { renameError.value = 'Name is required.'; return }
  if (newName === ruleName) { cancelRename(); return }
  const refs = store.config?.templates
    .filter(t => t.rules.includes(ruleName))
    .map(t => t.template) ?? []
  renameRefs.value = refs
  if (refs.length > 0) {
    renameStep.value = 'confirm'
  } else {
    executeRename(ruleName)
  }
}

async function executeRename(oldName: string) {
  renameError.value = null
  busy.value = true
  try {
    await store.renameRule(oldName, renameNewName.value.trim())
    draft.value = JSON.parse(JSON.stringify(store.config))
    cancelRename()
  } catch (e: any) {
    renameError.value = e.data?.detail ?? e.message ?? 'Rename failed'
    renameStep.value = 'input'
  } finally {
    busy.value = false
  }
}

function enterEdit(ruleName: string) {
  saveError.value = null
  deleteRuleTarget.value = null
  ruleError.value = null
  renameTarget.value = null
  // Re-sync this rule from canonical store state to discard any stale draft changes
  if (store.config && draft.value) {
    const ruleIdx = draft.value.rules.findIndex(r => r.name === ruleName)
    const canonical = store.config.rules.find(r => r.name === ruleName)
    if (ruleIdx !== -1 && canonical) {
      draft.value.rules[ruleIdx] = JSON.parse(JSON.stringify(canonical))
    }
  }
  editingRule.value = ruleName
}

function cancelEdit(ruleName: string) {
  // Restore rule from store, discarding all local edits
  if (store.config && draft.value) {
    const ruleIdx = draft.value.rules.findIndex(r => r.name === ruleName)
    const canonical = store.config.rules.find(r => r.name === ruleName)
    if (ruleIdx !== -1 && canonical) {
      draft.value.rules[ruleIdx] = JSON.parse(JSON.stringify(canonical))
    }
  }
  editingRule.value = null
  saveError.value = null
}

async function doneEdit(_ruleName: string) {
  if (!draft.value) return
  saveError.value = null
  busy.value = true
  try {
    await store.saveConfig(draft.value)
    draft.value = JSON.parse(JSON.stringify(store.config))
    editingRule.value = null
  } catch (e: any) {
    saveError.value = e.data?.detail ?? e.message ?? 'Save failed'
  } finally {
    busy.value = false
  }
}

// ── Entry mutations (local — committed on Done) ───────────────────────────────

function addEntry(ruleIndex: number) {
  draft.value?.rules[ruleIndex].entries.push(blankEntry())
}

function removeEntry(ruleIndex: number, entryIndex: number) {
  draft.value?.rules[ruleIndex].entries.splice(entryIndex, 1)
}

// ── Delete rule ───────────────────────────────────────────────────────────────

async function confirmDeleteRule(name: string) {
  ruleError.value = null
  busy.value = true
  try {
    await store.deleteRule(name)
    draft.value = JSON.parse(JSON.stringify(store.config))
    deleteRuleTarget.value = null
  } catch (e: any) {
    ruleError.value = e.data?.detail ?? e.message ?? 'Delete failed'
  } finally {
    busy.value = false
  }
}

// ── Create rule modal ─────────────────────────────────────────────────────────

const modal = ref({
  open: false,
  name: '',
  condition_code: '',
  function_block: '',
  entries: [blankEntry()] as RuleEntry[],
  error: null as string | null,
})

function openCreateModal() {
  modal.value = { open: true, name: '', condition_code: '', function_block: '', entries: [blankEntry()], error: null }
}

function closeModal() { modal.value.open = false }

function addModalEntry() { modal.value.entries.push(blankEntry()) }

async function submitCreate() {
  modal.value.error = null
  if (!modal.value.name.trim()) { modal.value.error = 'Rule name is required.'; return }
  if (modal.value.entries.some(e => !e.role.trim())) { modal.value.error = 'All entries must have a role.'; return }
  busy.value = true
  try {
    await store.createRule({
      name: modal.value.name.trim(),
      entries: modal.value.entries,
      condition_code: modal.value.condition_code.trim() || null,
      function_block: modal.value.function_block.trim() || null,
    })
    draft.value = JSON.parse(JSON.stringify(store.config))
    closeModal()
  } catch (e: any) {
    modal.value.error = e.data?.detail ?? e.message ?? 'Failed to create rule'
  } finally {
    busy.value = false
  }
}
</script>
