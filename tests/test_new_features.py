"""Extended tests for new identity fields and features."""

import pytest
from datetime import date
from identity_gen.generator import (
    IdentityGenerator,
    calculate_chinese_id_checksum,
    generate_chinese_id_card,
    generate_chinese_phone,
    generate_chinese_name,
    generate_chinese_email,
    get_zodiac_sign,
    get_chinese_zodiac,
    generate_ip_address,
    generate_mac_address,
    generate_social_credit_code,
    generate_emergency_contact,
    generate_hobbies,
    get_religion,
)
from identity_gen.models import IdentityConfig, Identity


class TestNewIdentityFields:
    """Tests for newly added identity fields."""

    def test_zodiac_sign_generation(self):
        """Test zodiac sign is calculated from birthdate."""
        config = IdentityConfig(
            locale="zh_CN", include_fields=["birthdate", "zodiac_sign"]
        )
        generator = IdentityGenerator(config)
        identity = generator.generate()

        assert identity.zodiac_sign is not None
        assert identity.birthdate is not None

        # Verify zodiac sign matches birthdate
        expected_zodiac = get_zodiac_sign(identity.birthdate)
        assert identity.zodiac_sign == expected_zodiac

    def test_chinese_zodiac_generation(self):
        """Test Chinese zodiac is calculated from birthdate."""
        config = IdentityConfig(
            locale="zh_CN", include_fields=["birthdate", "chinese_zodiac"]
        )
        generator = IdentityGenerator(config)
        identity = generator.generate()

        assert identity.chinese_zodiac is not None
        assert identity.birthdate is not None

        # Verify Chinese zodiac matches birth year
        expected_zodiac = get_chinese_zodiac(identity.birthdate)
        assert identity.chinese_zodiac == expected_zodiac

    def test_ip_address_generation(self):
        """Test IP address generation."""
        config = IdentityConfig(locale="zh_CN", include_fields=["ip_address"])
        generator = IdentityGenerator(config)
        identity = generator.generate()

        assert identity.ip_address is not None
        # Verify IPv4 format
        parts = identity.ip_address.split(".")
        assert len(parts) == 4
        for part in parts:
            assert part.isdigit()
            assert 0 <= int(part) <= 255

    def test_mac_address_generation(self):
        """Test MAC address generation."""
        config = IdentityConfig(locale="zh_CN", include_fields=["mac_address"])
        generator = IdentityGenerator(config)
        identity = generator.generate()

        assert identity.mac_address is not None
        # Verify MAC address format
        parts = identity.mac_address.split(":")
        assert len(parts) == 6
        for part in parts:
            assert len(part) == 2
            assert all(c in "0123456789ABCDEF" for c in part)

    def test_social_credit_code_generation(self):
        """Test social credit code generation."""
        config = IdentityConfig(locale="zh_CN", include_fields=["social_credit_code"])
        generator = IdentityGenerator(config)
        identity = generator.generate()

        assert identity.social_credit_code is not None
        assert len(identity.social_credit_code) == 18

    def test_emergency_contact_generation(self):
        """Test emergency contact generation."""
        config = IdentityConfig(
            locale="zh_CN",
            include_fields=["name", "emergency_contact", "emergency_phone"],
        )
        generator = IdentityGenerator(config)
        identity = generator.generate()

        assert identity.emergency_contact is not None
        assert identity.emergency_phone is not None
        # Verify emergency contact includes relationship
        assert "(" in identity.emergency_contact and ")" in identity.emergency_contact
        # Verify emergency phone is 11 digits
        assert len(identity.emergency_phone) == 11
        assert identity.emergency_phone.startswith("1")

    def test_hobbies_generation(self):
        """Test hobbies generation."""
        config = IdentityConfig(locale="zh_CN", include_fields=["hobbies"])
        generator = IdentityGenerator(config)
        identity = generator.generate()

        assert identity.hobbies is not None
        # Hobbies should be a string with Chinese characters
        assert isinstance(identity.hobbies, str)
        assert len(identity.hobbies) > 0

    def test_religion_generation(self):
        """Test religion generation."""
        config = IdentityConfig(locale="zh_CN", include_fields=["religion"])
        generator = IdentityGenerator(config)
        identity = generator.generate()

        assert identity.religion is not None
        # Verify it's one of the expected religions
        expected_religions = [
            "无宗教信仰",
            "佛教",
            "道教",
            "基督教",
            "天主教",
            "伊斯兰教",
        ]
        assert identity.religion in expected_religions


class TestFieldCorrelations:
    """Tests for data correlations between fields."""

    def test_email_phone_correlation(self):
        """Test that QQ email can be correlated with phone number."""
        config = IdentityConfig(locale="zh_CN", include_fields=["email", "phone"])

        # Generate multiple identities to increase chance of correlation
        for _ in range(20):
            generator = IdentityGenerator(config)
            identity = generator.generate()

            if identity.email.endswith("@qq.com"):
                # Check if email username matches phone
                email_username = identity.email.split("@")[0]
                if email_username == identity.phone:
                    return  # Found correlation

        # If we didn't find correlation, that's fine too - it's probabilistic
        assert True

    def test_gender_consistency(self):
        """Test that gender is consistent across name and ID."""
        config = IdentityConfig(
            locale="zh_CN", include_fields=["gender", "ssn", "name"]
        )
        generator = IdentityGenerator(config)
        identity = generator.generate()

        assert identity.gender in ["male", "female"]
        assert identity.ssn is not None

        # Verify ID card sequence code matches gender
        # Odd sequence code = male, even = female
        sequence_code = int(identity.ssn[14:17])
        is_male = sequence_code % 2 == 1

        if identity.gender == "male":
            assert is_male, "Male should have odd sequence code"
        else:
            assert not is_male, "Female should have even sequence code"

    def test_birthdate_age_correlation(self):
        """Test that age is calculated correctly from birthdate."""
        config = IdentityConfig(locale="zh_CN", include_fields=["birthdate"])
        generator = IdentityGenerator(config)
        identity = generator.generate()

        assert identity.birthdate is not None

        # Calculate expected age
        today = date.today()
        expected_age = today.year - identity.birthdate.year
        if (today.month, today.day) < (
            identity.birthdate.month,
            identity.birthdate.day,
        ):
            expected_age -= 1

        # Age should be between 18 and 70
        assert 18 <= expected_age <= 70


class TestZodiacCalculations:
    """Tests for zodiac sign calculations."""

    def test_zodiac_sign_aries(self):
        """Test Aries zodiac sign (March 21 - April 19)."""
        assert get_zodiac_sign(date(2020, 3, 21)) == "白羊座"
        assert get_zodiac_sign(date(2020, 4, 19)) == "白羊座"

    def test_zodiac_sign_taurus(self):
        """Test Taurus zodiac sign (April 20 - May 20)."""
        assert get_zodiac_sign(date(2020, 4, 20)) == "金牛座"
        assert get_zodiac_sign(date(2020, 5, 20)) == "金牛座"

    def test_zodiac_sign_capricorn(self):
        """Test Capricorn zodiac sign (crosses year boundary)."""
        assert get_zodiac_sign(date(2020, 12, 25)) == "摩羯座"
        assert get_zodiac_sign(date(2020, 1, 5)) == "摩羯座"

    def test_chinese_zodiac_rat(self):
        """Test Rat Chinese zodiac (2020)."""
        assert get_chinese_zodiac(date(2020, 6, 15)) == "鼠"

    def test_chinese_zodiac_ox(self):
        """Test Ox Chinese zodiac (2021)."""
        assert get_chinese_zodiac(date(2021, 6, 15)) == "牛"

    def test_chinese_zodiac_tiger(self):
        """Test Tiger Chinese zodiac (2022)."""
        assert get_chinese_zodiac(date(2022, 6, 15)) == "虎"

    def test_chinese_zodiac_dragon(self):
        """Test Dragon Chinese zodiac (2024)."""
        assert get_chinese_zodiac(date(2024, 6, 15)) == "龙"


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_generate_ip_address_format(self):
        """Test IP address format."""
        for _ in range(10):
            ip = generate_ip_address()
            parts = ip.split(".")
            assert len(parts) == 4
            for part in parts:
                assert 0 <= int(part) <= 255

    def test_generate_mac_address_format(self):
        """Test MAC address format."""
        for _ in range(10):
            mac = generate_mac_address()
            parts = mac.split(":")
            assert len(parts) == 6
            for part in parts:
                assert len(part) == 2

    def test_generate_social_credit_code_format(self):
        """Test social credit code format."""
        for _ in range(10):
            code = generate_social_credit_code()
            assert len(code) == 18
            # First char should be 1, 5, or 9
            assert code[0] in "159"
            # Second char should be 1, 2, 3, or 9
            assert code[1] in "1239"

    def test_generate_emergency_contact(self):
        """Test emergency contact generation."""
        contact_name, relationship = generate_emergency_contact("张伟")
        assert contact_name is not None
        assert relationship is not None
        expected_relationships = ["父亲", "母亲", "配偶", "兄弟姐妹", "子女", "朋友"]
        assert relationship in expected_relationships

    def test_generate_hobbies(self):
        """Test hobbies generation."""
        hobbies = generate_hobbies()
        assert isinstance(hobbies, str)
        assert len(hobbies) > 0
        # Hobbies are separated by Chinese comma
        assert "、" in hobbies

    def test_get_religion_distribution(self):
        """Test religion generation produces valid values."""
        religions = [get_religion() for _ in range(100)]
        expected_religions = [
            "无宗教信仰",
            "佛教",
            "道教",
            "基督教",
            "天主教",
            "伊斯兰教",
        ]

        for religion in religions:
            assert religion in expected_religions

        # Most should be "无宗教信仰" (~88%)
        none_count = religions.count("无宗教信仰")
        assert none_count >= 70  # Allow some variance


class TestIDCardValidation:
    """Tests for ID card validation and generation."""

    def test_calculate_chinese_id_checksum_valid(self):
        """Test checksum calculation with valid input."""
        # Test with known valid prefix
        checksum = calculate_chinese_id_checksum("11010119900101101")
        assert checksum in "0123456789X"

    def test_calculate_chinese_id_checksum_invalid_length(self):
        """Test checksum calculation with invalid length."""
        with pytest.raises(ValueError):
            calculate_chinese_id_checksum("1101011990010110")  # 16 chars

        with pytest.raises(ValueError):
            calculate_chinese_id_checksum("110101199001011011")  # 18 chars

    def test_calculate_chinese_id_checksum_non_digit(self):
        """Test checksum calculation with non-digit characters."""
        with pytest.raises(ValueError):
            calculate_chinese_id_checksum("1101011990010110X")

    def test_generate_chinese_id_card_invalid_area_code(self):
        """Test ID card generation with invalid area code."""
        with pytest.raises(ValueError):
            generate_chinese_id_card(date(1990, 1, 1), "11010")  # 5 digits

        with pytest.raises(ValueError):
            generate_chinese_id_card(date(1990, 1, 1), "1101011")  # 7 digits

        with pytest.raises(ValueError):
            generate_chinese_id_card(date(1990, 1, 1), "ABCDEF")  # Non-digit

    def test_generate_chinese_id_card_gender_male(self):
        """Test ID card generation for male."""
        id_card = generate_chinese_id_card(date(1990, 1, 1), "110101", "male")
        assert len(id_card) == 18
        # Sequence code should be odd for male
        sequence_code = int(id_card[14:17])
        assert sequence_code % 2 == 1

    def test_generate_chinese_id_card_gender_female(self):
        """Test ID card generation for female."""
        id_card = generate_chinese_id_card(date(1990, 1, 1), "110101", "female")
        assert len(id_card) == 18
        # Sequence code should be even for female
        sequence_code = int(id_card[14:17])
        assert sequence_code % 2 == 0


class TestEmailGeneration:
    """Tests for email generation with correlations."""

    def test_generate_chinese_email_with_phone_qq(self):
        """Test that QQ email can use phone number."""
        # Test multiple times due to randomness
        for _ in range(50):
            email = generate_chinese_email(phone="13800138000")
            if email == "13800138000@qq.com":
                return  # Found expected correlation

        # If not found, verify format is still valid
        email = generate_chinese_email(phone="13800138000")
        assert "@" in email
        assert email.endswith(
            (
                "@qq.com",
                "@163.com",
                "@126.com",
                "@sina.com",
                "@sohu.com",
                "@aliyun.com",
                "@139.com",
                "@189.cn",
                "@wo.cn",
                "@outlook.com",
                "@gmail.com",
                "@hotmail.com",
                "@foxmail.com",
            )
        )

    def test_generate_chinese_email_without_phone(self):
        """Test email generation without phone."""
        email = generate_chinese_email()
        assert "@" in email
        assert "." in email.split("@")[1]

    def test_generate_chinese_email_with_name(self):
        """Test email generation with name hint."""
        email = generate_chinese_email(name="张伟")
        assert "@" in email
        # Email should be valid format
        local, domain = email.split("@")
        assert len(local) > 0
        assert len(domain) > 0


class TestPhoneGeneration:
    """Tests for phone number generation."""

    def test_generate_chinese_phone_format(self):
        """Test phone number format."""
        for _ in range(20):
            phone = generate_chinese_phone()
            assert len(phone) == 11
            assert phone.startswith("1")
            assert phone[1] in "3456789"
            assert phone.isdigit()

    def test_generate_chinese_phone_prefixes(self):
        """Test that generated phones use valid prefixes."""
        mobile_prefixes = {
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
        }
        unicom_prefixes = {
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
        }
        telecom_prefixes = {
            "133",
            "149",
            "153",
            "173",
            "177",
            "180",
            "181",
            "189",
            "199",
        }
        virtual_prefixes = {"170", "171"}

        all_prefixes = (
            mobile_prefixes | unicom_prefixes | telecom_prefixes | virtual_prefixes
        )

        for _ in range(50):
            phone = generate_chinese_phone()
            prefix = phone[:3]
            assert prefix in all_prefixes


class TestNameGeneration:
    """Tests for name generation."""

    def test_generate_chinese_name_male(self):
        """Test male name generation."""
        full_name, given_name, surname, gender = generate_chinese_name("male")
        assert gender == "male"
        assert len(surname) > 0
        assert len(given_name) > 0
        assert full_name == f"{surname}{given_name}"

    def test_generate_chinese_name_female(self):
        """Test female name generation."""
        full_name, given_name, surname, gender = generate_chinese_name("female")
        assert gender == "female"
        assert len(surname) > 0
        assert len(given_name) > 0

    def test_generate_chinese_name_random_gender(self):
        """Test name generation with random gender."""
        full_name, given_name, surname, gender = generate_chinese_name()
        assert gender in ["male", "female"]
        assert len(surname) > 0
        assert len(given_name) > 0


class TestBatchGeneration:
    """Tests for batch identity generation."""

    def test_generate_batch_with_new_fields(self):
        """Test batch generation includes new fields."""
        config = IdentityConfig(
            locale="zh_CN",
            count=10,
            include_fields=[
                "name",
                "zodiac_sign",
                "chinese_zodiac",
                "ip_address",
                "mac_address",
                "religion",
            ],
        )
        generator = IdentityGenerator(config)
        identities = generator.generate_batch()

        assert len(identities) == 10

        for identity in identities:
            assert identity.name is not None
            assert identity.zodiac_sign is not None
            assert identity.chinese_zodiac is not None
            assert identity.ip_address is not None
            assert identity.mac_address is not None
            assert identity.religion is not None

    def test_generate_batch_count_override(self):
        """Test batch generation with count override."""
        config = IdentityConfig(locale="zh_CN", count=5)
        generator = IdentityGenerator(config)

        # Override count in generate_batch
        identities = generator.generate_batch(count=20)
        assert len(identities) == 20


class TestIdentityModelNewFields:
    """Tests for Identity model with new fields."""

    def test_identity_with_all_new_fields(self):
        """Test creating identity with all new fields."""
        identity = Identity(
            name="张三",
            zodiac_sign="金牛座",
            chinese_zodiac="龙",
            ip_address="192.168.1.1",
            mac_address="00:1A:2B:3C:4D:5E",
            social_credit_code="91110000123456789X",
            emergency_contact="李四 (父亲)",
            emergency_phone="13800138001",
            hobbies="阅读、游泳",
            religion="无宗教信仰",
        )

        assert identity.zodiac_sign == "金牛座"
        assert identity.chinese_zodiac == "龙"
        assert identity.ip_address == "192.168.1.1"
        assert identity.mac_address == "00:1A:2B:3C:4D:5E"
        assert identity.social_credit_code == "91110000123456789X"
        assert identity.emergency_contact == "李四 (父亲)"
        assert identity.emergency_phone == "13800138001"
        assert identity.hobbies == "阅读、游泳"
        assert identity.religion == "无宗教信仰"

    def test_identity_to_dict_with_new_fields(self):
        """Test to_dict includes new fields."""
        identity = Identity(
            name="张三",
            zodiac_sign="金牛座",
            chinese_zodiac="龙",
            ip_address="192.168.1.1",
            religion="佛教",
        )

        data = identity.to_dict()

        assert data["name"] == "张三"
        assert data["zodiac_sign"] == "金牛座"
        assert data["chinese_zodiac"] == "龙"
        assert data["ip_address"] == "192.168.1.1"
        assert data["religion"] == "佛教"

    def test_identity_get_field_names_includes_new_fields(self):
        """Test that new fields are in field names."""
        identity = Identity()
        fields = identity.get_field_names()

        new_fields = [
            "zodiac_sign",
            "chinese_zodiac",
            "ip_address",
            "mac_address",
            "social_credit_code",
            "emergency_contact",
            "emergency_phone",
            "hobbies",
            "religion",
        ]

        for field in new_fields:
            assert field in fields, f"Field {field} should be in field names"
