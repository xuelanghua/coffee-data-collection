<template>
  <view class="page">
    <view class="section">
      <text class="title">退回修改</text>
      <text class="status">本地修正草稿 {{ draftCount }} 条</text>
      <text class="status">重提状态 {{ resubmitStatus }}</text>
    </view>
    <button class="primary" @click="loadDrafts">刷新草稿</button>
    <button class="secondary" @click="prepareResubmit">准备重新提交</button>
    <button class="secondary" @click="submitCorrection">提交修正版本</button>
  </view>
</template>

<script>
import { CoffeeApiClient } from "../../services/api.js";
import { InMemoryDraftStorage, LocalDraftStore } from "../../services/draft-store.js";

export default {
  data() {
    return {
      client: new CoffeeApiClient({ baseUrl: "" }),
      store: new LocalDraftStore({ storage: new InMemoryDraftStorage() }),
      draftCount: 0,
      resubmitReady: false,
      resubmitStatus: "未准备",
      currentDraft: null,
    };
  },
  methods: {
    async loadDrafts() {
      const drafts = await this.store.listDrafts();
      this.draftCount = drafts.length;
      this.currentDraft = drafts[0] || null;
    },
    prepareResubmit() {
      this.resubmitReady = true;
      this.resubmitStatus = "待提交";
    },
    async submitCorrection() {
      if (!this.currentDraft?.eventId || !this.currentDraft?.submitPayload) {
        this.resubmitStatus = "缺少修正草稿";
        return;
      }
      this.resubmitStatus = "提交中";
      await this.client.resubmitEvent(this.currentDraft.eventId, this.currentDraft.submitPayload);
      this.resubmitStatus = "已重新提交";
    },
  },
};
</script>

<style scoped>
.page {
  padding: 24rpx;
}
.section {
  margin-bottom: 24rpx;
}
.title {
  display: block;
  font-size: 34rpx;
  font-weight: 600;
}
.status {
  color: #58665d;
}
.primary {
  background: #216b4e;
  color: #fff;
}
.secondary {
  margin-top: 16rpx;
  color: #216b4e;
  background: #eef4ef;
}
</style>
