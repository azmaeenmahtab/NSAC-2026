"""Static canonical division and district specifications for Bangladesh (Chunk P03)."""

from __future__ import annotations

GEOBOUNDARIES_URLS = {
    "ADM0": "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/BGD/ADM0/geoBoundaries-BGD-ADM0.geojson",
    "ADM1": "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/BGD/ADM1/geoBoundaries-BGD-ADM1.geojson",
    "ADM2": "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/BGD/ADM2/geoBoundaries-BGD-ADM2.geojson",
}

# Canonical division metadata keyed by geoBoundaries ADM1 shapeName
DIVISION_SPECS: dict[str, tuple[str, str, list[str]]] = {
    "Barisal": ("BGD-ADM1-barishal", "Barishal", ["Barishal", "Barisal", "Barishal Division", "Barisal Division"]),
    "Chittagong": (
        "BGD-ADM1-chattogram",
        "Chattogram",
        ["Chattogram", "Chittagong", "Chattogram Division", "Chittagong Division"],
    ),
    "Dhaka": ("BGD-ADM1-dhaka", "Dhaka", ["Dhaka", "Dhaka Division", "Dacca Division"]),
    "Khulna": ("BGD-ADM1-khulna", "Khulna", ["Khulna", "Khulna Division"]),
    "Mymensingh": ("BGD-ADM1-mymensingh", "Mymensingh", ["Mymensingh", "Mymensingh Division"]),
    "Rajshani": (
        "BGD-ADM1-rajshahi",
        "Rajshahi",
        ["Rajshahi", "Rajshahi Division", "Rajshani", "Rajshani Division"],
    ),
    "Rangpur": ("BGD-ADM1-rangpur", "Rangpur", ["Rangpur", "Rangpur Division"]),
    "Sylhet": ("BGD-ADM1-sylhet", "Sylhet", ["Sylhet", "Sylhet Division"]),
}

# Canonical overrides for districts with post-2018 spelling reforms or punctuation
DISTRICT_OVERRIDES: dict[str, tuple[str, str, list[str]]] = {
    "Barisal": ("barishal", "Barishal", ["Barishal", "Barisal", "Barishal District", "Barisal District"]),
    "Bogra": ("bogura", "Bogura", ["Bogura", "Bogra", "Bogura District", "Bogra District"]),
    "Brahamanbaria": (
        "brahmanbaria",
        "Brahmanbaria",
        ["Brahmanbaria", "Brahamanbaria", "B-Baria", "Brahmanbaria District"],
    ),
    "Chittagong": (
        "chattogram",
        "Chattogram",
        ["Chattogram", "Chittagong", "Chattogram District", "Chittagong District"],
    ),
    "Comilla": ("cumilla", "Cumilla", ["Cumilla", "Comilla", "Cumilla District", "Comilla District"]),
    "Cox's Bazar": ("coxs-bazar", "Cox's Bazar", ["Cox's Bazar", "Coxs Bazar", "Cox'SBazar"]),
    "Jessore": ("jashore", "Jashore", ["Jashore", "Jessore", "Jashore District", "Jessore District"]),
    "Khagrachhari": (
        "khagrachari",
        "Khagrachari",
        ["Khagrachari", "Khagrachhari", "Khagrachari District", "Khagrachhari District"],
    ),
    "Maulvibazar": (
        "moulvibazar",
        "Moulvibazar",
        ["Moulvibazar", "Maulvibazar", "Moulvibazar District", "Sylhet Moulvibazar"],
    ),
    "Nawabganj": (
        "nawabganj",
        "Chapai Nawabganj",
        ["Chapai Nawabganj", "Nawabganj", "Chapainawabganj", "Nawabganj District"],
    ),
}

CHT_DISTRICTS = ("BGD-ADM2-rangamati", "BGD-ADM2-bandarban", "BGD-ADM2-khagrachari")
