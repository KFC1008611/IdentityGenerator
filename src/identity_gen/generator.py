"""Enhanced Chinese identity generation logic with improved data quality and field correlations."""

import json
import logging
import os
import random
from datetime import date
from typing import Dict, List, Optional, Tuple, Any, Set, cast

from faker import Faker

from .models import Identity, IdentityConfig
from . import china_data

logger = logging.getLogger(__name__)


def _load_generation_rules() -> Dict[str, Any]:
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    rules_path = os.path.join(data_dir, "generation_rules.json")
    with open(rules_path, "r", encoding="utf-8") as f:
        return json.load(f)


_GENERATION_RULES = _load_generation_rules().get("generator", {})
_PHONE_RULES: Dict[str, Any] = _GENERATION_RULES.get("phone", {})
_EMAIL_RULES: Dict[str, Any] = _GENERATION_RULES.get("email", {})
_USERNAME_RULES: Dict[str, Any] = _GENERATION_RULES.get("username", {})
_NAME_PATTERN_RULES: Dict[str, float] = _GENERATION_RULES.get(
    "name_pattern_weights", {}
)
_ZODIAC_RULES: Dict[str, Any] = _GENERATION_RULES.get("zodiac", {})
_CHINESE_ZODIAC_RULES: Dict[str, Any] = _GENERATION_RULES.get("chinese_zodiac", {})
_SOCIAL_CREDIT_RULES: Dict[str, Any] = _GENERATION_RULES.get("social_credit", {})
_EMERGENCY_RULES: Dict[str, Any] = _GENERATION_RULES.get("emergency", {})
_HOBBY_RULES: Dict[str, Any] = _GENERATION_RULES.get("hobbies", {})
_DEFAULT_RULES: Dict[str, Any] = _GENERATION_RULES.get("defaults", {})


def calculate_chinese_id_checksum(id_17: str) -> str:
    """Calculate the last digit (checksum) of Chinese ID card using GB 11643-1999 standard."""
    if len(id_17) != 17:
        raise ValueError(f"ID prefix must be exactly 17 digits, got {len(id_17)}")
    if not id_17.isdigit():
        raise ValueError("ID prefix must contain only digits")

    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_codes = "10X98765432"

    sum_value = sum(int(id_17[i]) * weights[i] for i in range(17))
    return check_codes[sum_value % 11]


def generate_chinese_id_card(
    birthdate: date, area_code: str, gender: Optional[str] = None
) -> str:
    """Generate a valid Chinese ID card number following GB 11643-1999 standard."""
    if len(area_code) != 6 or not area_code.isdigit():
        raise ValueError("area_code must be exactly 6 digits")

    birth_str = birthdate.strftime("%Y%m%d")

    if gender == "male":
        sequence = str(random.randrange(1, 999, 2)).zfill(3)
    elif gender == "female":
        sequence = str(random.randrange(2, 999, 2)).zfill(3)
    else:
        sequence = str(random.randint(1, 999)).zfill(3)

    id_17 = area_code + birth_str + sequence
    checksum = calculate_chinese_id_checksum(id_17)

    return id_17 + checksum


def generate_chinese_phone() -> str:
    """Generate a realistic Chinese mobile phone number with carrier distribution."""
    carrier_weights = _PHONE_RULES.get("carrier_weights", {})
    carrier_types = list(carrier_weights.keys())
    carrier_probs = list(carrier_weights.values())
    prefixes = _PHONE_RULES.get("prefixes", {})
    carrier_type = random.choices(carrier_types, weights=carrier_probs, k=1)[0]
    prefix = random.choice(prefixes.get(carrier_type, prefixes.get("mobile", [])))

    suffix = "".join([str(random.randint(0, 9)) for _ in range(8)])
    return prefix + suffix


def generate_chinese_name(gender: Optional[str] = None) -> Tuple[str, str, str, str]:
    """Generate a realistic Chinese name with weighted surname distribution."""
    if gender is None:
        gender = random.choice(["male", "female"])

    surname = china_data.get_weighted_surname()

    name_patterns = list(_NAME_PATTERN_RULES.keys()) or ["single", "double", "triple"]
    name_weights = list(_NAME_PATTERN_RULES.values()) or [0.30, 0.65, 0.05]
    name_pattern = random.choices(name_patterns, weights=name_weights, k=1)[0]

    if gender == "male":
        name_pool = china_data.MALE_NAMES
    else:
        name_pool = china_data.FEMALE_NAMES

    if name_pattern == "single":
        given_name = random.choice(name_pool)
    elif name_pattern == "double":
        char1 = random.choice(name_pool)
        char2 = random.choice(name_pool)
        given_name = char1 + char2
    else:
        char1 = random.choice(name_pool)
        char2 = random.choice(name_pool)
        char3 = random.choice(name_pool)
        given_name = char1 + char2 + char3

    full_name = f"{surname}{given_name}"
    return full_name, given_name, surname, gender


def generate_chinese_email(
    name: Optional[str] = None, phone: Optional[str] = None
) -> str:
    """Generate a realistic Chinese email address with improved correlation."""
    domains = _EMAIL_RULES.get("domains", [])

    domain_names, domain_weights = zip(*domains)
    domain = random.choices(domain_names, weights=domain_weights)[0]

    if phone and domain == "qq.com":
        if random.random() < _EMAIL_RULES.get("qq_phone_probability", 0.6):
            return f"{phone}@qq.com"

    pinyin_prefixes = _EMAIL_RULES.get("pinyin_prefixes", [])

    patterns = [
        lambda: f"{random.choice(pinyin_prefixes)}{random.randint(10, 9999)}",
        lambda: f"{random.choice(pinyin_prefixes)}_{random.randint(10, 999)}",
        lambda: f"{random.choice(pinyin_prefixes)}.{random.randint(100, 999)}",
        lambda: f"{random.choice(pinyin_prefixes)}{random.choice(['vip', 'mail', ''])}{random.randint(1, 999)}",
        lambda: f"user{random.randint(1000, 9999999)}",
        lambda: f"a{random.randint(10000000, 99999999)}",
    ]

    username = random.choice(patterns)()
    return f"{username}@{domain}"


def generate_chinese_company() -> str:
    """Generate a realistic Chinese company name."""
    name_length = random.choice([2, 2, 3, 3, 4])
    company_name = "".join(random.choices(china_data.COMPANY_NAME_WORDS, k=name_length))
    company_type = random.choice(china_data.COMPANY_TYPES)
    return f"{company_name}{company_type}"


def generate_chinese_job_title() -> str:
    """Generate a realistic Chinese job title."""
    return random.choice(china_data.JOB_TITLES)


def generate_chinese_username(name: Optional[str] = None) -> str:
    """Generate a Chinese-style username."""
    pinyin_prefixes = _USERNAME_RULES.get("pinyin_prefixes", [])
    suffix_choices = _USERNAME_RULES.get(
        "suffix_choices", ["vip", "cn", "zh", "88", "2024"]
    )

    formats = [
        lambda p: f"{p}{random.randint(10, 9999)}",
        lambda p: f"{p}_{random.randint(10, 999)}",
        lambda p: f"{p}.{random.randint(100, 999)}",
        lambda p: f"{p}_{random.choice(suffix_choices)}",
        lambda p: f"user_{random.randint(1000, 999999)}",
    ]

    prefix = random.choice(pinyin_prefixes)
    return random.choice(formats)(prefix)


def get_zodiac_sign(birthdate: date) -> str:
    """Get Western zodiac sign from birthdate."""
    month = birthdate.month
    day = birthdate.day

    zodiac_dates = _ZODIAC_RULES.get("date_ranges", [])

    for start, end, sign in zodiac_dates:
        start_month, start_day = start
        end_month, end_day = end

        if start_month < end_month:
            if (
                (month == start_month and day >= start_day)
                or (month == end_month and day <= end_day)
                or (start_month < month < end_month)
            ):
                return sign
        else:
            if (
                (month == start_month and day >= start_day)
                or (month == end_month and day <= end_day)
                or (month > start_month or month < end_month)
            ):
                return sign

    return _ZODIAC_RULES.get("default_sign", "摩羯座")


def get_chinese_zodiac(birthdate: date) -> str:
    """Get Chinese zodiac from birth year."""
    animals = _CHINESE_ZODIAC_RULES.get(
        "animals",
        ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"],
    )
    base_year = _CHINESE_ZODIAC_RULES.get("base_year", 2020)
    year = birthdate.year
    index = (year - base_year) % len(animals)
    return animals[index]


def generate_ip_address() -> str:
    """Generate a realistic Chinese IPv4 address."""
    ip_types = _GENERATION_RULES.get("ip_types", [])

    first_octets, weights = zip(*ip_types)
    first = random.choices(first_octets, weights=weights)[0]

    if first == "172":
        second = random.randint(16, 31)
    elif first == "192":
        second = 168
    else:
        second = random.randint(0, 255)

    third = random.randint(0, 255)
    fourth = random.randint(1, 254)

    return f"{first}.{second}.{third}.{fourth}"


def generate_mac_address() -> str:
    """Generate a random MAC address."""
    oui_prefixes = _GENERATION_RULES.get("mac_oui_prefixes", [])

    oui = random.choice(oui_prefixes)
    remaining = ":".join([f"{random.randint(0, 255):02X}" for _ in range(3)])
    return f"{oui}:{remaining}"


def generate_social_credit_code() -> str:
    """Generate a valid Chinese Unified Social Credit Code."""
    authority_codes = _SOCIAL_CREDIT_RULES.get("authority_codes", ["1", "5", "9"])
    org_types = _SOCIAL_CREDIT_RULES.get("org_types", ["1", "2", "3", "9"])

    authority = random.choice(authority_codes)
    org_type = random.choice(org_types)

    province_code = random.choice(list(china_data.PROVINCES.keys()))
    if province_code in china_data.CITIES:
        city_code = random.choice(list(china_data.CITIES[province_code].keys()))
    else:
        city_code = "01"
    # Add district code (2 digits) to make 6-digit area code
    district_code = str(random.randint(1, 99)).zfill(2)
    area_code = f"{province_code}{city_code}{district_code}"

    org_code = "".join([str(random.randint(0, 9)) for _ in range(9)])
    code_17 = authority + org_type + area_code + org_code

    chars = _SOCIAL_CREDIT_RULES.get("chars", "0123456789ABCDEFGHJKLMNPQRTUWXY")
    weights = _SOCIAL_CREDIT_RULES.get(
        "weights", [1, 3, 9, 27, 19, 26, 16, 17, 20, 29, 25, 13, 8, 24, 10, 30, 28]
    )

    total = 0
    for i, char in enumerate(code_17):
        if char.isdigit():
            idx = int(char)
        else:
            idx = chars.index(char.upper()) if char.upper() in chars else 0
        total += idx * weights[i]

    check_digit = chars[(31 - (total % 31)) % 31]

    return code_17 + check_digit


def generate_emergency_contact(main_name: str) -> Tuple[str, str]:
    """Generate an emergency contact with relationship."""
    relationships = _EMERGENCY_RULES.get("relationships", [])

    rel_names, rel_weights = zip(*relationships)
    relationship = random.choices(rel_names, weights=rel_weights)[0]

    _, given_name, surname, _ = generate_chinese_name()

    if relationship == "父亲":
        fallback_pool = _EMERGENCY_RULES.get("fallback_surname_pool_size", 20)
        main_surname = random.choice(china_data.SURNAMES[:fallback_pool])
        for s in china_data.SURNAMES:
            if main_name.startswith(s):
                main_surname = s
                break
        name_pool = _EMERGENCY_RULES.get("gender_name_pool_size", 50)
        contact_name = (
            f"{main_surname}{random.choice(china_data.MALE_NAMES[:name_pool])}"
        )
    elif relationship == "母亲":
        name_pool = _EMERGENCY_RULES.get("gender_name_pool_size", 50)
        contact_name = f"{surname}{random.choice(china_data.FEMALE_NAMES[:name_pool])}"
    else:
        contact_name = f"{surname}{given_name}"

    return contact_name, relationship


def generate_hobbies() -> str:
    """Generate realistic hobbies."""
    hobby_categories = _HOBBY_RULES.get("categories", {})
    category_weights = _HOBBY_RULES.get(
        "category_count_weights", [[1, 10], [2, 40], [3, 35], [4, 15]]
    )
    num_options, num_weights = zip(*category_weights)
    num_categories = random.choices(num_options, weights=num_weights)[0]
    selected_categories = random.sample(list(hobby_categories.keys()), num_categories)

    hobbies = []
    for category in selected_categories:
        hobby_count_weights = _HOBBY_RULES.get(
            "per_category_hobby_count_weights", [[1, 70], [2, 30]]
        )
        count_options, count_weights = zip(*hobby_count_weights)
        num_hobbies = random.choices(count_options, weights=count_weights)[0]
        hobbies.extend(random.sample(hobby_categories[category], num_hobbies))

    if len(hobbies) < 2 and hobby_categories:
        remaining = [
            h
            for values in hobby_categories.values()
            for h in values
            if h not in hobbies
        ]
        if remaining:
            hobbies.append(random.choice(remaining))

    hobbies = hobbies[: _HOBBY_RULES.get("max_hobbies", 5)]
    return "、".join(hobbies)


def get_religion() -> str:
    """Get a random religion based on Chinese population distribution."""
    religions = _GENERATION_RULES.get("religions", [])

    names, weights = zip(*religions)
    return random.choices(names, weights=weights)[0]


class IdentityGenerator:
    """Generator for Chinese virtual identity information."""

    _DEDUP_FIELDS: List[str] = [
        "ssn",
        "phone",
        "email",
        "username",
        "bank_card",
        "social_credit_code",
        "wechat_id",
        "qq_number",
    ]
    _MAX_DEDUP_RETRIES: int = 50

    def __init__(self, config: IdentityConfig):
        """Initialize generator with configuration."""
        self.config = config
        self.faker = Faker("zh_CN")

        if config.seed is not None:
            self.faker.seed_instance(config.seed)
            random.seed(config.seed)
            logger.debug(f"Seeded generator with: {config.seed}")

    def _generate_address_bundle(self) -> Dict[str, str]:
        """Generate a consistent Chinese address bundle."""
        province, city, district, street, full_address, area_code = (
            china_data.get_random_address()
        )

        return {
            "province": province,
            "city": city,
            "district": district,
            "street": street,
            "address": full_address,
            "area_code": area_code,
            "zipcode": self._generate_zipcode(),
        }

    def _generate_zipcode(self) -> str:
        """Generate a realistic Chinese zipcode (6 digits)."""
        return str(random.randint(100000, 999999))

    def generate(self) -> Identity:
        """Generate a single Chinese identity with consistent correlations."""
        fields = self.config.get_effective_fields()
        identity_data: Dict[str, Any] = {}

        gender = random.choice(["male", "female"])
        address_bundle = {}
        birthdate = None
        age = 30
        phone = None
        name_info = None

        if any(f in fields for f in ["address", "city", "state", "zipcode", "ssn"]):
            address_bundle = self._generate_address_bundle()

        if any(
            f in fields
            for f in [
                "birthdate",
                "ssn",
                "age",
                "zodiac_sign",
                "chinese_zodiac",
                "education",
                "political_status",
                "marital_status",
            ]
        ):
            birthdate = self.faker.date_of_birth(minimum_age=18, maximum_age=70)
            age = (
                date.today().year
                - birthdate.year
                - (
                    (date.today().month, date.today().day)
                    < (birthdate.month, birthdate.day)
                )
            )
            if "birthdate" in fields:
                identity_data["birthdate"] = birthdate

        if any(f in fields for f in ["name", "first_name", "last_name"]):
            full_name, given_name, surname, _ = generate_chinese_name(gender)
            name_info = {"full": full_name, "given": given_name, "surname": surname}
            if "name" in fields:
                identity_data["name"] = full_name
            if "first_name" in fields:
                identity_data["first_name"] = given_name
            if "last_name" in fields:
                identity_data["last_name"] = surname

        if "gender" in fields:
            identity_data["gender"] = gender

        if "ssn" in fields:
            birthdate_for_ssn = cast(date, birthdate)
            area_code = address_bundle.get("area_code", "110101")
            identity_data["ssn"] = generate_chinese_id_card(
                birthdate_for_ssn, area_code, gender
            )

        if address_bundle:
            if "address" in fields:
                identity_data["address"] = address_bundle["address"]
            if "city" in fields:
                identity_data["city"] = address_bundle["city"]
            if "state" in fields:
                identity_data["state"] = address_bundle["province"]
            if "zipcode" in fields:
                identity_data["zipcode"] = address_bundle["zipcode"]

        if "country" in fields:
            identity_data["country"] = _DEFAULT_RULES.get("country", "中国")

        if "phone" in fields:
            phone = generate_chinese_phone()
            identity_data["phone"] = phone

        if "email" in fields:
            identity_data["email"] = generate_chinese_email(
                name_info["full"] if name_info else None, phone
            )

        if "company" in fields:
            identity_data["company"] = generate_chinese_company()

        if "job_title" in fields:
            identity_data["job_title"] = generate_chinese_job_title()

        if "username" in fields:
            identity_data["username"] = generate_chinese_username(
                name_info["full"] if name_info else None
            )

        if "password" in fields:
            identity_data["password"] = self.faker.password(
                length=12,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            )

        if "ethnicity" in fields:
            identity_data["ethnicity"] = china_data.get_random_ethnicity()

        if "education" in fields or "major" in fields:
            education_level, major = china_data.get_random_education(age)
            if "education" in fields:
                identity_data["education"] = education_level
            if "major" in fields:
                identity_data["major"] = major

        if "political_status" in fields:
            identity_data["political_status"] = china_data.get_random_political_status(
                age
            )

        if "marital_status" in fields:
            identity_data["marital_status"] = china_data.get_random_marital_status(age)

        if "blood_type" in fields:
            identity_data["blood_type"] = china_data.get_random_blood_type()

        if "height" in fields or "weight" in fields:
            height = china_data.generate_height(gender)
            if "height" in fields:
                identity_data["height"] = height
            if "weight" in fields:
                identity_data["weight"] = china_data.generate_weight(height, gender)

        if "bank_card" in fields:
            identity_data["bank_card"] = china_data.generate_bank_card()

        if "wechat_id" in fields:
            identity_data["wechat_id"] = china_data.generate_wechat_id()

        if "qq_number" in fields:
            identity_data["qq_number"] = china_data.generate_qq_number()

        if "license_plate" in fields:
            identity_data["license_plate"] = china_data.generate_license_plate()

        # New fields
        if "zodiac_sign" in fields and birthdate:
            identity_data["zodiac_sign"] = get_zodiac_sign(birthdate)

        if "chinese_zodiac" in fields and birthdate:
            identity_data["chinese_zodiac"] = get_chinese_zodiac(birthdate)

        if "ip_address" in fields:
            identity_data["ip_address"] = generate_ip_address()

        if "mac_address" in fields:
            identity_data["mac_address"] = generate_mac_address()

        if "social_credit_code" in fields:
            identity_data["social_credit_code"] = generate_social_credit_code()

        if "emergency_contact" in fields or "emergency_phone" in fields:
            if name_info:
                contact_name, relationship = generate_emergency_contact(
                    name_info["full"]
                )
                if "emergency_contact" in fields:
                    identity_data["emergency_contact"] = (
                        f"{contact_name} ({relationship})"
                    )
                if "emergency_phone" in fields:
                    identity_data["emergency_phone"] = generate_chinese_phone()

        if "hobbies" in fields:
            identity_data["hobbies"] = generate_hobbies()

        if "religion" in fields:
            identity_data["religion"] = get_religion()

        return Identity(**identity_data)

    def generate_batch(self, count: Optional[int] = None) -> List[Identity]:
        """Generate multiple identities."""
        count = count or self.config.count
        logger.info(f"Generating {count} Chinese identities")

        effective_fields = self.config.get_effective_fields()
        dedup_fields = [f for f in self._DEDUP_FIELDS if f in effective_fields]
        seen_values: Dict[str, Set[str]] = {field: set() for field in dedup_fields}

        identities: List[Identity] = []
        for i in range(count):
            identity = self.generate()
            retry_count = 0

            while dedup_fields:
                duplicate_fields = [
                    field
                    for field in dedup_fields
                    if getattr(identity, field)
                    and getattr(identity, field) in seen_values[field]
                ]
                if not duplicate_fields:
                    break

                retry_count += 1
                if retry_count >= self._MAX_DEDUP_RETRIES:
                    logger.warning(
                        "Max dedup retries reached at record %s; accepting possible duplicates in: %s",
                        i + 1,
                        ", ".join(duplicate_fields),
                    )
                    break
                identity = self.generate()

            for field in dedup_fields:
                value = getattr(identity, field)
                if value:
                    seen_values[field].add(value)

            identities.append(identity)
            logger.debug(f"Generated identity {i + 1}/{count}")

        return identities

    def get_supported_locales(self) -> List[str]:
        """Get list of supported locales."""
        return _DEFAULT_RULES.get("supported_locales", ["zh_CN"])
