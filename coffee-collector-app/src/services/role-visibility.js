const APP_ENTRIES = [
  { key: "tasks", label: "任务", roles: ["coffee_collector", "coffee_reviewer", "coffee_admin", "coffee_viewer"] },
  { key: "collect", label: "采集", roles: ["coffee_collector", "coffee_admin"] },
  { key: "uploadQueue", label: "上传队列", roles: ["coffee_collector", "coffee_admin"] },
  { key: "returns", label: "退回修改", roles: ["coffee_collector", "coffee_admin"] },
  { key: "review", label: "现场审核", roles: ["coffee_reviewer", "coffee_admin"] },
  { key: "ocrCorrection", label: "OCR 校正", roles: ["coffee_reviewer", "coffee_admin"] },
  { key: "myRecords", label: "我的记录", roles: ["coffee_collector", "coffee_admin", "coffee_viewer"] },
  { key: "providerConfig", label: "Provider 配置", roles: ["coffee_admin"] },
  { key: "statistics", label: "统计", roles: ["coffee_admin", "coffee_viewer"] },
  { key: "settings", label: "设置", roles: ["coffee_collector", "coffee_reviewer", "coffee_admin", "coffee_viewer"] },
];

export function getVisibleAppEntries(roleKeys = []) {
  const roleSet = new Set(roleKeys);
  return APP_ENTRIES.filter((entry) => entry.roles.some((role) => roleSet.has(role)));
}

export { APP_ENTRIES };
