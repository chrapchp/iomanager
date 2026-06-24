<!--*************************************************
 * Project:     IOManager
 * Author:      Peter Chrapchynski
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 *************************************************-->

<template>
  <div class="space-y-6">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h1 class="text-2xl font-semibold tracking-tight text-slate-100">Tags</h1>
        <p class="mt-1 text-sm text-slate-500">
          {{ gen.tags.length }} tag{{ gen.tags.length !== 1 ? 's' : '' }} generated
        </p>
      </div>
      <input
        v-model="search"
        type="text"
        placeholder="Filter…"
        class="px-3 py-1.5 rounded-md bg-slate-800 border border-slate-700 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-600 font-mono w-52"
      />
    </div>

    <!-- Empty state -->
    <div v-if="!gen.tags.length" class="rounded-lg bg-slate-900 border border-slate-800 p-12 text-center">
      <p class="text-slate-500 text-sm">No tags yet.</p>
      <NuxtLink to="/export" class="mt-2 inline-block text-sm text-cyan-400 hover:text-cyan-300 underline underline-offset-2">
        Run generation →
      </NuxtLink>
    </div>

    <!-- Table -->
    <div v-else class="rounded-lg bg-slate-900 border border-slate-800 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-xs font-mono">
          <thead>
            <tr class="border-b border-slate-800 bg-slate-900/80">
              <th class="px-4 py-3 text-left text-slate-500 font-medium">Name</th>
              <th class="px-4 py-3 text-left text-slate-500 font-medium">Type</th>
              <th class="px-4 py-3 text-right text-slate-500 font-medium">Address</th>
              <th class="px-4 py-3 text-left text-slate-500 font-medium">Group</th>
              <th class="px-4 py-3 text-left text-slate-500 font-medium">Comment</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="tag in filteredTags"
              :key="tag.name"
              class="border-b border-slate-800/50 hover:bg-slate-800/40 transition-colors"
            >
              <td class="px-4 py-2 text-cyan-300">{{ tag.name }}</td>
              <td class="px-4 py-2">
                <span class="px-1.5 py-0.5 rounded text-slate-300" :class="typeColor(tag.data_type)">
                  {{ tag.data_type }}
                </span>
              </td>
              <td class="px-4 py-2 text-right text-slate-400">{{ tag.modbus_address }}</td>
              <td class="px-4 py-2 text-slate-400">{{ tag.group || '—' }}</td>
              <td class="px-4 py-2 text-slate-500">{{ tag.comment || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="px-4 py-2 border-t border-slate-800 text-xs text-slate-600">
        Showing {{ filteredTags.length }} of {{ gen.tags.length }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const gen = useGenerationStore()
const search = ref('')

onMounted(async () => {
  if (!gen.tags.length) await gen.fetchTags()
})

const filteredTags = computed(() => {
  if (!search.value) return gen.tags
  const q = search.value.toLowerCase()
  return gen.tags.filter(
    (t) =>
      t.name.toLowerCase().includes(q) ||
      t.group?.toLowerCase().includes(q) ||
      t.comment?.toLowerCase().includes(q)
  )
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
