def get_country_from_icao(hex_code: str) -> str:
    """
    Get country code from ICAO hex code (official ICAO allocation)
    Based on official ICAO hex code allocation from aerotransport.org

    Args:
        hex_code (str): ICAO hex identifier (24-bit hex)

    Returns:
        str: Two-character ISO country code or "XX" for unknown
    """
    if not hex_code or len(hex_code) < 6:
        return "XX"

    # Convert to uppercase and get integer value
    hex_upper = hex_code.upper()

    try:
        hex_int = int(hex_upper, 16)
    except ValueError:
        return "XX"

    # ICAO 24-bit address allocation (official ranges from aerotransport.org)
    # Organized by hex range order

    # 000000-0FFFFF range
    if 0x004000 <= hex_int <= 0x0043FF:
        return "ZW"  # Zimbabwe
    elif 0x006000 <= hex_int <= 0x006FFF:
        return "MZ"  # Mozambique
    elif 0x008000 <= hex_int <= 0x00FFFF:
        return "ZA"  # South Africa
    elif 0x010000 <= hex_int <= 0x017FFF:
        return "EG"  # Egypt
    elif 0x018000 <= hex_int <= 0x01FFFF:
        return "LY"  # Libya
    elif 0x020000 <= hex_int <= 0x027FFF:
        return "MA"  # Morocco
    elif 0x028000 <= hex_int <= 0x02FFFF:
        return "TN"  # Tunisia
    elif 0x030000 <= hex_int <= 0x0303FF:
        return "BW"  # Botswana
    elif 0x032000 <= hex_int <= 0x032FFF:
        return "BI"  # Burundi
    elif 0x034000 <= hex_int <= 0x034FFF:
        return "CM"  # Cameroon
    elif 0x035000 <= hex_int <= 0x0353FF:
        return "KM"  # Comoros
    elif 0x036000 <= hex_int <= 0x036FFF:
        return "CG"  # Congo
    elif 0x038000 <= hex_int <= 0x038FFF:
        return "CI"  # Côte d'Ivoire
    elif 0x03E000 <= hex_int <= 0x03EFFF:
        return "GA"  # Gabon
    elif 0x040000 <= hex_int <= 0x040FFF:
        return "ET"  # Ethiopia
    elif 0x042000 <= hex_int <= 0x042FFF:
        return "GQ"  # Equatorial Guinea
    elif 0x044000 <= hex_int <= 0x044FFF:
        return "GH"  # Ghana
    elif 0x046000 <= hex_int <= 0x046FFF:
        return "GN"  # Guinea
    elif 0x048000 <= hex_int <= 0x0483FF:
        return "GW"  # Guinea-Bissau
    elif 0x04A000 <= hex_int <= 0x04A3FF:
        return "LS"  # Lesotho
    elif 0x04C000 <= hex_int <= 0x04CFFF:
        return "KE"  # Kenya
    elif 0x050000 <= hex_int <= 0x050FFF:
        return "LR"  # Liberia
    elif 0x054000 <= hex_int <= 0x054FFF:
        return "MG"  # Madagascar
    elif 0x058000 <= hex_int <= 0x058FFF:
        return "MW"  # Malawi
    elif 0x05A000 <= hex_int <= 0x05A3FF:
        return "MV"  # Maldives
    elif 0x05C000 <= hex_int <= 0x05CFFF:
        return "ML"  # Mali
    elif 0x05E000 <= hex_int <= 0x05E3FF:
        return "MR"  # Mauritania
    elif 0x060000 <= hex_int <= 0x0603FF:
        return "MU"  # Mauritius
    elif 0x062000 <= hex_int <= 0x062FFF:
        return "NE"  # Niger
    elif 0x064000 <= hex_int <= 0x064FFF:
        return "NG"  # Nigeria
    elif 0x068000 <= hex_int <= 0x068FFF:
        return "UG"  # Uganda
    elif 0x06A000 <= hex_int <= 0x06A3FF:
        return "QA"  # Qatar
    elif 0x06C000 <= hex_int <= 0x06CFFF:
        return "CF"  # Central African Republic
    elif 0x06E000 <= hex_int <= 0x06EFFF:
        return "RW"  # Rwanda
    elif 0x070000 <= hex_int <= 0x070FFF:
        return "SN"  # Senegal
    elif 0x074000 <= hex_int <= 0x0743FF:
        return "SC"  # Seychelles
    elif 0x076000 <= hex_int <= 0x0763FF:
        return "SL"  # Sierra Leone
    elif 0x078000 <= hex_int <= 0x078FFF:
        return "SO"  # Somalia
    elif 0x07A000 <= hex_int <= 0x07A3FF:
        return "SZ"  # Swaziland
    elif 0x07C000 <= hex_int <= 0x07CFFF:
        return "SD"  # Sudan
    elif 0x080000 <= hex_int <= 0x080FFF:
        return "TZ"  # Tanzania
    elif 0x084000 <= hex_int <= 0x084FFF:
        return "TD"  # Chad
    elif 0x088000 <= hex_int <= 0x088FFF:
        return "TG"  # Togo
    elif 0x08A000 <= hex_int <= 0x08AFFF:
        return "ZM"  # Zambia
    elif 0x08C000 <= hex_int <= 0x08CFFF:
        return "CD"  # DR Congo
    elif 0x090000 <= hex_int <= 0x090FFF:
        return "AO"  # Angola
    elif 0x094000 <= hex_int <= 0x0943FF:
        return "BJ"  # Benin
    elif 0x096000 <= hex_int <= 0x0963FF:
        return "CV"  # Cape Verde
    elif 0x098000 <= hex_int <= 0x0983FF:
        return "DJ"  # Djibouti
    elif 0x09A000 <= hex_int <= 0x09AFFF:
        return "GM"  # Gambia
    elif 0x09C000 <= hex_int <= 0x09CFFF:
        return "BF"  # Burkina Faso
    elif 0x09E000 <= hex_int <= 0x09E3FF:
        return "ST"  # Sao Tome
    elif 0x0A0000 <= hex_int <= 0x0A7FFF:
        return "DZ"  # Algeria
    elif 0x0A8000 <= hex_int <= 0x0A8FFF:
        return "BS"  # Bahamas
    elif 0x0AA000 <= hex_int <= 0x0AA3FF:
        return "BB"  # Barbados
    elif 0x0AB000 <= hex_int <= 0x0AB3FF:
        return "BZ"  # Belize
    elif 0x0AC000 <= hex_int <= 0x0ACFFF:
        return "CO"  # Colombia
    elif 0x0AE000 <= hex_int <= 0x0AEFFF:
        return "CR"  # Costa Rica
    elif 0x0B0000 <= hex_int <= 0x0B0FFF:
        return "CU"  # Cuba
    elif 0x0B2000 <= hex_int <= 0x0B2FFF:
        return "SV"  # El Salvador
    elif 0x0B4000 <= hex_int <= 0x0B4FFF:
        return "GT"  # Guatemala
    elif 0x0B6000 <= hex_int <= 0x0B6FFF:
        return "GY"  # Guyana
    elif 0x0B8000 <= hex_int <= 0x0B8FFF:
        return "HT"  # Haiti
    elif 0x0BA000 <= hex_int <= 0x0BAFFF:
        return "HN"  # Honduras
    elif 0x0BC000 <= hex_int <= 0x0BC3FF:
        return "VC"  # St.Vincent + Grenadines
    elif 0x0BE000 <= hex_int <= 0x0BEFFF:
        return "JM"  # Jamaica
    elif 0x0C0000 <= hex_int <= 0x0C0FFF:
        return "NI"  # Nicaragua
    elif 0x0C2000 <= hex_int <= 0x0C2FFF:
        return "PA"  # Panama
    elif 0x0C4000 <= hex_int <= 0x0C4FFF:
        return "DO"  # Dominican Republic
    elif 0x0C6000 <= hex_int <= 0x0C6FFF:
        return "TT"  # Trinidad and Tobago
    elif 0x0C8000 <= hex_int <= 0x0C8FFF:
        return "SR"  # Suriname
    elif 0x0CA000 <= hex_int <= 0x0CA3FF:
        return "AG"  # Antigua & Barbuda
    elif 0x0CC000 <= hex_int <= 0x0CC3FF:
        return "GD"  # Grenada
    elif 0x0D0000 <= hex_int <= 0x0D7FFF:
        return "MX"  # Mexico
    elif 0x0D8000 <= hex_int <= 0x0DFFFF:
        return "VE"  # Venezuela

    # 100000-1FFFFF range
    elif 0x100000 <= hex_int <= 0x1FFFFF:
        return "RU"  # Russia

    # 201000-2FFFFF range
    elif 0x201000 <= hex_int <= 0x2013FF:
        return "NA"  # Namibia
    elif 0x202000 <= hex_int <= 0x2023FF:
        return "ER"  # Eritrea

    # 300000-4FFFFF range (Europe)
    elif 0x300000 <= hex_int <= 0x33FFFF:
        return "IT"  # Italy
    elif 0x340000 <= hex_int <= 0x37FFFF:
        return "ES"  # Spain
    elif 0x380000 <= hex_int <= 0x3BFFFF:
        return "FR"  # France
    elif 0x3C0000 <= hex_int <= 0x3FFFFF:
        return "DE"  # Germany
    elif 0x400000 <= hex_int <= 0x43FFFF:
        return "GB"  # United Kingdom
    elif 0x440000 <= hex_int <= 0x447FFF:
        return "AT"  # Austria
    elif 0x448000 <= hex_int <= 0x44FFFF:
        return "BE"  # Belgium
    elif 0x450000 <= hex_int <= 0x457FFF:
        return "BG"  # Bulgaria
    elif 0x458000 <= hex_int <= 0x45FFFF:
        return "DK"  # Denmark
    elif 0x460000 <= hex_int <= 0x467FFF:
        return "FI"  # Finland
    elif 0x468000 <= hex_int <= 0x46FFFF:
        return "GR"  # Greece
    elif 0x470000 <= hex_int <= 0x477FFF:
        return "HU"  # Hungary
    elif 0x478000 <= hex_int <= 0x47FFFF:
        return "NO"  # Norway
    elif 0x480000 <= hex_int <= 0x487FFF:
        return "NL"  # Netherlands
    elif 0x488000 <= hex_int <= 0x48FFFF:
        return "PL"  # Poland
    elif 0x490000 <= hex_int <= 0x497FFF:
        return "PT"  # Portugal
    elif 0x498000 <= hex_int <= 0x49FFFF:
        return "CZ"  # Czech Republic
    elif 0x4A0000 <= hex_int <= 0x4A7FFF:
        return "RO"  # Romania
    elif 0x4A8000 <= hex_int <= 0x4AFFFF:
        return "SE"  # Sweden
    elif 0x4B0000 <= hex_int <= 0x4B7FFF:
        return "CH"  # Switzerland
    elif 0x4B8000 <= hex_int <= 0x4BFFFF:
        return "TR"  # Turkey
    elif 0x4C0000 <= hex_int <= 0x4C7FFF:
        return "YU"  # Yugoslavia (historical)
    elif 0x4C8000 <= hex_int <= 0x4C83FF:
        return "CY"  # Cyprus
    elif 0x4CA000 <= hex_int <= 0x4CAFFF:
        return "IE"  # Ireland
    elif 0x4CC000 <= hex_int <= 0x4CCFFF:
        return "IS"  # Iceland
    elif 0x4D0000 <= hex_int <= 0x4D03FF:
        return "LU"  # Luxembourg
    elif 0x4D2000 <= hex_int <= 0x4D23FF:
        return "MT"  # Malta
    elif 0x4D4000 <= hex_int <= 0x4D43FF:
        return "MC"  # Monaco

    # 500000-5FFFFF range (Europe reserved/small states)
    elif 0x500000 <= hex_int <= 0x5004FF:
        return "SM"  # San Marino
    elif 0x501000 <= hex_int <= 0x5013FF:
        return "AL"  # Albania
    elif 0x501C00 <= hex_int <= 0x501FFF:
        return "HR"  # Croatia
    elif 0x502C00 <= hex_int <= 0x502FFF:
        return "LV"  # Latvia
    elif 0x503C00 <= hex_int <= 0x503FFF:
        return "LT"  # Lithuania
    elif 0x504C00 <= hex_int <= 0x504FFF:
        return "MD"  # Moldova
    elif 0x505C00 <= hex_int <= 0x505FFF:
        return "SK"  # Slovakia
    elif 0x506C00 <= hex_int <= 0x506FFF:
        return "SI"  # Slovenia
    elif 0x507C00 <= hex_int <= 0x507FFF:
        return "UZ"  # Uzbekistan
    elif 0x508000 <= hex_int <= 0x50FFFF:
        return "UA"  # Ukraine
    elif 0x510000 <= hex_int <= 0x5103FF:
        return "BY"  # Belarus
    elif 0x511000 <= hex_int <= 0x5113FF:
        return "EE"  # Estonia
    elif 0x512000 <= hex_int <= 0x5123FF:
        return "MK"  # Macedonia
    elif 0x513000 <= hex_int <= 0x5133FF:
        return "BA"  # Bosnia & Herzegovina
    elif 0x514000 <= hex_int <= 0x5143FF:
        return "GE"  # Georgia
    elif 0x515000 <= hex_int <= 0x5153FF:
        return "TJ"  # Tajikistan

    # 600000-6FFFFF range (Middle East/Asia)
    elif 0x600000 <= hex_int <= 0x6003FF:
        return "AM"  # Armenia
    elif 0x600800 <= hex_int <= 0x600BFF:
        return "AZ"  # Azerbaijan
    elif 0x601000 <= hex_int <= 0x6013FF:
        return "KG"  # Kyrgyzstan
    elif 0x601800 <= hex_int <= 0x601BFF:
        return "TM"  # Turkmenistan
    elif 0x680000 <= hex_int <= 0x6803FF:
        return "BT"  # Bhutan
    elif 0x681000 <= hex_int <= 0x6813FF:
        return "FM"  # Micronesia
    elif 0x682000 <= hex_int <= 0x6823FF:
        return "MN"  # Mongolia
    elif 0x683000 <= hex_int <= 0x6833FF:
        return "KZ"  # Kazakhstan
    elif 0x684000 <= hex_int <= 0x6843FF:
        return "PW"  # Palau

    # 700000-7FFFFF range (Asia/Pacific)
    elif 0x700000 <= hex_int <= 0x700FFF:
        return "AF"  # Afghanistan
    elif 0x702000 <= hex_int <= 0x702FFF:
        return "BD"  # Bangladesh
    elif 0x704000 <= hex_int <= 0x704FFF:
        return "MM"  # Myanmar
    elif 0x706000 <= hex_int <= 0x706FFF:
        return "KW"  # Kuwait
    elif 0x708000 <= hex_int <= 0x708FFF:
        return "LA"  # Laos
    elif 0x70A000 <= hex_int <= 0x70AFFF:
        return "NP"  # Nepal
    elif 0x70C000 <= hex_int <= 0x70C3FF:
        return "OM"  # Oman
    elif 0x70E000 <= hex_int <= 0x70EFFF:
        return "KH"  # Cambodia
    elif 0x710000 <= hex_int <= 0x717FFF:
        return "SA"  # Saudi Arabia
    elif 0x718000 <= hex_int <= 0x71FFFF:
        return "KR"  # South Korea
    elif 0x720000 <= hex_int <= 0x727FFF:
        return "KP"  # North Korea
    elif 0x728000 <= hex_int <= 0x72FFFF:
        return "IQ"  # Iraq
    elif 0x730000 <= hex_int <= 0x737FFF:
        return "IR"  # Iran
    elif 0x738000 <= hex_int <= 0x73FFFF:
        return "IL"  # Israel
    elif 0x740000 <= hex_int <= 0x747FFF:
        return "JO"  # Jordan
    elif 0x748000 <= hex_int <= 0x74FFFF:
        return "LB"  # Lebanon
    elif 0x750000 <= hex_int <= 0x757FFF:
        return "MY"  # Malaysia
    elif 0x758000 <= hex_int <= 0x75FFFF:
        return "PH"  # Philippines
    elif 0x760000 <= hex_int <= 0x767FFF:
        return "PK"  # Pakistan
    elif 0x768000 <= hex_int <= 0x76FFFF:
        return "SG"  # Singapore
    elif 0x770000 <= hex_int <= 0x777FFF:
        return "LK"  # Sri Lanka
    elif 0x778000 <= hex_int <= 0x77FFFF:
        return "SY"  # Syria
    elif 0x780000 <= hex_int <= 0x7BFFFF:
        return "CN"  # China
    elif 0x7C0000 <= hex_int <= 0x7FFFFF:
        return "AU"  # Australia

    # 800000-8FFFFF range
    elif 0x800000 <= hex_int <= 0x83FFFF:
        return "IN"  # India
    elif 0x840000 <= hex_int <= 0x87FFFF:
        return "JP"  # Japan
    elif 0x880000 <= hex_int <= 0x887FFF:
        return "TH"  # Thailand
    elif 0x888000 <= hex_int <= 0x88FFFF:
        return "VN"  # Vietnam
    elif 0x890000 <= hex_int <= 0x890FFF:
        return "YE"  # Yemen
    elif 0x894000 <= hex_int <= 0x894FFF:
        return "BH"  # Bahrain
    elif 0x895000 <= hex_int <= 0x8953FF:
        return "BN"  # Brunei
    elif 0x896000 <= hex_int <= 0x896FFF:
        return "AE"  # United Arab Emirates
    elif 0x897000 <= hex_int <= 0x8973FF:
        return "SB"  # Solomon Islands
    elif 0x898000 <= hex_int <= 0x898FFF:
        return "PG"  # Papua New Guinea
    elif 0x899000 <= hex_int <= 0x8993FF:
        return "TW"  # Taiwan
    elif 0x8A0000 <= hex_int <= 0x8A7FFF:
        return "ID"  # Indonesia

    # 900000-9FFFFF range (Pacific)
    elif 0x900000 <= hex_int <= 0x9003FF:
        return "MH"  # Marshall Islands
    elif 0x901000 <= hex_int <= 0x9013FF:
        return "CK"  # Cook Islands
    elif 0x902000 <= hex_int <= 0x9023FF:
        return "WS"  # Samoa

    # A00000-AFFFFF range
    elif 0xA00000 <= hex_int <= 0xAFFFFF:
        return "US"  # United States

    # C00000-CFFFFF range
    elif 0xC00000 <= hex_int <= 0xC3FFFF:
        return "CA"  # Canada
    elif 0xC80000 <= hex_int <= 0xC87FFF:
        return "NZ"  # New Zealand
    elif 0xC88000 <= hex_int <= 0xC88FFF:
        return "FJ"  # Fiji
    elif 0xC8A000 <= hex_int <= 0xC8A3FF:
        return "NR"  # Nauru
    elif 0xC8C000 <= hex_int <= 0xC8C3FF:
        return "LC"  # Saint Lucia
    elif 0xC8D000 <= hex_int <= 0xC8D3FF:
        return "TO"  # Tonga
    elif 0xC8E000 <= hex_int <= 0xC8E3FF:
        return "KI"  # Kiribati
    elif 0xC90000 <= hex_int <= 0xC903FF:
        return "VU"  # Vanuatu

    # E00000-EFFFFF range (South America)
    elif 0xE00000 <= hex_int <= 0xE3FFFF:
        return "AR"  # Argentina
    elif 0xE40000 <= hex_int <= 0xE7FFFF:
        return "BR"  # Brazil
    elif 0xE80000 <= hex_int <= 0xE80FFF:
        return "CL"  # Chile
    elif 0xE84000 <= hex_int <= 0xE84FFF:
        return "EC"  # Ecuador
    elif 0xE88000 <= hex_int <= 0xE88FFF:
        return "PY"  # Paraguay
    elif 0xE8C000 <= hex_int <= 0xE8CFFF:
        return "PE"  # Peru
    elif 0xE90000 <= hex_int <= 0xE90FFF:
        return "UY"  # Uruguay
    elif 0xE94000 <= hex_int <= 0xE94FFF:
        return "BO"  # Bolivia

    else:
        return "XX"  # Unknown
