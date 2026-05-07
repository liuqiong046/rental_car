const { brandItems } = require("../../utils/data");
const { go, getNavMetrics } = require("../../utils/nav");

Page({
  data: {
    nav: getNavMetrics(),
    brands: brandItems,
    hotBrands: brandItems.slice(0, 4)
  },
  go
});
