<template>
  <view class="page">
    <view class="section">
      <text class="section-title">现场采集闭环</text>
      <text class="status">{{ statusText }}</text>
    </view>
    <view class="grid">
      <view v-for="field in fields" :key="field.code" class="field">
        <text class="label">{{ field.label }}</text>
        <input class="input" v-model="field.value" @input="onFieldInput(field)" />
      </view>
    </view>
    <button class="primary" @click="submit">提交</button>
  </view>
</template>

<script>
import { CoffeeApiClient } from "../../services/api.js";
import { DEVICE_FIELD_DEFINITIONS, FieldCollectionFlow } from "../../services/collection-flow.js";

export default {
  data() {
    const api = new CoffeeApiClient({ baseUrl: "" });
    const flow = new FieldCollectionFlow({ client: api });
    return {
      flow,
      statusText: "待采集",
      fields: DEVICE_FIELD_DEFINITIONS.map(([code, label]) => ({ code, label, value: "" })),
    };
  },
  methods: {
    onFieldInput(field) {
      this.flow.correctDeviceField(field.code, field.value, "现场手动校准");
    },
    async submit() {
      this.statusText = "提交中";
      const payload = this.flow.buildSubmitPayload();
      await this.flow.client.submitEvent(this.flow.event.eventId, payload);
      this.statusText = "已提交";
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
.section-title {
  display: block;
  font-size: 34rpx;
  font-weight: 600;
}
.status {
  color: #58665d;
}
.grid {
  display: grid;
  gap: 18rpx;
}
.field {
  padding: 18rpx;
  border: 1px solid #d9ded7;
  border-radius: 8rpx;
  background: #fff;
}
.label {
  display: block;
  margin-bottom: 10rpx;
  color: #3c4b42;
}
.input {
  height: 72rpx;
  padding: 0 16rpx;
  background: #f7f8f5;
}
.primary {
  margin-top: 24rpx;
  background: #216b4e;
  color: #fff;
}
</style>
