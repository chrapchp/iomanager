/***************************************************
 * Project:     IOManager
 * Author:      Peter Chrapchynski
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 ***************************************************/

import { defineStore } from 'pinia'
import type { AppConfig } from '~/types/api'

export const useConfigStore = defineStore('config', () => {
  const cfg = useRuntimeConfig()
  const base = cfg.public.apiBase

  const config = ref<AppConfig | null>(null)
  const loading = ref(false)
  const saving = ref(false)
  const error = ref<string | null>(null)

  async function fetchConfig() {
    loading.value = true
    error.value = null
    try {
      config.value = await $fetch<AppConfig>(`${base}/api/config`)
    } catch (e: any) {
      error.value = e.data?.detail ?? e.message ?? 'Failed to load config'
    } finally {
      loading.value = false
    }
  }

  async function saveConfig(updated: AppConfig) {
    saving.value = true
    error.value = null
    try {
      config.value = await $fetch<AppConfig>(`${base}/api/config`, {
        method: 'PUT',
        body: updated,
      })
    } catch (e: any) {
      error.value = e.data?.detail ?? e.message ?? 'Failed to save config'
      throw e
    } finally {
      saving.value = false
    }
  }

  return { config, loading, saving, error, fetchConfig, saveConfig }
})
