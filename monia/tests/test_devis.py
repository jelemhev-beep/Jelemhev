import pytest

from monia import devis


def test_calculate_known_values_gravier():
    result = devis.calculate("gravier", surface_m2=10, thickness_cm=5)
    # volume = 10 * 0.05 = 0.5 m3 ; weight = 0.5 * 1600/1000 = 0.8 tonnes
    assert result.volume_m3 == pytest.approx(0.5)
    assert result.weight_tonnes == pytest.approx(0.8)
    assert result.price_estimate == pytest.approx(0.8 * 35.0)


def test_calculate_is_case_insensitive_and_strips_spaces():
    a = devis.calculate("Gravier", 10, 5)
    b = devis.calculate("  gravier  ", 10, 5)
    assert a.volume_m3 == b.volume_m3


def test_calculate_default_thickness_is_5cm():
    result = devis.calculate("sable", surface_m2=4)
    assert result.thickness_cm == 5.0


def test_unknown_material_raises_with_helpful_message():
    with pytest.raises(ValueError, match="Materiau inconnu"):
        devis.calculate("licorne", 10, 5)


def test_negative_surface_rejected():
    with pytest.raises(ValueError):
        devis.calculate("gravier", -1, 5)


def test_zero_thickness_rejected():
    with pytest.raises(ValueError):
        devis.calculate("gravier", 10, 0)


def test_format_devis_contains_all_fields():
    result = devis.calculate("beton", 6, 10)
    text = devis.format_devis(result)
    assert "beton" in text
    assert "m3" in text
    assert "tonnes" in text
    assert "EUR" in text


def test_available_materials_lists_all():
    materials = devis.available_materials()
    assert "gravier" in materials
    assert "sable" in materials
    assert materials == sorted(materials)
