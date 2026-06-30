export function buildPhotoWatermark({
  taskId,
  plotId,
  pointId,
  eventId,
  photoId,
  capturedAt,
  collectorName,
  location = {},
}) {
  const coordinateSystem = location.coordinateSystem || "unknown";
  const coordinateText = formatCoordinate(location);
  const lines = [
    `Task: ${taskId}`,
    `Plot: ${plotId}`,
    `Point: ${pointId}`,
    `Event: ${eventId}`,
    `Photo: ${photoId}`,
    `Time: ${capturedAt}`,
    `Location: ${coordinateText} ${coordinateSystem}`,
    `Collector: ${collectorName || ""}`,
  ];
  return {
    lines,
    metadata: {
      task_id: taskId,
      plot_id: plotId,
      point_id: pointId,
      event_id: eventId,
      photo_id: photoId,
      captured_at: capturedAt,
      collector_name: collectorName || "",
      longitude: location.longitude ?? null,
      latitude: location.latitude ?? null,
      accuracy: location.accuracy ?? null,
      coordinate_system: coordinateSystem,
    },
  };
}

function formatCoordinate(location) {
  if (location.longitude === undefined || location.latitude === undefined) {
    return "unknown";
  }
  return `${location.longitude},${location.latitude}`;
}
