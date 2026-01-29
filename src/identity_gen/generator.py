"""Chinese identity generation logic.

This module provides functions and classes for generating realistic Chinese
virtual identity information including names, ID cards, phone numbers, addresses,
and other personal details with proper probability distributions.
"""

import logging
import random
from datetime import date
from typing import Dict, List, Optional, Set, Tuple

from faker import Faker

from .models import Identity, IdentityConfig
from . import china_data

logger = logging.getLogger(__name__)


def calculate_chinese_id_checksum(id_17: str) -> str:
    """Calculate the last digit (checksum) of Chinese ID card using GB 11643-1999 standard.

    The Chinese national ID card number uses a weighted sum algorithm where each
    of the first 17 digits is multiplied by a corresponding weight factor. The
    remainder of the sum divided by 11 is used to look up the check digit.

    Args:
        id_17: The first 17 digits of the ID card number.

    Returns:
        The check digit (0-9 or X).

    Raises:
        ValueError: If id_17 is not exactly 17 characters or contains non-digit characters.

    Example:
        >>> calculate_chinese_id_checksum("11010119900101101")
        '5'
    """
    if len(id_17) != 17:
        raise ValueError(f"ID prefix must be exactly 17 digits, got {len(id_17)}")
    if not id_17.isdigit():
        raise ValueError("ID prefix must contain only digits")

    # Weight factors for each position as defined in GB 11643-1999
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    # Check digit mapping based on remainder
    check_codes = "10X98765432"

    sum_value = sum(int(id_17[i]) * weights[i] for i in range(17))
    return check_codes[sum_value % 11]


def generate_chinese_id_card(
    birthdate: date, area_code: str, gender: Optional[str] = None
) -> str:
    """Generate a valid Chinese ID card number following GB 11643-1999 standard.

    The ID card number consists of:
    - 6-digit administrative division code (area_code)
    - 8-digit birth date (YYYYMMDD)
    - 3-digit sequence code (odd for male, even for female)
    - 1-digit check code calculated using weighted sum algorithm

    Args:
        birthdate: Date of birth for the ID card.
        area_code: 6-digit administrative division code.
        gender: Optional gender specification ('male' or 'female').
               If None, gender is randomly assigned.

    Returns:
        A valid 18-digit Chinese ID card number.

    Raises:
        ValueError: If area_code is not 6 digits.

    Example:
        >>> from datetime import date
        >>> generate_chinese_id_card(date(1990, 1, 1), "110101", "male")
        '11010119900101001X'
    """
    if len(area_code) != 6 or not area_code.isdigit():
        raise ValueError("area_code must be exactly 6 digits")

    birth_str = birthdate.strftime("%Y%m%d")

    # Sequence code: odd numbers (1,3,5...) for male, even (2,4,6...) for female
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
    """Generate a realistic Chinese mobile phone number with carrier distribution.

    Chinese mobile numbers are 11 digits:
    - First digit is always 1
    - Second digit indicates carrier type (3-9)
    - Third digit further identifies carrier
    - Last 8 digits are random

    Carrier distribution (approximate market share):
    - China Mobile: ~58% (prefixes: 134-139, 147, 150-152, 157-159, etc.)
    - China Unicom: ~26% (prefixes: 130-132, 145, 155-156, 166, 175-176, etc.)
    - China Telecom: ~15% (prefixes: 133, 149, 153, 173, 177, 180-181, 189, 199)
    - Virtual operators: ~1% (prefixes: 170, 171)

    Returns:
        An 11-digit Chinese mobile phone number string.

    Example:
        >>> generate_chinese_phone()
        '13812345678'
    """
    # Carrier prefixes with approximate market share distribution
    # China Mobile: ~58% market share
    mobile_prefixes = [
        "134",
        "135",
        "136",
        "137",
        "138",
        "139",  # Classic series
        "147",  # Data cards
        "150",
        "151",
        "152",
        "157",
        "158",
        "159",  # 3G era
        "178",  # 4G era
        "182",
        "183",
        "184",
        "187",
        "188",  # 4G era
        "198",  # 5G era
    ]
    # China Unicom: ~26% market share
    unicom_prefixes = [
        "130",
        "131",
        "132",  # Classic series
        "145",  # Data cards
        "155",
        "156",  # 3G era
        "166",  # 4G era
        "175",
        "176",  # 4G era
        "185",
        "186",  # 4G era
    ]
    # China Telecom: ~15% market share
    telecom_prefixes = [
        "133",  # Classic series
        "149",  # Data cards
        "153",  # 3G era
        "173",
        "177",  # 4G era
        "180",
        "181",
        "189",  # 4G era
        "199",  # 5G era
    ]
    # Virtual operators: ~1% market share
    virtual_prefixes = ["170", "171"]

    # Weighted selection based on market share
    carrier_type = random.choices(
        ["mobile", "unicom", "telecom", "virtual"], weights=[58, 26, 15, 1], k=1
    )[0]

    if carrier_type == "mobile":
        prefix = random.choice(mobile_prefixes)
    elif carrier_type == "unicom":
        prefix = random.choice(unicom_prefixes)
    elif carrier_type == "telecom":
        prefix = random.choice(telecom_prefixes)
    else:
        prefix = random.choice(virtual_prefixes)

    # Generate 8 random digits for the suffix
    suffix = "".join([str(random.randint(0, 9)) for _ in range(8)])
    return prefix + suffix


def generate_chinese_name(
    gender: Optional[str] = None,
) -> Tuple[str, str, str, str]:
    """Generate a realistic Chinese name with weighted surname distribution.

    Uses real surname frequency data from China (2020 census):
    - Top 5 surnames (王, 李, 张, 刘, 陈) account for ~30.8% of population
    - Top 10 surnames account for ~42.5% of population
    - Top 100 surnames account for ~85% of population

    Given name patterns follow modern Chinese naming conventions:
    - Single character names: ~30%
    - Double character names: ~65%
    - Triple character names: ~5%
    - Male names tend toward strength/wisdom characters (伟, 强, 磊, etc.)
    - Female names tend toward beauty/grace characters (芳, 娜, 丽, etc.)

    Args:
        gender: "male" or "female". If None, randomly chosen with equal probability.

    Returns:
        Tuple of (full_name, first_name, last_name, gender) where:
        - full_name: "GivenName Surname" format (Western style for compatibility)
        - first_name: Given name (名)
        - last_name: Surname (姓)
        - gender: "male" or "female"

    Example:
        >>> generate_chinese_name("male")
        ('Wei Wang', 'Wei', 'Wang', 'male')
    """
    if gender is None:
        gender = random.choice(["male", "female"])

    surname = china_data.get_weighted_surname()

    name_pattern = random.choices(
        ["single", "double", "triple"],
        weights=[0.30, 0.65, 0.05],
        k=1,
    )[0]

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

    full_name = f"{given_name} {surname}"
    return full_name, given_name, surname, gender


def generate_chinese_email(name: str) -> str:
    """Generate a realistic Chinese email address."""
    domains = [
        "qq.com",
        "163.com",
        "126.com",
        "sina.com",
        "sohu.com",
        "aliyun.com",
        "139.com",
        "189.cn",
        "wo.cn",
        "outlook.com",
        "gmail.com",
        "hotmail.com",
        "foxmail.com",
        "yeah.net",
    ]

    # 使用拼音风格或随机英文用户名
    pinyin_prefixes = [
        "zhang",
        "li",
        "wang",
        "liu",
        "chen",
        "yang",
        "zhao",
        "wu",
        "zhou",
        "xu",
        "sun",
        "ma",
        "hu",
        "guo",
        "lin",
        "he",
        "gao",
        "liang",
        "zheng",
        "xie",
        "song",
        "tang",
        "xu",
        "han",
        "feng",
        "deng",
        "cao",
        "peng",
        "zeng",
        "xiao",
        "dong",
        "yuan",
        "pan",
        "yu",
        "jiang",
        "cai",
        "jia",
        "wei",
        "luo",
        "tang",
    ]

    # 多种邮箱格式
    formats = [
        lambda: f"{random.choice(pinyin_prefixes)}{random.randint(10, 9999)}",
        lambda: f"{random.choice(pinyin_prefixes)}_{random.randint(10, 999)}",
        lambda: f"{random.choice(pinyin_prefixes)}.{random.randint(100, 999)}",
        lambda: f"{random.choice(pinyin_prefixes)}{random.choice(['vip', 'mail', ''])}{random.randint(1, 999)}",
        lambda: f"user{random.randint(1000, 9999999)}",
        lambda: f"a{random.randint(10000000, 99999999)}",
    ]

    username = random.choice(formats)()
    domain = random.choice(domains)
    return f"{username}@{domain}"


def generate_chinese_company() -> str:
    """Generate a realistic Chinese company name."""
    # 公司字号 (2-4个字)
    name_length = random.choice([2, 2, 3, 3, 4])  # 2-3字更常见
    company_name = "".join(random.choices(china_data.COMPANY_NAME_WORDS, k=name_length))

    # 公司类型
    company_type = random.choice(china_data.COMPANY_TYPES)

    return f"{company_name}{company_type}"


def generate_chinese_job_title() -> str:
    """Generate a realistic Chinese job title."""
    return random.choice(china_data.JOB_TITLES)


def generate_chinese_username(name: str) -> str:
    """Generate a Chinese-style username."""
    # 使用拼音前缀或随机英文
    pinyin_prefixes = [
        "zhang",
        "li",
        "wang",
        "liu",
        "chen",
        "yang",
        "zhao",
        "wu",
        "zhou",
        "xu",
        "sun",
        "ma",
        "hu",
        "guo",
        "lin",
        "he",
        "gao",
        "liang",
        "zheng",
        "xie",
        "user",
        "admin",
        "test",
        "demo",
        "guest",
        "member",
        "vip",
        "master",
    ]

    formats = [
        lambda p: f"{p}{random.randint(10, 9999)}",
        lambda p: f"{p}_{random.randint(10, 999)}",
        lambda p: f"{p}.{random.randint(100, 999)}",
        lambda p: f"{p}_{random.choice(['vip', 'cn', 'zh', '88', '2024'])}",
        lambda p: f"user_{random.randint(1000, 999999)}",
    ]

    prefix = random.choice(pinyin_prefixes)
    return random.choice(formats)(prefix)


class IdentityGenerator:
    """Generator for Chinese virtual identity information."""

    def __init__(self, config: IdentityConfig):
        """Initialize generator with configuration.

        Args:
            config: Configuration for identity generation.
        """
        self.config = config

        # 强制使用中文locale
        self.faker = Faker("zh_CN")

        # Set instance-level seed for reproducibility
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

    def _get_area_code_for_address(self, city: str, district: str = "") -> str:
        """Get area code for ID card based on city."""
        return china_data.get_area_code_by_address(city, district)

    def generate(self) -> Identity:
        """Generate a single Chinese identity with consistent gender across name and ID."""
        fields = self.config.get_effective_fields()
        identity_data = {}
        gender = random.choice(["male", "female"])
        address_bundle = {}
        birthdate = None

        if any(f in fields for f in ["address", "city", "state", "zipcode", "ssn"]):
            address_bundle = self._generate_address_bundle()

        if "birthdate" in fields or "ssn" in fields:
            birthdate = self.faker.date_of_birth(minimum_age=18, maximum_age=70)
            if "birthdate" in fields:
                identity_data["birthdate"] = birthdate

        if "ssn" in fields:
            if not birthdate:
                birthdate = self.faker.date_of_birth(minimum_age=18, maximum_age=70)
            area_code = address_bundle.get("area_code", "110101")
            identity_data["ssn"] = generate_chinese_id_card(
                birthdate, area_code, gender
            )

        if "name" in fields or "first_name" in fields or "last_name" in fields:
            full_name, given_name, surname, _ = generate_chinese_name(gender)
            if "name" in fields:
                identity_data["name"] = full_name
            if "first_name" in fields:
                identity_data["first_name"] = given_name
            if "last_name" in fields:
                identity_data["last_name"] = surname

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
            identity_data["country"] = "中国"

        if "email" in fields:
            name_for_email = identity_data.get("name", "user")
            identity_data["email"] = generate_chinese_email(name_for_email)

        if "phone" in fields:
            identity_data["phone"] = generate_chinese_phone()

        if "company" in fields:
            identity_data["company"] = generate_chinese_company()

        if "job_title" in fields:
            identity_data["job_title"] = generate_chinese_job_title()

        if "username" in fields:
            name_for_user = identity_data.get("name", "user")
            identity_data["username"] = generate_chinese_username(name_for_user)

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

        age = 30
        if birthdate:
            from datetime import date

            age = (
                date.today().year
                - birthdate.year
                - (
                    (date.today().month, date.today().day)
                    < (birthdate.month, birthdate.day)
                )
            )

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

        return Identity(**identity_data)

    def generate_batch(self, count: Optional[int] = None) -> List[Identity]:
        """Generate multiple identities.

        Args:
            count: Number to generate. Uses config.count if None.

        Returns:
            List of generated identities.
        """
        count = count or self.config.count
        logger.info(f"Generating {count} Chinese identities")

        identities = []
        for i in range(count):
            identity = self.generate()
            identities.append(identity)
            logger.debug(f"Generated identity {i + 1}/{count}")

        return identities

    def get_supported_locales(self) -> List[str]:
        """Get list of supported locales.

        Returns:
            List of locale codes (only zh_CN for China-only version).
        """
        return ["zh_CN"]
