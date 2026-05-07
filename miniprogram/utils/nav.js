function go(event) {
  const url = event.currentTarget.dataset.url;
  if (!url) return;
  wx.navigateTo({ url });
}

function redirect(event) {
  const url = event.currentTarget.dataset.url;
  if (!url) return;
  wx.redirectTo({ url });
}

function getNavMetrics() {
  const systemInfo = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync();
  const statusBarHeight = systemInfo.statusBarHeight || 0;
  let menu = null;

  try {
    menu = wx.getMenuButtonBoundingClientRect ? wx.getMenuButtonBoundingClientRect() : null;
  } catch (error) {
    menu = null;
  }

  const menuTop = menu && menu.top ? menu.top : statusBarHeight + 6;
  const menuHeight = menu && menu.height ? menu.height : 32;
  const navBarHeight = (menuTop - statusBarHeight) * 2 + menuHeight;

  return {
    statusBarHeight,
    menuTop,
    menuHeight,
    menuOffset: menuTop - statusBarHeight,
    navBarHeight,
    navHeight: statusBarHeight + navBarHeight
  };
}

module.exports = {
  go,
  redirect,
  getNavMetrics
};
