/***************************************************
 * Project:     IOManager
 * Author:      Peter Chrapchynski
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 ***************************************************/

import { defineStore } from 'pinia'
import type { ImportStatusResponse, TwinsoftImportResponse, IoIndexImportResponse } from '~/types/api'

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
  const uploading = ref(false)
  const error = ref<string | null>(null)

  async function refreshStatus() {
    status.value = await $fetch<ImportStatusResponse>(`${base}/api/imports/status`)
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
      await refreshStatus()
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
      await refreshStatus()
      return result
    } catch (e: any) {
      error.value = e.data?.detail ?? e.message ?? 'Upload failed'
      throw e
    } finally {
      uploading.value = false
    }
  }

  return { status, uploading, error, refreshStatus, uploadTwinsoft, uploadIoIndex }
})
