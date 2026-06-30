export class CoffeeApiClient {
  constructor({ baseUrl = "", fetch = globalThis.fetch, storage = null } = {}) {
    if (!fetch) {
      throw new Error("fetch is required");
    }
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.fetch = fetch;
    this.storage = storage;
    this.token = storage?.getItem?.("coffee_token") || "";
  }

  async loginByPassword({ phone, password }) {
    const data = await this.request("/api/coffee/auth/mobile-login/", {
      method: "POST",
      body: { username: phone, password },
      auth: false,
    });
    const token = data.access || data.token || data.access_token;
    if (token) {
      this.token = token;
      this.storage?.setItem?.("coffee_token", token);
    }
    return data;
  }

  createPlot(payload) {
    return this.request("/api/coffee/app/plots/", { method: "POST", body: payload });
  }

  createPoint(payload) {
    return this.request("/api/coffee/app/points/", { method: "POST", body: payload });
  }

  createEvent(payload) {
    return this.request("/api/coffee/app/events/", { method: "POST", body: payload });
  }

  initPhoto(payload) {
    return this.request("/api/coffee/app/photos/init/", { method: "POST", body: payload });
  }

  completePhoto(photoId, payload) {
    return this.request(`/api/coffee/app/photos/${encodeURIComponent(photoId)}/complete/`, { method: "POST", body: payload });
  }

  uploadPhotoChunk(photoId, index, payload) {
    return this.request(`/api/coffee/app/photos/${encodeURIComponent(photoId)}/chunks/${encodeURIComponent(index)}/`, { method: "PUT", body: payload });
  }

  runOcr(eventId, payload) {
    return this.request(`/api/coffee/app/events/${encodeURIComponent(eventId)}/ocr/`, { method: "POST", body: payload });
  }

  listOcrResults(eventId) {
    return this.request(`/api/coffee/app/events/${encodeURIComponent(eventId)}/ocr-results/`);
  }

  saveOcrCorrection(ocrResultId, payload) {
    return this.request(`/api/coffee/app/ocr-results/${encodeURIComponent(ocrResultId)}/corrections/`, { method: "POST", body: payload });
  }

  submitEvent(eventId, payload) {
    return this.request(`/api/coffee/app/events/${encodeURIComponent(eventId)}/submit/`, { method: "POST", body: payload });
  }

  resubmitEvent(eventId, payload) {
    return this.request(`/api/coffee/app/events/${encodeURIComponent(eventId)}/resubmit/`, { method: "POST", body: payload });
  }

  async request(path, { method = "GET", body = null, auth = true } = {}) {
    const headers = { Accept: "application/json" };
    const options = { method, headers };
    if (auth && this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }
    if (body !== null) {
      headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
    const response = await this.fetch(`${this.baseUrl}${path}`, options);
    const payload = await response.json();
    if (!response.ok || (payload.code && payload.code !== 2000)) {
      const message = payload.msg || payload.message || `HTTP ${response.status}`;
      const error = new Error(message);
      error.response = payload;
      throw error;
    }
    return payload.data;
  }
}
