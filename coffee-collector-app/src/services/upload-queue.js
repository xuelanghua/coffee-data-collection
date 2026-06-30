export class UploadQueue {
  constructor({ client, now = () => new Date().toISOString() }) {
    if (!client) {
      throw new Error("client is required");
    }
    this.client = client;
    this.now = now;
    this.items = [];
    this.history = [];
    this.failedItems = [];
    this.networkState = "online";
    this.paused = false;
  }

  get pendingCount() {
    return this.items.length;
  }

  get failedCount() {
    return this.failedItems.length;
  }

  setNetworkState(state) {
    if (!["online", "offline", "weak"].includes(state)) {
      throw new Error(`Unsupported network state: ${state}`);
    }
    this.networkState = state;
    return this.diagnostics();
  }

  pause() {
    this.paused = true;
    return this.diagnostics();
  }

  resume() {
    this.paused = false;
    if (this.networkState === "offline") {
      this.networkState = "online";
    }
    return this.diagnostics();
  }

  get isPaused() {
    return this.paused || this.networkState === "offline";
  }

  enqueueCollection({ eventId, idempotencyKey, photos = [], submitPayload }) {
    for (const photo of photos) {
      this.items.push({
        type: "photo",
        eventId,
        idempotencyKey,
        photo,
        submitPayload,
        attempts: 0,
        status: "pending",
      });
      if (photo.category === "device_reading") {
        this.items.push({
          type: "ocr",
          eventId,
          photo,
          attempts: 0,
          status: "pending",
        });
      }
    }
    this.items.push({
      type: "submit",
      eventId,
      idempotencyKey,
      submitPayload,
      attempts: 0,
      status: "pending",
    });
  }

  async drain({ maxSteps = 100, stopOnError = true } = {}) {
    if (this.isPaused) {
      return {
        completed: 0,
        failed: 0,
        pending: this.items.length,
        paused: true,
        networkState: this.networkState,
        failedItems: [...this.failedItems],
        history: [...this.history],
      };
    }
    let completed = 0;
    let failed = 0;
    while (this.items.length > 0 && completed < maxSteps) {
      const item = this.items.shift();
      try {
        completed += await this.processItem(item);
      } catch (error) {
        failed += 1;
        item.status = "failed";
        item.errorMessage = error.message;
        item.failedAt = this.now();
        this.failedItems.push(item);
        if (stopOnError) {
          throw error;
        }
        break;
      }
    }
    return {
      completed,
      failed,
      pending: this.items.length,
      paused: this.isPaused,
      networkState: this.networkState,
      failedItems: [...this.failedItems],
      history: [...this.history],
    };
  }

  retryFailed() {
    const retryItems = this.failedItems.map((item) => ({
      ...item,
      status: "pending",
      errorMessage: "",
    }));
    this.failedItems = [];
    this.items.unshift(...retryItems);
  }

  async processItem(item) {
    item.attempts += 1;
    item.startedAt = this.now();
    if (item.type === "photo") {
      await this.uploadPhoto(item);
    } else if (item.type === "ocr") {
      await this.runOcr(item);
    } else if (item.type === "submit") {
      await this.submitCollection(item);
    } else {
      throw new Error(`Unknown upload queue item type: ${item.type}`);
    }
    item.status = "completed";
    item.completedAt = this.now();
    this.history.push(item);
    return item.type === "photo" ? 2 : 1;
  }

  async uploadPhoto(item) {
    const photo = item.photo;
    const initResult = await this.client.initPhoto({
      event_id: item.eventId,
      photo_id: photo.photoId,
      category: photo.category,
      sha256: photo.sha256,
      metadata: photo.metadata || {},
    });
    photo.photoId = initResult.photo_id || photo.photoId;
    photo.uploadSessionId = initResult.upload_session_id || photo.uploadSessionId;
    this.applyConfirmedPhotoId(item.submitPayload, photo);
    const chunks = photo.chunks || [];
    photo.uploadedChunks = photo.uploadedChunks || 0;
    for (let index = 0; index < chunks.length; index += 1) {
      const chunk = chunks[index];
      await this.client.uploadPhotoChunk(photo.photoId, index, {
        chunk_hash: chunk.chunkHash,
        chunk_size: chunk.chunkSize,
      });
      photo.uploadedChunks = index + 1;
    }
    await this.client.completePhoto(photo.photoId, {
      original_file: photo.originalFile,
      watermarked_file: photo.watermarkedFile,
      sha256: photo.sha256,
      precheck_status: photo.precheckStatus || "precheck_pass",
      ...(chunks.length
        ? {
            chunk_count: chunks.length,
            chunk_hashes: chunks.map((chunk) => chunk.chunkHash),
          }
        : {}),
    });
  }

  async runOcr(item) {
    await this.client.runOcr(item.eventId, {
      photo_id: item.photo.photoId,
      provider: item.photo.ocrProvider || "manual",
      structured_json: {},
    });
  }

  async submitCollection(item) {
    await this.client.submitEvent(item.eventId, {
      ...item.submitPayload,
      idempotency_key: item.submitPayload?.idempotency_key || item.idempotencyKey,
    });
  }

  applyConfirmedPhotoId(submitPayload, photo) {
    const manifestPhotos = submitPayload?.manifest?.photos;
    if (!Array.isArray(manifestPhotos) || !photo.photoId) return;
    const target = manifestPhotos.find((item) => {
      if (photo.localPhotoId && item.local_photo_id === photo.localPhotoId) return true;
      if (item.photo_id && item.photo_id === photo.photoId) return true;
      return false;
    });
    if (target) {
      target.photo_id = photo.photoId;
    }
  }

  diagnostics() {
    const photoItems = [...this.items, ...this.history, ...this.failedItems]
      .filter((item) => item.type === "photo")
      .map((item) => {
        const chunks = item.photo.chunks || [];
        return {
          eventId: item.eventId,
          photoId: item.photo.photoId,
          category: item.photo.category,
          status: item.status,
          attempts: item.attempts,
          uploadSessionId: item.photo.uploadSessionId || "",
          uploadedChunks: item.photo.uploadedChunks || 0,
          totalChunks: chunks.length,
          errorMessage: item.errorMessage || "",
        };
      });

    return {
      networkState: this.networkState,
      paused: this.isPaused,
      pendingCount: this.pendingCount,
      failedCount: this.failedCount,
      completedCount: this.history.length,
      activeUploadSessions: photoItems
        .filter((item) => item.uploadSessionId)
        .map((item) => item.uploadSessionId),
      photos: photoItems,
      failedItems: this.failedItems.map((item) => ({
        type: item.type,
        eventId: item.eventId,
        status: item.status,
        attempts: item.attempts,
        errorMessage: item.errorMessage || "",
        failedAt: item.failedAt || "",
      })),
    };
  }
}
