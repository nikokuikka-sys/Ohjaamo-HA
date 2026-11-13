"""
Testien pystytys.

🔴 MITATTU 13.11.2026: pytest-homeassistant-custom-component EI lue reposta vaan
omasta `testing_config/custom_components`-kansiostaan. Ilman tata linkitysta HA
vastaa "Integration not found" ja testit menisivat lapi mittaamatta mitaan —
pahin mahdollinen vihrea.
"""
import os
import shutil
import sys
from pathlib import Path

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"

JUURI = Path(__file__).resolve().parent.parent
LAHDE = JUURI / "custom_components" / "klevra"


def _phcc_kansio() -> Path:
    import pytest_homeassistant_custom_component as phcc
    return Path(phcc.__file__).parent / "testing_config" / "custom_components"


@pytest.fixture(scope="session", autouse=True)
def integraatio_nakyviin():
    """Kopioi integraatio sinne mista HA sen loytaa, ja siivoa jalkeen."""
    kohde = _phcc_kansio() / "klevra"
    luotiin = False
    if not kohde.exists():
        try:
            shutil.copytree(LAHDE, kohde)
            luotiin = True
        except OSError as e:
            pytest.skip(f"Integraatiota ei saatu nakyviin HA:lle: {e}")
    yield
    if luotiin:
        shutil.rmtree(kohde, ignore_errors=True)


@pytest.fixture(autouse=True)
def salli_custom(enable_custom_integrations):
    """HA lataa custom_componentsin vain taman kanssa."""
    yield
