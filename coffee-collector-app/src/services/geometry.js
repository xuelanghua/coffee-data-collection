const EARTH_RADIUS_METERS = 6378137;
const SQUARE_METERS_PER_MU = 666.6666667;

export function createPlotGeoJson(points) {
  const normalized = normalizePolygonPoints(points);
  return {
    type: "Polygon",
    coordinates: [normalized.map((point) => [point.longitude, point.latitude])],
  };
}

export function calculatePolygonAreaMu(points) {
  const normalized = normalizePolygonPoints(points);
  if (normalized.length < 4) {
    return 0;
  }
  const origin = normalized[0];
  const projected = normalized.map((point) => projectToLocalMeters(point, origin));
  let doubleArea = 0;
  for (let index = 0; index < projected.length - 1; index += 1) {
    const current = projected[index];
    const next = projected[index + 1];
    doubleArea += current.x * next.y - next.x * current.y;
  }
  const squareMeters = Math.abs(doubleArea) / 2;
  return round(squareMeters / SQUARE_METERS_PER_MU, 4);
}

export function normalizePolygonPoints(points) {
  if (!Array.isArray(points)) {
    throw new Error("Polygon points must be an array");
  }
  const normalized = points.map(normalizePoint);
  if (normalized.length < 3) {
    throw new Error("A field plot polygon requires at least 3 points");
  }
  const first = normalized[0];
  const last = normalized.at(-1);
  if (first.longitude !== last.longitude || first.latitude !== last.latitude) {
    normalized.push({ ...first });
  }
  return normalized;
}

function normalizePoint(point) {
  const longitude = Number(point.longitude);
  const latitude = Number(point.latitude);
  if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) {
    throw new Error("Polygon point longitude and latitude are required");
  }
  return { longitude, latitude };
}

function projectToLocalMeters(point, origin) {
  const latitudeRadians = degreesToRadians(origin.latitude);
  return {
    x: degreesToRadians(point.longitude - origin.longitude) * EARTH_RADIUS_METERS * Math.cos(latitudeRadians),
    y: degreesToRadians(point.latitude - origin.latitude) * EARTH_RADIUS_METERS,
  };
}

function degreesToRadians(value) {
  return (value * Math.PI) / 180;
}

function round(value, precision) {
  const factor = 10 ** precision;
  return Math.round(value * factor) / factor;
}
