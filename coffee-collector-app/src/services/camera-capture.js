import { buildPhotoWatermark } from "./watermark.js";

export class CameraCaptureAdapter {
  constructor({ chooseImage, now = () => new Date().toISOString() } = {}) {
    if (!chooseImage) {
      throw new Error("chooseImage is required");
    }
    this.chooseImage = chooseImage;
    this.now = now;
  }

  async capturePhotoDraft({
    taskId,
    plotId,
    pointId,
    eventId,
    photoId,
    category,
    collectorName,
    location = {},
  }) {
    const image = await this.chooseImage({ count: 1, sourceType: ["camera"] });
    const capturedAt = this.now();
    const watermark = buildPhotoWatermark({
      taskId,
      plotId,
      pointId,
      eventId,
      photoId,
      capturedAt,
      collectorName,
      location,
    });
    return {
      photoId,
      category,
      localPath: image.tempFilePath,
      size: image.size ?? null,
      width: image.width ?? null,
      height: image.height ?? null,
      watermark,
      metadata: {
        width: image.width ?? null,
        height: image.height ?? null,
        size: image.size ?? null,
        captured_at: capturedAt,
        location,
        watermark: watermark.metadata,
      },
    };
  }
}
