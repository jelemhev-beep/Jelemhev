"""Material quote calculator (surface + thickness -> volume, weight,
price), the kind of thing MonIA used for landscaping/construction
estimates (gravel, sand, topsoil, ...).
"""

from dataclasses import dataclass

# density in kg/m3, price in EUR per tonne delivered -- rough, editable estimates
MATERIALS = {
    "gravier": {"density_kg_m3": 1600, "price_per_tonne": 35.0},
    "sable": {"density_kg_m3": 1500, "price_per_tonne": 30.0},
    "terre_vegetale": {"density_kg_m3": 1000, "price_per_tonne": 25.0},
    "beton": {"density_kg_m3": 2400, "price_per_tonne": 90.0},
    "galets": {"density_kg_m3": 1500, "price_per_tonne": 45.0},
    "paillis": {"density_kg_m3": 300, "price_per_tonne": 60.0},
}


@dataclass
class DevisResult:
    material: str
    surface_m2: float
    thickness_cm: float
    volume_m3: float
    weight_tonnes: float
    price_estimate: float


def available_materials() -> list[str]:
    return sorted(MATERIALS)


def calculate(material: str, surface_m2: float, thickness_cm: float = 5.0) -> DevisResult:
    if surface_m2 <= 0:
        raise ValueError("La surface doit etre positive")
    if thickness_cm <= 0:
        raise ValueError("L'epaisseur doit etre positive")

    key = material.lower().strip()
    if key not in MATERIALS:
        raise ValueError(f"Materiau inconnu '{material}'. Disponibles: {', '.join(available_materials())}")

    info = MATERIALS[key]
    volume_m3 = surface_m2 * (thickness_cm / 100.0)
    weight_tonnes = volume_m3 * info["density_kg_m3"] / 1000.0
    price_estimate = weight_tonnes * info["price_per_tonne"]

    return DevisResult(key, surface_m2, thickness_cm, volume_m3, weight_tonnes, price_estimate)


def format_devis(result: DevisResult) -> str:
    return (
        f"Materiau      : {result.material}\n"
        f"Surface       : {result.surface_m2:g} m2\n"
        f"Epaisseur     : {result.thickness_cm:g} cm\n"
        f"Volume        : {result.volume_m3:.2f} m3\n"
        f"Poids         : {result.weight_tonnes:.2f} tonnes\n"
        f"Prix estime   : {result.price_estimate:.2f} EUR\n"
    )
