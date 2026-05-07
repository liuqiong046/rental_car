const { getStoredCity } = require("./city");
const { request } = require("./request");

const DAY_MS = 24 * 60 * 60 * 1000;

function fetchAvailableVehicles(filters) {
  const city = getStoredCity();
  const params = Object.assign({}, filters || {}, city && city.city_code ? { city_code: city.city_code } : {});
  const query = buildQuery(params);
  return request({ url: `/api/v1/vehicles${query}` }).then((response) => response.items || []);
}

function fetchVehicleDetail(vehicleId) {
  return request({ url: `/api/v1/vehicles/${vehicleId}` });
}

function toMiniVehicle(item, index) {
  const price = item.today_price ? item.today_price.customer_price : 0;
  const calendar = (item.price_calendar || []).map(toCalendarDay);
  const sourceLabel = sourceText(item.source);
  const storeName = "三亚运营中心";
  const storeAddress = item.source === "dealer" ? "三亚凤凰机场合作门店" : "海棠湾海岸大道 88 号";
  const distanceKm = item.source === "dealer" ? "12.8" : "10.4";
  return {
    id: item.vehicle_id,
    key: `${item.vehicle_id}-${index}`,
    brand: item.model.brand,
    model: item.model.series,
    fullName: item.model.model_name,
    color: item.color,
    type: item.model.vehicle_type,
    seats: item.model.seats,
    distance: `${distanceKm}km`,
    plate: item.plate_mask,
    gearbox: item.model.gearbox,
    energy: item.model.energy_type,
    price,
    detailPrice: price,
    image: item.image_url,
    hero: item.image_url || "/assets/detail-main.jpg",
    source: item.source,
    mileage: `${item.mileage_km}km`,
    dailyMileageLimit: `${item.daily_mileage_limit}km`,
    deposit: item.model.deposit_amount,
    violationDeposit: item.model.violation_deposit_amount,
    calendar,
    storeName,
    storeAddress,
    distanceKm,
    sourceLabel,
    previewImages: buildPreviewImages(item.image_url),
    highlights: buildHighlights(item),
    bookingNotes: buildBookingNotes(item),
    supportText: "支持 24 小时客服、送车上门和门店自取",
    modelYear: String(item.model.year)
  };
}

function getStoredTrip() {
  const stored = wx.getStorageSync("rental_trip");
  if (stored && stored.pickup_at && stored.return_at) return withTripText(stored);
  return createDefaultTrip();
}

function setStoredTrip(trip) {
  const nextTrip = withTripText(trip);
  wx.setStorageSync("rental_trip", {
    pickup_at: nextTrip.pickup_at,
    return_at: nextTrip.return_at
  });
  return nextTrip;
}

function createDefaultTrip() {
  const pickup = new Date(Date.now() + 60 * 60 * 1000);
  pickup.setMinutes(0, 0, 0);
  const returnTime = new Date(pickup.getTime() + 2 * DAY_MS);
  return setStoredTrip({
    pickup_at: toIsoLocal(pickup),
    return_at: toIsoLocal(returnTime)
  });
}

function updateTripDate(trip, field, value) {
  const pickup = parseLocal(trip.pickup_at);
  const returnTime = parseLocal(trip.return_at);
  const target = field === "pickup" ? pickup : returnTime;
  const parts = value.split("-").map(Number);
  target.setFullYear(parts[0], parts[1] - 1, parts[2]);
  if (returnTime <= pickup) returnTime.setTime(pickup.getTime() + DAY_MS);
  return setStoredTrip({
    pickup_at: toIsoLocal(pickup),
    return_at: toIsoLocal(returnTime)
  });
}

function updateTripTime(trip, field, value) {
  const pickup = parseLocal(trip.pickup_at);
  const returnTime = parseLocal(trip.return_at);
  const target = field === "pickup" ? pickup : returnTime;
  const parts = value.split(":").map(Number);
  target.setHours(parts[0], parts[1], 0, 0);
  if (returnTime <= pickup) returnTime.setTime(pickup.getTime() + DAY_MS);
  return setStoredTrip({
    pickup_at: toIsoLocal(pickup),
    return_at: toIsoLocal(returnTime)
  });
}

function withTripText(trip) {
  const pickup = parseLocal(trip.pickup_at);
  const returnTime = parseLocal(trip.return_at);
  return Object.assign({}, trip, {
    pickupDate: toDateInput(pickup),
    pickupTime: toTimeInput(pickup),
    returnDate: toDateInput(returnTime),
    returnTime: toTimeInput(returnTime),
    pickupDateText: formatMonthDay(pickup),
    pickupTimeText: `${weekText(pickup)} ${toTimeInput(pickup)}`,
    returnDateText: formatMonthDay(returnTime),
    returnTimeText: `${weekText(returnTime)} ${toTimeInput(returnTime)}`,
    durationDays: Math.max(1, Math.ceil((returnTime - pickup) / DAY_MS))
  });
}

function toCalendarDay(item) {
  const date = parseLocal(`${item.date}T00:00:00`);
  const isFullDay = (item.available_periods || []).indexOf("00:00-24:00") >= 0;
  return {
    date: item.date,
    day: String(date.getDate()),
    week: weekText(date).replace("周", ""),
    price: item.customer_price,
    status: item.rentable ? (isFullDay ? "full" : "partial") : "off",
    statusText: item.rentable ? (isFullDay ? "全天可租" : "部分时段") : "不可租"
  };
}

function buildPreviewImages(imageUrl) {
  return [
    imageUrl || "/assets/detail-main.jpg",
    "/assets/detail-thumb-1.jpg",
    "/assets/detail-thumb-2.jpg",
    "/assets/detail-thumb-3.jpg",
    "/assets/detail-thumb-4.jpg"
  ];
}

function buildHighlights(item) {
  return [
    `${item.model.energy_type} ${item.model.gearbox}`,
    `${item.daily_mileage_limit}km/日限里程`,
    `${item.model.seats} 座舒适出行`,
    item.source === "dealer" ? "合作车行即时确认" : "运营中心直营保障"
  ];
}

function buildBookingNotes(item) {
  return [
    "取车需携带本人身份证和驾驶证原件",
    "默认按价格日历快照计费，临近节假日请尽早下单",
    item.source === "dealer" ? "合作车行车辆接单后会短信同步门店信息" : "直营车辆支持门店自取和上门送车",
    "违章押金和车辆押金在取车前线下或免押流程处理"
  ];
}

function buildQuery(params) {
  const pairs = Object.keys(params)
    .filter((key) => params[key] !== undefined && params[key] !== null && params[key] !== "")
    .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`);
  return pairs.length ? `?${pairs.join("&")}` : "";
}

function parseLocal(value) {
  return new Date(value.replace(/-/g, "/"));
}

function toIsoLocal(date) {
  return `${toDateInput(date)}T${toTimeInput(date)}:00`;
}

function toDateInput(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function toTimeInput(date) {
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function formatMonthDay(date) {
  return `${date.getMonth() + 1}月${date.getDate()}日`;
}

function weekText(date) {
  return ["周日", "周一", "周二", "周三", "周四", "周五", "周六"][date.getDay()];
}

function pad(value) {
  return String(value).padStart(2, "0");
}

module.exports = {
  fetchAvailableVehicles,
  fetchVehicleDetail,
  getStoredTrip,
  sourceText,
  setStoredTrip,
  toMiniVehicle,
  updateTripDate,
  updateTripTime
};

function sourceText(source) {
  const dict = {
    operation_owned: "运营中心自有",
    hosted: "托管车辆",
    dealer: "合作车行"
  };
  return dict[source] || "运营车辆";
}
