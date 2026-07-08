/***************************************************
 * Project:     IOManager
 * Author:      Peter Chrapchynski
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 *              2026Jul04 - Add template CRUD store methods
 *              2026Jul04 - Add rule CRUD store methods
 *              2026Jul07 - Add virtual tag CRUD store methods
 ***************************************************/

import { defineStore } from 'pinia'
import type { AppConfig, Rule, TemplateMapping, VirtualTagEntry } from '~/types/api'

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

  async function createTemplate(mapping: TemplateMapping): Promise<TemplateMapping> {
    const result = await $fetch<TemplateMapping>(`${base}/api/config/templates`, {
      method: 'POST',
      body: mapping,
    })
    if (config.value) config.value.templates.push(result)
    return result
  }

  async function updateTemplate(name: string, rules: string[]): Promise<TemplateMapping> {
    const result = await $fetch<TemplateMapping>(
      `${base}/api/config/templates/${encodeURIComponent(name)}`,
      { method: 'PUT', body: { rules } },
    )
    if (config.value) {
      const idx = config.value.templates.findIndex(t => t.template === name)
      if (idx !== -1) config.value.templates[idx] = result
    }
    return result
  }

  async function deleteTemplate(name: string): Promise<void> {
    await $fetch(`${base}/api/config/templates/${encodeURIComponent(name)}`, {
      method: 'DELETE',
    })
    if (config.value) {
      config.value.templates = config.value.templates.filter(t => t.template !== name)
    }
  }

  async function createRule(rule: Rule): Promise<Rule> {
    const result = await $fetch<Rule>(`${base}/api/config/rules`, {
      method: 'POST',
      body: rule,
    })
    if (config.value) config.value.rules.push(result)
    return result
  }

  async function deleteRule(name: string): Promise<void> {
    await $fetch(`${base}/api/config/rules/${encodeURIComponent(name)}`, { method: 'DELETE' })
    if (config.value) config.value.rules = config.value.rules.filter(r => r.name !== name)
  }

  async function deleteRuleEntry(ruleName: string, role: string): Promise<void> {
    await $fetch(
      `${base}/api/config/rules/${encodeURIComponent(ruleName)}/entries/${encodeURIComponent(role)}`,
      { method: 'DELETE' },
    )
    if (config.value) {
      const rule = config.value.rules.find(r => r.name === ruleName)
      if (rule) rule.entries = rule.entries.filter(e => e.role !== role)
    }
  }

  async function createVirtualTag(entry: Omit<VirtualTagEntry, 'id'>): Promise<VirtualTagEntry> {
    const result = await $fetch<VirtualTagEntry>(`${base}/api/config/virtual-tags`, {
      method: 'POST',
      body: entry,
    })
    if (config.value) config.value.virtual_tags.push(result)
    return result
  }

  async function updateVirtualTag(id: string, entry: Omit<VirtualTagEntry, 'id'>): Promise<VirtualTagEntry> {
    const result = await $fetch<VirtualTagEntry>(
      `${base}/api/config/virtual-tags/${encodeURIComponent(id)}`,
      { method: 'PUT', body: { ...entry, id } },
    )
    if (config.value) {
      const idx = config.value.virtual_tags.findIndex(vt => vt.id === id)
      if (idx !== -1) config.value.virtual_tags[idx] = result
    }
    return result
  }

  async function deleteVirtualTag(id: string): Promise<void> {
    await $fetch(`${base}/api/config/virtual-tags/${encodeURIComponent(id)}`, { method: 'DELETE' })
    if (config.value) config.value.virtual_tags = config.value.virtual_tags.filter(vt => vt.id !== id)
  }

  return {
    config, loading, saving, error,
    fetchConfig, saveConfig,
    createTemplate, updateTemplate, deleteTemplate,
    createRule, deleteRule, deleteRuleEntry,
    createVirtualTag, updateVirtualTag, deleteVirtualTag,
  }
})
