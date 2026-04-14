<template>
  <section v-if="proposal" class="revision-detail-page">
    <article class="detail-card">
      <header class="detail-head">
        <div>
          <h2>{{ proposal.article_title || proposal.proposed_title || "修订审核" }}</h2>
          <p class="meta">
            提交者 {{ proposal.proposer?.username || "-" }} · 提交时间 {{ formatDateTime(proposal.created_at) }}
          </p>
          <p class="meta">修订说明：{{ proposal.reason || "无" }}</p>
        </div>
        <div class="head-actions">
          <button class="btn" @click="goBack">返回审核列表</button>
          <button class="btn" @click="compareMode = !compareMode">
            {{ compareMode ? "返回默认视图" : "切换对比视图" }}
          </button>
        </div>
      </header>

      <section class="card preview-card">
        <div class="preview-head">
          <h3>{{ compareMode ? "对比预览" : "渲染预览" }}</h3>
          <button
            v-if="compareMode"
            class="btn btn-press"
            @mousedown.prevent="setPressingOriginal(true)"
            @mouseup="setPressingOriginal(false)"
            @mouseleave="setPressingOriginal(false)"
            @touchstart.prevent="setPressingOriginal(true)"
            @touchend="setPressingOriginal(false)"
            @touchcancel="setPressingOriginal(false)"
          >
            {{ pressingOriginal ? "松开返回修改版本" : "长按查看当前线上版本" }}
          </button>
        </div>
        <div v-if="compareMode" class="meta">
          当前显示：{{ pressingOriginal ? "当前线上版本" : mergeConflict ? "冲突解决稿" : "待审核修订稿" }}
        </div>
        <div class="markdown rendered-area" v-html="activeRenderHtml"></div>
      </section>

      <section class="card diff-card">
        <h3>修订差异</h3>
        <p class="meta">绿色为新增，红色为删除。</p>
        <div class="diff-render" v-html="diffHtml"></div>
      </section>

      <section v-if="proposal.status === 'pending'" class="card review-action-card">
        <h3>审核操作</h3>
        <textarea class="textarea" v-model="reviewNote" placeholder="审核备注（可选）"></textarea>
        <div class="review-actions">
          <button class="btn btn-accent" :disabled="submittingReview" @click="approve">
            {{ submittingReview ? "处理中..." : mergeConflict ? "解决冲突并通过" : "通过" }}
          </button>
          <button class="btn" :disabled="submittingReview" @click="reject">
            {{ submittingReview ? "处理中..." : "驳回" }}
          </button>
        </div>
      </section>

      <section v-if="proposal.status === 'pending' && mergeConflict" class="card review-action-card">
        <h3>Merge Conflict</h3>
        <p class="meta">{{ mergeConflict.detail }}</p>
        <p v-if="mergeConflict.conflicts?.length" class="meta">
          冲突字段：{{ mergeConflict.conflicts.map((item) => item.field).join(" / ") }}
        </p>
        <input class="input" v-model="resolutionForm.title" placeholder="Resolved title" />
        <textarea class="textarea" v-model="resolutionForm.summary" placeholder="Resolved summary (optional)"></textarea>
        <textarea
          class="textarea resolution-textarea"
          v-model="resolutionForm.content_md"
          placeholder="Resolve merge conflicts here"
        ></textarea>
        <p class="meta">上面已经放入后端生成的合并草稿。删除冲突标记并确认内容后，再点击通过。</p>
      </section>

      <section v-if="proposal.status !== 'pending'" class="card review-action-card">
        <h3>审核结果</h3>
        <p class="meta">结果：{{ statusText(proposal.status) }}</p>
        <p class="meta">审核人：{{ proposal.reviewer?.username || "-" }}</p>
        <p class="meta">审核时间：{{ formatDateTime(proposal.reviewed_at) }}</p>
        <p class="meta">审核备注：{{ proposal.review_note || "无" }}</p>
      </section>
    </article>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import api from "../services/api";
import { renderMarkdown } from "../services/markdown";
import { renderUnifiedDiffHtml } from "../services/revisionDiff";
import { useUiStore } from "../stores/ui";

const route = useRoute();
const router = useRouter();
const ui = useUiStore();

const proposal = ref(null);
const reviewNote = ref("");
const submittingReview = ref(false);
const compareMode = ref(false);
const pressingOriginal = ref(false);
const mergeConflict = ref(null);
const resolutionForm = reactive({
  title: "",
  summary: "",
  content_md: "",
  base_updated_at: "",
});

const activeRenderHtml = computed(() => {
  const item = proposal.value;
  if (!item) return "";
  if (compareMode.value && pressingOriginal.value) {
    return renderMarkdown(mergeConflict.value?.current?.content_md || item.article_content_md || "");
  }
  if (mergeConflict.value) {
    return renderMarkdown(resolutionForm.content_md || mergeConflict.value?.merged?.content_md || "");
  }
  return renderMarkdown(item.proposed_content_md || "");
});

const diffHtml = computed(() => {
  const item = proposal.value;
  if (!item) return "";
  const beforeText = mergeConflict.value?.current?.content_md || item.article_content_md || "";
  const afterText = mergeConflict.value ? resolutionForm.content_md : (item.proposed_content_md || "");
  return renderUnifiedDiffHtml(beforeText, afterText);
});

function formatDateTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function statusText(status) {
  const mapping = {
    pending: "待审核",
    approved: "通过",
    rejected: "驳回",
  };
  return mapping[status] || status || "-";
}

function setPressingOriginal(flag) {
  pressingOriginal.value = Boolean(flag);
}

function getErrorText(error, fallback = "操作失败") {
  const payload = error?.response?.data;
  if (!payload) return fallback;
  if (typeof payload === "string") return payload;
  if (typeof payload.detail === "string") return payload.detail;
  return fallback;
}

function resetMergeConflict() {
  mergeConflict.value = null;
  resolutionForm.title = "";
  resolutionForm.summary = "";
  resolutionForm.content_md = "";
  resolutionForm.base_updated_at = "";
}

function applyMergeConflict(error) {
  const payload = error?.response?.data;
  const merge = payload?.merge;
  if (error?.response?.status !== 409 || payload?.code !== "revision_merge_conflict" || !merge) {
    return false;
  }

  mergeConflict.value = {
    detail: payload?.detail || "Merge conflict",
    conflicts: Array.isArray(merge?.conflicts) ? merge.conflicts : [],
    current: merge?.current || null,
    merged: merge?.merged || null,
  };
  resolutionForm.title = merge?.merged?.title ?? proposal.value?.proposed_title ?? "";
  resolutionForm.summary = merge?.merged?.summary ?? proposal.value?.proposed_summary ?? "";
  resolutionForm.content_md = merge?.merged?.content_md ?? proposal.value?.proposed_content_md ?? "";
  resolutionForm.base_updated_at = merge?.current?.updated_at || "";
  ui.error(payload?.detail || "修订和当前线上版本冲突，请先解决冲突。");
  return true;
}

function goBack() {
  router.push({ name: "review" });
}

async function loadProposal() {
  try {
    const { data } = await api.get(`/revisions/${route.params.id}/`);
    proposal.value = data;
    reviewNote.value = data.review_note || "";
    resetMergeConflict();
  } catch (error) {
    ui.error(getErrorText(error, "审核条目加载失败"));
    goBack();
  }
}

async function approve() {
  if (!proposal.value || proposal.value.status !== "pending") return;
  submittingReview.value = true;
  try {
    const payload = {
      review_note: reviewNote.value.trim(),
    };
    if (mergeConflict.value) {
      payload.resolved_title = resolutionForm.title.trim();
      payload.resolved_summary = resolutionForm.summary.trim();
      payload.resolved_content_md = resolutionForm.content_md;
      payload.resolution_base_updated_at = resolutionForm.base_updated_at || null;
    }
    const { data } = await api.post(`/revisions/${proposal.value.id}/approve/`, payload);
    proposal.value = data;
    resetMergeConflict();
    ui.success("修订已通过");
  } catch (error) {
    if (applyMergeConflict(error)) {
      return;
    }
    ui.error(getErrorText(error, "通过失败"));
  } finally {
    submittingReview.value = false;
  }
}

async function reject() {
  if (!proposal.value || proposal.value.status !== "pending") return;
  submittingReview.value = true;
  try {
    const { data } = await api.post(`/revisions/${proposal.value.id}/reject/`, {
      review_note: reviewNote.value.trim(),
    });
    proposal.value = data;
    resetMergeConflict();
    ui.success("修订已驳回");
  } catch (error) {
    ui.error(getErrorText(error, "驳回失败"));
  } finally {
    submittingReview.value = false;
  }
}

onMounted(async () => {
  await loadProposal();
});
</script>

<style scoped>
.revision-detail-page {
  max-width: 1320px;
  margin: 0 auto;
}

.detail-card {
  display: grid;
  gap: 12px;
}

.detail-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.detail-head h2 {
  font-size: 34px;
}

.head-actions {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.preview-card,
.diff-card,
.review-action-card {
  padding: 14px;
}

.preview-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.preview-head h3,
.diff-card h3,
.review-action-card h3 {
  font-size: 24px;
  margin: 0;
}

.rendered-area {
  max-height: 72vh;
  overflow: auto;
  border-radius: 12px;
  border: 1px solid var(--hairline);
  padding: 12px;
  background: var(--surface-strong);
}

.btn-press {
  user-select: none;
}

.diff-render {
  border-radius: 12px;
  border: 1px solid var(--hairline);
  background: var(--surface-strong);
  max-height: 58vh;
  overflow: auto;
}

.diff-render :deep(.diff-line) {
  display: grid;
  grid-template-columns: 24px minmax(0, 1fr);
  gap: 8px;
  align-items: baseline;
  padding: 4px 10px;
  font-family: var(--font-mono);
  white-space: pre-wrap;
  line-height: 1.55;
}

.diff-render :deep(.diff-line--insert) {
  background: color-mix(in srgb, var(--success) 15%, transparent);
  color: var(--success);
}

.diff-render :deep(.diff-line--delete) {
  background: color-mix(in srgb, var(--danger) 15%, transparent);
  color: var(--danger);
}

.diff-render :deep(.diff-line--equal) {
  color: var(--text);
}

.diff-render :deep(.diff-line--ellipsis) {
  color: var(--muted);
}

.diff-render :deep(.diff-sign) {
  text-align: center;
  opacity: 0.8;
}

.diff-render :deep(.diff-inline-delete) {
  background: color-mix(in srgb, var(--danger) 24%, transparent);
  color: var(--danger);
  text-decoration: line-through;
  padding: 0 2px;
  border-radius: 4px;
}

.diff-render :deep(.diff-inline-insert) {
  background: color-mix(in srgb, var(--success) 24%, transparent);
  color: var(--success);
  padding: 0 2px;
  border-radius: 4px;
}

.review-actions {
  display: flex;
  gap: 8px;
}

.resolution-textarea {
  min-height: 280px;
}

@media (max-width: 960px) {
  .detail-head {
    flex-direction: column;
  }

  .head-actions {
    width: 100%;
    flex-wrap: wrap;
  }
}
</style>
