<template>
  <view class="app-shell">
    <slot />
  </view>
</template>

<script>
export default {
  onLaunch() {
    console.log("Pu'er coffee collector app launched");
  },
};
</script>

<style>
.app-shell {
  min-height: 100vh;
  background: #f6f7f2;
  color: #1f2a24;
}
</style>
