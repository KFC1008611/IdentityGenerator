"""Chinese administrative divisions data (国家统计局行政区划代码).

Contains complete province-city-district mappings for realistic address generation.
数据来源: 国家统计局行政区划代码 (最新)
"""

import json
import os
from typing import Dict, List, Tuple, Any
import random


def _load_json_data(filename: str) -> Any:
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    json_path = os.path.join(data_dir, filename)
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {} if filename.endswith(".json") else []


def _load_area_codes() -> Dict[str, Dict[str, str]]:
    """Load area codes from JSON file."""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    json_path = os.path.join(data_dir, "area_codes.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


AREA_CODES = _load_area_codes()

_name_data = _load_json_data("names.json")
SURNAMES: List[str] = _name_data.get("surnames", [])
# Weighted surnames based on 2020 China census data
# Top 5: 王(7.21%), 李(7.18%), 张(6.74%), 刘(5.38%), 陈(4.53%)
SURNAME_WEIGHTS: List[float] = _name_data.get(
    "surname_weights",
    [],
)
MALE_NAMES: List[str] = _name_data.get("male_names", [])
FEMALE_NAMES: List[str] = _name_data.get("female_names", [])

_job_data = _load_json_data("jobs.json")
JOBS: List[Dict[str, Any]] = _job_data.get("jobs", [])
JOB_TITLES: List[str] = [job["title"] for job in JOBS]

_company_data = _load_json_data("companies.json")
COMPANY_TYPES: List[str] = _company_data.get("company_types", [])
COMPANY_NAME_WORDS: List[str] = _company_data.get("company_name_words", [])

_ethnicity_data = _load_json_data("ethnicities.json")
ETHNICITIES: List[Dict[str, Any]] = _ethnicity_data.get("ethnicities", [])

_education_data = _load_json_data("education.json")
EDUCATION_LEVELS: List[Dict[str, Any]] = _education_data.get("education_levels", [])
MAJORS: List[str] = _education_data.get("majors", [])

_political_data = _load_json_data("political.json")
POLITICAL_STATUSES: List[Dict[str, Any]] = _political_data.get("political_statuses", [])
POLITICAL_ABBREVIATIONS: Dict[str, str] = _political_data.get("party_abbreviations", {})

_marital_data = _load_json_data("marital.json")
MARITAL_STATUSES: List[Dict[str, Any]] = _marital_data.get("marital_statuses", [])

_medical_data = _load_json_data("medical.json")
BLOOD_TYPES: List[Dict[str, Any]] = _medical_data.get("blood_types", [])


_geo_data = _load_json_data("geo_data.json")
PROVINCES: Dict[str, str] = _geo_data.get("provinces", {})
CITIES: Dict[str, Dict[str, str]] = _geo_data.get("cities", {})
DISTRICTS: Dict[str, List[str]] = _geo_data.get("districts", {})
STREET_NAMES: List[str] = _geo_data.get("street_names", [])
BUILDING_NAMES: List[str] = _geo_data.get("building_names", [])

_generation_rules = _load_json_data("generation_rules.json")
_china_rules = _generation_rules.get("china_data", {})
_ADDRESS_RULES: Dict[str, Any] = _china_rules.get("address", {})
_STREET_NUMBER_RULES: Dict[str, Any] = _china_rules.get("street_number", {})
_EDUCATION_RULES: Dict[str, Any] = _china_rules.get("education", {})
_BLOOD_TYPE_RULES: Dict[str, Any] = _china_rules.get("blood_type", {})
_HEIGHT_RULES: Dict[str, Dict[str, Any]] = _china_rules.get("height", {})
_WEIGHT_RULES: Dict[str, Any] = _china_rules.get("weight", {})
_BANK_CARD_RULES: Dict[str, Any] = _china_rules.get("bank_card", {})
_WECHAT_RULES: Dict[str, Any] = _china_rules.get("wechat", {})
_QQ_RULES: Dict[str, Any] = _china_rules.get("qq", {})
_LICENSE_PLATE_RULES: Dict[str, Any] = _china_rules.get("license_plate", {})


# 门牌号格式
def generate_street_number() -> str:
    """Generate realistic Chinese street number."""
    number_range = _STREET_NUMBER_RULES.get("number_range", [1, 999])
    unit_range = _STREET_NUMBER_RULES.get("unit_range", [1, 20])
    room_range = _STREET_NUMBER_RULES.get("room_range", [101, 2500])
    building_range = _STREET_NUMBER_RULES.get("building_range", [1, 30])
    building_unit_range = _STREET_NUMBER_RULES.get("building_unit_range", [1, 4])
    unit_probability = _STREET_NUMBER_RULES.get("unit_probability", 0.3)
    building_probability = _STREET_NUMBER_RULES.get("building_probability", 0.5)

    num = random.randint(number_range[0], number_range[1])
    if random.random() < unit_probability:
        unit = random.randint(unit_range[0], unit_range[1])
        room = random.randint(room_range[0], room_range[1])
        return f"{num}号{unit}单元{room}室"
    elif random.random() < building_probability:
        building = random.randint(building_range[0], building_range[1])
        unit = random.randint(building_unit_range[0], building_unit_range[1])
        room = random.randint(room_range[0], room_range[1])
        return f"{num}号{building}栋{unit}单元{room}室"
    else:
        return f"{num}号"


def get_random_address() -> Tuple[str, str, str, str, str, str]:
    """Generate a complete Chinese address.

    Returns:
        Tuple of (province, city, district, street, full_address, area_code)
    """
    province_code = random.choice(list(PROVINCES.keys()))
    province_name = PROVINCES[province_code]

    if province_code in CITIES:
        city_code = random.choice(list(CITIES[province_code].keys()))
        city_name = CITIES[province_code][city_code]
    else:
        city_name = province_name
        city_code = _ADDRESS_RULES.get("default_city_code", "01")

    full_code = province_code + city_code

    district = _ADDRESS_RULES.get("default_district", "市辖区")
    area_code = ""
    if full_code in DISTRICTS:
        district = random.choice(DISTRICTS[full_code])
        if full_code in AREA_CODES and district in AREA_CODES[full_code]:
            area_code = AREA_CODES[full_code][district]

    if not area_code:
        area_code = f"{full_code}{_ADDRESS_RULES.get('default_city_code', '01')}"

    street = random.choice(STREET_NAMES)
    street_number = generate_street_number()

    municipalities = _ADDRESS_RULES.get("municipalities", [])
    if province_name in municipalities:
        full_address = f"{province_name}{district}{street}{street_number}"
    else:
        full_address = f"{province_name}{city_name}{district}{street}{street_number}"

    return province_name, city_name, district, street, full_address, area_code


def get_area_code_by_address(city_name: str, district: str = "") -> str:
    """Get area code for ID card based on city and district.

    Args:
        city_name: City name like "北京市"
        district: District name like "朝阳区"

    Returns:
        6-digit area code
    """
    # 查找省份和城市代码
    for prov_code, prov_name in PROVINCES.items():
        if prov_code in CITIES:
            for city_code, c_name in CITIES[prov_code].items():
                if c_name == city_name:
                    # 返回前4位 + 随机2位 (模拟区县代码，01-99)
                    district_code = str(random.randint(1, 99)).zfill(2)
                    return f"{prov_code}{city_code}{district_code}"

    # 默认返回北京东城区
    return _ADDRESS_RULES.get("default_area_code", "110101")


def get_weighted_surname() -> str:
    """Select a surname using weighted random choice based on real frequency data.

    Uses 2020 China census data where the top 5 surnames (王, 李, 张, 刘, 陈)
    account for approximately 30.8% of the population, and the top 100 surnames
    cover about 85% of the population.

    Returns:
        A randomly selected surname with probability matching real-world distribution.
    """
    n_surnames = len(SURNAMES)
    n_weights = len(SURNAME_WEIGHTS)

    if n_weights > 0 and n_surnames > 0:
        # Extend weights if needed: remaining surnames get exponentially smaller weights
        if n_weights < n_surnames:
            weights = list(SURNAME_WEIGHTS)
            # Remaining surnames (after top 100) share 1% with exponential decay
            remaining = n_surnames - n_weights
            if remaining > 0:
                # Exponential decay for less common surnames
                tail_weights = [0.0005 * (0.98**i) for i in range(remaining)]
                weights.extend(tail_weights)
        else:
            weights = SURNAME_WEIGHTS[:n_surnames]

        return random.choices(SURNAMES, weights=weights)[0]

    return random.choice(SURNAMES)


def get_random_ethnicity() -> str:
    """Generate a random Chinese ethnicity based on population ratios."""
    total = sum(e.get("population_ratio", 0.01) for e in ETHNICITIES)
    r = random.uniform(0, total)
    cumulative = 0
    for ethnicity in ETHNICITIES:
        cumulative += ethnicity.get("population_ratio", 0.01)
        if r <= cumulative:
            return ethnicity["name"]
    return "汉族"


def get_random_education(age: int = 30) -> tuple[str, str]:
    """Generate random education level and major based on age.

    Args:
        age: Person's age

    Returns:
        Tuple of (education_level, major)
    """
    valid_educations = [
        e
        for e in EDUCATION_LEVELS
        if e.get("min_age", 18) <= age <= e.get("max_age", 100)
    ]

    if not valid_educations:
        return _EDUCATION_RULES.get("default_level", "初中"), ""

    total = sum(e.get("probability", 0.1) for e in valid_educations)
    r = random.uniform(0, total)
    cumulative = 0
    education = valid_educations[0]
    for e in valid_educations:
        cumulative += e.get("probability", 0.1)
        if r <= cumulative:
            education = e
            break

    level = education["level"]

    major = ""
    major_levels = _EDUCATION_RULES.get(
        "major_levels", ["大专", "本科", "硕士研究生", "博士研究生"]
    )
    if level in major_levels and MAJORS:
        major = random.choice(MAJORS)

    return level, major


def get_random_political_status(age: int = 30) -> str:
    """Generate random political status based on age."""
    valid_statuses = [
        s
        for s in POLITICAL_STATUSES
        if s.get("min_age", 18) <= age <= s.get("max_age", 100)
    ]

    if not valid_statuses:
        return "群众"

    total = sum(s.get("probability", 0.1) for s in valid_statuses)
    r = random.uniform(0, total)
    cumulative = 0
    for status in valid_statuses:
        cumulative += status.get("probability", 0.1)
        if r <= cumulative:
            return status["status"]
    return "群众"


def get_random_marital_status(age: int = 30) -> str:
    """Generate random marital status based on age."""
    age_range = ""
    age_keys: List[str] = []
    for status in MARITAL_STATUSES:
        prob_map = status.get("probability_by_age", {})
        for key in prob_map.keys():
            if key not in age_keys:
                age_keys.append(key)
    age_keys.sort(key=lambda x: int(x.split("-")[0]))

    for range_key in age_keys:
        min_age, max_age = map(int, range_key.split("-"))
        if min_age <= age <= max_age:
            age_range = range_key
            break

    if not age_range:
        age_range = age_keys[-1] if age_keys else "50-100"

    probabilities = []
    for status in MARITAL_STATUSES:
        prob_map = status.get("probability_by_age", {})
        prob = prob_map.get(age_range, 0.1)
        probabilities.append((status["status"], prob))

    total = sum(p[1] for p in probabilities)
    r = random.uniform(0, total)
    cumulative = 0
    for status, prob in probabilities:
        cumulative += prob
        if r <= cumulative:
            return status
    return "未婚"


def get_random_blood_type() -> str:
    """Generate random blood type with RH factor."""
    total = sum(b.get("probability", 0.25) for b in BLOOD_TYPES)
    r = random.uniform(0, total)
    cumulative = 0
    blood_type = _BLOOD_TYPE_RULES.get("default_type", "O型")
    for bt in BLOOD_TYPES:
        cumulative += bt.get("probability", 0.25)
        if r <= cumulative:
            blood_type = bt["type"]
            break

    if random.random() < _BLOOD_TYPE_RULES.get("rh_negative_probability", 0.005):
        blood_type += _BLOOD_TYPE_RULES.get("rh_negative_suffix", "(RH阴性)")
    else:
        blood_type += _BLOOD_TYPE_RULES.get("rh_positive_suffix", "(RH阳性)")

    return blood_type


def generate_height(gender: str = "male") -> int:
    """Generate realistic height in cm based on gender.

    Args:
        gender: "male" or "female"

    Returns:
        Height in centimeters
    """
    profile_key = "male" if gender == "male" else "female"
    profile = _HEIGHT_RULES.get(profile_key, {})
    mean = profile.get("mean", 169 if profile_key == "male" else 158)
    std = profile.get("std", 6 if profile_key == "male" else 5)
    min_h = profile.get("min", 155 if profile_key == "male" else 145)
    max_h = profile.get("max", 195 if profile_key == "male" else 180)
    height = int(random.gauss(mean, std))
    return max(min_h, min(max_h, height))


def generate_weight(height: int, gender: str = "male") -> int:
    """Generate realistic weight in kg based on height and gender.

    Args:
        height: Height in cm
        gender: "male" or "female"

    Returns:
        Weight in kilograms
    """
    # BMI = weight(kg) / height(m)^2
    # 正常BMI范围 18.5 - 24
    height_m = height / 100
    min_bmi = _WEIGHT_RULES.get("min_bmi", 18.5)
    max_bmi = _WEIGHT_RULES.get("max_bmi", 26.0)

    # 男性BMI略高
    if gender == "male":
        min_bmi += _WEIGHT_RULES.get("male_adjust_min", 0.5)
        max_bmi += _WEIGHT_RULES.get("male_adjust_max", 1.0)

    min_weight = int(min_bmi * height_m * height_m)
    max_weight = int(max_bmi * height_m * height_m)

    return random.randint(min_weight, max_weight)


def generate_bank_card() -> str:
    """Generate a valid Chinese UnionPay bank card number using Luhn algorithm."""
    bins = _BANK_CARD_RULES.get("bins", [])
    remaining_lengths = _BANK_CARD_RULES.get("remaining_lengths", [10, 11, 12])
    bin_code = random.choice(bins)

    remaining_length = random.choice(remaining_lengths)
    partial_number = bin_code + "".join(
        [str(random.randint(0, 9)) for _ in range(remaining_length - 1)]
    )

    # 使用Luhn算法计算校验位
    def luhn_checksum(card_number: str) -> int:
        digits = [int(d) for d in card_number]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(int(digit) for digit in str(d * 2))
        return (10 - checksum % 10) % 10

    check_digit = luhn_checksum(partial_number + "0")
    return partial_number + str(check_digit)


def generate_wechat_id() -> str:
    """Generate a realistic WeChat ID."""
    charset = _WECHAT_RULES.get("wxid_charset", "abcdefghijklmnopqrstuvwxyz0123456789")
    wxid_length = _WECHAT_RULES.get("wxid_length", 12)
    prefixes = _WECHAT_RULES.get("prefixes", ["wx", "we", "wei"])
    letters = _WECHAT_RULES.get("letters", list("abcdefghijklmnopqrstuvwxyz"))
    surname_prefixes = _WECHAT_RULES.get(
        "surname_prefixes",
        ["zhang", "li", "wang", "liu", "chen", "yang", "zhao", "wu", "zhou"],
    )
    adjectives = _WECHAT_RULES.get(
        "adjectives",
        [
            "happy",
            "lucky",
            "sunny",
            "cool",
            "sweet",
            "lovely",
            "nice",
            "good",
            "great",
            "super",
        ],
    )
    concepts = _WECHAT_RULES.get(
        "concepts", ["love", "life", "dream", "hope", "faith", "peace", "joy", "smile"]
    )

    patterns = [
        lambda: f"wxid_{''.join(random.choices(charset, k=wxid_length))}",
        lambda: f"{random.choice(prefixes)}{random.randint(10000000, 99999999)}",
        lambda: f"{random.choice(letters)}{random.randint(10000000, 99999999)}",
        lambda: f"{random.choice(surname_prefixes)}{random.randint(1000, 999999)}",
        lambda: f"{random.choice(adjectives)}{random.randint(1000, 999999)}",
        lambda: f"{random.choice(concepts)}{random.randint(1000, 999999)}",
    ]
    return random.choice(patterns)()


def generate_qq_number() -> str:
    """Generate a realistic QQ number."""
    length_weights = _QQ_RULES.get("length_weights", [])
    ranges = _QQ_RULES.get("ranges", {})
    lengths, weights = zip(*length_weights)
    length = random.choices(lengths, weights=weights)[0]

    range_key = str(length)
    value_range = ranges.get(range_key)
    if not value_range:
        value_range = [10 ** (int(length) - 1), (10 ** int(length)) - 1]
    return str(random.randint(value_range[0], value_range[1]))


def generate_license_plate() -> str:
    """Generate a realistic Chinese license plate number."""
    provinces = _LICENSE_PLATE_RULES.get("provinces", [])
    excluded = set(_LICENSE_PLATE_RULES.get("excluded_letters", ["I", "O"]))
    city_codes = [
        chr(i) for i in range(ord("A"), ord("Z") + 1) if chr(i) not in excluded
    ]
    plate_chars = [str(i) for i in range(10)] + city_codes
    new_energy_probability = _LICENSE_PLATE_RULES.get("new_energy_probability", 0.15)
    new_energy_types = _LICENSE_PLATE_RULES.get("new_energy_types", ["D", "F"])

    province = random.choice(provinces)
    city_code = random.choice(city_codes)

    if random.random() < new_energy_probability:
        energy_type = random.choice(new_energy_types)
        plate = "".join(random.choices(plate_chars, k=5))
        return f"{province}{city_code}{energy_type}{plate}"
    else:
        plate = "".join(random.choices(plate_chars, k=5))
        return f"{province}{city_code}{plate}"
