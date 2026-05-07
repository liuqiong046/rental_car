"""Mock WeChat Pay adapter for local and sandbox flows."""

from uuid import uuid4


def build_mock_wechat_pay_params(payment_id: str) -> dict[str, str]:
    prepay_id = f"wx_mock_{payment_id}"
    nonce = uuid4().hex[:16]
    return {
        "timeStamp": "1700000000",
        "nonceStr": nonce,
        "package": f"prepay_id={prepay_id}",
        "signType": "MOCK",
        "paySign": f"mock-sign-{payment_id[-8:]}",
    }
