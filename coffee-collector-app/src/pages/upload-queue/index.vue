<template>
  <view class="page">
    <view class="section">
      <text class="title">上传队列</text>
      <text class="status">网络 {{ networkState }}</text>
      <text class="status">状态 {{ paused ? "已暂停" : "可上传" }}</text>
      <text class="status">待上传 {{ pendingCount }} 项</text>
      <text class="status">失败 {{ failedCount }} 项</text>
      <text class="status">已完成 {{ completedCount }} 项</text>
    </view>
    <button class="primary" @click="startUpload">开始上传</button>
    <button class="secondary" @click="pauseUpload">暂停上传</button>
    <button class="secondary" @click="resumeUpload">继续上传</button>
    <button class="secondary" @click="retry">重试失败项</button>
    <button class="secondary" @click="refreshDiagnostics">刷新诊断</button>
  </view>
</template>

<script>
import { CoffeeApiClient } from "../../services/api.js";
import { UploadQueue } from "../../services/upload-queue.js";

export default {
  data() {
    const queue = new UploadQueue({ client: new CoffeeApiClient({ baseUrl: "" }) });
    return {
      queue,
      pendingCount: queue.pendingCount,
      failedCount: queue.failedCount,
      completedCount: 0,
      networkState: queue.networkState,
      paused: queue.paused,
      diagnostics: queue.diagnostics(),
    };
  },
  methods: {
    async startUpload() {
      await this.queue.drain({ stopOnError: false });
      this.refreshDiagnostics();
    },
    pauseUpload() {
      this.queue.pause();
      this.refreshDiagnostics();
    },
    resumeUpload() {
      this.queue.resume();
      this.refreshDiagnostics();
    },
    retry() {
      this.queue.retryFailed();
      this.refreshDiagnostics();
    },
    refreshDiagnostics() {
      const diagnostics = this.queue.diagnostics();
      this.diagnostics = diagnostics;
      this.pendingCount = diagnostics.pendingCount;
      this.failedCount = diagnostics.failedCount;
      this.completedCount = diagnostics.completedCount;
      this.networkState = diagnostics.networkState;
      this.paused = diagnostics.paused;
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
