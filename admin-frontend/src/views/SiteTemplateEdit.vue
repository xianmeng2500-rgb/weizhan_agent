<template>
  <div class="visual-editor">
    <!-- 顶部工具栏 -->
    <div class="editor-topbar">
      <div class="topbar-left">
        <span class="topbar-title">{{ isEdit ? '编辑模板' : '新建模板' }}</span>
        <el-tag v-if="isDirty" type="warning" size="small" effect="plain" class="dirty-tag">未保存</el-tag>
        <el-tag v-else-if="isEdit" type="success" size="small" effect="plain" class="dirty-tag">已保存</el-tag>
      </div>

      <div class="topbar-center">
        <el-radio-group v-model="form.layout" size="small" @change="onLayoutChange">
          <el-radio-button value="grid">
            <el-icon class="layout-icon"><Grid /></el-icon>九宫格
          </el-radio-button>
          <el-radio-button value="button">
            <el-icon class="layout-icon"><Tickets /></el-icon>按钮列表
          </el-radio-button>
          <el-radio-button value="free">
            <el-icon class="layout-icon"><Rank /></el-icon>自由拖拽
          </el-radio-button>
        </el-radio-group>
      </div>

      <div class="topbar-right">
        <el-button size="small" @click="handleBack">返回</el-button>
        <el-button type="primary" size="small" :loading="saving" @click="handleSave">
          保存{{ isDirty ? ' *' : '' }}
        </el-button>
      </div>
    </div>

    <div class="editor-body">
      <!-- 左侧面板 -->
      <div class="editor-left">
        <div class="left-tabs">
          <div class="left-tab-nav" role="tablist" aria-label="编辑面板">
            <button
              class="left-tab-button"
              :class="{ active: leftTab === 'site' }"
              type="button"
              role="tab"
              :aria-selected="leftTab === 'site'"
              @click="leftTab = 'site'"
            >模板设置</button>
            <button
              class="left-tab-button"
              :class="{ active: leftTab === 'modules' }"
              type="button"
              role="tab"
              :aria-selected="leftTab === 'modules'"
              @click="leftTab = 'modules'"
            >页面和按钮管理 ({{ modules.length }})</button>
          </div>

          <div v-show="leftTab === 'site'" class="left-tab-panel">
            <div class="left-scroll">
              <el-collapse v-model="activeSettingGroups" class="setting-collapse">
                <!-- 基本信息 -->
                <el-collapse-item name="basic">
                  <template #title>
                    <div class="collapse-title">
                      <el-icon><Document /></el-icon>
                      <span>基本信息</span>
                    </div>
                  </template>
                  <el-form label-width="76px" size="small">
                    <el-form-item label="模板名称" required>
                      <el-input v-model="form.name" placeholder="如：周年庆活动模板" @input="markDirty" />
                    </el-form-item>
                    <el-form-item label="模板描述">
                      <el-input v-model="form.description" type="textarea" :rows="2" maxlength="255" show-word-limit placeholder="模板用途说明，展示给选择模板的用户" @input="markDirty" />
                    </el-form-item>
                    <el-form-item label="排序值">
                      <el-input-number v-model="form.sort_order" :min="0" :max="9999" style="width: 100%" @change="markDirty" />
                    </el-form-item>
                  </el-form>
                </el-collapse-item>

                <!-- 页面外观：KV图 + 背景设置 + 模板风格 -->
                <el-collapse-item name="appearance">
                  <template #title>
                    <div class="collapse-title">
                      <el-icon><Brush /></el-icon>
                      <span>页面外观</span>
                    </div>
                  </template>
                  <!-- KV 图 -->
                  <div class="sub-section">
                    <div class="sub-section-label">KV 图</div>
                    <el-upload
                      action="/api/v1/upload/image"
                      :headers="uploadHeaders"
                      :show-file-list="false"
                      :on-success="onUploadSuccess('kv_image')"
                      accept="image/*"
                    >
                      <div v-if="form.kv_image" class="upload-preview">
                        <img :src="form.kv_image" class="preview-img" />
                        <div class="preview-mask">点击更换</div>
                      </div>
                      <div v-else class="upload-placeholder">
                        <el-icon size="28"><Plus /></el-icon>
                        <span>上传 KV 图</span>
                        <span class="upload-tip">建议 750×340 或等比横幅</span>
                      </div>
                    </el-upload>
                    <div class="upload-actions">
                      <el-button size="small" type="primary" plain :icon="MagicStick" @click="openAiDialog('kv')">AI 生成 KV 图</el-button>
                      <el-button v-if="form.kv_image" text size="small" @click="form.kv_image = ''; markDirty()">移除 KV 图</el-button>
                    </div>
                  </div>

                  <el-divider class="sub-divider" />

                  <!-- 背景设置 -->
                  <div class="sub-section">
                    <div class="sub-section-label">背景设置</div>
                    <el-form label-width="70px" size="small">
                      <el-form-item label="背景图">
                        <el-upload
                          action="/api/v1/upload/image"
                          :headers="uploadHeaders"
                          :show-file-list="false"
                          :on-success="onUploadSuccess('background_image')"
                          accept="image/*"
                        >
                          <div v-if="form.background_image" class="upload-preview small">
                            <img :src="form.background_image" class="preview-img" />
                            <div class="preview-mask">更换</div>
                          </div>
                          <div v-else class="upload-placeholder small">
                            <el-icon size="22"><Plus /></el-icon>
                            <span>上传背景图</span>
                          </div>
                        </el-upload>
                        <div class="upload-actions">
                          <el-button size="small" type="primary" plain :icon="MagicStick" @click="openAiDialog('background')">AI 生成背景</el-button>
                          <el-button v-if="form.background_image" text size="small" @click="form.background_image = ''; markDirty()">移除背景图</el-button>
                        </div>
                      </el-form-item>
                      <el-form-item label="背景色">
                        <div class="color-row">
                          <el-color-picker v-model="form.background_color" @change="markDirty" />
                          <el-button v-if="form.background_color" text size="small" @click="form.background_color = ''; markDirty()">清除</el-button>
                        </div>
                        <div class="hint">优先级：背景图 > 背景色 > 模板默认</div>
                      </el-form-item>
                    </el-form>
                  </div>

                  <el-divider class="sub-divider" />

                  <!-- 模板风格 -->
                  <div class="sub-section">
                    <div class="sub-section-label">模板风格</div>
                    <el-radio-group v-model="form.template_key" size="small" @change="markDirty">
                      <el-radio-button value="default">默认</el-radio-button>
                      <el-radio-button value="classic">经典蓝紫</el-radio-button>
                      <el-radio-button value="dark">暗夜科技</el-radio-button>
                      <el-radio-button value="festive">节日红金</el-radio-button>
                    </el-radio-group>
                  </div>

                  <el-divider class="sub-divider" />

                  <!-- 预览图 -->
                  <div class="sub-section">
                    <div class="sub-section-label">模板预览图</div>
                    <el-upload
                      action="/api/v1/upload/image"
                      :headers="uploadHeaders"
                      :show-file-list="false"
                      :on-success="onUploadSuccess('preview_image')"
                      accept="image/*"
                    >
                      <div v-if="form.preview_image" class="upload-preview">
                        <img :src="form.preview_image" class="preview-img" />
                        <div class="preview-mask">点击更换</div>
                      </div>
                      <div v-else class="upload-placeholder small">
                        <el-icon size="22"><Plus /></el-icon>
                        <span>上传模板预览图（模板选择时展示）</span>
                      </div>
                    </el-upload>
                    <div class="hint" style="margin-top: 6px">不传时模板选择页将展示风格占位背景</div>
                  </div>
                </el-collapse-item>

                <!-- 微信分享 -->
                <el-collapse-item name="share">
                  <template #title>
                    <div class="collapse-title">
                      <el-icon><Share /></el-icon>
                      <span>微信分享</span>
                    </div>
                  </template>
                  <el-form label-width="76px" size="small">
                    <el-form-item label="分享图标">
                      <el-upload
                        action="/api/v1/upload/image"
                        :headers="uploadHeaders"
                        :show-file-list="false"
                        :on-success="onUploadSuccess('share_image')"
                        accept="image/*"
                      >
                        <div v-if="form.share_image" class="share-image-preview">
                          <img :src="form.share_image" class="preview-img" />
                          <div class="preview-mask">点击更换</div>
                        </div>
                        <div v-else class="upload-placeholder share-image-placeholder">
                          <el-icon size="22"><Plus /></el-icon>
                          <span>上传分享图标</span>
                        </div>
                      </el-upload>
                      <div class="upload-actions">
                        <el-button size="small" type="primary" plain :icon="MagicStick" @click="openAiDialog('share')">AI 生成分享图</el-button>
                        <el-button v-if="form.share_image" text size="small" @click="form.share_image = ''; markDirty()">移除图标</el-button>
                      </div>
                    </el-form-item>
                    <el-form-item label="分享标题">
                      <el-input v-model="form.share_title" maxlength="128" show-word-limit placeholder="默认使用微站名称" @input="markDirty" />
                    </el-form-item>
                    <el-form-item label="分享副标题">
                      <el-input v-model="form.share_subtitle" type="textarea" :rows="2" maxlength="255" show-word-limit placeholder="可选，展示在微信分享描述中" @input="markDirty" />
                    </el-form-item>
                  </el-form>
                </el-collapse-item>
              </el-collapse>
            </div>
          </div>

          <div v-show="leftTab === 'modules'" class="left-tab-panel">
            <div class="left-scroll">
              <div class="module-list">
                <!-- 页面标题（页面装饰元素，层级最高，可在预览区拖拽定位） -->
                <div
                  class="module-item title-item"
                  :class="{ active: selectedModuleId === TITLE_DECO_ID }"
                  @click="selectedModuleId = TITLE_DECO_ID"
                >
                  <span class="layer-drag-handle" style="visibility: hidden"><Rank /></span>
                  <div class="module-icon title-icon">
                    <el-icon :size="18"><EditPen /></el-icon>
                  </div>
                  <div class="module-info">
                    <div class="module-title">页面标题</div>
                    <div class="module-meta">
                      <el-tag size="small" type="warning">页面装饰</el-tag>
                      <span v-if="!form.title_config.enabled" class="disabled-tag">已隐藏</span>
                    </div>
                  </div>
                  <div class="module-actions">
                    <el-switch v-model="form.title_config.enabled" size="small" @change="markDirty" @click.stop />
                  </div>
                </div>
                <div
                  v-for="(m, idx) in modules"
                  :key="m.id"
                  class="module-item"
                  :class="{ active: selectedModuleId === m.id }"
                  draggable="true"
                  @dragstart="onLayerDragStart($event, idx)"
                  @dragover.prevent="onLayerDragOver(idx)"
                  @drop="onLayerDrop(idx)"
                  @dragend="layerDragIndex = null"
                  @click="selectedModuleId = m.id"
                >
                  <el-icon class="layer-drag-handle"><Rank /></el-icon>
                  <div class="module-icon">
                    <img v-if="m.icon" :src="m.icon" />
                    <span v-else>{{ (m.title || '?').charAt(0) }}</span>
                  </div>
                  <div class="module-info">
                    <div class="module-title">{{ m.title || '未命名按钮' }}</div>
                    <div class="module-meta">
                      <el-tag size="small" :type="metaTagType(m.content_type)">{{ metaTagText(m.content_type) }}</el-tag>
                      <span v-if="!m.is_active" class="disabled-tag">已禁用</span>
                    </div>
                  </div>
                  <div class="module-actions">
                    <el-switch v-model="m.is_active" size="small" @change="markDirty" @click.stop />
                    <el-popconfirm title="确认删除？" @confirm="deleteModule(m)">
                      <template #reference>
                        <el-button text size="small" type="danger" @click.stop>删除</el-button>
                      </template>
                    </el-popconfirm>
                  </div>
                </div>
              </div>
              <el-button class="add-module-btn" type="primary" plain @click="addModule">
                <el-icon><Plus /></el-icon>添加按钮
              </el-button>
              <div class="hint" style="margin-top: 10px; text-align: center">
                模板中的按钮为预置按钮，用户套用模板后自动创建，可在微站编辑器中继续维护内容
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间手机预览 -->
      <div class="editor-center">
        <div class="preview-wrapper">
          <div ref="deviceFrameRef" class="device-frame" :class="'tpl-' + form.template_key" :style="previewBgStyle">
            <div class="device-notch"></div>
            <div class="status-bar">
              <span class="status-time">9:41</span>
              <div class="status-icons">
                <span class="signal"></span>
                <span class="wifi"></span>
                <span class="battery"></span>
              </div>
            </div>
            <div v-if="form.background_image" class="bg-layer">
              <img :src="form.background_image" class="bg-image" alt="" />
            </div>
            <!-- 自由拖拽布局 -->
            <div
              v-if="form.layout === 'free'"
              class="free-layout"
              ref="freeLayoutRef"
              @pointerdown.self="selectedModuleId = null"
            >
              <div
                v-for="m in modules"
                :key="m.id"
                class="preview-btn free-btn icon-only"
                :class="{ dragging: draggingId === m.id, resizing: resizingId === m.id, selected: selectedModuleId === m.id, 'has-height': m.height != null, disabled: !m.is_active }"
                :style="freeBtnStyle(m)"
                @pointerdown="startDrag($event, m)"
                @click.stop="selectedModuleId = m.id"
                @dblclick="selectedModuleId = m.id"
              >
                <div class="free-btn-inner">
                  <img v-if="m.icon" :src="m.icon" class="btn-icon" />
                  <div v-else class="btn-icon-placeholder">{{ (m.title || '?').charAt(0) }}</div>
                </div>

                <template v-if="selectedModuleId === m.id">
                  <span class="resize-handle rh-nw" @pointerdown.stop="startResize($event, m, 'nw')" />
                  <span class="resize-handle rh-n" @pointerdown.stop="startResize($event, m, 'n')" />
                  <span class="resize-handle rh-ne" @pointerdown.stop="startResize($event, m, 'ne')" />
                  <span class="resize-handle rh-e" @pointerdown.stop="startResize($event, m, 'e')" />
                  <span class="resize-handle rh-se" @pointerdown.stop="startResize($event, m, 'se')" />
                  <span class="resize-handle rh-s" @pointerdown.stop="startResize($event, m, 's')" />
                  <span class="resize-handle rh-sw" @pointerdown.stop="startResize($event, m, 'sw')" />
                  <span class="resize-handle rh-w" @pointerdown.stop="startResize($event, m, 'w')" />
                </template>
              </div>
            </div>
            <!-- 页面标题装饰：绝对定位、层级最高、可拖拽 -->
            <div
              v-if="form.title_config.enabled"
              class="site-title-deco"
              :class="{ selected: selectedModuleId === TITLE_DECO_ID }"
              :style="previewTitleStyle"
              @pointerdown="startTitleDrag"
              @click.stop="selectedModuleId = TITLE_DECO_ID"
            >
              {{ previewTitleText }}
            </div>
            <!-- 拖拽辅助线 -->
            <template v-if="guides.vLines.length || guides.hLines.length">
              <div v-for="(v, i) in guides.vLines" :key="'gv' + i" class="guide-line guide-v" :style="{ left: v + '%' }"></div>
              <div v-for="(h, i) in guides.hLines" :key="'gh' + i" class="guide-line guide-h" :style="{ top: h + '%' }"></div>
            </template>
            <div class="device-screen">
              <!-- KV 区域 -->
              <div class="kv-area" v-if="form.kv_image">
                <img :src="form.kv_image" class="kv-image" />
              </div>

              <!-- 九宫格布局 -->
              <div v-if="form.layout === 'grid'" class="content-area">
                <div class="grid-layout">
                  <div
                    v-for="m in modules"
                    :key="m.id"
                    class="preview-btn grid-item"
                    :class="{ selected: selectedModuleId === m.id, disabled: !m.is_active }"
                    @click.stop="selectedModuleId = m.id"
                  >
                    <img v-if="m.icon" :src="m.icon" class="grid-icon" />
                    <div v-else class="grid-icon-placeholder">{{ (m.title || '?').charAt(0) }}</div>
                    <div class="grid-title">{{ m.title }}</div>
                  </div>
                </div>
              </div>

              <!-- 按钮列表布局 -->
              <div v-else-if="form.layout === 'button'" class="content-area">
                <div class="button-layout">
                  <div
                    v-for="m in modules"
                    :key="m.id"
                    class="preview-btn button-item"
                    :class="{ selected: selectedModuleId === m.id, disabled: !m.is_active }"
                    @click.stop="selectedModuleId = m.id"
                  >
                    <img v-if="m.icon" :src="m.icon" class="btn-icon" />
                    <div v-else class="btn-icon-placeholder">{{ (m.title || '?').charAt(0) }}</div>
                    <span class="btn-text">{{ m.title }}</span>
                    <span class="btn-arrow">›</span>
                  </div>
                </div>
              </div>

              <!-- 空状态提示 -->
              <div v-if="modules.length === 0" class="empty-tip">
                <el-icon size="40"><Plus /></el-icon>
                <div>点击左侧「添加按钮」创建第一个按钮</div>
              </div>
            </div>
          </div>

          <!-- 预览提示 -->
          <div class="preview-tips">
            <span v-if="form.layout === 'free'">拖动按钮调整位置 · 选中后拖动手柄调整大小与形状</span>
            <span v-else>在「页面和按钮管理」标签拖拽调整顺序</span>
          </div>
        </div>
      </div>

      <!-- 右侧属性面板 -->
      <div class="editor-inspector">
        <template v-if="selectedModule">
          <div class="inspector-head">
            <span class="inspector-title">按钮属性</span>
            <el-button text size="small" type="danger" @click="deleteModule(selectedModule)">删除</el-button>
          </div>
          <div class="inspector-body">
            <div class="field-block">
              <label class="field-label">标题</label>
              <el-input v-model="selectedModule.title" size="small" placeholder="按钮标题" @input="markDirty" />
            </div>

            <div class="field-block">
              <label class="field-label">图标</label>
              <IconPicker
                :model-value="selectedModule.icon"
                @update:model-value="onIconChange"
              />
              <div class="hint" style="margin-top: 4px">可从图标库选择或上传自定义图标，建议 128×128 正方形</div>
            </div>

            <div class="field-block">
              <label class="field-label">内容类型</label>
              <el-select v-model="selectedModule.content_type" size="small" @change="markDirty">
                <el-option label="富文本" value="rich_text" />
                <el-option label="外链" value="external_link" />
                <el-option label="报名表单" value="registration_form" />
                <el-option label="日程" value="schedule" />
                <el-option label="二维码" value="qrcode" />
              </el-select>
            </div>

            <div v-if="selectedModule.content_type === 'external_link'" class="field-block">
              <label class="field-label">外链地址</label>
              <el-input v-model="selectedModule.external_url" size="small" placeholder="https://" @input="markDirty" />
            </div>

            <div class="field-block">
              <label class="field-label">启用</label>
              <el-switch v-model="selectedModule.is_active" @change="markDirty" />
              <span class="field-hint" style="margin-left: 8px">关闭后套用模板时不创建该按钮</span>
            </div>

            <!-- 自由拖拽模式: 尺寸与形状 -->
            <template v-if="form.layout === 'free'">
              <div class="inspector-divider">尺寸与形状</div>

              <div class="field-block">
                <label class="field-label">
                  宽度
                  <span class="field-unit">占画布 %</span>
                </label>
                <div class="size-row">
                  <el-slider
                    v-model="widthSliderValue"
                    :min="10"
                    :max="100"
                    :step="1"
                    size="small"
                    class="size-slider"
                    @input="onWidthInput"
                    @change="onStyleFieldChange('width', widthSliderValue)"
                  />
                  <el-input-number
                    v-model="widthSliderValue"
                    :min="10"
                    :max="100"
                    :step="1"
                    size="small"
                    controls-position="right"
                    class="size-number"
                    @change="onStyleFieldChange('width', widthSliderValue)"
                  />
                </div>
              </div>

              <div class="field-block">
                <label class="field-label">
                  高度
                  <span class="field-unit">占画布 %</span>
                  <el-button
                    v-if="selectedModule.height != null"
                    text
                    size="small"
                    class="reset-btn"
                    @click="resetHeight"
                  >自适应</el-button>
                </label>
                <div class="size-row">
                  <el-slider
                    v-model="heightSliderValue"
                    :min="5"
                    :max="60"
                    :step="1"
                    size="small"
                    class="size-slider"
                    :disabled="selectedModule.height == null"
                    @input="onHeightInput"
                    @change="onStyleFieldChange('height', heightSliderValue)"
                  />
                  <el-input-number
                    v-model="heightSliderValue"
                    :min="5"
                    :max="60"
                    :step="1"
                    size="small"
                    controls-position="right"
                    class="size-number"
                    :disabled="selectedModule.height == null"
                    @change="onStyleFieldChange('height', heightSliderValue)"
                  />
                </div>
                <div class="field-hint">默认高度随内容自适应，设置后高度固定</div>
              </div>

              <div class="field-block">
                <label class="field-label">图标位置</label>
                <div class="seg-row">
                  <button
                    v-for="p in iconPositionOptions"
                    :key="p.value"
                    type="button"
                    class="seg-btn"
                    :class="{ active: (selectedModule.icon_position || 'left') === p.value }"
                    :title="p.label"
                    @click="setStyleField('icon_position', p.value)"
                  >{{ p.icon }}</button>
                </div>
              </div>

              <div class="field-block">
                <label class="field-label">内容对齐</label>
                <div class="seg-row">
                  <button
                    v-for="p in alignOptions"
                    :key="p.value"
                    type="button"
                    class="seg-btn seg-text"
                    :class="{ active: (selectedModule.content_align || 'left') === p.value }"
                    :title="p.label"
                    @click="setStyleField('content_align', p.value)"
                  >{{ p.label }}</button>
                </div>
              </div>

              <div class="field-block">
                <label class="field-label">圆角</label>
                <div class="radius-presets">
                  <button
                    v-for="p in radiusPresets"
                    :key="p.value"
                    type="button"
                    class="radius-preset"
                    :class="{ active: selectedModule.border_radius === p.value }"
                    :style="{ borderRadius: p.value === 999 ? '50%' : p.value + 'px' }"
                    :title="p.label"
                    @click="setBorderRadius(p.value)"
                  ></button>
                  <span class="preset-value">{{ selectedModule.border_radius ?? 10 }} px</span>
                </div>
                <div class="radius-slider-row">
                  <el-slider
                    v-model="radiusSliderValue"
                    :min="0"
                    :max="50"
                    :step="1"
                    size="small"
                    class="size-slider"
                    @change="onStyleFieldChange('border_radius', radiusSliderValue)"
                  />
                </div>
              </div>

              <div class="field-block">
                <label class="field-label">背景色</label>
                <div class="color-row">
                  <el-color-picker
                    :model-value="selectedModule.bg_color || null"
                    @change="(v: any) => onColorChange('bg_color', v)"
                  />
                  <el-button v-if="selectedModule.bg_color" text size="small" @click="onColorChange('bg_color', null)">清除</el-button>
                  <span v-else class="field-hint">跟随模板默认</span>
                </div>
              </div>

              <div class="field-block">
                <label class="field-label">文字颜色</label>
                <div class="color-row">
                  <el-color-picker
                    :model-value="selectedModule.font_color || null"
                    @change="(v: any) => onColorChange('font_color', v)"
                  />
                  <el-button v-if="selectedModule.font_color" text size="small" @click="onColorChange('font_color', null)">清除</el-button>
                  <span v-else class="field-hint">跟随模板默认</span>
                </div>
              </div>

              <div class="field-block">
                <label class="field-label">显示箭头</label>
                <el-switch
                  :model-value="selectedModule.show_arrow !== false"
                  @change="(v: any) => onShowArrowChange(v)"
                />
                <span class="field-hint" style="margin-left: 8px">关闭后隐藏按钮右侧的 › 箭头</span>
              </div>
            </template>
          </div>
        </template>

        <!-- 页面标题（页面装饰）属性面板 -->
        <template v-else-if="selectedModuleId === TITLE_DECO_ID">
          <div class="inspector-head">
            <span class="inspector-title">页面标题属性</span>
          </div>
          <div class="inspector-body">
            <div class="field-block">
              <label class="field-label">启用</label>
              <el-switch v-model="form.title_config.enabled" @change="markDirty" />
              <span class="field-hint" style="margin-left: 8px">作为页面装饰显示在最高层级</span>
            </div>

            <template v-if="form.title_config.enabled">
              <div class="field-block">
                <label class="field-label">标题文本</label>
                <el-input
                  v-model="form.title_config.text"
                  size="small"
                  :placeholder="form.name || '默认显示微站名称'"
                  maxlength="60"
                  @input="markDirty"
                />
              </div>

              <div class="field-block">
                <label class="field-label">字体</label>
                <el-select v-model="form.title_config.font" size="small" @change="markDirty">
                  <el-option label="黑体" value="sans" />
                  <el-option label="宋体" value="song" />
                  <el-option label="楷体" value="kai" />
                  <el-option label="仿宋" value="fangsong" />
                </el-select>
              </div>

              <div class="field-block">
                <label class="field-label">颜色</label>
                <div class="color-row">
                  <el-color-picker v-model="form.title_config.color" @change="markDirty" />
                </div>
              </div>

              <div class="field-block">
                <label class="field-label">
                  大小
                  <span class="field-unit">px</span>
                </label>
                <div class="size-row">
                  <el-slider
                    v-model="form.title_config.size"
                    :min="12"
                    :max="48"
                    :step="1"
                    size="small"
                    class="size-slider"
                    @input="markDirty"
                  />
                  <el-input-number
                    v-model="form.title_config.size"
                    :min="12"
                    :max="48"
                    :step="1"
                    size="small"
                    controls-position="right"
                    class="size-number"
                    @change="markDirty"
                  />
                </div>
              </div>

              <div class="field-block">
                <label class="field-label">粗细</label>
                <el-radio-group v-model="form.title_config.bold" size="small" @change="markDirty">
                  <el-radio-button :value="false">常规</el-radio-button>
                  <el-radio-button :value="true">加粗</el-radio-button>
                </el-radio-group>
              </div>

              <div class="inspector-divider">位置与尺寸</div>

              <div class="field-block">
                <label class="field-label">
                  水平位置
                  <span class="field-unit">占画布 %</span>
                </label>
                <div class="size-row">
                  <el-slider
                    v-model="form.title_config.position_x"
                    :min="0"
                    :max="100"
                    :step="0.5"
                    size="small"
                    class="size-slider"
                    @input="markDirty"
                  />
                  <el-input-number
                    v-model="form.title_config.position_x"
                    :min="0"
                    :max="100"
                    :step="0.5"
                    size="small"
                    controls-position="right"
                    class="size-number"
                    @change="markDirty"
                  />
                </div>
              </div>

              <div class="field-block">
                <label class="field-label">
                  垂直位置
                  <span class="field-unit">占画布 %</span>
                </label>
                <div class="size-row">
                  <el-slider
                    v-model="form.title_config.position_y"
                    :min="0"
                    :max="100"
                    :step="0.5"
                    size="small"
                    class="size-slider"
                    @input="markDirty"
                  />
                  <el-input-number
                    v-model="form.title_config.position_y"
                    :min="0"
                    :max="100"
                    :step="0.5"
                    size="small"
                    controls-position="right"
                    class="size-number"
                    @change="markDirty"
                  />
                </div>
                <div class="field-hint">也可以直接在预览区拖拽标题调整位置</div>
              </div>

              <div class="field-block">
                <label class="field-label">
                  最大宽度
                  <span class="field-unit">占画布 %</span>
                </label>
                <div class="size-row">
                  <el-slider
                    v-model="form.title_config.max_width"
                    :min="20"
                    :max="100"
                    :step="1"
                    size="small"
                    class="size-slider"
                    @input="markDirty"
                  />
                  <el-input-number
                    v-model="form.title_config.max_width"
                    :min="20"
                    :max="100"
                    :step="1"
                    size="small"
                    controls-position="right"
                    class="size-number"
                    @change="markDirty"
                  />
                </div>
              </div>
            </template>
          </div>
        </template>

        <div v-else class="inspector-empty">
          <el-icon size="40"><Edit /></el-icon>
          <div class="ie-title">未选择元素</div>
          <div class="ie-desc">点击左侧列表或中间预览区的按钮，在此编辑属性；「页面标题」为页面装饰元素。</div>
        </div>
      </div>
    </div>

    <!-- AI 生图弹窗 -->
    <AiGenerateDialog v-model:visible="aiDialog.visible" :use="aiDialog.use" @select="onAiImageSelect" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Rank, Grid, Tickets, Document, Brush,
  Edit, Share, MagicStick, EditPen,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'
import api from '@/api'
import IconPicker from '@/components/IconPicker.vue'
import AiGenerateDialog from '@/components/AiGenerateDialog.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const isEdit = computed(() => !!route.params.id)
const uploadHeaders = computed(() => ({ Authorization: `Bearer ${auth.token}` }))

const saving = ref(false)
const isDirty = ref(false)
const leftTab = ref<'site' | 'modules'>('site')
const activeSettingGroups = ref<string[]>(['basic'])

function markDirty() {
  isDirty.value = true
}

// 未保存离开确认（覆盖返回按钮 / 浏览器返回 / 侧边栏跳转等所有离开路径）
onBeforeRouteLeave(async () => {
  if (!isDirty.value) return true
  try {
    await ElMessageBox.confirm('模板有未保存的修改（包括添加的按钮模块），离开后将丢失，确定离开吗？', '未保存的修改', {
      confirmButtonText: '离开',
      cancelButtonText: '留下来',
      type: 'warning',
    })
    return true
  } catch {
    return false
  }
})

function handleBack() {
  router.back()
}

function metaTagType(contentType: string): 'success' | 'warning' | 'info' {
  const map: Record<string, 'success' | 'warning' | 'info'> = {
    rich_text: 'info',
    external_link: 'warning',
    registration_form: 'success',
    schedule: 'success',
    qrcode: 'info',
  }
  return map[contentType] || 'info'
}

function metaTagText(contentType: string): string {
  const map: Record<string, string> = {
    rich_text: '富文本',
    external_link: '外链',
    registration_form: '报名表单',
    schedule: '日程',
    qrcode: '二维码',
  }
  return map[contentType] || '未设置'
}

// --- 表单数据 ---
const DEFAULT_TITLE_CONFIG = {
  enabled: false,
  text: '',
  font: 'sans',
  color: '#333333',
  size: 20,
  bold: true,
  position_x: 5,
  position_y: 5,
  max_width: 80,
}

const form = reactive({
  name: '',
  description: '',
  sort_order: 0,
  template_key: 'default',
  layout: 'grid',
  kv_image: '',
  title_config: { ...DEFAULT_TITLE_CONFIG },
  background_color: '',
  background_image: '',
  share_image: '',
  share_title: '',
  share_subtitle: '',
  preview_image: '',
})

// --- 模块（本地数组，保存时统一提交） ---
let localIdSeed = 1
const modules = ref<any[]>([])
const selectedModuleId = ref<number | null>(null)
const selectedModule = computed(() => modules.value.find((m) => m.id === selectedModuleId.value) || null)

const TITLE_DECO_ID = 0

watch(selectedModule, (m) => {
  syncSliderValues(m)
})

function newModule(): any {
  const idx = modules.value.length
  const m: any = {
    id: localIdSeed++,
    title: '新按钮',
    content_type: 'rich_text',
    external_url: '',
    icon: '',
    is_active: true,
    sort_order: idx,
  }
  if (form.layout === 'free') {
    m.position_x = 10
    m.position_y = 15 + idx * 12
    m.width = 80
  }
  return m
}

function addModule() {
  const m = newModule()
  modules.value.push(m)
  selectedModuleId.value = m.id
  markDirty()
}

function deleteModule(m: any) {
  const idx = modules.value.findIndex((x) => x.id === m.id)
  if (idx >= 0) modules.value.splice(idx, 1)
  if (selectedModuleId.value === m.id) selectedModuleId.value = null
  markDirty()
}

// --- 预览背景样式（背景图走 bg-layer 图层，这里只兜底背景色） ---
const previewBgStyle = computed(() => {
  if (form.background_color) {
    return { background: form.background_color }
  }
  return {}
})

// --- 页面标题装饰 ---
const TITLE_FONT_STACKS: Record<string, string> = {
  sans: "'PingFang SC', 'Helvetica Neue', 'Microsoft YaHei', sans-serif",
  song: "'Songti SC', 'SimSun', serif",
  kai: "'Kaiti SC', 'STKaiti', 'KaiTi', serif",
  fangsong: "'Fangsong SC', 'STFangsong', 'FangSong', serif",
}
const previewTitleText = computed(() => form.title_config.text || form.name || '微站标题')
const previewTitleStyle = computed(() => {
  const t = form.title_config
  return {
    position: 'absolute',
    left: (t.position_x ?? 5) + '%',
    top: (t.position_y ?? 5) + '%',
    maxWidth: (t.max_width ?? 80) + '%',
    fontFamily: TITLE_FONT_STACKS[t.font] || TITLE_FONT_STACKS.sans,
    color: t.color || '#333333',
    fontSize: (t.size || 20) + 'px',
    fontWeight: t.bold ? '700' : '400',
  }
})

// --- 拖拽（自由模式） ---
const freeLayoutRef = ref<HTMLElement>()
const deviceFrameRef = ref<HTMLElement>()
const draggingId = ref<number | null>(null)
const resizingId = ref<number | null>(null)

// --- 拖拽辅助线（对齐吸附） ---
const SNAP_THRESHOLD = 1.5 // 百分比阈值
const guides = ref<{ vLines: number[]; hLines: number[] }>({ vLines: [], hLines: [] })

function computeGuides(
  bounds: { left: number; top: number; width: number; height: number },
  excludeModuleId?: number,
  isTitle?: boolean,
) {
  const vLines = new Set<number>()
  const hLines = new Set<number>()

  // 参考元素的 X/Y 值：左、右、中心
  const refXs: number[] = [50] // 容器中心
  const refYs: number[] = [50]

  for (const m of modules.value) {
    if (m.id === excludeModuleId) continue
    if (m.is_active === false) continue
    const mw = m.width ?? 30
    const mh = m.height ?? 10
    const mx = m.position_x ?? 5
    const my = m.position_y ?? 10
    refXs.push(mx, mx + mw, mx + mw / 2)
    if (mh > 0) refYs.push(my, my + mh, my + mh / 2)
  }

  // 拖拽标题时，模块仍作为参考；拖拽模块时，标题也作为参考
  if (!isTitle && form.title_config?.enabled) {
    const tc = form.title_config
    const tw = tc.max_width ?? 80
    const tx = tc.position_x ?? 5
    refXs.push(tx, tx + tw, tx + tw / 2)
  }

  // 被拖拽元素的参考点：左、右、中心
  const dragXRefs = [bounds.left, bounds.left + bounds.width, bounds.left + bounds.width / 2]
  const dragYRefs = [bounds.top, bounds.top + bounds.height, bounds.top + bounds.height / 2]

  let snappedX = bounds.left
  let snappedY = bounds.top

  // X 轴最近对齐
  let bestXDist = SNAP_THRESHOLD
  for (const dragVal of dragXRefs) {
    for (const refVal of refXs) {
      const dist = Math.abs(dragVal - refVal)
      if (dist < bestXDist) {
        bestXDist = dist
        snappedX = bounds.left + (refVal - dragVal)
        vLines.add(Math.round(refVal * 10) / 10)
      }
    }
  }

  // Y 轴最近对齐（标题高度不确定，跳过 Y 吸附）
  if (!isTitle) {
    let bestYDist = SNAP_THRESHOLD
    for (const dragVal of dragYRefs) {
      for (const refVal of refYs) {
        const dist = Math.abs(dragVal - refVal)
        if (dist < bestYDist) {
          bestYDist = dist
          snappedY = bounds.top + (refVal - dragVal)
          hLines.add(Math.round(refVal * 10) / 10)
        }
      }
    }
  }

  // 边界约束
  snappedX = Math.max(0, Math.min(100 - bounds.width, snappedX))
  if (!isTitle) {
    snappedY = Math.max(0, Math.min(100 - bounds.height, snappedY))
  } else {
    snappedY = Math.max(0, Math.min(100, snappedY))
  }

  return {
    snappedX: Math.round(snappedX * 10) / 10,
    snappedY: Math.round(snappedY * 10) / 10,
    vLines: [...vLines],
    hLines: [...hLines],
  }
}

function freeBtnStyle(m: any) {
  const style: Record<string, string> = {
    left: (m.position_x ?? 5) + '%',
    top: (m.position_y ?? 10) + '%',
  }
  if (m.width != null) style.width = m.width + '%'
  if (m.height != null) style.height = m.height + '%'
  if (m.border_radius != null) style.borderRadius = m.border_radius + 'px'
  if (m.bg_color) style.background = m.bg_color
  if (m.font_color) style.color = m.font_color
  return style
}

// 属性面板: 宽度/高度/圆角滑块
const widthSliderValue = ref(40)
const heightSliderValue = ref(20)
const radiusSliderValue = ref(10)
const radiusPresets = [
  { value: 0, label: '直角' },
  { value: 10, label: '圆角' },
  { value: 25, label: '胶囊' },
  { value: 999, label: '圆形' },
]

const iconPositionOptions = [
  { value: 'left', label: '图标在左', icon: '←' },
  { value: 'right', label: '图标在右', icon: '→' },
  { value: 'top', label: '图标在上', icon: '↑' },
  { value: 'bottom', label: '图标在下', icon: '↓' },
]
const alignOptions = [
  { value: 'left', label: '左对齐', icon: '左' },
  { value: 'center', label: '居中', icon: '中' },
  { value: 'right', label: '右对齐', icon: '右' },
]

function syncSliderValues(m: any) {
  if (!m) return
  widthSliderValue.value = m.width != null ? Math.round(m.width) : 40
  heightSliderValue.value = m.height != null ? Math.round(m.height) : 20
  radiusSliderValue.value = m.border_radius != null ? Math.min(m.border_radius, 50) : 10
}

function onWidthInput(v: number) {
  const m = selectedModule.value
  if (m) m.width = v
}

function onHeightInput(v: number) {
  const m = selectedModule.value
  if (m) m.height = v
}

function resetHeight() {
  const m = selectedModule.value
  if (!m) return
  m.height = null
  heightSliderValue.value = 20
  markDirty()
}

function setStyleField(field: string, value: any) {
  const m = selectedModule.value
  if (!m) return
  m[field] = value
  markDirty()
}

function onStyleFieldChange(field: string, value: any) {
  const m = selectedModule.value
  if (!m) return
  m[field] = value
  markDirty()
}

function setBorderRadius(v: number) {
  const m = selectedModule.value
  if (!m) return
  m.border_radius = v
  radiusSliderValue.value = Math.min(v, 50)
  markDirty()
}

function onColorChange(field: 'bg_color' | 'font_color', value: string | null) {
  const m = selectedModule.value
  if (!m) return
  m[field] = value || null
  markDirty()
}

function onShowArrowChange(v: boolean) {
  const m = selectedModule.value
  if (!m) return
  m.show_arrow = v ? null : false
  markDirty()
}

function onIconChange(icon: string) {
  const m = selectedModule.value
  if (!m) return
  m.icon = icon
  markDirty()
}

// 缩放手柄拖拽
function startResize(e: PointerEvent, module: any, dir: string) {
  if (!freeLayoutRef.value) return
  e.preventDefault()
  e.stopPropagation()

  const container = freeLayoutRef.value
  const containerRect = container.getBoundingClientRect()
  const btn = e.currentTarget as HTMLElement
  const btnRect = btn.getBoundingClientRect()

  const startX = e.clientX
  const startY = e.clientY
  const startWidthPct = module.width != null
    ? module.width
    : Math.round(((btnRect.width / containerRect.width) * 100) * 10) / 10
  const startHeightPct = module.height != null
    ? module.height
    : Math.round(((btnRect.height / containerRect.height) * 100) * 10) / 10
  const startLeftPct = module.position_x ?? 5
  const startTopPct = module.position_y ?? 10

  resizingId.value = module.id
  btn.style.zIndex = '998'
  btn.setPointerCapture(e.pointerId)

  function onMove(ev: PointerEvent) {
    const dxPct = ((ev.clientX - startX) / containerRect.width) * 100
    const dyPct = ((ev.clientY - startY) / containerRect.height) * 100
    let newWidth = startWidthPct
    let newHeight = startHeightPct
    let newLeft = startLeftPct
    let newTop = startTopPct

    if (dir.includes('e')) newWidth = startWidthPct + dxPct
    if (dir.includes('w')) {
      newWidth = startWidthPct - dxPct
      newLeft = startLeftPct + dxPct
    }
    if (dir.includes('s')) newHeight = startHeightPct + dyPct
    if (dir.includes('n')) {
      newHeight = startHeightPct - dyPct
      newTop = startTopPct + dyPct
    }

    newWidth = Math.max(8, Math.min(100, newWidth))
    newHeight = Math.max(5, Math.min(60, newHeight))
    module.width = Math.round(newWidth * 10) / 10
    module.height = Math.round(newHeight * 10) / 10
    module.position_x = Math.max(0, Math.min(100 - module.width, Math.round(newLeft * 10) / 10))
    if (dir.includes('n') || dir.includes('s')) {
      module.position_y = Math.max(0, Math.min(100 - module.height, Math.round(newTop * 10) / 10))
    }
  }

  function onUp(ev: PointerEvent) {
    resizingId.value = null
    btn.style.zIndex = ''
    btn.releasePointerCapture(ev.pointerId)
    document.removeEventListener('pointermove', onMove)
    document.removeEventListener('pointerup', onUp)
    markDirty()
  }

  document.addEventListener('pointermove', onMove)
  document.addEventListener('pointerup', onUp)
}

function startDrag(e: PointerEvent, module: any) {
  if (!freeLayoutRef.value) return
  e.preventDefault()

  const container = freeLayoutRef.value
  const containerRect = container.getBoundingClientRect()
  const btn = e.currentTarget as HTMLElement
  const btnRect = btn.getBoundingClientRect()

  const offsetX = e.clientX - btnRect.left
  const offsetY = e.clientY - btnRect.top

  draggingId.value = module.id
  btn.style.zIndex = '999'
  btn.setPointerCapture(e.pointerId)

  function onMove(ev: PointerEvent) {
    const x = ev.clientX - containerRect.left - offsetX
    const y = ev.clientY - containerRect.top - offsetY

    const btnWidthPct = (btnRect.width / containerRect.width) * 100
    const btnHeightPct = (btnRect.height / containerRect.height) * 100

    let xPct = Math.max(0, Math.min(100 - btnWidthPct, (x / containerRect.width) * 100))
    let yPct = Math.max(0, Math.min(100 - btnHeightPct, (y / containerRect.height) * 100))

    // 辅助线对齐吸附
    const g = computeGuides({ left: xPct, top: yPct, width: btnWidthPct, height: btnHeightPct }, module.id, false)
    xPct = g.snappedX
    yPct = g.snappedY
    guides.value = { vLines: g.vLines, hLines: g.hLines }

    module.position_x = Math.round(xPct * 10) / 10
    module.position_y = Math.round(yPct * 10) / 10
  }

  function onUp(ev: PointerEvent) {
    draggingId.value = null
    btn.style.zIndex = ''
    btn.releasePointerCapture(ev.pointerId)
    document.removeEventListener('pointermove', onMove)
    document.removeEventListener('pointerup', onUp)
    guides.value = { vLines: [], hLines: [] }
    markDirty()
  }

  document.addEventListener('pointermove', onMove)
  document.addEventListener('pointerup', onUp)
}

// 页面标题装饰拖拽
function startTitleDrag(e: PointerEvent) {
  if (!deviceFrameRef.value) return
  e.preventDefault()

  const container = deviceFrameRef.value
  const containerRect = container.getBoundingClientRect()
  const el = e.currentTarget as HTMLElement
  const elRect = el.getBoundingClientRect()

  const offsetX = e.clientX - elRect.left
  const offsetY = e.clientY - elRect.top

  el.setPointerCapture(e.pointerId)

  function onMove(ev: PointerEvent) {
    const x = ev.clientX - containerRect.left - offsetX
    const y = ev.clientY - containerRect.top - offsetY

    const wPct = (elRect.width / containerRect.width) * 100
    const hPct = (elRect.height / containerRect.height) * 100

    let xPct = Math.max(0, Math.min(100 - wPct, (x / containerRect.width) * 100))
    let yPct = Math.max(0, Math.min(100 - hPct, (y / containerRect.height) * 100))

    // 辅助线对齐吸附
    const g = computeGuides({ left: xPct, top: yPct, width: wPct, height: hPct }, undefined, true)
    xPct = g.snappedX
    yPct = g.snappedY
    guides.value = { vLines: g.vLines, hLines: g.hLines }

    form.title_config.position_x = Math.round(xPct * 10) / 10
    form.title_config.position_y = Math.round(yPct * 10) / 10
  }

  function onUp(ev: PointerEvent) {
    el.releasePointerCapture(ev.pointerId)
    document.removeEventListener('pointermove', onMove)
    document.removeEventListener('pointerup', onUp)
    guides.value = { vLines: [], hLines: [] }
    markDirty()
  }

  document.addEventListener('pointermove', onMove)
  document.addEventListener('pointerup', onUp)
}

// --- 左侧图层拖拽排序 ---
const layerDragIndex = ref<number | null>(null)

function onLayerDragStart(_e: DragEvent, index: number) {
  layerDragIndex.value = index
}
function onLayerDragOver(index: number) {
  if (layerDragIndex.value === null || layerDragIndex.value === index) return
  const item = modules.value.splice(layerDragIndex.value, 1)[0]
  modules.value.splice(index, 0, item)
  modules.value.forEach((m, i) => (m.sort_order = i))
  layerDragIndex.value = index
  markDirty()
}
function onLayerDrop(_index: number) {
  layerDragIndex.value = null
  markDirty()
}

// --- 布局切换 ---
function onLayoutChange() {
  if (form.layout === 'free') {
    modules.value.forEach((m, i) => {
      if (m.position_x == null || m.position_y == null) {
        m.position_x = 10
        m.position_y = 15 + i * 12
      }
      if (m.width == null) m.width = 80
    })
  }
  markDirty()
}

// --- AI 生图弹窗 ---
const aiDialog = reactive({ visible: false, use: 'kv' as string })
function openAiDialog(use: string) {
  aiDialog.use = use
  aiDialog.visible = true
}
function onAiImageSelect(url: string) {
  if (aiDialog.use === 'kv') form.kv_image = url
  else if (aiDialog.use === 'background') form.background_image = url
  else if (aiDialog.use === 'share') form.share_image = url
  markDirty()
  ElMessage.success('AI 图片已应用，记得点击「保存」按钮生效')
}

// --- 上传回调 ---
function onUploadSuccess(field: 'kv_image' | 'background_image' | 'share_image' | 'preview_image') {
  return (res: any) => {
    if (res?.url) {
      ;(form as any)[field] = res.url
      markDirty()
    } else {
      ElMessage.error(res?.detail || '上传失败')
    }
  }
}

// --- 保存 ---
async function handleSave() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入模板名称')
    return
  }
  saving.value = true
  try {
    const payload: Record<string, any> = {
      name: form.name.trim(),
      description: form.description || null,
      template_key: form.template_key,
      layout: form.layout,
      kv_image: form.kv_image || null,
      title_config: { ...form.title_config },
      background_color: form.background_color || null,
      background_image: form.background_image || null,
      share_image: form.share_image || null,
      share_title: form.share_title || null,
      share_subtitle: form.share_subtitle || null,
      preview_image: form.preview_image || null,
      sort_order: form.sort_order,
      modules_config: modules.value
        .filter((m) => (m.title || '').trim())
        .map((m, idx) => {
          const item: Record<string, any> = {
            title: m.title.trim(),
            content_type: m.content_type,
            is_active: m.is_active !== false,
            sort_order: idx,
          }
          if (m.external_url) item.external_url = m.external_url
          if (m.icon) item.icon = m.icon
          if (form.layout === 'free') {
            if (m.position_x != null) item.position_x = m.position_x
            if (m.position_y != null) item.position_y = m.position_y
            if (m.width != null) item.width = m.width
            if (m.height != null) item.height = m.height
            if (m.border_radius != null) item.border_radius = m.border_radius
            if (m.bg_color) item.bg_color = m.bg_color
            if (m.font_color) item.font_color = m.font_color
            if (m.icon_position) item.icon_position = m.icon_position
            if (m.content_align) item.content_align = m.content_align
            if (m.show_arrow === false) item.show_arrow = false
          }
          return item
        }),
    }
    if (isEdit.value) {
      await api.put(`/templates/${route.params.id}`, payload)
      ElMessage.success('模板已保存')
      isDirty.value = false
    } else {
      const res: any = await api.post('/templates', payload)
      ElMessage.success('模板已创建')
      isDirty.value = false
      router.replace(`/templates/edit/${res.id}`)
    }
  } finally {
    saving.value = false
  }
}

// --- 加载 ---
onMounted(async () => {
  if (!isEdit.value) return
  try {
    const res: any = await api.get(`/templates/${route.params.id}`)
    Object.assign(form, {
      name: res.name || '',
      description: res.description || '',
      sort_order: res.sort_order ?? 0,
      template_key: res.template_key || 'default',
      layout: res.layout || 'grid',
      kv_image: res.kv_image || '',
      title_config: { ...DEFAULT_TITLE_CONFIG, ...(res.title_config || {}) },
      background_color: res.background_color || '',
      background_image: res.background_image || '',
      share_image: res.share_image || '',
      share_title: res.share_title || '',
      share_subtitle: res.share_subtitle || '',
      preview_image: res.preview_image || '',
    })
    localIdSeed = 1
    modules.value = (res.modules_config || []).map((m: any) => ({
      id: localIdSeed++,
      title: m.title || '',
      content_type: m.content_type || 'rich_text',
      external_url: m.external_url || '',
      icon: m.icon || '',
      is_active: m.is_active !== false,
      position_x: m.position_x ?? null,
      position_y: m.position_y ?? null,
      width: m.width ?? null,
      height: m.height ?? null,
      border_radius: m.border_radius ?? null,
      bg_color: m.bg_color || null,
      font_color: m.font_color || null,
      icon_position: m.icon_position || 'left',
      content_align: m.content_align || 'left',
      show_arrow: m.show_arrow,
      sort_order: m.sort_order ?? 0,
    }))
    isDirty.value = false
  } catch {
    ElMessage.error('模板加载失败')
    router.replace('/templates')
  }
})
</script>

<style scoped>
.visual-editor {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 50px - 32px);
  background: var(--app-content-bg-color);
  margin: -16px;
}

/* 顶部工具栏 */
.editor-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
  gap: 16px;
}
.topbar-left, .topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}
.topbar-right { justify-content: flex-end; }
.topbar-center {
  display: flex;
  align-items: center;
  justify-content: center;
}
.topbar-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}
.dirty-tag { font-weight: 500; }
.layout-icon {
  margin-right: 4px;
  vertical-align: middle;
}

/* 主体：三栏 */
.editor-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* 左侧面板 */
.editor-left {
  width: 460px;
  flex-shrink: 0;
  background: #fff;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
}
.left-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.left-tab-nav {
  display: flex;
  flex-shrink: 0;
  padding: 0 16px;
  border-bottom: 1px solid #e8e8e8;
  background: #fafafa;
}
.left-tab-button {
  padding: 13px 12px 11px;
  color: #606266;
  font-size: 14px;
  line-height: 20px;
  cursor: pointer;
  border: 0;
  border-bottom: 2px solid transparent;
  background: transparent;
}
.left-tab-button:hover { color: #409eff; }
.left-tab-button.active {
  color: #409eff;
  font-weight: 500;
  border-bottom-color: #409eff;
}
.left-tab-panel {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
.left-scroll {
  height: 100%;
  overflow-y: auto;
  padding: 12px 16px 16px;
}

/* 折叠面板 */
.setting-collapse { border: none; }
.setting-collapse :deep(.el-collapse-item) {
  margin-bottom: 10px;
  border: 1px solid #ebeef5;
  border-radius: 10px;
  overflow: hidden;
  transition: box-shadow 0.2s;
}
.setting-collapse :deep(.el-collapse-item:hover) {
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.setting-collapse :deep(.el-collapse-item__header) {
  padding: 0 16px;
  height: 46px;
  line-height: 46px;
  background: #fafbfc;
  border-bottom: none;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}
.setting-collapse :deep(.el-collapse-item__header.is-active) {
  background: #f0f7ff;
  border-bottom: 1px solid #ebeef5;
}
.setting-collapse :deep(.el-collapse-item__wrap) { border-bottom: none; }
.setting-collapse :deep(.el-collapse-item__content) { padding: 16px; }
.collapse-title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.collapse-title .el-icon {
  color: #409eff;
  font-size: 16px;
}

/* 子分区 */
.sub-section { margin-bottom: 4px; }
.sub-section-label {
  font-size: 13px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 10px;
  padding-left: 2px;
}
.sub-divider { margin: 16px 0; }

.hint {
  color: #999;
  font-size: 12px;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

/* 上传组件 */
.upload-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
}
.upload-preview {
  position: relative;
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
}
.upload-preview.small { max-width: 220px; }
.share-image-preview {
  position: relative;
  width: 96px;
  height: 96px;
  overflow: hidden;
  cursor: pointer;
  border-radius: 12px;
}
.share-image-placeholder { width: 96px; height: 96px; }
.preview-img {
  width: 100%;
  display: block;
}
.preview-mask {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  opacity: 0;
  transition: opacity 0.2s;
}
.upload-preview:hover .preview-mask { opacity: 1; }
.share-image-preview:hover .preview-mask { opacity: 1; }
.upload-placeholder {
  width: 100%;
  height: 110px;
  border: 1px dashed #d0d7de;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: #8c8c8c;
  cursor: pointer;
  font-size: 13px;
  background: #fafafa;
  transition: all 0.2s;
}
.upload-placeholder.small { height: 80px; }
.upload-placeholder:hover {
  border-color: #409eff;
  color: #409eff;
  background: #f0f9ff;
}
.upload-tip {
  font-size: 11px;
  color: #aaa;
}

.color-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 模块列表 */
.module-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.module-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}
.module-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64,158,255,0.1);
}
.module-item.active {
  border-color: #409eff;
  background: #f0f9ff;
}
.layer-drag-handle {
  color: #c0c4cc;
  cursor: grab;
  font-size: 16px;
}
.module-item:active .layer-drag-handle { cursor: grabbing; }
.module-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
  font-weight: bold;
  flex-shrink: 0;
  overflow: hidden;
}
.module-icon img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.title-item .module-icon.title-icon {
  background: linear-gradient(135deg, #f59e0b, #ef4444);
}
.module-info {
  flex: 1;
  min-width: 0;
}
.module-title {
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #1f2937;
}
.module-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 3px;
}
.disabled-tag {
  font-size: 11px;
  color: #f56c6c;
}
.module-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}
.add-module-btn {
  width: 100%;
  margin-top: 12px;
}

/* 中间预览 */
.editor-center {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  padding: 24px;
}
.preview-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}

/* 手机外框 */
.device-frame {
  width: 300px;
  height: 585px;
  border: 9px solid #1a1a1a;
  border-radius: 34px;
  overflow: hidden;
  position: relative;
  --status-area: 22px;
  background:
    linear-gradient(to bottom, #1a1a1a 0, #1a1a1a var(--status-area), transparent var(--status-area)),
    linear-gradient(135deg, #c5cef5 0%, #c8bde0 100%);
  box-shadow:
    0 0 0 2px #2a2a2a,
    0 24px 60px rgba(0,0,0,0.35),
    0 8px 20px rgba(0,0,0,0.18);
}
.device-frame.tpl-default {
  background:
    linear-gradient(to bottom, #1a1a1a 0, #1a1a1a var(--status-area), transparent var(--status-area)),
    #ffffff;
}
.device-frame.tpl-classic {
  background:
    linear-gradient(to bottom, #1a1a1a 0, #1a1a1a var(--status-area), transparent var(--status-area)),
    linear-gradient(135deg, #c5cef5 0%, #c8bde0 100%);
}
.device-frame.tpl-dark {
  background:
    linear-gradient(to bottom, #1a1a1a 0, #1a1a1a var(--status-area), transparent var(--status-area)),
    linear-gradient(135deg, #4a4a68 0%, #3e3e5a 100%);
}
.device-frame.tpl-festive {
  background:
    linear-gradient(to bottom, #1a1a1a 0, #1a1a1a var(--status-area), transparent var(--status-area)),
    linear-gradient(135deg, #e8c5c5 0%, #e0b8b8 100%);
}

.device-notch {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 92px;
  height: 22px;
  background: #1a1a1a;
  border-bottom-left-radius: 11px;
  border-bottom-right-radius: 11px;
  z-index: 20;
}
.device-screen {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
  z-index: 1;
  box-sizing: border-box;
  padding-top: var(--status-area);
}

.bg-layer { position: absolute; top: var(--status-area); left: 0; right: 0; bottom: 0; z-index: 0; overflow: hidden; line-height: 0; }
.bg-image { width: 100%; height: 100%; object-fit: cover; display: block; }

.status-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  color: rgba(255,255,255,0.95);
  font-size: 12px;
  font-weight: 600;
  z-index: 20;
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
  pointer-events: none;
}
.status-icons {
  display: flex;
  align-items: center;
  gap: 5px;
}
.signal {
  width: 14px; height: 10px;
  background-image:
    linear-gradient(to top, rgba(255,255,255,0.9) 3px, transparent 3px),
    linear-gradient(to top, rgba(255,255,255,0.9) 6px, transparent 6px),
    linear-gradient(to top, rgba(255,255,255,0.9) 9px, transparent 9px);
  background-size: 3.5px 100%;
  background-position: 0 100%, 5px 100%, 10px 100%;
  background-repeat: no-repeat;
}
.wifi {
  width: 12px; height: 10px;
  border: 2px solid rgba(255,255,255,0.9);
  border-radius: 50% 50% 0 0;
  border-bottom: none;
}
.battery {
  width: 18px; height: 8px;
  border: 1px solid rgba(255,255,255,0.9);
  border-radius: 2px;
  position: relative;
  background: rgba(255,255,255,0.8);
}
.battery::after {
  content: '';
  position: absolute;
  right: -3px; top: 2px;
  width: 2px; height: 4px;
  background: rgba(255,255,255,0.9);
  border-radius: 0 1px 1px 0;
}

/* KV 区域 */
.kv-area {
  width: 100%;
  position: relative;
  z-index: 1;
}
.kv-image {
  width: 100%;
  display: block;
}
/* 页面标题装饰 */
.site-title-deco {
  line-height: 1.4;
  word-break: break-all;
  cursor: move;
  user-select: none;
  z-index: 999;
}
.site-title-deco.selected {
  outline: 2px dashed #409eff;
  outline-offset: 3px;
}

/* 拖拽辅助线 */
.guide-line {
  position: absolute;
  z-index: 1000;
  pointer-events: none;
  background: #ff4d4f;
}
.guide-v {
  width: 1px;
  height: 100%;
  top: 0;
}
.guide-h {
  height: 1px;
  width: 100%;
  left: 0;
}

/* 内容区域 */
.content-area {
  padding: 16px;
  position: relative;
  z-index: 1;
}

/* 自由布局容器 */
.free-layout {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2;
}

/* 预览按钮通用样式 */
.preview-btn {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 10px;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
  user-select: none;
}
.preview-btn:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
.preview-btn.selected {
  outline: 3px solid #409eff;
  outline-offset: 2px;
  box-shadow: 0 0 0 4px rgba(64, 158, 255, 0.2);
}
.preview-btn.disabled {
  opacity: 0.55;
  filter: grayscale(0.6);
}

/* 自由布局按钮 */
.free-btn {
  position: absolute;
  display: flex;
  align-items: center;
  padding: 8px 14px;
  gap: 6px;
  white-space: nowrap;
  touch-action: none;
  box-sizing: border-box;
}
/* 自由布局纯图标模式：只显示图标，隐藏文字/箭头，缩放即缩放图标 */
.free-btn.icon-only {
  padding: 0;
  width: 44px;
  height: 44px;
  background: transparent;
  justify-content: center;
  align-items: center;
}
.free-btn.icon-only .free-btn-inner {
  display: block;
  width: 100%;
  height: 100%;
}
.free-btn.icon-only .btn-icon,
.free-btn.icon-only .btn-icon-placeholder {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: inherit;
  font-size: 20px;
}
.free-btn-inner {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  min-width: 0;
}
.free-btn-inner .btn-icon,
.free-btn-inner .btn-icon-placeholder { order: 0; flex-shrink: 0; }
.free-btn-inner .btn-text { order: 1; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; }
.free-btn-inner .btn-arrow { order: 2; flex-shrink: 0; }

.free-btn-inner.icon-left { flex-direction: row; justify-content: flex-start; }
.free-btn-inner.icon-right { flex-direction: row; }
.free-btn-inner.icon-right .btn-icon,
.free-btn-inner.icon-right .btn-icon-placeholder { order: 2; }
.free-btn-inner.icon-right .btn-text { order: 0; }
.free-btn-inner.icon-right .btn-arrow { order: 1; }

.free-btn-inner.icon-top,
.free-btn-inner.icon-bottom {
  flex-direction: column;
  justify-content: center;
}
.free-btn-inner.icon-top .btn-icon,
.free-btn-inner.icon-top .btn-icon-placeholder { order: 0; }
.free-btn-inner.icon-top .btn-text { order: 1; flex: 0 0 auto; }
.free-btn-inner.icon-bottom .btn-icon,
.free-btn-inner.icon-bottom .btn-icon-placeholder { order: 1; }
.free-btn-inner.icon-bottom .btn-text { order: 0; flex: 0 0 auto; }
.free-btn-inner.icon-top .btn-arrow,
.free-btn-inner.icon-bottom .btn-arrow {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
}

.free-btn-inner.align-left { justify-content: flex-start; }
.free-btn-inner.align-center { justify-content: center; }
.free-btn-inner.align-right { justify-content: flex-end; }
.free-btn-inner.icon-top.align-left,
.free-btn-inner.icon-bottom.align-left { align-items: flex-start; }
.free-btn-inner.icon-top.align-center,
.free-btn-inner.icon-bottom.align-center { align-items: center; }
.free-btn-inner.icon-top.align-right,
.free-btn-inner.icon-bottom.align-right { align-items: flex-end; }

.free-btn.has-height .free-btn-inner { height: 100%; }
.free-btn.dragging {
  cursor: grabbing;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
  opacity: 0.95;
}
.free-btn.resizing {
  cursor: ew-resize;
  user-select: none;
}

/* 选中态缩放手柄 */
.resize-handle {
  position: absolute;
  width: 10px;
  height: 10px;
  background: #fff;
  border: 1.5px solid #409eff;
  border-radius: 2px;
  z-index: 20;
  box-sizing: border-box;
}
.rh-nw { top: -6px; left: -6px; cursor: nwse-resize; }
.rh-n  { top: -6px; left: 50%; margin-left: -5px; cursor: ns-resize; }
.rh-ne { top: -6px; right: -6px; cursor: nesw-resize; }
.rh-e  { top: 50%; right: -6px; margin-top: -5px; cursor: ew-resize; }
.rh-se { bottom: -6px; right: -6px; cursor: nwse-resize; }
.rh-s  { bottom: -6px; left: 50%; margin-left: -5px; cursor: ns-resize; }
.rh-sw { bottom: -6px; left: -6px; cursor: nesw-resize; }
.rh-w  { top: 50%; left: -6px; margin-top: -5px; cursor: ew-resize; }
.resize-handle:hover {
  background: #409eff;
  transform: scale(1.2);
}

/* 按钮列表 */
.button-layout {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.button-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  gap: 10px;
}

/* 九宫格 */
.grid-layout {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.grid-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px 8px;
}
.grid-icon {
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: 8px;
}
.grid-icon-placeholder {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-size: 20px;
  font-weight: bold;
}
.grid-title {
  margin-top: 8px;
  font-size: 12px;
  text-align: center;
  color: #333;
}
.tpl-dark .grid-title { color: #fff; }

/* 按钮内元素 */
.btn-icon {
  width: 36px;
  height: 36px;
  object-fit: cover;
  border-radius: 8px;
  flex-shrink: 0;
}
.btn-icon-placeholder {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-size: 16px;
  font-weight: bold;
  flex-shrink: 0;
}
.btn-text {
  font-size: 14px;
  color: #333;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tpl-dark .btn-text { color: #fff; }
.tpl-dark .preview-btn { background: rgba(255, 255, 255, 0.1); }
.tpl-festive .preview-btn { border: 1px solid #ffd700; }
.btn-arrow {
  color: #ccc;
  font-size: 18px;
  flex-shrink: 0;
}

/* 空状态 */
.empty-tip {
  position: absolute;
  top: 55%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: rgba(255, 255, 255, 0.75);
  font-size: 13px;
  text-align: center;
  z-index: 3;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

/* 预览提示 */
.preview-tips {
  font-size: 12px;
  color: #888;
  text-align: center;
}

/* 右侧属性面板 */
.editor-inspector {
  width: 300px;
  flex-shrink: 0;
  background: #fff;
  border-left: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
}
.inspector-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid #e8e8e8;
  flex-shrink: 0;
}
.inspector-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}
.inspector-body {
  padding: 16px;
  overflow-y: auto;
}
.field-block { margin-bottom: 18px; }
.field-label {
  display: block;
  font-size: 12px;
  color: #646a73;
  margin-bottom: 8px;
}

.inspector-divider {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
  margin: 4px 0 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 6px;
}
.size-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.size-slider {
  flex: 1;
  min-width: 0;
}
.size-number {
  width: 110px;
  flex-shrink: 0;
}
.field-unit {
  font-weight: 400;
  color: #999;
  font-size: 11px;
  margin-left: 4px;
}
.field-hint {
  font-size: 12px;
  color: #999;
  line-height: 1.5;
  margin-top: 6px;
}
.radius-presets {
  display: flex;
  align-items: center;
  gap: 8px;
}
.radius-preset {
  width: 34px;
  height: 26px;
  border: 1.5px solid #d0d7de;
  background: #fafafa;
  cursor: pointer;
  padding: 0;
  transition: all 0.15s;
}
.radius-preset:hover { border-color: #409eff; }
.radius-preset.active {
  border-color: #409eff;
  border-width: 2px;
  background: #f0f9ff;
}
.preset-value {
  margin-left: 4px;
  font-size: 12px;
  color: #606266;
}
.radius-slider-row { margin-top: 10px; }
.seg-row {
  display: flex;
  gap: 6px;
}
.seg-btn {
  flex: 1;
  height: 30px;
  border: 1.5px solid #d0d7de;
  background: #fafafa;
  color: #606266;
  font-size: 13px;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.seg-btn:hover { border-color: #409eff; color: #409eff; }
.seg-btn.active {
  border-color: #409eff;
  background: #f0f9ff;
  color: #409eff;
  font-weight: 500;
}
.seg-btn.seg-text { font-size: 12px; }
.reset-btn { margin-left: auto; }
.inspector-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 24px;
  text-align: center;
  color: #909399;
}
.inspector-empty .el-icon { color: #c0c4cc; }
.ie-title {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
}
.ie-desc {
  font-size: 12px;
  line-height: 1.6;
  color: #909399;
}
</style>
