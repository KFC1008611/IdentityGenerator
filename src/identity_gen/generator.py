"""Enhanced Chinese identity generation logic with improved data quality and field correlations."""

import logging
import random
from datetime import date
from typing import Dict, List, Optional, Tuple, Any

from faker import Faker

from .models import Identity, IdentityConfig
from . import china_data

logger = logging.getLogger(__name__)


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
    mobile_prefixes = [
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
    ]
    unicom_prefixes = [
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
    ]
    telecom_prefixes = [
        "133",
        "149",
        "153",
        "173",
        "177",
        "180",
        "181",
        "189",
        "199",
    ]
    virtual_prefixes = ["170", "171"]

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

    suffix = "".join([str(random.randint(0, 9)) for _ in range(8)])
    return prefix + suffix


def generate_chinese_name(gender: Optional[str] = None) -> Tuple[str, str, str, str]:
    """Generate a realistic Chinese name with weighted surname distribution."""
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

    full_name = f"{surname}{given_name}"
    return full_name, given_name, surname, gender


def generate_chinese_email(
    name: Optional[str] = None, phone: Optional[str] = None
) -> str:
    """Generate a realistic Chinese email address with improved correlation."""
    domains = [
        ("qq.com", 35),
        ("163.com", 20),
        ("126.com", 10),
        ("sina.com", 8),
        ("sohu.com", 5),
        ("aliyun.com", 5),
        ("139.com", 4),
        ("189.cn", 4),
        ("wo.cn", 2),
        ("outlook.com", 3),
        ("gmail.com", 2),
        ("hotmail.com", 1),
        ("foxmail.com", 1),
    ]

    domain_names, domain_weights = zip(*domains)
    domain = random.choices(domain_names, weights=domain_weights)[0]

    if phone and domain == "qq.com":
        if random.random() < 0.6:
            return f"{phone}@qq.com"

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
        "han",
        "feng",
        "deng",
        "cao",
        "peng",
        "zeng",
        "xiao",
    ]

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


def get_zodiac_sign(birthdate: date) -> str:
    """Get Western zodiac sign from birthdate."""
    month = birthdate.month
    day = birthdate.day

    zodiac_dates = [
        ((3, 21), (4, 19), "白羊座"),
        ((4, 20), (5, 20), "金牛座"),
        ((5, 21), (6, 21), "双子座"),
        ((6, 22), (7, 22), "巨蟹座"),
        ((7, 23), (8, 22), "狮子座"),
        ((8, 23), (9, 22), "处女座"),
        ((9, 23), (10, 23), "天秤座"),
        ((10, 24), (11, 22), "天蝎座"),
        ((11, 23), (12, 21), "射手座"),
        ((12, 22), (1, 19), "摩羯座"),
        ((1, 20), (2, 18), "水瓶座"),
        ((2, 19), (3, 20), "双鱼座"),
    ]

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

    return "摩羯座"


def get_chinese_zodiac(birthdate: date) -> str:
    """Get Chinese zodiac from birth year."""
    animals = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
    year = birthdate.year
    index = (year - 2020) % 12
    return animals[index]


def generate_ip_address() -> str:
    """Generate a realistic Chinese IPv4 address."""
    ip_types = [
        ("10", 10),
        ("172", 5),
        ("192", 15),
        ("116", 5),
        ("117", 5),
        ("118", 5),
        ("119", 5),
        ("120", 5),
        ("121", 5),
        ("122", 5),
        ("123", 5),
        ("124", 5),
        ("125", 5),
        ("126", 5),
        ("202", 5),
        ("203", 5),
        ("210", 5),
        ("211", 5),
        ("218", 5),
        ("219", 5),
        ("220", 5),
        ("221", 5),
        ("222", 5),
    ]

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
    oui_prefixes = [
        "00:1A:2B",
        "00:1C:C4",
        "00:25:9E",
        "00:0C:6E",
        "64:69:4E",
        "78:02:F8",
        "AC:DE:48",
        "00:08:22",
        "00:15:EB",
        "00:19:C6",
        "00:22:93",
        "00:1F:3A",
        "00:24:11",
        "00:26:C6",
        "00:1F:16",
        "00:E0:4C",
        "00:1A:1E",
        "00:21:CC",
        "00:24:D6",
    ]

    oui = random.choice(oui_prefixes)
    remaining = ":".join([f"{random.randint(0, 255):02X}" for _ in range(3)])
    return f"{oui}:{remaining}"


def generate_social_credit_code() -> str:
    """Generate a valid Chinese Unified Social Credit Code."""
    authority_codes = ["1", "5", "9"]
    org_types = ["1", "2", "3", "9"]

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

    chars = "0123456789ABCDEFGHJKLMNPQRTUWXY"
    weights = [1, 3, 9, 27, 19, 26, 16, 17, 20, 29, 25, 13, 8, 24, 10, 30, 28]

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
    relationships = [
        ("父亲", 25),
        ("母亲", 25),
        ("配偶", 30),
        ("兄弟姐妹", 10),
        ("子女", 5),
        ("朋友", 5),
    ]

    rel_names, rel_weights = zip(*relationships)
    relationship = random.choices(rel_names, weights=rel_weights)[0]

    _, given_name, surname, _ = generate_chinese_name()

    if relationship == "父亲":
        main_surname = random.choice(china_data.SURNAMES[:20])
        for s in china_data.SURNAMES:
            if main_name.startswith(s):
                main_surname = s
                break
        contact_name = f"{main_surname}{random.choice(china_data.MALE_NAMES[:50])}"
    elif relationship == "母亲":
        contact_name = f"{surname}{random.choice(china_data.FEMALE_NAMES[:50])}"
    else:
        contact_name = f"{surname}{given_name}"

    return contact_name, relationship


def generate_hobbies() -> str:
    """Generate realistic hobbies."""
    hobby_categories = {
        "sports": [
            "跑步",
            "游泳",
            "篮球",
            "足球",
            "羽毛球",
            "乒乓球",
            "网球",
            "健身",
            "瑜伽",
            "骑行",
            "登山",
            "滑雪",
        ],
        "arts": [
            "绘画",
            "书法",
            "摄影",
            "音乐",
            "舞蹈",
            "唱歌",
            "乐器",
            "写作",
            "阅读",
            "看电影",
            "看剧",
            "追综艺",
        ],
        "entertainment": [
            "打游戏",
            "追剧",
            "刷短视频",
            "看直播",
            "K歌",
            "桌游",
            "密室逃脱",
            "剧本杀",
        ],
        "outdoor": ["旅游", "露营", "徒步", "钓鱼", "摄影采风", "自驾游"],
        "food": ["烹饪", "烘焙", "品茶", "咖啡", "探店", "美食"],
        "learning": ["学习外语", "编程", "阅读", "听播客", "看纪录片", "在线课程"],
        "social": ["聚会", "交友", "社团活动", "志愿服务", "公益活动"],
        "collection": ["集邮", "收藏", "手办", "模型", "乐高", "盲盒"],
        "crafts": ["手工", "DIY", "编织", "刺绣", "木工", "陶艺"],
    }

    num_categories = random.choices([1, 2, 3, 4], weights=[10, 40, 35, 15])[0]
    selected_categories = random.sample(list(hobby_categories.keys()), num_categories)

    hobbies = []
    for category in selected_categories:
        num_hobbies = random.choices([1, 2], weights=[70, 30])[0]
        hobbies.extend(random.sample(hobby_categories[category], num_hobbies))

    hobbies = hobbies[:5]
    return "、".join(hobbies)


def get_religion() -> str:
    """Get a random religion based on Chinese population distribution."""
    religions = [
        ("无宗教信仰", 88.0),
        ("佛教", 6.0),
        ("道教", 1.5),
        ("基督教", 2.5),
        ("天主教", 0.5),
        ("伊斯兰教", 1.5),
    ]

    names, weights = zip(*religions)
    return random.choices(names, weights=weights)[0]


class IdentityGenerator:
    """Generator for Chinese virtual identity information."""

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
            if not birthdate:
                birthdate = self.faker.date_of_birth(minimum_age=18, maximum_age=70)
            area_code = address_bundle.get("area_code", "110101")
            identity_data["ssn"] = generate_chinese_id_card(
                birthdate, area_code, gender
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
            identity_data["country"] = "中国"

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

        identities = []
        for i in range(count):
            identity = self.generate()
            identities.append(identity)
            logger.debug(f"Generated identity {i + 1}/{count}")

        return identities

    def get_supported_locales(self) -> List[str]:
        """Get list of supported locales."""
        return ["zh_CN"]
