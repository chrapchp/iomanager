/***************************************************
 * Project:     IOManager
 * Author:      Peter Chrapchynski
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 ***************************************************/

import { defineStore } from 'pinia'
import type { GenerateResponse, Tag, Alarm } from '~/types/api'

export const useGenerationStore = defineStore('generation', () => {
  const cfg = useRuntimeConfig()
  const base = cfg.public.apiBase

  const result = ref<GenerateResponse | null>(null)
  const tags = ref<Tag[]>([])
  const alarms = ref<Alarm[]>([])
  const generating = ref(false)
  const error = ref<string | null>(null)

  async function generate(): Promise<GenerateResponse> {
    generating.value = true
    error.value = null
    try {
      const res = await $fetch<GenerateResponse>(`${base}/api/exports/generate`, {
        method: 'POST',
      })
      result.value = res
      await Promise.all([fetchTags(), fetchAlarms()])
      return res
    } catch (e: any) {
      error.value = e.data?.detail ?? e.message ?? 'Generation failed'
      throw e
    } finally {
      generating.value = false
    }
  }

  async function fetchTags() {
    try {
      tags.value = await $fetch<Tag[]>(`${base}/api/tags`)
    } catch {
      tags.value = []
    }
  }

  async function fetchAlarms() {
    try {
      alarms.value = await $fetch<Alarm[]>(`${base}/api/alarms`)
    } catch {
      alarms.value = []
    }
  }

  const downloadUrl = (filename: string) =>
    `${base}/api/exports/download/${filename}`

  return { result, tags, alarms, generating, error, generate, fetchTags, fetchAlarms, downloadUrl }
})
