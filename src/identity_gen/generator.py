"""Chinese identity generation logic."""

import logging
import random
from datetime import date
from typing import Dict, List, Optional, Set, Tuple

from faker import Faker

from .models import Identity, IdentityConfig
from . import china_data

logger = logging.getLogger(__name__)


def calculate_chinese_id_checksum(id_17: str) -> str:
    """Calculate the last digit (checksum) of Chinese ID card using GB 11643-1999 standard."""
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_codes = "10X98765432"

    sum_value = sum(int(id_17[i]) * weights[i] for i in range(17))
    return check_codes[sum_value % 11]


def generate_chinese_id_card(
    birthdate: date, area_code: str, gender: Optional[str] = None
) -> str:
    """Generate a valid Chinese ID card number."""
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
    """Generate a realistic Chinese mobile phone number."""
    # 手机号前三位运营商号段
    prefixes = [
        # 中国移动
        "134",
        "135",
        "136",
        "137",
        "138",
        "139",
        "147",
        "150",
        "151",
        "152",
        "157",
        "158",
        "159",
        "178",
        "182",
        "183",
        "184",
        "187",
        "188",
        "198",
        # 中国联通
        "130",
        "131",
        "132",
        "145",
        "155",
        "156",
        "166",
        "175",
        "176",
        "185",
        "186",
        # 中国电信
        "133",
        "149",
        "153",
        "173",
        "177",
        "180",
        "181",
        "189",
        "199",
        # 虚拟运营商
        "170",
        "171",
    ]
    prefix = random.choice(prefixes)
    suffix = "".join([str(random.randint(0, 9)) for _ in range(8)])
    return prefix + suffix


def generate_chinese_name(gender: Optional[str] = None) -> Tuple[str, str, str, str]:
    """Generate a realistic Chinese name.

    Args:
        gender: "male" or "female". If None, randomly chosen.

    Returns:
        Tuple of (full_name, first_name, last_name, gender)
        Note: In Chinese, surname comes first, but for compatibility we return:
        - full_name: "GivenName Surname" (Western format for display)
        - first_name: Given name (ming)
        - last_name: Surname (xing)
        - gender: "male" or "female"
    """
    if gender is None:
        gender = random.choice(["male", "female"])

    surname = random.choice(china_data.SURNAMES)

    if gender == "male":
        given_name = random.choice(china_data.MALE_NAMES)
        if random.random() < 0.5:
            given_name += random.choice(china_data.MALE_NAMES)
    else:
        given_name = random.choice(china_data.FEMALE_NAMES)
        if random.random() < 0.5:
            given_name += random.choice(china_data.FEMALE_NAMES)

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
