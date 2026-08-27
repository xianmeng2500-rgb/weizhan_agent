<template>
  <div class="form-page" :class="themeClass">
    <van-nav-bar :title="module.title || '报名表'" left-arrow @click-left="goBack" />

    <div v-if="loading" class="loading-area">
      <van-loading type="spinner" color="#667eea" />
    </div>

    <!-- 提交成功页 -->
    <div v-else-if="successVisible" class="success-page">
      <div class="success-card">
        <div class="success-icon-wrap">
          <van-icon name="checked" class="success-icon" />
        </div>
        <h2 class="success-title">{{ successTitle }}</h2>
        <p class="success-desc">{{ successDesc }}</p>
        <van-button round block class="success-btn" @click="goBack">返回首页</van-button>
      </div>
    </div>

    <div v-else class="form-body">
      <!-- 表单头部 -->
      <div class="form-header">
        <div class="header-decor decor-1"></div>
        <div class="header-decor decor-2"></div>
        <div class="header-decor decor-3"></div>
        <div class="form-header-content">
          <div class="form-icon-wrap">
            <van-icon name="notes-o" class="form-icon" />
          </div>
          <h2 class="form-title">{{ formConfig.title || module.title }}</h2>
          <p v-if="formConfig.description" class="form-desc">{{ formConfig.description }}</p>
        </div>
      </div>

      <div v-if="isSubmitted" class="submitted-notice">
        <van-icon :name="canEdit ? 'edit' : 'info-o'" />
        <span>{{ canEdit ? '您已提交过该报名表单，可修改信息后点击“保存修改”。' : '您已提交过该报名表单，以下信息仅供查看，暂不支持修改。' }}</span>
      </div>

      <van-form :class="{ 'form-readonly': formReadonly }" @submit="onSubmit">
        <div v-for="(field, index) in formConfig.fields" :key="field.id" class="field-wrapper"
             :class="wrapperClass(field, index)">

          <!-- 分割线 -->
          <template v-if="field.type === 'divider'">
            <div class="form-divider"><span v-if="field.props?.text">{{ field.props.text }}</span></div>
          </template>

          <!-- 提示文本 -->
          <template v-else-if="field.type === 'tip_text'">
            <div class="form-tip" :class="`form-tip--${field.props?.tone || 'info'}`">
              <van-icon :name="tipIcon(field.props?.tone || 'info')" class="tip-icon" />
              <span>{{ field.props?.content || field.title }}</span>
            </div>
          </template>

          <!-- 文本/手机号/身份证/邮箱/数字/日期/时间/地区/下拉（Vant 横向单元格） -->
          <template v-else-if="isSimpleInput(field.type)">
            <div class="field-cell" :class="cellGroupClass(index)">
              <van-field
                v-model="formData[field.id]"
                :name="field.id"
                :label="field.title"
                :required="field.required"
                :placeholder="placeholderOf(field)"
                :rules="getRules(field)"
                :readonly="isPickerField(field.type)"
                :clickable="isPickerField(field.type)"
                :border="!isCellGroupLast(index)"
                :maxlength="field.props?.maxLength"
                :type="field.type === 'number' ? 'number' : 'text'"
                @click="handleFieldClick(field)"
              />
            </div>
          </template>

          <!-- 多行文本 -->
          <template v-else-if="field.type === 'textarea'">
            <div class="field-card">
              <div class="field-header">
                <span class="field-icon"><van-icon name="notes-o" /></span>
                <span class="field-label">{{ field.title }}</span>
                <span v-if="field.required" class="required-mark">*</span>
              </div>
              <van-field v-model="formData[field.id]" :name="field.id"
                :placeholder="field.placeholder || '请输入'" :rules="getRules(field)"
                rows="3" autosize type="textarea" :border="false" />
            </div>
          </template>

          <!-- 单选 -->
          <template v-else-if="field.type === 'radio'">
            <div class="field-card">
              <div class="field-header">
                <span class="field-icon"><van-icon name="circle" /></span>
                <span class="field-label">{{ field.title }}</span>
                <span v-if="field.required" class="required-mark">*</span>
              </div>
              <van-radio-group v-model="formData[field.id]" :name="field.id" :rules="getRules(field)">
                <div class="option-list">
                  <div v-for="opt in (field.options || [])" :key="opt"
                    class="option-item" :class="{ 'option-item--active': formData[field.id] === opt }"
                    @click="formData[field.id] = opt">
                    <span class="option-text">{{ opt }}</span>
                    <span class="option-radio" :class="{ 'option-radio--checked': formData[field.id] === opt }">
                      <span v-if="formData[field.id] === opt" class="option-radio-dot"></span>
                    </span>
                  </div>
                </div>
              </van-radio-group>
            </div>
          </template>

          <!-- 多选 -->
          <template v-else-if="field.type === 'checkbox'">
            <div class="field-card">
              <div class="field-header">
                <span class="field-icon"><van-icon name="certificate" /></span>
                <span class="field-label">{{ field.title }}</span>
                <span v-if="field.required" class="required-mark">*</span>
              </div>
              <van-checkbox-group v-model="formData[field.id]" :name="field.id" :rules="getRules(field)">
                <div class="option-list">
                  <div v-for="opt in (field.options || [])" :key="opt"
                    class="option-item" :class="{ 'option-item--active': isChecked(field.id, opt) }"
                    @click="toggleCheckbox(field.id, opt)">
                    <span class="option-text">{{ opt }}</span>
                    <span class="option-checkbox" :class="{ 'option-checkbox--checked': isChecked(field.id, opt) }">
                      <van-icon v-if="isChecked(field.id, opt)" name="checked" size="12" />
                    </span>
                  </div>
                </div>
              </van-checkbox-group>
            </div>
          </template>

          <!-- 协议勾选 -->
          <template v-else-if="field.type === 'agreement'">
            <div class="field-card agreement-block">
              <div class="agreement-check" :class="{ 'agreement-check--checked': Boolean(formData[field.id]) }"
                @click="onAgreementToggle(field)">
                <span class="agreement-box" :class="{ 'agreement-box--checked': Boolean(formData[field.id]) }">
                  <van-icon v-if="formData[field.id]" name="checked" size="14" />
                </span>
                <span class="agreement-text">
                  <template v-if="field.props?.agreementContent">
                    <text class="agreement-link" @click.stop="openAgreement(field)">《{{ field.placeholder || '相关协议' }}》</text>
                  </template>
                  <template v-else>{{ field.placeholder || '我已阅读并同意相关协议' }}</template>
                </span>
              </div>
            </div>
          </template>

          <!-- 交通信息（去程/回程/备注） -->
          <template v-else-if="field.type === 'transport_info'">
            <div class="field-card">
              <div class="field-header">
                <span class="field-icon"><van-icon name="under-way-o" /></span>
                <span class="field-label">{{ field.title }}</span>
                <span v-if="field.required" class="required-mark">*</span>
              </div>
              <div class="transport-info-block">
                <div v-if="field.props?.showDeparture !== false" class="transport-section">
                  <div class="transport-section-title"><van-icon name="logistics" class="section-icon" />去程信息</div>
                  <van-field v-model="formData[field.id].departure_method"
                    :name="field.id + '_departure_method'" placeholder="选择去程方式" readonly clickable
                    :rules="field.required ? [{ required: true, message: '请选择去程方式' }] : []"
                    :border="false" @click="openTransportPicker(field, 'departure_method')" />
                  <van-field v-model="formData[field.id].departure_number"
                    :name="field.id + '_departure_number'" placeholder="航班/车次号" :border="false" />
                </div>
                <div v-if="field.props?.showReturn !== false" class="transport-section">
                  <div class="transport-section-title"><van-icon name="logistics" class="section-icon" />回程信息</div>
                  <van-field v-model="formData[field.id].return_method"
                    :name="field.id + '_return_method'" placeholder="选择回程方式" readonly clickable
                    :rules="field.required ? [{ required: true, message: '请选择回程方式' }] : []"
                    :border="false" @click="openTransportPicker(field, 'return_method')" />
                  <van-field v-model="formData[field.id].return_number"
                    :name="field.id + '_return_number'" placeholder="航班/车次号" :border="false" />
                </div>
                <div v-if="field.props?.showRemark !== false" class="transport-section">
                  <van-field v-model="formData[field.id].remark" :name="field.id + '_remark'"
                    placeholder="备注信息" type="textarea" :rows="2" autosize :border="false" />
                </div>
              </div>
            </div>
          </template>

          <!-- 图片上传 -->
          <template v-else-if="field.type === 'image'">
            <div class="field-card">
              <div class="field-header">
                <span class="field-icon"><van-icon name="photo-o" /></span>
                <span class="field-label">{{ field.title }}</span>
                <span v-if="field.required" class="required-mark">*</span>
              </div>
              <van-uploader v-model="fileList[field.id]" :name="field.id" :max-count="3"
                :after-read="(file: any) => afterRead(field.id, file)"
                @delete="onDeleteImage(field.id, $event)" />
              <div v-if="fieldError[field.id]" class="field-error">{{ fieldError[field.id] }}</div>
            </div>
          </template>
        </div>

        <div class="submit-area">
          <van-button round block type="primary" native-type="submit" :loading="submitting" :disabled="formReadonly" class="submit-btn">
            <van-icon v-if="!isSubmitted" name="send" class="submit-icon" />
            {{ canEdit ? '保存修改' : (isSubmitted ? '已提交' : (formConfig.buttonText || '提交')) }}
          </van-button>
          <p class="submit-tip">{{ canEdit ? '修改后请确认信息无误再保存' : '请确认信息无误后提交' }}</p>
        </div>
      </van-form>
    </div>

    <!-- 选择器弹窗 -->
    <van-popup v-model:show="showPicker" position="bottom" round teleport="body">
      <van-picker :columns="currentOptions" @confirm="onPickerConfirm" @cancel="showPicker = false" />
    </van-popup>
    <van-popup v-model:show="showDatePicker" position="bottom" round teleport="body">
      <van-date-picker title="选择日期" @confirm="onDateConfirm" @cancel="showDatePicker = false" />
    </van-popup>
    <van-popup v-model:show="showTimePicker" position="bottom" round teleport="body">
      <van-time-picker title="选择时间" @confirm="onTimeConfirm" @cancel="showTimePicker = false" />
    </van-popup>
    <van-popup v-model:show="showAreaPicker" position="bottom" round teleport="body">
      <van-area title="选择地区" :area-list="areaList" @confirm="onAreaConfirm" @cancel="showAreaPicker = false" />
    </van-popup>
    <van-popup v-model:show="showTransportPicker" position="bottom" round teleport="body">
      <van-picker title="选择交通方式" :columns="currentTransportOptions"
        @confirm="onTransportPickerConfirm" @cancel="showTransportPicker = false" />
    </van-popup>
    <!-- 协议正文弹窗 -->
    <van-popup v-model:show="showAgreementPopup" position="bottom" round teleport="body" @closed="onAgreementPopupClosed">
      <div class="agreement-popup">
        <div class="agreement-popup-title">协议内容</div>
        <div class="agreement-popup-content">{{ currentAgreementContent }}</div>
        <div class="agreement-popup-footer">
          <van-button block round type="primary" class="agreement-popup-btn" @click="confirmAgreement">
            我已阅读并同意
          </van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import api from '@/api'
import { areaList } from '@vant/area-data'

const route = useRoute()
const router = useRouter()
const code = route.params.code as string
const moduleId = route.params.moduleId as string

const loading = ref(true)
const submitting = ref(false)
const module = ref<any>({})
const formConfig = ref<any>({ fields: [] })          // 表单配置（来自后端 form_config）
const formData = ref<Record<string, any>>({})        // 表单数据
const fileList = ref<Record<string, any[]>>({})      // 图片文件列表
const fieldError = ref<Record<string, string>>({})
const needsLogin = ref(false)
const isSubmitted = ref(false)                       // 是否已提交（只读模式）
const submission = ref<any>(null)                    // 我的报名记录（含 allow_edit 等）
const successVisible = ref(false)                    // 提交成功页
const successTitle = ref('提交成功')                 // 成功页标题（提交/修改共用）
const successDesc = ref('感谢您的报名，信息已成功提交！') // 成功页描述
const site = ref<any>({})                            // 微站信息（用于主题）

// 最终可修改 = 模块级允许提交后修改 且 单条数据级允许修改
const canEdit = computed(() => {
  return isSubmitted.value
    && Boolean(formConfig.value.allowEditAfterSubmit)
    && submission.value?.allow_edit !== false
})
// 表单只读（已提交且不可修改）
const formReadonly = computed(() => isSubmitted.value && !canEdit.value)

const themeClass = computed(() => `tpl-${site.value.template || 'classic'}`)

// 字段图标映射
const fieldIconMap: Record<string, string> = {
  text: 'edit', phone: 'phone-o', idcard: 'idcard', email: 'envelope-o',
  number: 'bar-chart-o', date: 'calendar-o', time: 'clock-o', region: 'location-o',
  select: 'bars', radio: 'circle', checkbox: 'certificate',
  textarea: 'notes-o', transport_info: 'under-way-o', image: 'photo-o',
  agreement: 'shield-o',
}
function fieldIcon(type: string) {
  return fieldIconMap[type] || 'edit'
}
function tipIcon(tone: string) {
  return { info: 'info-o', success: 'success', warning: 'warning-o' }[tone] || 'info-o'
}
function isChecked(fieldId: string, opt: string) {
  const arr = formData.value[fieldId] || []
  return arr.includes(opt)
}

// Vant 式单元格分组：相邻简单字段合并为一个圆角卡片
const SIMPLE_INPUT_TYPES = ['text', 'phone', 'idcard', 'email', 'number', 'date', 'time', 'region', 'select']
const PICKER_FIELD_TYPES = ['date', 'time', 'region', 'select']

function isSimpleInput(type: string) {
  return SIMPLE_INPUT_TYPES.includes(type)
}
function isPickerField(type: string) {
  return PICKER_FIELD_TYPES.includes(type)
}
function placeholderOf(field: any) {
  if (field.placeholder) return field.placeholder
  if (field.type === 'select') return '请选择'
  if (field.type === 'date') return '选择日期'
  if (field.type === 'time') return '选择时间'
  if (field.type === 'region') return '请选择地区'
  return '请输入'
}
// 字段外层容器：中间简单字段之间不保留间距（合并进同一卡片）
function wrapperClass(field: any, index: number) {
  const display = ['divider', 'tip_text'].includes(field.type)
  const classes: Record<string, boolean> = { 'field-wrapper--display': display }
  if (isSimpleInput(field.type)) {
    const fields = formConfig.value.fields || []
    const nextIsSimple = index < fields.length - 1 && isSimpleInput(fields[index + 1]?.type)
    if (nextIsSimple) classes['field-wrapper--compact'] = true
  }
  return classes
}
// 单元格圆角：组内第一个/最后一个分别圆上/下角
function cellGroupClass(index: number) {
  const fields = formConfig.value.fields || []
  const prevIsSimple = index > 0 && isSimpleInput(fields[index - 1]?.type)
  const nextIsSimple = index < fields.length - 1 && isSimpleInput(fields[index + 1]?.type)
  return {
    'field-cell--first': !prevIsSimple,
    'field-cell--last': !nextIsSimple,
  }
}
// 是否单元格分组内的最后一项（决定底部是否画分隔线）
function isCellGroupLast(index: number) {
  const fields = formConfig.value.fields || []
  return !(index < fields.length - 1 && isSimpleInput(fields[index + 1]?.type))
}
// 选择类字段点击：统一分发到对应 picker
function handleFieldClick(field: any) {
  if (formReadonly.value) return
  if (field.type === 'select') openPicker(field)
  else if (field.type === 'date') openDatePicker(field)
  else if (field.type === 'time') openTimePicker(field)
  else if (field.type === 'region') {
    showAreaPicker.value = true
    currentAreaField.value = field.id
  }
}

// 各选择器状态
const showPicker = ref(false)
const currentPickerField = ref<string>('')
const currentOptions = ref<string[]>([])
const showDatePicker = ref(false)
const currentDateField = ref<string>('')
const showTimePicker = ref(false)
const currentTimeField = ref<string>('')
const showAreaPicker = ref(false)
const currentAreaField = ref<string>('')
const showTransportPicker = ref(false)
const currentTransportFieldId = ref<string>('')
const currentTransportSubKey = ref<string>('')
const currentTransportOptions = ref<string[]>([])
// 协议弹窗状态
const showAgreementPopup = ref(false)
const currentAgreementField = ref<string>('')
const currentAgreementContent = ref('')

function goBack() {
  router.push(`/s/${code}`)
}

// 字段校验规则
function getRules(field: any) {
  if (formReadonly.value) return []
  const rules = []
  if (field.required) {
    rules.push({ required: true, message: `请填写${field.title}` })
  }
  if (field.type === 'phone') {
    rules.push({ validator: (value: string) => !value || /^1[3-9]\d{9}$/.test(value), message: '请输入正确的手机号' })
  }
  if (field.type === 'email') {
    rules.push({ validator: (value: string) => !value || /^\S+@\S+\.\S+$/.test(value), message: '请输入正确的邮箱' })
  }
  if (field.type === 'idcard') {
    rules.push({ validator: (value: string) => !value || /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/.test(value), message: '请输入正确的身份证号' })
  }
  return rules
}

// 多选切换
function toggleCheckbox(fieldId: string, opt: string) {
  if (formReadonly.value) return
  const arr = formData.value[fieldId] || []
  const idx = arr.indexOf(opt)
  if (idx > -1) { arr.splice(idx, 1) } else { arr.push(opt) }
  formData.value[fieldId] = [...arr]
}

// 下拉选择
function openPicker(field: any) {
  if (formReadonly.value) return
  currentPickerField.value = field.id
  // Vant 4 picker 对 string[] columns 在 getColumnsType 中会触发
  // "Cannot use 'in' operator to search for 'children' in xxx"，因此统一转成对象数组
  const opts = field.options || []
  currentOptions.value = opts.map((s: string) => ({ text: s, value: s }))
  showPicker.value = true
}
function onPickerConfirm({ selectedOptions }: any) {
  formData.value[currentPickerField.value] = selectedOptions[0]?.text || ''
  showPicker.value = false
}

// 日期/时间
function openDatePicker(field: any) {
  if (formReadonly.value) return
  currentDateField.value = field.id
  showDatePicker.value = true
}
function openTimePicker(field: any) {
  if (formReadonly.value) return
  currentTimeField.value = field.id
  showTimePicker.value = true
}
function onDateConfirm({ selectedValues }: any) {
  formData.value[currentDateField.value] = selectedValues.join('-')
  showDatePicker.value = false
}
function onTimeConfirm({ selectedValues }: any) {
  formData.value[currentTimeField.value] = selectedValues.join(':')
  showTimePicker.value = false
}

// 地区
function onAreaConfirm({ selectedOptions }: any) {
  formData.value[currentAreaField.value] = selectedOptions.map((o: any) => o.text).join(' ')
  showAreaPicker.value = false
}

// 交通方式选择器
function openTransportPicker(field: any, subKey: string) {
  if (formReadonly.value) return
  currentTransportFieldId.value = field.id
  currentTransportSubKey.value = subKey
  const optionKey = subKey === 'departure_method' ? 'departureOptions' : 'returnOptions'
  const raw = field.props?.[optionKey] || ['飞机', '火车', '其他']
  // Vant 4 picker 对 string[] columns 在 getColumnsType 中会触发
  // "Cannot use 'in' operator to search for 'children' in xxx"，统一转成对象数组
  currentTransportOptions.value = raw.map((s: string) => ({ text: s, value: s }))
  showTransportPicker.value = true
}
function onTransportPickerConfirm({ selectedOptions }: any) {
  const fieldId = currentTransportFieldId.value
  const subKey = currentTransportSubKey.value
  if (formData.value[fieldId]) {
    formData.value[fieldId][subKey] = selectedOptions[0]?.text || ''
  }
  showTransportPicker.value = false
}

// 协议勾选：点击勾选框
function onAgreementToggle(field: any) {
  if (formReadonly.value) return
  const checked = Boolean(formData.value[field.id])
  if (!checked && field.props?.agreementContent) {
    // 未勾选且有协议正文 → 弹窗展示正文，关闭弹窗即视为已读并勾选
    currentAgreementField.value = field.id
    currentAgreementContent.value = field.props.agreementContent
    showAgreementPopup.value = true
  } else {
    formData.value[field.id] = !checked
  }
}
// 协议勾选：点击协议文字 → 查看正文
function openAgreement(field: any) {
  if (formReadonly.value) return
  if (!field.props?.agreementContent) return
  currentAgreementField.value = field.id
  currentAgreementContent.value = field.props.agreementContent
  showAgreementPopup.value = true
}
// 弹窗内点击“我已阅读并同意”→ 关闭弹窗（关闭时统一勾选）
function confirmAgreement() {
  showAgreementPopup.value = false
}
// 弹窗关闭：已打开过即视为已读协议，自动勾选
function onAgreementPopupClosed() {
  if (currentAgreementField.value) {
    formData.value[currentAgreementField.value] = true
  }
  currentAgreementField.value = ''
  currentAgreementContent.value = ''
}

// 图片上传（multipart）
async function afterRead(fieldId: string, file: any) {
  const form = new FormData()
  form.append('file', file.file)
  try {
    const res: any = await api.post('/p/upload/image', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    file.url = res.url
    file.status = 'done'
    fieldError.value[fieldId] = ''
  } catch (err: any) {
    file.status = 'failed'
    showToast('图片上传失败')
  }
}
function onDeleteImage(fieldId: string, file: any) {
  const list = fileList.value[fieldId] || []
  const idx = list.findIndex((item: any) => item.url === file.url || item === file)
  if (idx > -1) list.splice(idx, 1)
}
function collectImageUrls(fieldId: string): string[] {
  const list = fileList.value[fieldId] || []
  return list.map((item: any) => item.url || (item.objectUrl ? '' : item.content)).filter(Boolean)
}

// 提交
async function onSubmit() {
  if (formReadonly.value) return
  // 图片必填校验
  let valid = true
  for (const field of formConfig.value.fields || []) {
    if (field.type === 'image' && field.required) {
      const urls = collectImageUrls(field.id)
      if (urls.length === 0) { fieldError.value[field.id] = `请上传${field.title}`; valid = false }
      else { fieldError.value[field.id] = '' }
    }
    // 协议必填校验（自定义勾选，不走 van-checkbox rules）
    if (field.type === 'agreement' && field.required && !formData.value[field.id]) {
      showToast(`请先${field.placeholder || '同意相关协议'}`)
      valid = false
    }
  }
  if (!valid) { showToast('请完善表单'); return }

  const data: Record<string, any> = {}
  for (const field of formConfig.value.fields || []) {
    data[field.id] = field.type === 'image' ? collectImageUrls(field.id) : formData.value[field.id]
  }

  // 自动提取姓名/手机号
  let submitterName = ''
  let submitterPhone = ''
  for (const field of formConfig.value.fields || []) {
    const val = formData.value[field.id]
    if (!submitterName && field.type === 'text' && (field.title || '').includes('姓名')) submitterName = val
    if (!submitterPhone && (field.type === 'phone' || (field.title || '').includes('手机号'))) submitterPhone = val
  }

  submitting.value = true
  try {
    if (canEdit.value) {
      // 修改模式：更新原记录
      await api.put(`/p/sites/${code}/modules/${moduleId}/form-submissions/mine`, {
        data,
        submitter_name: submitterName,
        submitter_phone: submitterPhone,
      })
      showSuccessToast('修改成功')
      successTitle.value = '修改成功'
      successDesc.value = '您的报名信息已成功更新！'
    } else {
      await api.post(`/p/sites/${code}/modules/${moduleId}/form-submissions`, {
        data,
        submitter_name: submitterName,
        submitter_phone: submitterPhone,
      })
      showSuccessToast('提交成功')
      successTitle.value = '提交成功'
      successDesc.value = '感谢您的报名，信息已成功提交！'
    }
    successVisible.value = true
  } catch (err: any) {
    showToast(err.response?.data?.detail || (canEdit.value ? '修改失败' : '提交失败'))
  } finally {
    submitting.value = false
  }
}

// 已提交数据回填（只读展示）
function applySubmittedData(data: Record<string, any>) {
  for (const field of formConfig.value.fields || []) {
    const value = data[field.id]
    if (field.type === 'image') {
      fileList.value[field.id] = (Array.isArray(value) ? value : []).map((url: string) => ({ url, isImage: true }))
    } else if (value !== undefined) {
      formData.value[field.id] = value
    }
  }
}

// 加载模块配置
async function loadModule() {
  try {
    loading.value = true
    const [res, siteInfo]: any[] = await Promise.all([
      api.get(`/p/modules/${moduleId}`),
      api.get(`/p/sites/${code}`),
    ])
    module.value = res
    formConfig.value = res.form_config || { fields: [] }
    needsLogin.value = Boolean(siteInfo.need_login)
    site.value = siteInfo

    // 初始化表单数据
    const initData: Record<string, any> = {}
    const initFiles: Record<string, any[]> = {}
    for (const field of formConfig.value.fields || []) {
      if (field.type === 'checkbox') initData[field.id] = field.defaultValue || []
      else if (field.type === 'agreement') initData[field.id] = field.defaultValue || false
      else if (field.type === 'image') initFiles[field.id] = []
      else if (field.type === 'transport_info') {
        initData[field.id] = { departure_method: '', departure_number: '', return_method: '', return_number: '', remark: '' }
      } else initData[field.id] = field.defaultValue || ''
    }
    formData.value = initData
    fileList.value = initFiles

    // 需要登录的微站：读取当前账号既有报名记录，回填展示（是否可修改由模块级与数据级共同决定）
    if (needsLogin.value) {
      const sub: any = await api.get(`/p/sites/${code}/modules/${moduleId}/form-submissions/mine`)
      if (sub?.data) {
        submission.value = sub
        applySubmittedData(sub.data)
        isSubmitted.value = true
      }
    }
  } catch (err: any) {
    showToast(err.response?.data?.detail || '表单加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadModule)
</script>

<style scoped>
/* ===== 主题变量 ===== */
.form-page {
  --form-primary: #667eea;
  --form-primary-2: #764ba2;
  --form-primary-light: rgba(102, 126, 234, 0.1);
  --form-primary-soft: #eef1fd;
  --form-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.form-page.tpl-dark {
  --form-primary: #5dcaa5;
  --form-primary-2: #2e9c8f;
  --form-primary-light: rgba(93, 202, 165, 0.12);
  --form-primary-soft: #e6f7f1;
  --form-gradient: linear-gradient(135deg, #1a1a2e 0%, #2e5f6b 100%);
}
.form-page.tpl-festive {
  --form-primary: #e74c3c;
  --form-primary-2: #c0392b;
  --form-primary-light: rgba(231, 76, 60, 0.1);
  --form-primary-soft: #fdeeee;
  --form-gradient: linear-gradient(135deg, #c0392b 0%, #e74c3c 100%);
}

.form-page {
  min-height: 100vh;
  background: #f5f6fa;
}

.loading-area {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

/* ===== 表单头部 ===== */
.form-body {
  padding: 14px 14px calc(24px + env(safe-area-inset-bottom));
}
.form-header {
  position: relative;
  overflow: hidden;
  background: var(--form-gradient);
  border-radius: 16px;
  padding: 28px 20px;
  margin-bottom: 14px;
  color: #fff;
  text-align: center;
}
.header-decor {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  pointer-events: none;
}
.decor-1 { width: 160px; height: 160px; top: -60px; right: -40px; }
.decor-2 { width: 90px; height: 90px; bottom: -30px; left: -20px; }
.decor-3 { width: 50px; height: 50px; top: 20px; left: 12%; background: rgba(255, 255, 255, 0.12); }
.form-header-content {
  position: relative;
  z-index: 1;
}
.form-icon-wrap {
  width: 56px;
  height: 56px;
  margin: 0 auto 14px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  border: 1.5px solid rgba(255, 255, 255, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
}
.form-icon {
  font-size: 28px;
}
.form-title {
  margin: 0;
  font-size: 21px;
  font-weight: 700;
  letter-spacing: 1px;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}
.form-desc {
  margin: 10px auto 0;
  max-width: 90%;
  font-size: 14px;
  line-height: 1.6;
  opacity: 0.92;
}

/* ===== 已提交提示 ===== */
.submitted-notice {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 14px;
  padding: 13px 15px;
  border-radius: 12px;
  color: var(--form-primary);
  background: var(--form-primary-soft);
  font-size: 14px;
  line-height: 1.6;
}
.submitted-notice .van-icon {
  margin-top: 2px;
  flex-shrink: 0;
}

/* ===== 字段卡片 ===== */
.field-wrapper {
  margin-bottom: 14px;
}
.field-wrapper--compact {
  margin-bottom: 0;
}
.field-wrapper--display {
  padding: 0;
}
.field-card {
  background: #fff;
  border-radius: 14px;
  padding: 18px 16px 12px;
}

/* ===== Vant 式单元格字段（简单字段横向分组） ===== */
.field-cell {
  background: #fff;
  overflow: hidden;
}
.field-cell--first {
  border-radius: 14px 14px 0 0;
}
.field-cell--last {
  border-radius: 0 0 14px 14px;
}
.field-cell--first.field-cell--last {
  border-radius: 14px;
}
.field-cell :deep(.van-field) {
  background: transparent;
}
.field-cell :deep(.van-field__label) {
  font-size: 16px;
  font-weight: 500;
  color: #323233;
  min-width: 76px;
  margin-right: 12px;
}
.field-cell :deep(.van-field__control) {
  font-size: 16px;
}
.field-cell :deep(.van-field__control::placeholder) {
  color: #c0c4cc;
}
.field-cell :deep(.van-field__control--readonly) {
  color: #323233;
  text-align: right;
}
.field-cell :deep(.van-field__right-icon) {
  color: #c0c4cc;
}
.field-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding: 0 2px;
}
.field-icon {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--form-primary);
  background: var(--form-primary-soft);
  font-size: 15px;
  flex-shrink: 0;
}
.field-label {
  font-size: 16px;
  font-weight: 600;
  color: #323233;
}
.required-mark {
  color: #ee0a24;
  font-size: 15px;
  margin-left: 2px;
}

/* 输入框 */
.field-card :deep(.van-field) {
  padding: 6px 2px;
  background: transparent;
}
.field-card :deep(.van-field__control) {
  font-size: 16px;
}
.field-card :deep(.van-field__control::placeholder) {
  color: #c0c4cc;
}
.field-arrow {
  color: #c0c4cc;
  font-size: 14px;
}

/* ===== 单选/多选 ===== */
.option-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 6px 2px 8px;
}
.option-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 14px;
  border-radius: 10px;
  border: 1.5px solid #ebeef5;
  background: #fafbfc;
  transition: all 0.2s;
}
.option-item--active {
  border-color: var(--form-primary);
  background: var(--form-primary-light);
}
.option-text {
  font-size: 16px;
  color: #323233;
  flex: 1;
}
.option-radio {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid #dcdee0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}
.option-radio--checked {
  border-color: var(--form-primary);
}
.option-radio-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--form-primary);
}
.option-checkbox {
  width: 20px;
  height: 20px;
  border-radius: 6px;
  border: 2px solid #dcdee0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #fff;
  transition: all 0.2s;
}
.option-checkbox--checked {
  background: var(--form-primary);
  border-color: var(--form-primary);
}

/* ===== 分割线 ===== */
.form-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #969799;
  font-size: 14px;
  padding: 8px 8px;
}
.form-divider::before,
.form-divider::after {
  height: 1px;
  flex: 1;
  content: '';
  background: #e4e7ed;
}
.form-divider span {
  white-space: nowrap;
}

/* ===== 提示文本 ===== */
.form-tip {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 13px 15px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
}
.tip-icon {
  margin-top: 2px;
  flex-shrink: 0;
}
.form-tip--info { color: #337ecc; background: #ecf5ff; }
.form-tip--success { color: #529b2e; background: #f0f9eb; }
.form-tip--warning { color: #b88230; background: #fdf6ec; }

/* ===== 协议 ===== */
.agreement-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.agreement-check {
  display: flex;
  align-items: flex-start;
  cursor: pointer;
  padding: 4px 2px 10px;
  margin: 0;
  background: transparent;
  user-select: none;
}
.agreement-box {
  width: 22px;
  height: 22px;
  border-radius: 7px;
  border: 2px solid #dcdee0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  margin-top: 1px;
  transition: all 0.2s;
}
.agreement-box--checked {
  background: var(--form-primary);
  border-color: var(--form-primary);
}
.agreement-text {
  font-size: 14px;
  color: #646566;
  line-height: 1.5;
  flex: 1;
  margin-left: 10px;
}
.agreement-link {
  color: var(--form-primary);
  text-decoration: underline;
  text-underline-offset: 3px;
}
/* 协议正文弹窗 */
.agreement-popup {
  display: flex;
  flex-direction: column;
  height: 70vh;
}
.agreement-popup-title {
  padding: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #323233;
  text-align: center;
  border-bottom: 1px solid #f0f0f0;
}
.agreement-popup-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  color: #646566;
  font-size: 15px;
  line-height: 1.7;
  white-space: pre-wrap;
}
.agreement-popup-footer {
  padding: 12px 16px;
  padding-bottom: calc(12px + constant(safe-area-inset-bottom));
  padding-bottom: calc(12px + env(safe-area-inset-bottom));
  background: #fff;
}
.agreement-popup-btn {
  background: var(--form-gradient);
  border: none;
}

/* ===== 交通信息 ===== */
.transport-info-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-bottom: 8px;
}
.transport-section {
  background: #f7f8fa;
  border-radius: 10px;
  padding: 4px 12px 0;
}
.transport-section-title {
  font-size: 14px;
  font-weight: 600;
  color: #646566;
  margin-bottom: 0;
  padding: 10px 0 0;
  display: flex;
  align-items: center;
  gap: 5px;
}
.section-icon {
  color: var(--form-primary);
}
.transport-section :deep(.van-field) {
  background: transparent;
  padding: 6px 2px;
}

/* ===== 图片上传 ===== */
.field-card :deep(.van-uploader__upload) {
  background: var(--form-primary-soft);
  border: 1.5px dashed var(--form-primary);
  border-radius: 10px;
}
.field-card :deep(.van-uploader__upload-icon) {
  color: var(--form-primary);
}
.field-error {
  color: #ee0a24;
  font-size: 13px;
  padding: 6px 2px 8px;
}

/* ===== 只读模式 ===== */
.form-readonly .field-wrapper:not(.field-wrapper--display) {
  pointer-events: none;
}
.form-readonly :deep(.van-field__control) {
  color: #646566;
  -webkit-text-fill-color: #646566;
}

/* ===== 提交按钮 ===== */
.submit-area {
  margin-top: 28px;
  padding: 0 4px;
}
.submit-btn {
  height: 50px;
  font-size: 17px;
  font-weight: 600;
  letter-spacing: 2px;
  background: var(--form-gradient);
  border: none;
  box-shadow: 0 6px 16px var(--form-primary-light);
}
.submit-btn:active {
  opacity: 0.92;
}
.submit-icon {
  margin-right: 6px;
}
.submit-tip {
  text-align: center;
  color: #c0c4cc;
  font-size: 13px;
  margin-top: 12px;
}

/* ===== 提交成功页 ===== */
.success-page {
  min-height: calc(100vh - 46px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.success-card {
  width: 100%;
  max-width: 340px;
  background: #fff;
  border-radius: 20px;
  padding: 44px 28px 32px;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
  animation: success-in 0.4s ease;
}
@keyframes success-in {
  from { opacity: 0; transform: scale(0.92) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
.success-icon-wrap {
  width: 76px;
  height: 76px;
  margin: 0 auto 20px;
  border-radius: 50%;
  background: var(--form-primary-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: success-pop 0.5s 0.15s ease both;
}
@keyframes success-pop {
  from { transform: scale(0.4); }
  60% { transform: scale(1.15); }
  to { transform: scale(1); }
}
.success-icon {
  font-size: 40px;
  color: var(--form-primary);
}
.success-title {
  margin: 0 0 8px;
  font-size: 22px;
  font-weight: 700;
  color: #323233;
}
.success-desc {
  margin: 0 0 28px;
  font-size: 14px;
  color: #969799;
}
.success-btn {
  height: 44px;
  font-size: 15px;
  font-weight: 600;
  background: var(--form-gradient);
  border: none;
}
</style>
