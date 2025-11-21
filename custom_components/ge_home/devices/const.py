from gehomesdk import ErdBrand

BRAND_FIRST_LETTER_MAP: dict[str, ErdBrand] = {
    "C": ErdBrand.GE_CAFE,
    "G": ErdBrand.GE,
    "J": ErdBrand.GE,
    "N": ErdBrand.GE,
    "A": ErdBrand.GE,
    "F": ErdBrand.GE,
    "H": ErdBrand.HOTPOINT,
    "P": ErdBrand.GE_PROFILE,
    "Q": ErdBrand.HEIER,
    "Z": ErdBrand.GE_MONOGRAM,
    "R": ErdBrand.HOTPOINT,
    "M": ErdBrand.HEIER,
    "U": ErdBrand.UNKNOWN,  # also might be universal
}

BRAND_SPECIAL_PREFIXES: dict[str, int] = {
    "OPAL01": 6,  # Opal ice maker: brand letter at 7th position
    "XP": 1,      # XP Opal variant: brand letter at 2nd position
}
