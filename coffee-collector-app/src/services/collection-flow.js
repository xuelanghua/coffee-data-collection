export const DEVICE_FIELD_DEFINITIONS = [
  ["wind_speed", "风速"],
  ["wind_direction", "风向"],
  ["air_temperature", "空气温度"],
  ["air_humidity", "空气湿度"],
  ["atmospheric_pressure", "大气压力"],
  ["rainfall", "雨量"],
  ["soil_moisture", "土壤湿度"],
  ["soil_temperature", "土壤温度"],
  ["soil_salinity", "土壤盐分"],
  ["soil_ph", "土壤 PH 值"],
];

export class FieldCollectionFlow {
  constructor({ client, draftStore = null, now = () => new Date().toISOString() }) {
    this.client = client;
    this.draftStore = draftStore;
    this.now = now;
    this.event = null;
    this.photos = [];
    this.ocrResults = [];
    this.measurementRetakes = [];
    this.deviceFields = Object.fromEntries(
      DEVICE_FIELD_DEFINITIONS.map(([code, label]) => [
        code,
        {
          code,
          label,
          value: "",
          rawValue: "",
          confidence: null,
          correctedFrom: "",
          correctionReason: "",
          sourcePhotoId: "",
          ocrResultId: "",
        },
      ]),
    );
  }

  async createServerConfirmedCollection({ taskId, plot, point, event }) {
    const plotResult = await this.client.createPlot({
      task_id: taskId,
      plot_id: plot.plotId,
      name: plot.name,
      boundary_geojson: plot.boundaryGeojson,
      area_mu: plot.areaMu,
      area_calc_method: plot.areaCalcMethod || "geodesic",
      coordinate_system: plot.coordinateSystem || "gcj02",
      source_type: plot.sourceType || "app_drawn",
      idempotency_key: plot.idempotencyKey || `${event.idempotencyKey}:plot`,
    });
    const plotId = plotResult.plot_id;
    const pointResult = await this.client.createPoint({
      task_id: taskId,
      plot_id: plotId,
      point_id: point.pointId,
      longitude: point.longitude,
      latitude: point.latitude,
      altitude: point.altitude,
      coordinate_system: point.coordinateSystem || "gcj02",
      source_type: point.sourceType || "app_selected",
      idempotency_key: point.idempotencyKey || `${event.idempotencyKey}:point`,
    });
    const pointId = pointResult.point_id;
    const eventResult = await this.client.createEvent({
      task_id: taskId,
      plot_id: plotId,
      point_id: pointId,
      event_id: event.eventId,
      idempotency_key: event.idempotencyKey,
      manifest_hash: event.manifestHash || "draft",
      location_snapshot: event.locationSnapshot || {},
      weather_snapshot: event.weatherSnapshot || {},
    });
    const eventId = eventResult.event_id;
    this.event = {
      taskId,
      plotId,
      pointId,
      eventId,
      idempotencyKey: event.idempotencyKey,
      manifestHash: event.manifestHash || "draft",
    };
    const confirmed = { taskId, plotId, pointId, eventId };
    await this.draftStore?.saveDraft?.({
      ...confirmed,
      status: "draft",
      idempotencyKey: event.idempotencyKey,
      manifestHash: this.event.manifestHash,
    });
    return confirmed;
  }

  async startEvent({ taskId, plotId, pointId, eventId, idempotencyKey, locationSnapshot = {}, weatherSnapshot = {} }) {
    this.event = {
      taskId,
      plotId,
      pointId,
      eventId,
      idempotencyKey,
      manifestHash: "draft",
    };
    return this.client.createEvent({
      task_id: taskId,
      plot_id: plotId,
      point_id: pointId,
      event_id: eventId,
      idempotency_key: idempotencyKey,
      manifest_hash: "draft",
      location_snapshot: locationSnapshot,
      weather_snapshot: weatherSnapshot,
    });
  }

  async applyOcrResult({ eventId, photoId, provider }) {
    const result = await this.client.runOcr(eventId, {
      photo_id: photoId,
      provider,
      structured_json: {},
    });
    this.ocrResults.push(result);
    for (const [fieldCode] of DEVICE_FIELD_DEFINITIONS) {
      const recognized = result.structured_json?.[fieldCode];
      if (!recognized) continue;
      const field = this.deviceFields[fieldCode];
      field.value = String(recognized.value ?? "");
      field.rawValue = field.value;
      field.confidence = recognized.confidence ?? null;
      field.sourcePhotoId = photoId;
      field.ocrResultId = result.ocr_result_id;
    }
    return result;
  }

  correctDeviceField(fieldCode, value, reason = "") {
    const field = this.deviceFields[fieldCode];
    if (!field) {
      throw new Error(`Unknown device field: ${fieldCode}`);
    }
    if (!field.correctedFrom && field.rawValue && String(value) !== field.rawValue) {
      field.correctedFrom = field.rawValue;
    }
    field.value = String(value);
    field.correctionReason = reason;
  }

  recordMeasurementRetake({ reason, values }) {
    this.measurementRetakes.push({
      reason,
      values: Object.fromEntries(
        DEVICE_FIELD_DEFINITIONS.map(([code]) => [
          code,
          (values?.[code] ?? this.deviceFields[code].value) || null,
        ]),
      ),
    });
  }

  buildSubmitPayload() {
    if (!this.event) {
      throw new Error("Event has not been started");
    }
    const fieldValues = Object.values(this.deviceFields)
      .filter((field) => field.value !== "")
      .map((field) => ({
        field_code: field.code,
        field_label: field.label,
        value_text: field.value,
        value_number: numericOrNull(field.value),
        source_type: field.ocrResultId ? "ocr" : "manual",
        source_photo_id: field.sourcePhotoId,
        ocr_result_id: field.ocrResultId,
        ocr_raw_value: field.rawValue,
        ocr_confidence: field.confidence,
        corrected_from: field.correctedFrom,
        correction_reason: field.correctionReason,
      }));
    const baseMeasurement = {
      client_measurement_id: "MEASURE-001",
      device_no: "ENV-001",
      measured_at: this.now(),
      ...Object.fromEntries(
        DEVICE_FIELD_DEFINITIONS.map(([code]) => [code, this.deviceFields[code].value || null]),
      ),
      source_photo_id: fieldValues[0]?.source_photo_id || "",
      ocr_result_id: fieldValues[0]?.ocr_result_id || "",
      is_abnormal: this.measurementRetakes.length > 0,
      remark: this.measurementRetakes[0]?.reason || "",
    };
    const measurements = [
      baseMeasurement,
      ...this.measurementRetakes.map((retake, index) => ({
        client_measurement_id: `MEASURE-001-RETAKE-${String(index + 1).padStart(3, "0")}`,
        retake_of_client_id: "MEASURE-001",
        device_no: "ENV-001",
        measured_at: this.now(),
        ...retake.values,
        source_photo_id: fieldValues[0]?.source_photo_id || "",
        ocr_result_id: fieldValues[0]?.ocr_result_id || "",
        is_abnormal: false,
        remark: "复测通过",
      })),
    ];
    return {
      idempotency_key: this.event.idempotencyKey,
      manifest: {
        event_id: this.event.eventId,
        plot_id: this.event.plotId,
        point_id: this.event.pointId,
        manifest_hash: this.event.manifestHash,
      },
      field_values: fieldValues,
      measurements,
      ocr_corrections: fieldValues
        .filter((field) => field.corrected_from)
        .map((field) => ({
          field_name: field.field_code,
          raw_value: field.corrected_from,
          corrected_value: field.value_text,
          reason: field.correction_reason,
        })),
    };
  }
}

function numericOrNull(value) {
  if (value === "" || value === null || value === undefined) return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}
