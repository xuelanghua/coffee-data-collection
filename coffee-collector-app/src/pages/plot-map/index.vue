<template>
  <view class="page">
    <view class="section">
      <text class="title">现场圈选地块</text>
      <text class="metric">{{ areaMu }} 亩</text>
    </view>
    <view class="panel">
      <text class="label">边界点</text>
      <text v-for="point in points" :key="`${point.longitude}-${point.latitude}`" class="row">
        {{ point.longitude }}, {{ point.latitude }}
      </text>
    </view>
    <button class="secondary" @click="undoPoint">撤销上一点</button>
    <button class="primary" @click="savePlot">保存正式地块</button>
  </view>
</template>

<script>
import { PlotDrawingSession } from "../../services/plot-drawing.js";

export default {
  data() {
    const points = [
      { longitude: 100, latitude: 22 },
      { longitude: 100.001, latitude: 22 },
      { longitude: 100.001, latitude: 22.001 },
      { longitude: 100, latitude: 22.001 },
    ];
    const drawing = new PlotDrawingSession();
    for (const point of points) {
      drawing.addPoint(point);
    }
    const snapshot = drawing.snapshot();
    return {
      drawing,
      points: snapshot.points,
      areaMu: snapshot.areaMu,
      createPayload: null,
      statusText: "待保存",
    };
  },
  methods: {
    undoPoint() {
      const snapshot = this.drawing.undoPoint();
      this.points = snapshot.points;
      this.areaMu = snapshot.areaMu;
    },
    savePlot() {
      this.createPayload = this.drawing.buildCreatePlotPayload({
        taskId: "TASK-DEMO",
        plotId: "PL-DEMO",
        name: "现场地块",
        idempotencyKey: "plot-demo-key",
      });
      this.statusText = `待同步 ${this.createPayload.boundary_geojson.type}`;
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
.metric {
  color: #216b4e;
}
.panel {
  padding: 20rpx;
  border: 1px solid #d9ded7;
  border-radius: 8rpx;
  background: #fff;
}
.label,
.row {
  display: block;
  margin-bottom: 10rpx;
}
.primary {
  margin-top: 24rpx;
  background: #216b4e;
  color: #fff;
}
.secondary {
  margin-top: 24rpx;
  color: #216b4e;
  background: #eef4ef;
}
</style>
