import { calculatePolygonAreaMu, createPlotGeoJson } from "./geometry.js";

export class PlotDrawingSession {
  constructor({ coordinateSystem = "gcj02" } = {}) {
    this.coordinateSystem = coordinateSystem;
    this.points = [];
  }

  addPoint(point) {
    const longitude = Number(point.longitude);
    const latitude = Number(point.latitude);
    if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) {
      throw new Error("longitude and latitude are required");
    }
    this.points.push({ longitude, latitude });
    return this.snapshot();
  }

  undoPoint() {
    this.points.pop();
    return this.snapshot();
  }

  clear() {
    this.points = [];
    return this.snapshot();
  }

  snapshot() {
    const areaMu = this.points.length >= 3 ? calculatePolygonAreaMu(this.points) : 0;
    return {
      points: [...this.points],
      areaMu,
      canClose: this.points.length >= 3,
    };
  }

  buildCreatePlotPayload({ taskId, plotId, name, idempotencyKey }) {
    if (this.points.length < 3) {
      throw new Error("A plot boundary requires at least 3 points");
    }
    return {
      task_id: taskId,
      plot_id: plotId,
      name,
      boundary_geojson: createPlotGeoJson(this.points),
      area_mu: calculatePolygonAreaMu(this.points),
      area_calc_method: "local_projected",
      coordinate_system: this.coordinateSystem,
      source_type: "app_drawn",
      idempotency_key: idempotencyKey,
    };
  }
}
