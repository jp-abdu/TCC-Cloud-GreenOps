"""
scripts/check_setup.py
----------------------
Verifica se o ambiente esta configurado corretamente.
Testa as tres fontes de dados e o motor SCI.

Uso:
    python scripts/check_setup.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def check(label, fn):
    try:
        fn()
        print(f"  OK  {label}")
        return True
    except Exception as e:
        print(f"  FALHOU  {label}")
        print(f"          {e}")
        return False


def main():
    print("\nVerificando ambiente GreenArch...\n")
    ok = True

    # Fonte 1: instance_energy (offline)
    def test_energy():
        from core.data_sources.instance_energy import get_instance_energy_kwh
        r = get_instance_energy_kwh("t3.medium")
        assert r["energy_kwh_hour"] > 0

    # Fonte 2: carbon_intensity (offline)
    def test_carbon():
        from core.data_sources.carbon_intensity import get_carbon_intensity
        r = get_carbon_intensity("us-east-1")
        assert r["carbon_intensity_gco2_kwh"] > 0

    # Fonte 3: aws_pricing (requer internet)
    def test_pricing():
        from core.data_sources.aws_pricing import get_ec2_ondemand_price
        r = get_ec2_ondemand_price("t3.medium", "us-east-1")
        assert r["price_usd_hour"] > 0

    # Motor SCI completo
    def test_sci():
        from core.sci_calculator import SCICalculator
        calc = SCICalculator()
        r = calc.calculate({"instance_type": "t3.medium", "region": "us-east-1"})
        assert r["sci_score_gco2_per_hour"] > 0

    ok &= check("instance_energy.py  (offline)", test_energy)
    ok &= check("carbon_intensity.py (offline)", test_carbon)
    ok &= check("aws_pricing.py      (internet)", test_pricing)
    ok &= check("sci_calculator.py   (completo)", test_sci)

    print()
    if ok:
        print("  Tudo funcionando. Pode rodar o dashboard.\n")
        print("  streamlit run dashboard/app.py\n")
    else:
        print("  Corrija os erros acima antes de continuar.\n")


if __name__ == "__main__":
    main()
