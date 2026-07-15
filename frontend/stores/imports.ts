/***************************************************
 * Project:     IOManager
 * Author:      Peter C
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 *              2026Jul04 - Add importedTags state and fetchImportedTags()
 *              2026Jul15 - Clear generation result on any upload to prevent stale display
 ***************************************************/

import { defineStore } from 'pinia'
import type { ImportStatusResponse, TwinsoftImportResponse, IoIndexImportResponse, Tag } from '~/types/api'
import { useGenerationStore } from '~/stores/generation'

export const useImportsStore = defineStore('imports', () => {
  const cfg = useRuntimeConfig()
  const base = cfg.public.apiBase

  const status = ref<ImportStatusResponse>({
    twinsoft_loaded: false,
    io_index_loaded: false,
    row_count: 0,
    coil_occupied: 0,
    register_occupied: 0,
  })
  const importedTags = ref<Tag[]>([])
  const uploading = ref(false)
  const error = ref<string | null>(null)

  async function refreshStatus() {
    status.value = await $fetch<ImportStatusResponse>(`${base}/api/imports/status`)
  }

  async function fetchImportedTags() {
    try {
      importedTags.value = await $fetch<Tag[]>(`${base}/api/tags/imported`)
    } catch {
      importedTags.value = []
    }
  }

  async function uploadTwinsoft(file: File): Promise<TwinsoftImportResponse> {
    uploading.value = true
    error.value = null
    try {
      const body = new FormData()
      body.append('file', file)
      const result = await $fetch<TwinsoftImportResponse>(`${base}/api/imports/twinsoft`, {
        method: 'POST',
        body,
      })
      useGenerationStore().clearResult()
      await Promise.all([refreshStatus(), fetchImportedTags()])
      return result
    } catch (e: any) {
      error.value = e.data?.detail ?? e.message ?? 'Upload failed'
      throw e
    } finally {
      uploading.value = false
    }
  }

  async function uploadIoIndex(file: File): Promise<IoIndexImportResponse> {
    uploading.value = true
    error.value = null
    try {
      const body = new FormData()
      body.append('file', file)
      const result = await $fetch<IoIndexImportResponse>(`${base}/api/imports/io-index`, {
        method: 'POST',
        body,
      })
      useGenerationStore().clearResult()
      await refreshStatus()
      return result
    } catch (e: any) {
      error.value = e.data?.detail ?? e.message ?? 'Upload failed'
      throw e
    } finally {
      uploading.value = false
    }
  }

  return { status, importedTags, uploading, error, refreshStatus, fetchImportedTags, uploadTwinsoft, uploadIoIndex }
})
