const { request } = require("./request");
const LOCAL_AVATAR_KEY = "customer_avatar_map";

function getStoredProfile() {
  return wx.getStorageSync("customer_profile") || null;
}

function getLocalAvatarMap() {
  return wx.getStorageSync(LOCAL_AVATAR_KEY) || {};
}

function decorateProfile(profile) {
  if (!profile || !profile.user_id) return profile || null;
  const avatarUrl = getLocalAvatarMap()[profile.user_id];
  return avatarUrl ? { ...profile, avatar_url: avatarUrl } : profile;
}

function persistProfile(profile) {
  const nextProfile = decorateProfile(profile);
  wx.setStorageSync("customer_profile", nextProfile);
  return nextProfile;
}

function getChannelSource() {
  return wx.getStorageSync("channel_source") || {};
}

function isLoggedIn() {
  return Boolean(wx.getStorageSync("customer_token"));
}

function buildLoginUrl(targetUrl) {
  if (!targetUrl) return "/pages/login/login";
  return `/pages/login/login?redirect=${encodeURIComponent(targetUrl)}`;
}

function requireLogin(targetUrl) {
  if (isLoggedIn()) return true;
  wx.navigateTo({ url: buildLoginUrl(targetUrl) });
  return false;
}

function sendSmsCode(phone) {
  return request({
    url: "/api/v1/auth/sms-code",
    method: "POST",
    data: { phone }
  });
}

function loginByPhone(phone, verificationCode) {
  return request({
    url: "/api/v1/auth/phone-login",
    method: "POST",
    data: {
      phone,
      verification_code: verificationCode,
      channel_source: getChannelSource()
    }
  }).then((response) => {
    wx.setStorageSync("customer_token", response.access_token);
    return persistProfile(response.user);
  });
}

function fetchProfile() {
  return request({ url: "/api/v1/users/me" }).then((profile) => {
    return persistProfile(profile);
  });
}

function updateProfile(payload) {
  return request({ url: "/api/v1/users/me", method: "PATCH", data: payload }).then((profile) => {
    return persistProfile(profile);
  });
}

function updatePhone(phone, verificationCode) {
  return request({
    url: "/api/v1/users/me/phone",
    method: "PATCH",
    data: {
      phone,
      verification_code: verificationCode
    }
  }).then((profile) => {
    return persistProfile(profile);
  });
}

function setLocalAvatar(userId, avatarUrl) {
  if (!userId) return null;
  const avatarMap = getLocalAvatarMap();
  if (avatarUrl) {
    avatarMap[userId] = avatarUrl;
  } else {
    delete avatarMap[userId];
  }
  wx.setStorageSync(LOCAL_AVATAR_KEY, avatarMap);

  const profile = getStoredProfile();
  if (!profile || profile.user_id !== userId) return null;

  const nextProfile = decorateProfile({
    ...profile,
    avatar_url: avatarUrl || ""
  });
  wx.setStorageSync("customer_profile", nextProfile);
  return nextProfile;
}

function logout() {
  return request({ url: "/api/v1/auth/logout", method: "POST" })
    .catch(() => null)
    .then(() => {
      wx.removeStorageSync("customer_token");
      wx.removeStorageSync("customer_profile");
    });
}

module.exports = {
  buildLoginUrl,
  fetchProfile,
  getStoredProfile,
  isLoggedIn,
  loginByPhone,
  logout,
  requireLogin,
  sendSmsCode,
  setLocalAvatar,
  updatePhone,
  updateProfile
};
