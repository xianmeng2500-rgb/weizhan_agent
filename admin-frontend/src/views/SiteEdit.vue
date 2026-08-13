<template>
  <div class="visual-editor">
    <!-- 顶部工具栏 -->
    <div class="editor-topbar">
      <div class="topbar-left">
        <span class="topbar-title">{{ isEdit ? '可视化编辑' : '创建微站' }}</span>
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
        <el-button v-if="isEdit" size="small" :href="previewUrl" target="_blank" tag="a">预览</el-button>
        <el-button size="small" @click="$router.back()">返回</el-button>
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
              @click="switchLeftTab('site')"
            >站点设置</button>
            <button
              class="left-tab-button"
              :class="{ active: leftTab === 'modules' }"
              type="button"
              role="tab"
              :aria-selected="leftTab === 'modules'"
              @click="switchLeftTab('modules')"
            >按钮管理 ({{ modules.length }})</button>
          </div>

          <div v-show="leftTab === 'site'" class="left-tab-panel">
            <div class="left-scroll">
              <!-- 基本信息 -->
              <div class="config-card">
                <div class="card-title"><el-icon><Document /></el-icon>基本信息</div>
                <el-form label-width="76px" size="small">
                  <el-form-item label="微站名称" required>
                    <el-input v-model="form.name" placeholder="请输入名称" @input="markDirty" />
                  </el-form-item>
                  <el-form-item label="访问码" required>
                    <el-input v-model="form.code" placeholder="英文+数字" :disabled="isCodeLocked" @input="markDirty">
                      <template #append>
                        <div class="code-actions">
                          <el-button text :disabled="isCodeLocked" @click="generateCode">随机</el-button>
                          <el-button text :disabled="!form.code" @click="showQrDialog = true">二维码</el-button>
                        </div>
                      </template>
                    </el-input>
                    <div class="hint">访问链接: {{ accessUrl }}</div>
                    <div v-if="isCodeLocked" class="hint code-lock-hint">微站已上线，访问码已锁定，避免已分享的链接失效。</div>
                  </el-form-item>
                </el-form>
              </div>

              <!-- KV 图 -->
              <div class="config-card">
                <div class="card-title"><el-icon><Picture /></el-icon>KV 图</div>
                <el-upload
                  action="/api/v1/upload/image"
                  :headers="uploadHeaders"
                  :show-file-list="false"
                  :on-success="onKvSuccess"
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
                <el-button v-if="form.kv_image" text size="small" @click="form.kv_image = ''; markDirty()" style="margin-top: 8px">移除 KV 图</el-button>
              </div>

              <!-- 背景设置 -->
              <div class="config-card">
                <div class="card-title"><el-icon><Brush /></el-icon>背景设置</div>
                <el-form label-width="70px" size="small">
                  <el-form-item label="背景图">
                    <el-upload
                      action="/api/v1/upload/image"
                      :headers="uploadHeaders"
                      :show-file-list="false"
                      :on-success="onBgSuccess"
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
                    <el-button v-if="form.background_image" text size="small" @click="form.background_image = ''; markDirty()" style="margin-top: 8px">移除背景图</el-button>
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

              <!-- 模板 -->
              <div class="config-card">
                <div class="card-title"><el-icon><MagicStick /></el-icon>模板风格</div>
                <el-form label-width="0" size="small">
                  <el-form-item>
                    <el-radio-group v-model="form.template" @change="markDirty">
                      <el-radio-button value="classic">经典蓝紫</el-radio-button>
                      <el-radio-button value="dark">暗夜科技</el-radio-button>
                      <el-radio-button value="festive">节日红金</el-radio-button>
                    </el-radio-group>
                  </el-form-item>
                </el-form>
              </div>

              <!-- 微信分享 -->
              <div class="config-card">
                <div class="card-title"><el-icon><Share /></el-icon>微信分享</div>
                <el-form label-width="76px" size="small">
                  <el-form-item label="分享图标">
                    <el-upload
                      action="/api/v1/upload/image"
                      :headers="uploadHeaders"
                      :show-file-list="false"
                      :on-success="onShareImageSuccess"
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
                    <el-button v-if="form.share_image" text size="small" @click="form.share_image = ''; markDirty()" style="margin-top: 8px">移除图标</el-button>
                  </el-form-item>
                  <el-form-item label="分享标题">
                    <el-input v-model="form.share_title" maxlength="128" show-word-limit placeholder="默认使用微站名称" @input="markDirty" />
                  </el-form-item>
                  <el-form-item label="分享副标题">
                    <el-input v-model="form.share_subtitle" type="textarea" :rows="2" maxlength="255" show-word-limit placeholder="可选，展示在微信分享描述中" @input="markDirty" />
                  </el-form-item>
                </el-form>
                <div class="hint">需先在“管理员配置”中启用微信分享并填写全局接入参数。</div>
              </div>

              <!-- 客服设置 -->
              <div class="config-card">
                <div class="card-title"><el-icon><Service /></el-icon>客服设置</div>
                <el-form label-width="82px" size="small">
                  <el-form-item label="开启客服">
                    <el-switch v-model="form.customer_service_config.enabled" @change="markDirty" />
                    <span class="hint inline-hint">在移动端右下角显示客服入口</span>
                  </el-form-item>
                  <template v-if="form.customer_service_config.enabled">
                    <el-form-item label="说明文案">
                      <el-input v-model="form.customer_service_config.description" type="textarea" :rows="2" maxlength="255" show-word-limit placeholder="例如：报名、交通及活动问题，请联系工作人员" @input="markDirty" />
                    </el-form-item>
                    <el-form-item label="客服电话">
                      <el-input v-model="form.customer_service_config.phone" placeholder="例如：400-123-4567" @input="markDirty" />
                    </el-form-item>
                    <el-form-item label="客服微信">
                      <el-input v-model="form.customer_service_config.wechat" placeholder="点击后可一键复制" @input="markDirty" />
                    </el-form-item>
                    <el-form-item label="客服链接">
                      <el-input v-model="form.customer_service_config.link" placeholder="在线客服或企业微信链接" @input="markDirty" />
                    </el-form-item>
                    <el-form-item label="服务时间">
                      <el-input v-model="form.customer_service_config.service_hours" placeholder="例如：工作日 09:00-18:00" @input="markDirty" />
                    </el-form-item>
                    <el-form-item label="客服二维码">
                      <el-upload
                        action="/api/v1/upload/image"
                        :headers="uploadHeaders"
                        :show-file-list="false"
                        :on-success="onServiceQrSuccess"
                        accept="image/*"
                      >
                        <div v-if="form.customer_service_config.qrcode_url" class="share-image-preview">
                          <img :src="form.customer_service_config.qrcode_url" class="preview-img" />
                          <div class="preview-mask">点击更换</div>
                        </div>
                        <div v-else class="upload-placeholder share-image-placeholder">
                          <el-icon size="22"><Plus /></el-icon>
                          <span>上传二维码</span>
                        </div>
                      </el-upload>
                      <el-button v-if="form.customer_service_config.qrcode_url" text size="small" @click="form.customer_service_config.qrcode_url = ''; markDirty()" style="margin-top: 8px">移除二维码</el-button>
                    </el-form-item>
                  </template>
                </el-form>
                <div v-if="form.customer_service_config.enabled" class="hint">至少配置电话、微信、客服链接或二维码中的一种联系方式。</div>
              </div>

              <!-- 高级设置 -->
              <div class="config-card">
                <div class="card-title"><el-icon><Setting /></el-icon>高级设置</div>
                <el-form label-width="80px" size="small">
                  <el-form-item label="需要登录">
                    <el-switch v-model="form.need_login" @change="markDirty" />
                  </el-form-item>

                  <!-- 登录字段配置 -->
                  <template v-if="form.need_login">
                    <el-form-item label="需要密码">
                      <el-switch v-model="form.login_require_password" @change="markDirty" />
                      <span class="inline-hint" style="color: #999; font-size: 12px">关闭后用户输入账号即可登录</span>
                    </el-form-item>
                    <el-form-item label="签到系统">
                      <el-switch v-model="form.need_checkin" @change="markDirty" />
                      <span class="inline-hint" style="color: #999; font-size: 12px">开启后可在模块中添加「我的二维码」</span>
                    </el-form-item>
                    <el-form-item label="登录方式">
                      <div class="login-fields-config">
                        <div
                          v-for="(field, idx) in form.login_fields_config"
                          :key="idx"
                          class="login-field-item"
                        >
                          <div class="login-field-row">
                            <el-select
                              v-model="field.key"
                              placeholder="选择字段"
                              style="width: 120px"
                              @change="onLoginFieldKeyChange(field)"
                            >
                              <el-option label="账号" value="username" />
                              <el-option label="手机号" value="phone" />
                              <el-option label="自定义字段" value="custom" />
                            </el-select>
                            <el-input
                              v-model="field.display_name"
                              placeholder="显示名称"
                              style="width: 100px; margin-left: 6px"
                              @input="markDirty"
                            />
                            <el-button
                              type="danger"
                              text
                              size="small"
                              @click="removeLoginField(idx)"
                              style="margin-left: 4px"
                            >删除</el-button>
                          </div>
                          <div v-if="field.key === 'custom'" class="login-field-row" style="margin-top: 6px">
                            <el-input
                              v-model="field.custom_key"
                              placeholder="自定义字段标识(英文)"
                              style="width: 140px"
                              @input="onCustomKeyChange(field)"
                            />
                            <el-select
                              v-model="field.type"
                              placeholder="输入类型"
                              style="width: 100px; margin-left: 6px"
                              @change="markDirty"
                            >
                              <el-option label="文本" value="text" />
                              <el-option label="数字" value="number" />
                              <el-option label="邮箱" value="email" />
                            </el-select>
                          </div>
                        </div>
                        <el-button
                          type="primary"
                          text
                          size="small"
                          @click="addLoginField"
                          style="margin-top: 6px"
                        >+ 添加登录字段</el-button>
                        <div class="hint" style="margin-top: 6px">选择一种或多种登录方式，用户可用任一已配置字段登录。自定义字段需确保唯一性。</div>
                      </div>
                    </el-form-item>
                    <el-form-item label="表单位置">
                      <el-radio-group v-model="form.login_form_config.position" @change="markDirty">
                        <el-radio-button value="top">居上</el-radio-button>
                        <el-radio-button value="center">居中</el-radio-button>
                        <el-radio-button value="bottom">居下</el-radio-button>
                      </el-radio-group>
                    </el-form-item>
                  </template>

                  <el-form-item label="开启时间">
                    <el-date-picker v-model="form.start_time" type="datetime" placeholder="不选则始终" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DDTHH:mm:ss" @change="markDirty" style="width: 100%" />
                  </el-form-item>
                  <el-form-item label="关闭时间">
                    <el-date-picker v-model="form.end_time" type="datetime" placeholder="不选则始终" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DDTHH:mm:ss" @change="markDirty" style="width: 100%" />
                  </el-form-item>
                  <el-form-item label="关闭文案">
                    <el-input v-model="form.close_message" type="textarea" :rows="2" placeholder="微站关闭后展示" @input="markDirty" />
                  </el-form-item>
                </el-form>
              </div>
            </div>
          </div>

          <div v-show="leftTab === 'modules'" class="left-tab-panel">
            <div class="left-scroll">
              <div v-if="!isEdit" class="empty-hint">请先保存微站基本信息，再管理按钮</div>
              <div v-else class="module-list">
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
                    <el-switch v-model="m.is_active" size="small" @change="patchModule(m, { is_active: m.is_active })" @click.stop />
                    <el-popconfirm title="确认删除？" @confirm="deleteModule(m)">
                      <template #reference>
                        <el-button text size="small" type="danger" @click.stop>删除</el-button>
                      </template>
                    </el-popconfirm>
                  </div>
                </div>
              </div>
              <!-- 九宫格/按钮列表模式：按钮垂直位置设置 -->
              <div v-if="isEdit && (form.layout === 'grid' || form.layout === 'button')" class="grid-offset-config">
                <div class="grid-offset-title">按钮位置</div>
                <div class="grid-offset-row">
                  <el-slider
                    v-model="form.grid_offset_y"
                    :min="0"
                    :max="60"
                    :step="0.5"
                    :show-tooltip="false"
                    style="flex: 1"
                    @input="markDirty"
                    @change="patchGridOffset"
                  />
                  <span class="grid-offset-value">{{ (form.grid_offset_y || 0).toFixed(1) }}%</span>
                </div>
                <div class="hint">调整按钮在页面上的垂直距离，可拖拽预览区手柄微调</div>
              </div>
              <el-button v-if="isEdit" class="add-module-btn" type="primary" plain @click="addModule">
                <el-icon><Plus /></el-icon>添加按钮
              </el-button>
              <br>
              <el-button v-if="isEdit" class="manage-module-btn" plain @click="goModuleManage">
                前往模块管理维护内容
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间手机预览 -->
      <div class="editor-center">
        <div class="preview-wrapper">
          <div class="device-frame" :class="'tpl-' + form.template" :style="previewBgStyle">
            <div class="device-notch"></div>
            <!-- 状态栏：位于刘海两侧"耳朵区"，与真机一致 -->
            <div class="status-bar">
              <span class="status-time">9:41</span>
              <div class="status-icons">
                <span class="signal"></span>
                <span class="wifi"></span>
                <span class="battery"></span>
              </div>
            </div>
            <!-- 背景图：铺满整个屏幕（含刘海区域），固定不滚动（与 H5 一致） -->
            <div v-if="form.background_image" class="bg-layer">
              <img :src="form.background_image" class="bg-image" alt="" />
            </div>
            <!-- 自由拖拽布局：覆盖全屏，固定不随内容滚动（与 H5 fixed 一致） -->
            <div
              v-if="previewMode === 'main' && form.layout === 'free'"
              class="free-layout"
              ref="freeLayoutRef"
              @pointerdown.self="selectedModuleId = null"
            >
              <div
                v-for="m in modules"
                :key="m.id"
                class="preview-btn free-btn"
                :class="{ dragging: draggingId === m.id, resizing: resizingId === m.id, selected: selectedModuleId === m.id, 'has-height': m.height != null }"
                :style="freeBtnStyle(m)"
                @pointerdown="startDrag($event, m)"
                @click.stop="selectedModuleId = m.id"
                @dblclick="selectedModuleId = m.id"
              >
                <div class="free-btn-inner" :class="freeBtnClass(m)">
                  <img v-if="m.icon" :src="m.icon" class="btn-icon" />
                  <div v-else class="btn-icon-placeholder">{{ (m.title || '?').charAt(0) }}</div>
                  <span class="btn-text">{{ m.title }}</span>
                  <span v-if="m.show_arrow !== false" class="btn-arrow">›</span>
                </div>

                <!-- 选中态缩放手柄 -->
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
            <div class="device-screen">
              <!-- ====== 主页预览 ====== -->
              <template v-if="previewMode === 'main'">
                <!-- KV 区域 -->
                <div class="kv-area" v-if="form.kv_image">
                  <img :src="form.kv_image" class="kv-image" />
                </div>

                <!-- 九宫格布局 -->
                <div v-if="form.layout === 'grid'" class="content-area" :style="{ paddingTop: (form.grid_offset_y || 0) + '%' }">
                  <div
                    class="grid-drag-handle"
                    @pointerdown.prevent="startGridDrag"
                    title="拖拽调整宫格位置"
                  >⋮⋮</div>
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
                <div v-else-if="form.layout === 'button'" class="content-area" :style="{ paddingTop: (form.grid_offset_y || 0) + '%' }">
                  <div
                    class="grid-drag-handle"
                    @pointerdown.prevent="startGridDrag"
                    title="拖拽调整按钮列表位置"
                  >⋮⋮</div>
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
                <div v-if="modules.length === 0 && isEdit" class="empty-tip">
                  <el-icon size="40"><Plus /></el-icon>
                  <div>点击左侧「添加按钮」创建第一个按钮</div>
                </div>
              </template>

              <!-- ====== 登录页预览 ====== -->
              <template v-else>
                <div class="login-preview" :class="'login-pos-' + loginFormPosition">
                  <!-- KV 图 -->
                  <div class="login-preview-kv" v-if="form.kv_image">
                    <img :src="form.kv_image" class="login-preview-kv-img" />
                  </div>

                  <!-- 登录卡片 -->
                  <div class="login-preview-card" :class="{ 'has-kv': !!form.kv_image }">
                    <!-- 品牌区域：无 KV 时显示 Logo + 标题，有 KV 时紧凑标题 -->
                    <div class="login-preview-brand" :class="{ compact: !!form.kv_image }">
                      <div class="login-preview-title">{{ form.name || '欢迎登录' }}</div>
                      <div class="login-preview-sub">请登录后继续访问</div>
                    </div>

                    <div class="login-preview-form">
                      <template v-if="form.login_fields_config && form.login_fields_config.length">
                        <div
                          v-for="(field, idx) in form.login_fields_config"
                          :key="idx"
                          class="login-preview-field"
                        >
                          <el-icon class="field-icon"><Phone v-if="field.key === 'phone'" /><User v-else /></el-icon>
                          <span class="field-placeholder">请输入{{ field.display_name }}</span>
                        </div>
                      </template>
                      <template v-else>
                        <div class="login-preview-field">
                          <el-icon class="field-icon"><User /></el-icon>
                          <span class="field-placeholder">请输入账号</span>
                        </div>
                      </template>
                      <div v-if="form.login_require_password !== false" class="login-preview-field">
                        <el-icon class="field-icon"><Lock /></el-icon>
                        <span class="field-placeholder">请输入密码</span>
                      </div>
                      <div class="login-preview-btn">登 录</div>
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </div>

          <!-- 预览切换标签（仅开启登录时显示） -->
          <div v-if="form.need_login" class="preview-tab-bar">
            <div
              class="preview-tab"
              :class="{ active: previewMode === 'main' }"
              @click="previewMode = 'main'"
            >主页</div>
            <div
              class="preview-tab"
              :class="{ active: previewMode === 'login' }"
              @click="previewMode = 'login'"
            >登录页</div>
          </div>

          <!-- 预览提示 -->
          <div class="preview-tips">
            <template v-if="previewMode === 'login'">
              <span>在左侧「高级设置」中调整登录表单的对齐位置</span>
            </template>
            <template v-else>
              <span v-if="form.layout === 'free'">拖动按钮调整位置 · 选中后拖动手柄调整大小与形状</span>
              <span v-else-if="form.layout === 'button'">在「按钮管理」标签拖拽调整顺序 · 拖拽预览区手柄调整位置</span>
              <span v-else>点击预览区按钮可在右侧编辑</span>
            </template>
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
              <el-input v-model="selectedModule.title" size="small" placeholder="按钮标题" @change="patchModule(selectedModule, { title: selectedModule.title })" />
            </div>

            <div class="field-block">
              <label class="field-label">图标</label>
              <el-upload
                action="/api/v1/upload/image"
                :headers="uploadHeaders"
                :show-file-list="false"
                :on-success="onIconSuccess"
                accept="image/*"
              >
                <div class="icon-target">
                  <img v-if="selectedModule.icon" :src="selectedModule.icon" />
                  <div v-else class="icon-placeholder"><el-icon><Plus /></el-icon></div>
                </div>
              </el-upload>
              <div class="hint" style="margin-top: 4px">建议 128×128 正方形图标</div>
            </div>

            <div class="field-block">
              <label class="field-label">按钮类型</label>
              <el-tag size="small" :type="metaTagType(selectedModule.content_type)">
                {{ metaTagText(selectedModule.content_type) }}
              </el-tag>
              <div class="hint inspector-hint">内容类型及具体内容请在“模块管理”页面维护。</div>
            </div>

            <div class="field-block">
              <label class="field-label">启用</label>
              <el-switch v-model="selectedModule.is_active" @change="patchModule(selectedModule, { is_active: selectedModule.is_active })" />
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
                    @click="setIconPosition(p.value)"
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
                    @click="setContentAlign(p.value)"
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

            <el-button class="module-manage-link" type="primary" plain @click="goModuleManage">
              前往模块管理维护内容
            </el-button>
          </div>
        </template>

        <div v-else class="inspector-empty">
          <el-icon size="40"><Edit /></el-icon>
          <div class="ie-title">{{ isEdit ? '未选择按钮' : '微站预览' }}</div>
          <div class="ie-desc" v-if="isEdit">点击左侧列表或中间预览区的按钮，在此编辑标题、图标、内容类型与启用状态。</div>
          <div class="ie-desc" v-else>保存微站基本信息后，即可在中间预览区添加并编辑按钮。</div>
        </div>
      </div>
    </div>

    <el-dialog v-model="showQrDialog" title="微站访问二维码" width="360px" align-center>
      <div class="qr-dialog-content">
        <img v-if="qrCodeUrl" :src="qrCodeUrl" class="qr-code" alt="微站访问二维码" />
        <p class="qr-url">{{ accessUrl }}</p>
        <p class="hint">请使用手机扫码访问微站</p>
      </div>
      <template #footer><el-button type="primary" @click="showQrDialog = false">关闭</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Plus, Rank, Grid, Tickets, Document, Picture, Brush,
  MagicStick, Setting, Edit, Share, Service, User, Lock, Phone,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'
import api from '@/api'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const isEdit = computed(() => !!route.params.id)
const uploadHeaders = computed(() => ({ Authorization: `Bearer ${auth.token}` }))
const h5Domain = ref('')
const siteStatus = ref('draft')
const showQrDialog = ref(false)
const isCodeLocked = computed(() => isEdit.value && siteStatus.value === 'online')
const accessUrl = computed(() => {
  const base = (h5Domain.value || 'http://localhost:5174').replace(/\/$/, '')
  return form.code ? `${base}/s/${form.code}` : base
})
const previewUrl = computed(() => (isEdit.value ? accessUrl.value : '#'))
const qrCodeUrl = computed(() => form.code
  ? `https://api.qrserver.com/v1/create-qr-code/?size=240x240&margin=12&data=${encodeURIComponent(accessUrl.value)}`
  : '')

const saving = ref(false)
const isDirty = ref(false)
const leftTab = ref<'site' | 'modules'>('site')
const previewMode = ref<'main' | 'login'>('main')
const loginFormPosition = computed(() => form.login_form_config?.position || 'center')

function switchLeftTab(tab: 'site' | 'modules') {
  leftTab.value = tab
  if (tab === 'modules' && isEdit.value && modules.value.length === 0) {
    loadModules()
  }
}

function metaTagType(contentType: string): 'success' | 'warning' | 'info' {
  const map: Record<string, 'success' | 'warning' | 'info'> = {
    rich_text: 'info',
    external_link: 'warning',
    registration_form: 'success',
  }
  return map[contentType] || 'info'
}

function metaTagText(contentType: string): string {
  const map: Record<string, string> = {
    rich_text: '富文本',
    external_link: '外链',
    registration_form: '报名表单',
  }
  return map[contentType] || '未设置'
}

// --- 表单数据 ---
const form = reactive({
  name: '',
  code: '',
  template: 'classic',
  layout: 'grid',
  kv_image: '',
  background_color: '',
  background_image: '',
  share_image: '',
  share_title: '',
  share_subtitle: '',
  customer_service_config: {
    enabled: false,
    description: '',
    phone: '',
    wechat: '',
    link: '',
    qrcode_url: '',
    service_hours: '',
  },
  need_login: false,
  login_require_password: true,
  need_checkin: false,
  login_fields_config: [] as Array<{
    key: string
    display_name: string
    type: string
    custom_key?: string
  }>,
  login_form_config: { position: 'center' } as { position?: string },
  grid_offset_y: 0,
  start_time: '',
  end_time: '',
  close_message: '',
})

const modules = ref<any[]>([])
const selectedModuleId = ref<number | null>(null)
const selectedModule = computed(() => modules.value.find((m) => m.id === selectedModuleId.value) || null)

// 切换选中按钮时，同步尺寸/形状滑块
watch(selectedModule, (m) => {
  syncSliderValues(m)
})

// --- 预览背景样式（背景图走 bg-layer 图层，这里只兜底背景色） ---
const previewBgStyle = computed(() => {
  if (form.background_color) {
    return { background: form.background_color }
  }
  return {}
})

// --- 拖拽（自由模式） ---
const freeLayoutRef = ref<HTMLElement>()
const draggingId = ref<number | null>(null)
const resizingId = ref<number | null>(null)

// 自由按钮样式（尺寸/形状）
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

// 自由按钮布局类（图标位置 + 内容对齐，用 CSS class 控制）
function freeBtnClass(m: any) {
  const cls: string[] = []
  cls.push('icon-' + (m.icon_position || 'left'))
  if (m.content_align) cls.push('align-' + m.content_align)
  return cls.join(' ')
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

// 图标位置 / 内容对齐选项
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
  patchModule(m, { height: null })
}

function setIconPosition(v: string) {
  const m = selectedModule.value
  if (!m) return
  m.icon_position = v
  patchModule(m, { icon_position: v })
}

function setContentAlign(v: string) {
  const m = selectedModule.value
  if (!m) return
  m.content_align = v
  patchModule(m, { content_align: v })
}

function onStyleFieldChange(field: string, value: any) {
  const m = selectedModule.value
  if (!m) return
  m[field] = value
  patchModule(m, { [field]: value })
}

function setBorderRadius(v: number) {
  const m = selectedModule.value
  if (!m) return
  m.border_radius = v
  radiusSliderValue.value = Math.min(v, 50)
  patchModule(m, { border_radius: v })
}

function onColorChange(field: 'bg_color' | 'font_color', value: string | null) {
  const m = selectedModule.value
  if (!m) return
  m[field] = value || null
  patchModule(m, { [field]: m[field] })
}

// 箭头显示开关: null=默认显示, false=隐藏, true=强制显示
function onShowArrowChange(v: boolean) {
  const m = selectedModule.value
  if (!m) return
  m.show_arrow = v ? null : false
  patchModule(m, { show_arrow: m.show_arrow })
}

// 缩放手柄拖拽: e/w 调宽, n/s 调高, 四角同时调
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
  // 若按钮尚未设置自定义宽高，以当前渲染尺寸作为起点（相对容器百分比）
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
    patchModule(module, {
      width: module.width,
      height: module.height,
      position_x: module.position_x,
      position_y: module.position_y,
    })
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

    const xPct = Math.max(0, Math.min(100 - btnWidthPct, (x / containerRect.width) * 100))
    const yPct = Math.max(0, Math.min(100 - btnHeightPct, (y / containerRect.height) * 100))

    module.position_x = Math.round(xPct * 10) / 10
    module.position_y = Math.round(yPct * 10) / 10
  }

  function onUp(ev: PointerEvent) {
    draggingId.value = null
    btn.style.zIndex = ''
    btn.releasePointerCapture(ev.pointerId)
    document.removeEventListener('pointermove', onMove)
    document.removeEventListener('pointerup', onUp)
    markDirty()
  }

  document.addEventListener('pointermove', onMove)
  document.addEventListener('pointerup', onUp)
}

// --- 九宫格整体拖拽 ---
const gridDragging = ref(false)

function startGridDrag(e: PointerEvent) {
  const container = e.currentTarget?.closest('.device-screen') as HTMLElement
  if (!container) return
  e.preventDefault()

  const containerRect = container.getBoundingClientRect()
  const startY = e.clientY
  const startOffset = form.grid_offset_y || 0
  gridDragging.value = true

  function onMove(ev: PointerEvent) {
    const dy = ev.clientY - startY
    const dyPct = (dy / containerRect.height) * 100
    form.grid_offset_y = Math.max(0, Math.min(60, Math.round((startOffset + dyPct) * 10) / 10))
  }

  function onUp() {
    gridDragging.value = false
    document.removeEventListener('pointermove', onMove)
    document.removeEventListener('pointerup', onUp)
    patchGridOffset()
  }

  document.addEventListener('pointermove', onMove)
  document.addEventListener('pointerup', onUp)
}

async function patchGridOffset() {
  if (!isEdit.value) return
  try {
    const siteId = route.params.id as string
    await api.put(`/sites/${siteId}`, { grid_offset_y: form.grid_offset_y })
  } catch { /* 位置变更不弹错误提示 */ }
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
function onLayerDrop(index: number) {
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
    })
  }
  markDirty()
}

// --- 上传回调 ---
function onKvSuccess(res: any) {
  if (res.url) {
    form.kv_image = res.url
    markDirty()
  } else ElMessage.error('上传失败')
}

function onBgSuccess(res: any) {
  if (res.url) {
    form.background_image = res.url
    markDirty()
  } else ElMessage.error('上传失败')
}

function onShareImageSuccess(res: any) {
  if (res.url) {
    form.share_image = res.url
    markDirty()
  } else ElMessage.error('上传失败')
}

function onServiceQrSuccess(res: any) {
  if (res.url) {
    form.customer_service_config.qrcode_url = res.url
    markDirty()
  } else ElMessage.error('上传失败')
}

function onIconSuccess(res: any) {
  const m = selectedModule.value
  if (!m) return
  if (res.url) {
    m.icon = res.url
    patchModule(m, { icon: res.url })
  } else ElMessage.error('上传失败')
}

// --- 生成访问码 ---
function generateCode() {
  if (isCodeLocked.value) {
    ElMessage.warning('微站已上线，访问码不可修改')
    return
  }
  const chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
  let code = ''
  for (let i = 0; i < 8; i++) code += chars[Math.floor(Math.random() * chars.length)]
  form.code = code
  markDirty()
}

// --- 标记脏数据 ---
function markDirty() {
  isDirty.value = true
}

// --- 登录字段配置 ---
function addLoginField() {
  form.login_fields_config.push({
    key: 'username',
    display_name: '账号',
    type: 'text',
  })
  markDirty()
}

function removeLoginField(idx: number) {
  form.login_fields_config.splice(idx, 1)
  markDirty()
}

function onLoginFieldKeyChange(field: any) {
  if (field.key === 'username') {
    field.display_name = '账号'
    field.type = 'text'
  } else if (field.key === 'phone') {
    field.display_name = '手机号'
    field.type = 'text'
  } else if (field.key === 'custom') {
    field.display_name = '自定义字段'
    field.custom_key = ''
  }
  markDirty()
}

function onCustomKeyChange(field: any) {
  markDirty()
}


// --- 模块即时保存 ---
async function patchModule(m: any, patch: Record<string, any>) {
  const siteId = route.params.id as string
  try {
    await api.put(`/sites/${siteId}/modules/${m.id}`, patch)
  } catch {
    ElMessage.error('保存失败')
  }
}

async function goModuleManage() {
  if (!isEdit.value) return
  router.push(`/sites/${route.params.id}/modules`)
}

async function addModule() {
  if (!isEdit.value) {
    ElMessage.warning('请先保存微站基本信息')
    return
  }
  const siteId = route.params.id as string
  const idx = modules.value.length
  const data: Record<string, any> = {
    title: '新按钮',
    content_type: 'rich_text',
    is_active: true,
    sort_order: idx,
  }
  if (form.layout === 'free') {
    data.position_x = 10
    data.position_y = 15 + idx * 12
  }
  try {
    const res: any = await api.post(`/sites/${siteId}/modules`, data)
    modules.value.push(res)
    selectedModuleId.value = res.id
  } catch {
    ElMessage.error('创建失败')
  }
}

async function deleteModule(m: any) {
  const siteId = route.params.id as string
  try {
    await api.delete(`/sites/${siteId}/modules/${m.id}`)
    ElMessage.success('已删除')
    if (selectedModuleId.value === m.id) selectedModuleId.value = null
    await loadModules()
  } catch {
    ElMessage.error('删除失败')
  }
}

// --- 加载数据 ---
async function loadModules() {
  if (!isEdit.value) return
  const siteId = route.params.id as string
  const res: any = await api.get(`/sites/${siteId}/modules`)
  modules.value = res
}

// --- 保存 ---
async function handleSave() {
  if (!form.name) {
    ElMessage.warning('请输入微站名称')
    return
  }
  if (!form.code) {
    ElMessage.warning('请输入访问码')
    return
  }
  saving.value = true
  try {
    const data: Record<string, any> = {}
    for (const [key, value] of Object.entries(form)) {
      if (value === undefined) continue
      data[key] = value === '' ? null : value
    }

    if (isEdit.value) {
      const siteId = route.params.id as string
      await api.put(`/sites/${siteId}`, data)

      if (form.layout === 'free') {
        const positions = modules.value.map((m) => ({
          module_id: m.id,
          position_x: m.position_x,
          position_y: m.position_y,
        }))
        await api.put(`/sites/${siteId}/modules/positions`, { items: positions })
      } else {
        const sorts = modules.value.map((m, i) => ({
          module_id: m.id,
          sort_order: m.sort_order ?? i,
        }))
        await api.put(`/sites/${siteId}/modules/sort`, { items: sorts })
      }

      ElMessage.success('保存成功')
      isDirty.value = false
    } else {
      const res: any = await api.post('/sites', data)
      ElMessage.success('创建成功')
      router.replace(`/sites/${res.id}/edit`)
    }
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  if (isEdit.value) {
    const siteId = route.params.id as string
    const [res, systemConfig]: any[] = await Promise.all([
      api.get(`/sites/${siteId}`),
      api.get('/system-config/runtime').catch(() => ({ h5_domain: '' })), 
    ])
    h5Domain.value = systemConfig.h5_domain || ''
    siteStatus.value = res.status || 'draft'
    Object.assign(form, {
      name: res.name || '',
      code: res.code || '',
      template: res.template || 'classic',
      layout: res.layout || 'grid',
      kv_image: res.kv_image || '',
      background_color: res.background_color || '',
      background_image: res.background_image || '',
      share_image: res.share_image || '',
      share_title: res.share_title || '',
      share_subtitle: res.share_subtitle || '',
      customer_service_config: {
        enabled: false,
        description: '',
        phone: '',
        wechat: '',
        link: '',
        qrcode_url: '',
        service_hours: '',
        ...(res.customer_service_config || {}),
      },
      need_login: res.need_login || false,
      login_require_password: res.login_require_password !== false,
      need_checkin: res.need_checkin || false,
      login_fields_config: (res.login_fields_config || []).map((f: any) => ({
        ...f,
        type: f.type || 'text',
      })),
      login_form_config: {
        position: 'center',
        ...(res.login_form_config || {}),
      },
      grid_offset_y: res.grid_offset_y ?? 0,
      start_time: res.start_time || '',
      end_time: res.end_time || '',
      close_message: res.close_message || '',
    })
    await loadModules()
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
.topbar-right {
  justify-content: flex-end;
}
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
.dirty-tag {
  font-weight: 500;
}
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
  padding: 16px;
}

.config-card {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}
.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.card-title .el-icon { color: #409eff; }

.hint {
  color: #999;
  font-size: 12px;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

/* 登录字段配置 */
.login-fields-config {
  width: 100%;
}
.login-field-item {
  background: #f8f9fb;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 8px;
}
.login-field-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.code-lock-hint { margin-top: 4px; color: #e6a23c; }
.inline-hint { margin-left: 8px; }
.code-actions {
  display: flex;
  align-items: center;
  min-width: 112px;
}
.code-actions .el-button {
  height: 30px;
  margin: 0;
  padding: 0 10px;
}
.code-actions .el-button + .el-button {
  border-left: 1px solid var(--el-border-color-lighter);
}

/* 上传组件 */
.upload-preview {
  position: relative;
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
}
.upload-preview.small {
  max-width: 220px;
}
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
.upload-preview:hover .preview-mask {
  opacity: 1;
}
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
.upload-placeholder.small {
  height: 80px;
}
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
.empty-hint {
  padding: 40px 20px;
  text-align: center;
  color: #999;
  font-size: 13px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px dashed #e0e0e0;
}
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
.module-item:active .layer-drag-handle {
  cursor: grabbing;
}
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
.manage-module-btn {
  width: 100%;
  margin-top: 8px;
}

/* 按钮管理面板：九宫格垂直位置设置 */
.grid-offset-config {
  margin-top: 12px;
  padding: 10px 12px;
  background: #f5f7fa;
  border: 1px solid #ebeef5;
  border-radius: 8px;
}
.grid-offset-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}
.grid-offset-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}
.grid-offset-value {
  width: 44px;
  color: #666;
  font-size: 12px;
  text-align: right;
  flex-shrink: 0;
}
.grid-offset-config .hint {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
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
  /* 刘海高度：背景图从刘海下方紧贴开始 */
  --status-area: 22px;
  /* 顶部刘海区域渲染为黑色（设备屏幕顶部），模板渐变从刘海下方开始 */
  background:
    linear-gradient(to bottom, #1a1a1a 0, #1a1a1a var(--status-area), transparent var(--status-area)),
    linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow:
    0 0 0 2px #2a2a2a,
    0 24px 60px rgba(0,0,0,0.35),
    0 8px 20px rgba(0,0,0,0.18);
}
.device-frame.tpl-classic {
  background:
    linear-gradient(to bottom, #1a1a1a 0, #1a1a1a var(--status-area), transparent var(--status-area)),
    linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.device-frame.tpl-dark {
  background:
    linear-gradient(to bottom, #1a1a1a 0, #1a1a1a var(--status-area), transparent var(--status-area)),
    linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}
.device-frame.tpl-festive {
  background:
    linear-gradient(to bottom, #1a1a1a 0, #1a1a1a var(--status-area), transparent var(--status-area)),
    linear-gradient(135deg, #c0392b 0%, #e74c3c 100%);
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
}

/* 背景图：铺满整个屏幕内容区域，但不包含刘海/状态栏顶部区域 */
.bg-layer { position: absolute; top: var(--status-area); left: 0; right: 0; bottom: 0; z-index: 0; overflow: hidden; line-height: 0; }
.bg-image { width: 100%; height: 100%; object-fit: cover; display: block; }

/* 状态栏：位于刘海两侧"耳朵区"，与真机系统状态栏位置一致 */
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
/* 内部内容容器：图标/标题/箭头按布局方向排列 */
.free-btn-inner {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  min-width: 0;
}
/* 基础顺序: 图标0 标题1 箭头2 */
.free-btn-inner .btn-icon,
.free-btn-inner .btn-icon-placeholder { order: 0; flex-shrink: 0; }
.free-btn-inner .btn-text { order: 1; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; }
.free-btn-inner .btn-arrow { order: 2; flex-shrink: 0; }

/* 图标位置: 水平（默认 left） */
.free-btn-inner.icon-left { flex-direction: row; justify-content: flex-start; }
.free-btn-inner.icon-right { flex-direction: row; }
.free-btn-inner.icon-right .btn-icon,
.free-btn-inner.icon-right .btn-icon-placeholder { order: 2; }
.free-btn-inner.icon-right .btn-text { order: 0; }
.free-btn-inner.icon-right .btn-arrow { order: 1; }

/* 图标位置: 垂直（图标上/下），内容垂直居中 */
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
/* 垂直布局时箭头绝对定位在按钮右侧中部 */
.free-btn-inner.icon-top .btn-arrow,
.free-btn-inner.icon-bottom .btn-arrow {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
}

/* 内容水平对齐 */
.free-btn-inner.align-left { justify-content: flex-start; }
.free-btn-inner.align-center { justify-content: center; }
.free-btn-inner.align-right { justify-content: flex-end; }
/* 垂直布局时水平对齐用 align-items */
.free-btn-inner.icon-top.align-left,
.free-btn-inner.icon-bottom.align-left { align-items: flex-start; }
.free-btn-inner.icon-top.align-center,
.free-btn-inner.icon-bottom.align-center { align-items: center; }
.free-btn-inner.icon-top.align-right,
.free-btn-inner.icon-bottom.align-right { align-items: flex-end; }

/* 固定高度时内容垂直居中 */
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

/* 九宫格拖拽手柄 */
.grid-drag-handle {
  text-align: center;
  padding: 4px 0 2px;
  color: rgba(255,255,255,0.35);
  font-size: 14px;
  line-height: 1;
  cursor: grab;
  user-select: none;
  letter-spacing: 2px;
  margin-bottom: 4px;
}
.grid-drag-handle:active { cursor: grabbing; }

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
.field-block {
  margin-bottom: 18px;
}
.field-label {
  display: block;
  font-size: 12px;
  color: #646a73;
  margin-bottom: 8px;
}
.inspector-hint { margin-top: 8px; }
.module-manage-link { width: 100%; }

/* 尺寸与形状面板 */
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
.radius-preset:hover {
  border-color: #409eff;
}
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
.radius-slider-row {
  margin-top: 10px;
}
/* 分段选择控件（图标位置/内容对齐） */
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
.qr-dialog-content { display: flex; flex-direction: column; align-items: center; gap: 12px; text-align: center; }
.qr-code { width: 240px; height: 240px; border: 1px solid #ebeef5; border-radius: 8px; }
.qr-url { width: 100%; margin: 0; color: #606266; font-size: 12px; line-height: 1.5; overflow-wrap: anywhere; }
.icon-target {
  width: 72px;
  height: 72px;
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  border: 1px dashed #d0d7de;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
  transition: border-color 0.2s;
}
.icon-target:hover {
  border-color: #409eff;
}
.icon-target img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.icon-placeholder {
  color: #8c8c8c;
  display: flex;
  align-items: center;
  justify-content: center;
}
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
.inspector-empty .el-icon {
  color: #c0c4cc;
}
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

/* ====== 预览标签切换 ====== */
.preview-tab-bar {
  display: flex;
  margin: 10px auto 0;
  width: 160px;
  background: #e8eaed;
  border-radius: 6px;
  padding: 2px;
}
.preview-tab {
  flex: 1;
  text-align: center;
  padding: 5px 0;
  font-size: 12px;
  color: #646a73;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
  user-select: none;
}
.preview-tab:hover { color: #1f2937; }
.preview-tab.active {
  background: #fff;
  color: #1f2937;
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.login-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100%;
  position: relative;
  padding: 0 14px;
}

/* 登录卡片位置 */
.login-preview.login-pos-top { justify-content: flex-start; }
.login-preview.login-pos-top .login-preview-card { margin-top: 8px; }
.login-preview.login-pos-center { justify-content: center; }
.login-preview.login-pos-bottom { justify-content: flex-end; padding-bottom: 16px; }

/* KV 图 */
.login-preview-kv {
  width: calc(100% + 28px);
  margin-left: -14px;
  margin-right: -14px;
  overflow: hidden;
  border-bottom-left-radius: 18px;
  border-bottom-right-radius: 18px;
  flex-shrink: 0;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}
.login-preview-kv-img {
  width: 100%;
  display: block;
  object-fit: cover;
  max-height: 160px;
}

/* 品牌区域 */
.login-preview-brand {
  text-align: center;
  margin-bottom: 14px;
}
.login-preview-brand.compact {
  margin-bottom: 10px;
}
.login-preview-title {
  font-size: 16px;
  font-weight: 700;
  color: #1f2330;
  letter-spacing: 0.5px;
}
.login-preview-sub {
  margin-top: 4px;
  font-size: 11px;
  color: #8a8f9c;
}

/* 登录卡片 */
.login-preview-card {
  width: 100%;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
  border-radius: 16px;
  padding: 20px 16px 18px;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.15);
  flex-shrink: 0;
}
.login-preview-card.has-kv {
  margin-top: -24px;
  position: relative;
  z-index: 2;
}

/* 模拟输入框 */
.login-preview-field {
  display: flex;
  align-items: center;
  background: #f4f5f8;
  border-radius: 10px;
  margin-bottom: 12px;
  padding: 10px 12px;
  gap: 8px;
}
.login-preview-field .field-icon {
  font-size: 14px;
  color: #667eea;
  flex-shrink: 0;
}
.login-preview-field .field-placeholder {
  font-size: 12px;
  color: #b0b4be;
}

/* 模拟登录按钮 */
.login-preview-btn {
  text-align: center;
  padding: 10px 0;
  border-radius: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 4px;
  margin-top: 6px;
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.3);
  cursor: default;
}
</style>
