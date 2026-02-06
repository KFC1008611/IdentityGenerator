"""Edge-case tests for china_data helper branches."""

import identity_gen.china_data as cd


def test_load_json_data_file_not_found(monkeypatch) -> None:
    def fake_open(*_args, **_kwargs):
        raise FileNotFoundError

    monkeypatch.setattr("builtins.open", fake_open)
    assert cd._load_json_data("x.json") == {}


def test_get_area_code_by_address_found_and_default(monkeypatch) -> None:
    monkeypatch.setattr(cd, "PROVINCES", {"11": "北京市"})
    monkeypatch.setattr(cd, "CITIES", {"11": {"01": "北京市"}})
    monkeypatch.setattr(cd.random, "randint", lambda *_: 5)
    assert cd.get_area_code_by_address("北京市") == "110105"
    assert cd.get_area_code_by_address("不存在") == "110101"


def test_weighted_surname_branches(monkeypatch) -> None:
    monkeypatch.setattr(cd, "SURNAMES", ["王", "李", "张"])
    monkeypatch.setattr(cd, "SURNAME_WEIGHTS", [0.7])
    monkeypatch.setattr(cd.random, "choices", lambda names, weights: [names[0]])
    assert cd.get_weighted_surname() == "王"

    monkeypatch.setattr(cd, "SURNAME_WEIGHTS", [])
    monkeypatch.setattr(cd.random, "choice", lambda names: names[-1])
    assert cd.get_weighted_surname() == "张"

    monkeypatch.setattr(cd, "SURNAME_WEIGHTS", [0.7, 0.2, 0.1, 0.05])
    monkeypatch.setattr(cd.random, "choices", lambda names, weights: [names[1]])
    assert cd.get_weighted_surname() == "李"


def test_random_ethnicity_and_defaults(monkeypatch) -> None:
    monkeypatch.setattr(cd, "ETHNICITIES", [{"name": "汉族", "population_ratio": 0.0}])
    monkeypatch.setattr(cd.random, "uniform", lambda *_: 9.9)
    assert cd.get_random_ethnicity() == "汉族"


def test_random_education_and_political_status_defaults(monkeypatch) -> None:
    monkeypatch.setattr(cd, "EDUCATION_LEVELS", [])
    assert cd.get_random_education(age=10)[0] == "初中"

    monkeypatch.setattr(cd, "POLITICAL_STATUSES", [])
    assert cd.get_random_political_status(age=10) == "群众"

    monkeypatch.setattr(
        cd,
        "POLITICAL_STATUSES",
        [{"status": "党员", "min_age": 18, "max_age": 60, "probability": 1.0}],
    )
    monkeypatch.setattr(cd.random, "uniform", lambda *_: 9.9)
    assert cd.get_random_political_status(age=30) == "群众"


def test_random_marital_status_and_qq_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        cd,
        "MARITAL_STATUSES",
        [
            {"status": "未婚", "probability_by_age": {"18-22": 1.0}},
            {"status": "已婚", "probability_by_age": {"23-40": 1.0}},
        ],
    )
    monkeypatch.setattr(cd.random, "uniform", lambda *_: 0.1)
    assert cd.get_random_marital_status(age=99) in {"未婚", "已婚"}

    monkeypatch.setattr(cd.random, "uniform", lambda *_: 9.9)
    assert cd.get_random_marital_status(age=30) == "未婚"


def test_random_blood_type_negative_suffix(monkeypatch) -> None:
    monkeypatch.setattr(cd, "BLOOD_TYPES", [{"type": "A型", "probability": 1.0}])
    monkeypatch.setattr(
        cd,
        "_BLOOD_TYPE_RULES",
        {
            "rh_negative_probability": 1.0,
            "rh_negative_suffix": "(RH阴性)",
            "rh_positive_suffix": "(RH阳性)",
            "default_type": "O型",
        },
    )
    monkeypatch.setattr(cd.random, "uniform", lambda *_: 0.0)
    monkeypatch.setattr(cd.random, "random", lambda: 0.0)
    assert cd.get_random_blood_type().endswith("(RH阴性)")

    monkeypatch.setattr(cd, "_QQ_RULES", {"length_weights": [(10, 1)], "ranges": {}})
    monkeypatch.setattr(cd.random, "choices", lambda lengths, weights: [10])
    monkeypatch.setattr(cd.random, "randint", lambda a, b: a)
    assert cd.generate_qq_number() == str(10**9)
