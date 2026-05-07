const cars = [
  {
    id: "su7-blue",
    brand: "小米",
    model: "SU7",
    fullName: "小米汽车 SU7",
    color: "海湾蓝",
    type: "轿车",
    seats: 5,
    distance: "10.4km",
    plate: "湘 A •••• 29",
    gearbox: "自动挡",
    energy: "纯电动",
    price: 197,
    detailPrice: 500,
    image: "/assets/car-blue.jpg",
    hero: "/assets/detail-main.jpg"
  },
  {
    id: "su7-white",
    brand: "小米",
    model: "SU7",
    fullName: "小米汽车 SU7",
    color: "珍珠白",
    type: "轿车",
    seats: 5,
    distance: "12.8km",
    plate: "琼 B •••• 18",
    gearbox: "自动挡",
    energy: "纯电动",
    price: 197,
    detailPrice: 500,
    image: "/assets/car-white.jpg",
    hero: "/assets/detail-main.jpg"
  }
];

const order = {
  no: "YC20250717125645",
  status: "待支付",
  renter: "张三",
  phone: "19578012123",
  pickupDate: "7月18日",
  pickupTime: "09:30",
  returnDate: "7月18日",
  returnTime: "09:30",
  duration: "2 天 13 小时",
  pickupAddress: "三亚市海棠湾xxxx酒店",
  returnAddress: "三亚市凤凰机场",
  rentFee: 1000,
  serviceFee: 100,
  total: 1100,
  deposit: 8000,
  violationDeposit: 3000
};

const categories = ["租车", "游艇", "别墅", "水上项目", "特产"];
const brands = ["阿尔法罗密欧", "小米SU7", "奔驰E", "大众", "保时捷", "奥迪", "宝马", "特斯拉"];
const brandItems = brands.map((name) => ({ name, short: name.slice(0, 1) }));

module.exports = {
  cars,
  order,
  categories,
  brands,
  brandItems
};
