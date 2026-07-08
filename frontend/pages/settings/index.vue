<!--*************************************************
 * Project:     IOManager
 * Author:      Peter Chrapchynski
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 *              2026Jun24 - Guard template on draft as well as store.config to avoid null render
 *              2026Jul04 - Add template CRUD (create, edit, delete) with modal and inline confirm
 *              2026Jul04 - Make rule entry Modbus addresses editable
 *              2026Jul04 - Expand rules table to all editable fields
 *              2026Jul04 - Amber accent throughout
 *              2026Jul04 - Rename to Config; move rules to /settings/rules; add sub-nav
 *              2026Jul07 - Fix: resync draft.templates after modal CRUD so global Save doesn't overwrite
 *              2026Jul07 - Add template rename with virtual-tag reference warning
 *************************************************-->

<template>
  <div class="max-w-3xl space-y-8">
    <div>
      <h1 class="text-2xl font-semibold tracking-tight text-slate-100">Config</h1>
      <p class="mt-1 text-sm text-slate-500">Application configuration and template mappings.</p>
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
      <!-- Target system -->
      <div class="rounded-lg bg-slate-900 border border-slate-800 p-5 space-y-3">
        <h2 class="text-sm font-semibold text-slate-300">Target System</h2>
        <select
          v-model="draft.target_system"
          class="px-3 py-1.5 rounded-md bg-slate-800 border border-slate-700 text-sm text-slate-200 focus:outline-none focus:border-amber-500 font-mono"
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
              class="w-full px-3 py-1.5 rounded-md bg-slate-800 border border-slate-700 text-slate-200 focus:outline-none focus:border-amber-500 font-mono text-xs"
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
              class="w-full px-3 py-1.5 rounded-md bg-slate-800 border border-slate-700 text-slate-200 focus:outline-none focus:border-amber-500 font-mono text-xs"
            />
          </div>

          <div class="space-y-1">
            <label class="text-xs text-slate-500">Handling</label>
            <select
              v-model="draft.alarm_defaults.options.handling"
              class="w-full px-3 py-1.5 rounded-md bg-slate-800 border border-slate-700 text-slate-200 focus:outline-none focus:border-amber-500 font-mono text-xs"
            >
              <option value="ENABLED">ENABLED</option>
              <option value="DISABLED">DISABLED</option>
            </select>
          </div>

          <div class="space-y-1 flex flex-col">
            <label class="text-xs text-slate-500">Options</label>
            <div class="flex flex-col gap-1 mt-1">
              <label class="flex items-center gap-2 text-xs text-slate-400">
                <input v-model="draft.alarm_defaults.options.notify_end_of_alarm" type="checkbox" class="accent-amber-500" />
                Notify end of alarm
              </label>
              <label class="flex items-center gap-2 text-xs text-slate-400">
                <input v-model="draft.alarm_defaults.call_all_recipients" type="checkbox" class="accent-amber-500" />
                Call all recipients
              </label>
              <label class="flex items-center gap-2 text-xs text-slate-400">
                <input v-model="draft.alarm_defaults.is_report" type="checkbox" class="accent-amber-500" />
                Is report
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Templates CRUD -->
      <div class="rounded-lg bg-slate-900 border border-slate-800 overflow-hidden">
        <div class="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
          <h2 class="text-sm font-semibold text-slate-300">
            Templates
            <span class="ml-2 text-xs text-slate-600 font-normal">({{ store.config.templates.length }} defined)</span>
          </h2>
          <button
            class="px-3 py-1 rounded text-xs font-semibold bg-amber-500/10 border border-amber-500/30 text-amber-400 hover:bg-amber-500/20 transition-colors"
            @click="openCreateModal"
          >
            + New Template
          </button>
        </div>
        <table class="w-full text-xs font-mono">
          <thead>
            <tr class="border-b border-slate-800">
              <th class="px-4 py-2 text-left text-slate-500 font-medium">Template</th>
              <th class="px-4 py-2 text-left text-slate-500 font-medium">Rules</th>
              <th class="px-4 py-2 text-right text-slate-500 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="t in store.config.templates"
              :key="t.template"
              class="border-b border-slate-800/50"
            >
              <!-- ── Normal row ── -->
              <template v-if="renameTemplateTarget !== t.template && deleteTarget !== t.template">
                <td class="px-4 py-2 text-amber-300">{{ t.template }}</td>
                <td class="px-4 py-2 text-slate-400">{{ t.rules.join(', ') }}</td>
                <td class="px-4 py-2 text-right space-x-2">
                  <button class="text-slate-500 hover:text-amber-400 transition-colors" @click="openEditModal(t)">Edit</button>
                  <button class="text-slate-500 hover:text-slate-300 transition-colors" @click="startTemplateRename(t.template)">Rename</button>
                  <button class="text-slate-500 hover:text-red-400 transition-colors" @click="deleteTarget = t.template; renameTemplateTarget = null">Delete</button>
                </td>
              </template>

              <!-- ── Rename: step 1 — input ── -->
              <template v-else-if="renameTemplateTarget === t.template && renameTemplateStep === 'input'">
                <td class="px-4 py-2" colspan="2">
                  <div class="flex items-center gap-2">
                    <span class="text-xs text-slate-500">Rename</span>
                    <span class="text-xs text-amber-300 font-mono">{{ t.template }}</span>
                    <span class="text-xs text-slate-500">→</span>
                    <input
                      v-model="renameTemplateNewName"
                      type="text"
                      class="w-32 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-amber-300 focus:outline-none focus:border-amber-500 text-xs font-mono"
                      @keydown.enter="requestTemplateRename(t.template)"
                      @keydown.esc="cancelTemplateRename"
                    />
                    <span v-if="renameTemplateError" class="text-red-400 text-xs">{{ renameTemplateError }}</span>
                  </div>
                </td>
                <td class="px-4 py-2 text-right space-x-2">
                  <button
                    :disabled="templateBusy"
                    class="text-amber-400 hover:text-amber-300 disabled:opacity-40 transition-colors"
                    @click="requestTemplateRename(t.template)"
                  >{{ templateBusy ? 'Renaming…' : 'Rename' }}</button>
                  <button class="text-slate-500 hover:text-slate-300 transition-colors" @click="cancelTemplateRename">Cancel</button>
                </td>
              </template>

              <!-- ── Rename: step 2 — confirm virtual-tag cascade ── -->
              <template v-else-if="renameTemplateTarget === t.template && renameTemplateStep === 'confirm'">
                <td class="px-4 py-2 text-amber-300/80 text-xs" colspan="2">
                  Referenced by <span class="font-semibold">{{ renameTemplateRefs }}</span>
                  virtual tag {{ renameTemplateRefs === 1 ? 'entry' : 'entries' }} — those references will also be renamed.
                </td>
                <td class="px-4 py-2 text-right space-x-2">
                  <button class="text-slate-500 hover:text-slate-300 transition-colors" @click="cancelTemplateRename">Cancel</button>
                  <button
                    :disabled="templateBusy"
                    class="text-amber-400 hover:text-amber-300 disabled:opacity-40 transition-colors"
                    @click="executeTemplateRename(t.template)"
                  >{{ templateBusy ? 'Renaming…' : 'Proceed' }}</button>
                </td>
              </template>

              <!-- ── Delete confirmation ── -->
              <template v-else>
                <td class="px-4 py-2 text-red-400 text-xs" colspan="2">
                  Delete <span class="font-semibold">{{ t.template }}</span>? This cannot be undone.
                </td>
                <td class="px-4 py-2 text-right space-x-2">
                  <button class="text-slate-500 hover:text-slate-300 transition-colors" @click="deleteTarget = null">Cancel</button>
                  <button
                    :disabled="templateBusy"
                    class="text-red-400 hover:text-red-300 disabled:opacity-40 transition-colors"
                    @click="confirmDelete(t.template)"
                  >Yes, delete</button>
                </td>
              </template>
            </tr>
          </tbody>
        </table>
        <p v-if="templateError" class="px-4 py-2 text-xs text-red-400">{{ templateError }}</p>
      </div>

      <!-- Save / status -->
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

    <!-- Template modal (create / edit) -->
    <Teleport to="body">
      <div
        v-if="modal.open"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/70"
        @click.self="closeModal"
      >
        <div class="bg-slate-900 border border-slate-700 rounded-lg p-6 w-full max-w-md space-y-5 shadow-2xl">
          <h3 class="text-sm font-semibold text-slate-200">
            {{ modal.mode === 'create' ? 'New Template' : `Edit Template — ${modal.name}` }}
          </h3>

          <!-- Template name (create only) -->
          <div v-if="modal.mode === 'create'" class="space-y-1">
            <label class="text-xs text-slate-500">Template Name</label>
            <input
              v-model="modal.name"
              type="text"
              placeholder="e.g. TC"
              class="w-full px-3 py-1.5 rounded-md bg-slate-800 border border-slate-700 text-slate-200 focus:outline-none focus:border-amber-500 font-mono text-xs"
            />
          </div>

          <!-- Rule checkboxes -->
          <div class="space-y-2">
            <label class="text-xs text-slate-500">Rules <span class="text-slate-600">(select one or more)</span></label>
            <div class="max-h-52 overflow-y-auto rounded border border-slate-800 divide-y divide-slate-800">
              <label
                v-for="rule in store.config?.rules ?? []"
                :key="rule.name"
                class="flex items-center gap-3 px-3 py-2 hover:bg-slate-800/50 cursor-pointer"
              >
                <input
                  type="checkbox"
                  :checked="modal.rules.includes(rule.name)"
                  class="accent-amber-500"
                  @change="toggleRule(rule.name)"
                />
                <span class="font-mono text-xs text-amber-300">{{ rule.name }}</span>
                <span class="text-xs text-slate-500">{{ rule.entries.map(e => e.role).join(', ') }}</span>
              </label>
            </div>
          </div>

          <p v-if="modal.error" class="text-xs text-red-400">{{ modal.error }}</p>

          <div class="flex gap-3 pt-1">
            <button
              :disabled="templateBusy"
              class="px-4 py-1.5 rounded-md bg-amber-500 hover:bg-amber-400 disabled:opacity-40 disabled:cursor-not-allowed text-xs font-semibold text-slate-950 transition-colors"
              @click="submitModal"
            >
              {{ templateBusy ? 'Saving…' : 'Save' }}
            </button>
            <button
              class="px-4 py-1.5 rounded-md border border-slate-700 text-xs text-slate-400 hover:text-slate-200 transition-colors"
              @click="closeModal"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import type { AppConfig, TemplateMapping } from '~/types/api'

const store = useConfigStore()
const saved = ref(false)
const draft = ref<AppConfig | null>(null)

// Template CRUD state
const templateBusy = ref(false)
const templateError = ref<string | null>(null)
const deleteTarget = ref<string | null>(null)

// Template rename state
const renameTemplateTarget = ref<string | null>(null)
const renameTemplateNewName = ref('')
const renameTemplateStep = ref<'input' | 'confirm'>('input')
const renameTemplateRefs = ref(0)
const renameTemplateError = ref<string | null>(null)

const modal = ref({
  open: false,
  mode: 'create' as 'create' | 'edit',
  name: '',
  rules: [] as string[],
  error: null as string | null,
})

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

// ── Template CRUD ────────────────────────────────────────────────────────────

function openCreateModal() {
  modal.value = { open: true, mode: 'create', name: '', rules: [], error: null }
}

function openEditModal(t: TemplateMapping) {
  modal.value = { open: true, mode: 'edit', name: t.template, rules: [...t.rules], error: null }
}

function closeModal() {
  modal.value.open = false
}

function toggleRule(ruleName: string) {
  const idx = modal.value.rules.indexOf(ruleName)
  if (idx === -1) modal.value.rules.push(ruleName)
  else modal.value.rules.splice(idx, 1)
}

async function submitModal() {
  modal.value.error = null
  if (!modal.value.name.trim()) {
    modal.value.error = 'Template name is required.'
    return
  }
  if (modal.value.rules.length === 0) {
    modal.value.error = 'Select at least one rule.'
    return
  }
  templateBusy.value = true
  try {
    if (modal.value.mode === 'create') {
      await store.createTemplate({ template: modal.value.name.trim(), rules: modal.value.rules })
    } else {
      await store.updateTemplate(modal.value.name, modal.value.rules)
    }
    if (draft.value && store.config) {
      draft.value.templates = JSON.parse(JSON.stringify(store.config.templates))
    }
    closeModal()
  } catch (e: any) {
    modal.value.error = e.data?.detail ?? e.message ?? 'Failed to save template'
  } finally {
    templateBusy.value = false
  }
}

// ── Template rename ───────────────────────────────────────────────────────────

function startTemplateRename(tmplName: string) {
  deleteTarget.value = null
  renameTemplateTarget.value = tmplName
  renameTemplateNewName.value = tmplName
  renameTemplateStep.value = 'input'
  renameTemplateRefs.value = 0
  renameTemplateError.value = null
}

function cancelTemplateRename() {
  renameTemplateTarget.value = null
  renameTemplateStep.value = 'input'
  renameTemplateError.value = null
}

function requestTemplateRename(tmplName: string) {
  const newName = renameTemplateNewName.value.trim()
  if (!newName) { renameTemplateError.value = 'Name is required.'; return }
  if (newName === tmplName) { cancelTemplateRename(); return }
  const refs = store.config?.virtual_tags.filter(vt => vt.template === tmplName).length ?? 0
  renameTemplateRefs.value = refs
  if (refs > 0) {
    renameTemplateStep.value = 'confirm'
  } else {
    executeTemplateRename(tmplName)
  }
}

async function executeTemplateRename(oldName: string) {
  renameTemplateError.value = null
  templateBusy.value = true
  try {
    await store.renameTemplate(oldName, renameTemplateNewName.value.trim())
    if (draft.value && store.config) {
      draft.value.templates = JSON.parse(JSON.stringify(store.config.templates))
    }
    cancelTemplateRename()
  } catch (e: any) {
    renameTemplateError.value = e.data?.detail ?? e.message ?? 'Rename failed'
    renameTemplateStep.value = 'input'
  } finally {
    templateBusy.value = false
  }
}

async function confirmDelete(name: string) {
  templateError.value = null
  templateBusy.value = true
  try {
    await store.deleteTemplate(name)
    if (draft.value && store.config) {
      draft.value.templates = JSON.parse(JSON.stringify(store.config.templates))
    }
    deleteTarget.value = null
  } catch (e: any) {
    templateError.value = e.data?.detail ?? e.message ?? 'Failed to delete template'
    deleteTarget.value = null
  } finally {
    templateBusy.value = false
  }
}
</script>
