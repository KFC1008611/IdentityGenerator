"""Extra generator branch tests for full coverage."""

from datetime import date

import identity_gen.generator as gen
from identity_gen.models import IdentityConfig


def test_generate_id_card_gender_none_branch(monkeypatch) -> None:
    monkeypatch.setattr(gen.random, "randint", lambda *_: 7)
    out = gen.generate_chinese_id_card(date(2000, 1, 2), "110101", gender=None)
    assert len(out) == 18


def test_get_zodiac_default_branch(monkeypatch) -> None:
    monkeypatch.setattr(
        gen, "_ZODIAC_RULES", {"date_ranges": [], "default_sign": "默认星座"}
    )
    assert gen.get_zodiac_sign(date(2000, 1, 1)) == "默认星座"


def test_social_credit_nondigit_branch(monkeypatch) -> None:
    monkeypatch.setattr(
        gen,
        "_SOCIAL_CREDIT_RULES",
        {
            "authority_codes": ["A"],
            "org_types": ["1"],
            "chars": "0123456789ABCDEFGHJKLMNPQRTUWXY",
            "weights": [1] * 17,
        },
    )
    monkeypatch.setattr(gen.china_data, "PROVINCES", {"11": "北京"})
    monkeypatch.setattr(gen.china_data, "CITIES", {"11": {"01": "北京"}})
    monkeypatch.setattr(gen.random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(gen.random, "randint", lambda a, b: a)
    out = gen.generate_social_credit_code()
    assert len(out) == 18


def test_generate_batch_dedup_retry_warning_branch(monkeypatch) -> None:
    config = IdentityConfig(locale="zh_CN", count=2, include_fields=["phone"])
    g = gen.IdentityGenerator(config)
    g._MAX_DEDUP_RETRIES = 1

    class _Obj:
        def __init__(self, phone):
            self.phone = phone

    seq = [_Obj("13800000000"), _Obj("13800000000"), _Obj("13800000000")]
    it = iter(seq)
    monkeypatch.setattr(g, "generate", lambda: next(it))
    out = g.generate_batch()
    assert len(out) == 2
