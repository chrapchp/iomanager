<!--*************************************************
 * Project:     IOManager
 * Author:      Peter C
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 *              2026Jul04 - Amber accent
 *************************************************-->

<template>
  <div class="max-w-3xl space-y-8">
    <div>
      <h1 class="text-2xl font-semibold tracking-tight text-slate-100">Import</h1>
      <p class="mt-1 text-sm text-slate-500">
        Load source files before running generation.
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Twinsoft address map -->
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <h2 class="text-sm font-medium text-slate-300">Twinsoft Export XML</h2>
          <StatusBadge
            :status="imports.status.twinsoft_loaded ? 'success' : 'idle'"
            :label="imports.status.twinsoft_loaded ? `${imports.status.coil_occupied}C ${imports.status.register_occupied}R` : 'Optional'"
          />
        </div>
        <UploadDropzone
          label="Drop address map here"
          accept=".xml"
          :loading="uploading === 'twinsoft'"
          @change="handleTwinsoft"
        />
        <p class="text-xs text-slate-600">
          Pre-occupies existing Modbus addresses before allocating new ones.
        </p>
        <div v-if="twinsoftMsg" class="rounded-md px-3 py-2 text-xs font-mono" :class="twinsoftError ? 'bg-red-950 text-red-300 border border-red-800' : 'bg-green-950 text-green-300 border border-green-800'">
          {{ twinsoftMsg }}
        </div>
      </div>

      <!-- IO Index Excel -->
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <h2 class="text-sm font-medium text-slate-300">I/O Index Excel</h2>
          <StatusBadge
            :status="imports.status.io_index_loaded ? 'success' : 'warning'"
            :label="imports.status.io_index_loaded ? `${imports.status.row_count} rows` : 'Required'"
          />
        </div>
        <UploadDropzone
          label="Drop IO Dist file here"
          accept=".xlsx,.xls"
          :loading="uploading === 'io-index'"
          @change="handleIoIndex"
        />
        <p class="text-xs text-slate-600">
          Reads the <span class="font-mono text-slate-500">IO Dist</span> sheet. Must be loaded before generating.
        </p>
        <div v-if="ioMsg" class="rounded-md px-3 py-2 text-xs font-mono" :class="ioError ? 'bg-red-950 text-red-300 border border-red-800' : 'bg-green-950 text-green-300 border border-green-800'">
          {{ ioMsg }}
        </div>
      </div>
    </div>

    <!-- Next step hint -->
    <div v-if="imports.status.io_index_loaded" class="flex items-center gap-3 text-sm text-slate-500">
      <span class="text-green-400">✓</span>
      I/O Index loaded.
      <NuxtLink to="/export" class="text-amber-400 hover:text-amber-300 underline underline-offset-2">
        Go to Generate →
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
const imports = useImportsStore()

const uploading = ref<'twinsoft' | 'io-index' | null>(null)
const twinsoftMsg = ref('')
const twinsoftError = ref(false)
const ioMsg = ref('')
const ioError = ref(false)

onMounted(() => imports.refreshStatus())

async function handleTwinsoft(file: File) {
  uploading.value = 'twinsoft'
  twinsoftMsg.value = ''
  twinsoftError.value = false
  try {
    const res = await imports.uploadTwinsoft(file)
    twinsoftMsg.value = res.message
    twinsoftError.value = false
  } catch (e: any) {
    twinsoftMsg.value = imports.error ?? 'Upload failed'
    twinsoftError.value = true
  } finally {
    uploading.value = null
  }
}

async function handleIoIndex(file: File) {
  uploading.value = 'io-index'
  ioMsg.value = ''
  ioError.value = false
  try {
    const res = await imports.uploadIoIndex(file)
    ioMsg.value = res.message
    ioError.value = false
  } catch (e: any) {
    ioMsg.value = imports.error ?? 'Upload failed'
    ioError.value = true
  } finally {
    uploading.value = null
  }
}
</script>
