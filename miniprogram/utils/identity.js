const { request } = require("./request");

function fetchIdentity() {
  return request({ url: "/api/v1/identity/me" });
}

function submitIdentity(payload) {
  return request({
    url: "/api/v1/identity/submissions",
    method: "POST",
    data: payload
  });
}

function prepareIdentityAsset(payload) {
  return request({
    url: "/api/v1/identity/assets",
    method: "POST",
    data: payload
  });
}

function ensureIdentityApproved() {
  return fetchIdentity().then((identity) => {
    if (identity.status !== "approved") {
      throw new Error(identity.reject_reason || "请先完成身份认证审核");
    }
    return identity;
  });
}

module.exports = {
  ensureIdentityApproved,
  fetchIdentity,
  prepareIdentityAsset,
  submitIdentity
};
