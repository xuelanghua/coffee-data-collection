<template>
  <view class="page">
    <view class="title">普洱咖啡采集</view>
    <input v-model="phone" class="input" placeholder="手机号" />
    <input v-model="password" class="input" password placeholder="密码" />
    <button class="primary" :disabled="loading" @click="login">登录</button>
    <text class="error" v-if="error">{{ error }}</text>
  </view>
</template>

<script>
import { CoffeeApiClient } from "../../services/api.js";

export default {
  data() {
    return {
      phone: "",
      password: "",
      loading: false,
      error: "",
      api: new CoffeeApiClient({ baseUrl: "" }),
    };
  },
  methods: {
    async login() {
      this.loading = true;
      this.error = "";
      try {
        await this.api.loginByPassword({ phone: this.phone, password: this.password });
        uni.navigateTo({ url: "/src/pages/collect/index" });
      } catch (error) {
        this.error = error.message || "登录失败";
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
.page {
  padding: 48rpx 32rpx;
}
.title {
  font-size: 40rpx;
  font-weight: 600;
  margin-bottom: 40rpx;
}
.input {
  height: 88rpx;
  margin-bottom: 24rpx;
  padding: 0 24rpx;
  border: 1px solid #c8d1c7;
  border-radius: 8rpx;
  background: #fff;
}
.primary {
  background: #216b4e;
  color: #fff;
}
.error {
  display: block;
  margin-top: 20rpx;
  color: #b42318;
}
</style>
