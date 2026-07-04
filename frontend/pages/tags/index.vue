<!--*************************************************
 * Project:     IOManager
 * Author:      Peter C
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 *              2026Jul04 - Amber accent; amber tag names
 *              2026Jul04 - Show imported tags with toggle; sortable columns
 *************************************************-->

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-start justify-between gap-4 flex-wrap">
      <div>
        <h1 class="text-2xl font-semibold tracking-tight text-slate-100">Tags</h1>
        <p class="mt-1 text-sm text-slate-500">
          <span>{{ gen.tags.length }} generated</span>
          <template v-if="showImported && imports.importedTags.length">
            <span class="mx-1 text-slate-700">·</span>
            <span>{{ imports.importedTags.length }} imported</span>
          </template>
        </p>
      </div>

      <div class="flex items-center gap-3 flex-wrap">
        <!-- Imported toggle -->
        <label
          v-if="imports.importedTags.length || imports.status.twinsoft_loaded"
          class="flex items-center gap-2 text-xs text-slate-400 cursor-pointer select-none"
        >
          <input
            v-model="showImported"
            type="checkbox"
            class="accent-amber-500"
          />
          Show imported
        </label>

        <!-- Filter -->
        <input
          v-model="search"
          type="text"
          placeholder="Filter…"
          class="px-3 py-1.5 rounded-md bg-slate-800 border border-slate-700 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-amber-500 font-mono w-48"
        />
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!gen.tags.length && !displayRows.length" class="rounded-lg bg-slate-900 border border-slate-800 p-12 text-center">
      <p class="text-slate-500 text-sm">No tags yet.</p>
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
              <th
                v-for="col in columns"
                :key="col.key"
                class="px-4 py-3 font-medium cursor-pointer select-none group"
                :class="[col.align === 'right' ? 'text-right' : 'text-left', 'text-slate-500 hover:text-slate-300 transition-colors']"
                @click="toggleSort(col.key)"
              >
                <span class="inline-flex items-center gap-1" :class="col.align === 'right' ? 'flex-row-reverse' : ''">
                  {{ col.label }}
                  <span class="text-slate-700 group-hover:text-slate-500 transition-colors w-3 text-center">
                    <template v-if="sortKey === col.key">{{ sortDir === 'asc' ? '↑' : '↓' }}</template>
                    <template v-else>·</template>
                  </span>
                </span>
              </th>
              <th class="px-4 py-3 text-left text-slate-500 font-medium">Comment</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in displayRows"
              :key="`${row.source}-${row.name}`"
              class="border-b border-slate-800/50 hover:bg-slate-800/40 transition-colors"
            >
              <td class="px-4 py-2" :class="row.source === 'generated' ? 'text-amber-300' : 'text-slate-400'">
                {{ row.name }}
              </td>
              <td class="px-4 py-2">
                <span class="px-1.5 py-0.5 rounded text-slate-300" :class="typeColor(row.data_type)">
                  {{ row.data_type }}
                </span>
              </td>
              <td class="px-4 py-2 text-right text-slate-400">{{ row.modbus_address }}</td>
              <td class="px-4 py-2 text-slate-400">{{ row.group || '—' }}</td>
              <td class="px-4 py-2 text-slate-500">{{ row.comment || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="px-4 py-2 border-t border-slate-800 text-xs text-slate-600 flex items-center gap-3">
        <span>Showing {{ displayRows.length }} of {{ totalCount }}</span>
        <template v-if="showImported && imports.importedTags.length">
          <span class="flex items-center gap-1.5">
            <span class="inline-block w-2 h-2 rounded-sm bg-amber-500/40"></span>
            <span>generated</span>
          </span>
          <span class="flex items-center gap-1.5">
            <span class="inline-block w-2 h-2 rounded-sm bg-slate-600"></span>
            <span>imported</span>
          </span>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Tag } from '~/types/api'

type SortKey = 'name' | 'data_type' | 'modbus_address' | 'group'
type RowWithSource = Tag & { source: 'generated' | 'imported' }

const gen = useGenerationStore()
const imports = useImportsStore()

const search = ref('')
const showImported = ref(false)
const sortKey = ref<SortKey>('name')
const sortDir = ref<'asc' | 'desc'>('asc')

const columns: { key: SortKey; label: string; align?: 'right' }[] = [
  { key: 'name', label: 'Name' },
  { key: 'data_type', label: 'Type' },
  { key: 'modbus_address', label: 'Address', align: 'right' },
  { key: 'group', label: 'Group' },
]

onMounted(async () => {
  await Promise.all([
    gen.tags.length ? Promise.resolve() : gen.fetchTags(),
    imports.fetchImportedTags(),
  ])
})

function toggleSort(key: SortKey) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'asc'
  }
}

const mergedRows = computed((): RowWithSource[] => {
  const generated: RowWithSource[] = gen.tags.map(t => ({ ...t, source: 'generated' }))
  if (!showImported.value) return generated
  const imported: RowWithSource[] = imports.importedTags.map(t => ({ ...t, source: 'imported' }))
  return [...generated, ...imported]
})

const filteredRows = computed((): RowWithSource[] => {
  if (!search.value) return mergedRows.value
  const q = search.value.toLowerCase()
  return mergedRows.value.filter(
    t =>
      t.name.toLowerCase().includes(q) ||
      t.group?.toLowerCase().includes(q) ||
      t.comment?.toLowerCase().includes(q)
  )
})

const displayRows = computed((): RowWithSource[] => {
  const rows = [...filteredRows.value]
  const key = sortKey.value
  const dir = sortDir.value === 'asc' ? 1 : -1
  rows.sort((a, b) => {
    const av = a[key] ?? ''
    const bv = b[key] ?? ''
    if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * dir
    return String(av).localeCompare(String(bv)) * dir
  })
  return rows
})

const totalCount = computed(() => {
  if (!showImported.value) return gen.tags.length
  return gen.tags.length + imports.importedTags.length
})

function typeColor(dt: string): string {
  switch (dt) {
    case 'BOOL': return 'bg-green-950 text-green-300'
    case 'FLOAT': return 'bg-blue-950 text-blue-300'
    case 'INT16': case 'UINT16': return 'bg-purple-950 text-purple-300'
    case 'INT32': case 'UINT32': return 'bg-indigo-950 text-indigo-300'
    case 'TEXT': return 'bg-amber-950 text-amber-300'
    default: return 'bg-slate-800 text-slate-400'
  }
}
</script>
