/***************************************************
 * Project:     IOManager
 * Author:      Peter Chrapchynski
 * Date:        2026Jun23
 * History:     2026Jun23 - Initial creation
 ***************************************************/

export interface TwinsoftImportResponse {
  coil_count: number
  register_count: number
  message: string
}

export interface IoIndexImportResponse {
  row_count: number
  message: string
}

export interface ImportStatusResponse {
  twinsoft_loaded: boolean
  io_index_loaded: boolean
  row_count: number
  coil_occupied: number
  register_occupied: number
}

export interface ErrorDetail {
  row_number: number
  tag_name: string
  template: string
  message: string
}

export interface GenerateResponse {
  tag_count: number
  alarm_count: number
  conditioning_count: number
  function_block_count: number
  error_count: number
  errors: ErrorDetail[]
}

export interface PresentationConfig {
  enabled: boolean
  description: string
  state_on: string
  state_off: string
  units: string
  nbr_decimals: string
}

export interface WriteAllowedConfig {
  enabled: boolean
  minimum: string
  maximum: string
}

export interface Tag {
  name: string
  new_name: string | null
  data_type: string
  modbus_address: number
  text_tag_size: number | null
  comment: string
  initial_value: string
  minimum: string
  maximum: string
  resolution: string
  group: string
  presentation: PresentationConfig
  write_allowed: WriteAllowedConfig
}

export interface FilterConfig {
  hours: number
  minutes: number
  seconds: number
}

export interface AlarmOptions {
  notify_end_of_alarm: boolean
  sms_acknowledge: boolean
  pop3_acknowledge: boolean
  handling: 'ENABLED' | 'DISABLED'
}

export interface Alarm {
  tag_name: string
  condition: 'POS' | 'NEG'
  recipient: string
  call_all_recipients: boolean
  message: string
  is_report: boolean
  filter: FilterConfig
  options: AlarmOptions
}

export interface RuleEntry {
  role: string
  addr: number
  tag_suffix: string
  data_class: string
  desc_delimiter: string
  desc_suffix: string
  folder: string
  write_allowed: boolean
  write_allowed_min: string
  write_allowed_max: string
}

export interface Rule {
  name: string
  entries: RuleEntry[]
  condition_code: string | null
  function_block: string | null
}

export interface TemplateMapping {
  template: string
  rules: string[]
}

export interface AlarmDefaults {
  condition: 'POS' | 'NEG'
  recipient: string
  call_all_recipients: boolean
  is_report: boolean
  filter: FilterConfig
  options: AlarmOptions
}

export interface AppConfig {
  target_system: string
  rules: Rule[]
  templates: TemplateMapping[]
  alarm_defaults: AlarmDefaults
}
