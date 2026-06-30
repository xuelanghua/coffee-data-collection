<template>
  <view class="page">
    <view class="section">
      <text class="title">拍照水印</text>
      <text class="status">{{ watermark.metadata.photo_id }}</text>
    </view>
    <view class="panel">
      <text v-for="line in watermark.lines" :key="line" class="row">{{ line }}</text>
    </view>
    <button class="primary" @click="capture">拍照生成草稿</button>
  </view>
</template>

<script>
import { CameraCaptureAdapter } from "../../services/camera-capture.js";
import { buildPhotoWatermark } from "../../services/watermark.js";

export default {
  data() {
    const adapter = new CameraCaptureAdapter({
      chooseImage: async () => ({
        tempFilePath: "local://device-demo.jpg",
        size: 0,
        width: 0,
        height: 0,
      }),
    });
    return {
      adapter,
      draft: null,
      watermark: buildPhotoWatermark({
        taskId: "TASK-DEMO",
        plotId: "PL-DEMO",
        pointId: "PT-DEMO",
        eventId: "EV-DEMO",
        photoId: "PH-DEMO",
        capturedAt: "2026-06-24T10:30:00+08:00",
        collectorName: "采集员",
        location: { longitude: 100.1, latitude: 22.1, accuracy: 6, coordinateSystem: "gcj02" },
      }),
    };
  },
  methods: {
    async capture() {
      this.draft = await this.adapter.capturePhotoDraft({
        taskId: "TASK-DEMO",
        plotId: "PL-DEMO",
        pointId: "PT-DEMO",
        eventId: "EV-DEMO",
        photoId: "PH-DEMO",
        category: "device_reading",
        collectorName: "采集员",
        location: { longitude: 100.1, latitude: 22.1, accuracy: 6, coordinateSystem: "gcj02" },
      });
      this.watermark = this.draft.watermark;
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
.panel {
  padding: 20rpx;
  border: 1px solid #d9ded7;
  border-radius: 8rpx;
  background: #fff;
}
.row {
  display: block;
  margin-bottom: 10rpx;
}
.primary {
  margin-top: 24rpx;
  background: #216b4e;
  color: #fff;
}
</style>
