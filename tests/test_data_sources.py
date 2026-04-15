"""
test_data_sources.py
--------------------
Testes unitários para as três fontes de dados do GreenArch.
Roda completamente offline (sem chamadas de rede) exceto test_aws_pricing_live.

Execute com:
    cd greenarch
    pytest tests/ -v

Para pular o teste que faz chamada real à AWS:
    pytest tests/ -v -m "not live"
"""

import pytest
import sys
from pathlib import Path

# Adiciona o root do projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.data_sources.instance_energy import (
    get_instance_energy_kwh,
    list_supported_instances,
    DEFAULT_CPU_UTILIZATION,
    AWS_PUE,
)
from core.data_sources.carbon_intensity import (
    get_carbon_intensity,
    get_all_regions_intensity,
    rank_regions_by_carbon,
)


# ─────────────────────────────────────────────────────────────────────────────
# TESTES: instance_energy.py
# ─────────────────────────────────────────────────────────────────────────────

class TestInstanceEnergy:

    def test_t3_medium_returns_correct_structure(self):
        """Verifica que o retorno tem todos os campos esperados."""
        result = get_instance_energy_kwh("t3.medium")
        assert "instance_type" in result
        assert "energy_kwh_hour" in result
        assert "energy_kwh_hour_with_pue" in result
        assert "watts_at_utilization" in result
        assert "pue" in result

    def test_t3_medium_values_are_positive(self):
        """Energia deve ser sempre positiva."""
        result = get_instance_energy_kwh("t3.medium")
        assert result["energy_kwh_hour"] > 0
        assert result["energy_kwh_hour_with_pue"] > 0
        assert result["watts_at_utilization"] > 0

    def test_pue_applied_correctly(self):
        """energy_with_pue deve ser energy × PUE."""
        result = get_instance_energy_kwh("t3.medium")
        expected = result["energy_kwh_hour"] * AWS_PUE
        assert abs(result["energy_kwh_hour_with_pue"] - expected) < 1e-6

    def test_higher_utilization_means_more_energy(self):
        """CPU mais alto deve consumir mais energia."""
        low = get_instance_energy_kwh("m5.large", cpu_utilization=0.1)
        high = get_instance_energy_kwh("m5.large", cpu_utilization=0.9)
        assert high["energy_kwh_hour"] > low["energy_kwh_hour"]

    def test_zero_utilization_equals_min_watts(self):
        """Com 0% de CPU, watts deve igual ao min_watts."""
        result = get_instance_energy_kwh("c5.xlarge", cpu_utilization=0.0)
        assert abs(result["watts_at_utilization"] - result["min_watts"]) < 1e-3

    def test_full_utilization_equals_max_watts(self):
        """Com 100% de CPU, watts deve igual ao max_watts."""
        result = get_instance_energy_kwh("c5.xlarge", cpu_utilization=1.0)
        assert abs(result["watts_at_utilization"] - result["max_watts"]) < 1e-3

    def test_gpu_instance_has_higher_consumption(self):
        """Instância GPU deve consumir mais que instância de propósito geral similar."""
        gpu = get_instance_energy_kwh("g4dn.xlarge", cpu_utilization=0.5)
        general = get_instance_energy_kwh("t3.xlarge", cpu_utilization=0.5)
        assert gpu["energy_kwh_hour"] > general["energy_kwh_hour"]

    def test_unknown_instance_raises_valueerror(self):
        """Instância inexistente deve lançar ValueError."""
        with pytest.raises(ValueError, match="não encontrada"):
            get_instance_energy_kwh("z99.supermega", cpu_utilization=0.5)

    def test_graviton_more_efficient_than_intel(self):
        """Família Graviton (t4g) deve ser mais eficiente que Intel (t3) no mesmo tamanho."""
        graviton = get_instance_energy_kwh("t4g.medium", cpu_utilization=0.5)
        intel = get_instance_energy_kwh("t3.medium", cpu_utilization=0.5)
        assert graviton["energy_kwh_hour"] < intel["energy_kwh_hour"]

    def test_list_supported_instances_not_empty(self):
        """Dataset deve ter instâncias cadastradas."""
        instances = list_supported_instances()
        assert len(instances) > 30
        assert "t3.medium" in instances
        assert "m5.large" in instances
        assert "c5.2xlarge" in instances


# ─────────────────────────────────────────────────────────────────────────────
# TESTES: carbon_intensity.py
# ─────────────────────────────────────────────────────────────────────────────

class TestCarbonIntensity:

    def test_us_east_1_returns_correct_structure(self):
        """Verifica estrutura do retorno."""
        result = get_carbon_intensity("us-east-1")
        assert "region" in result
        assert "carbon_intensity_gco2_kwh" in result
        assert "source" in result

    def test_all_known_regions_return_positive_values(self):
        """Todas as regiões devem ter intensidade positiva."""
        all_regions = get_all_regions_intensity()
        for region, intensity in all_regions.items():
            assert intensity > 0, f"Região {region} tem intensidade zero ou negativa"

    def test_eu_north_1_cleaner_than_us_east_1(self):
        """Estocolmo (hidro+nuclear) deve ser mais limpa que Virginia (carvão+gás)."""
        stockholm = get_carbon_intensity("eu-north-1")
        virginia = get_carbon_intensity("us-east-1")
        assert stockholm["carbon_intensity_gco2_kwh"] < virginia["carbon_intensity_gco2_kwh"]

    def test_sa_east_1_cleaner_than_ap_south_1(self):
        """São Paulo (hidro) deve ser mais limpa que Mumbai (carvão)."""
        sao_paulo = get_carbon_intensity("sa-east-1")
        mumbai = get_carbon_intensity("ap-south-1")
        assert sao_paulo["carbon_intensity_gco2_kwh"] < mumbai["carbon_intensity_gco2_kwh"]

    def test_unknown_region_raises_valueerror(self):
        """Região inexistente deve lançar ValueError."""
        with pytest.raises(ValueError, match="não encontrada"):
            get_carbon_intensity("br-south-99")

    def test_rank_ascending_starts_with_cleanest(self):
        """Ranking ascendente deve começar com a região mais limpa."""
        ranked = rank_regions_by_carbon(ascending=True)
        assert len(ranked) > 0
        # eu-north-1 (Estocolmo, 13 gCO2/kWh) deve ser a primeira
        assert ranked[0]["region"] == "eu-north-1"
        # E o valor deve ser o menor
        intensities = [r["carbon_intensity_gco2_kwh"] for r in ranked]
        assert intensities == sorted(intensities)

    def test_rank_descending_starts_with_dirtiest(self):
        """Ranking descendente deve começar com a região mais carbono-intensiva."""
        ranked = rank_regions_by_carbon(ascending=False)
        intensities = [r["carbon_intensity_gco2_kwh"] for r in ranked]
        assert intensities == sorted(intensities, reverse=True)

    def test_all_regions_present_in_ranking(self):
        """Ranking deve incluir todas as regiões do dataset."""
        all_regions = get_all_regions_intensity()
        ranked = rank_regions_by_carbon()
        assert len(ranked) == len(all_regions)

    def test_oregon_cleaner_than_ohio(self):
        """Oregon (us-west-2, hidro) deve ser mais limpa que Ohio (us-east-2, carvão)."""
        oregon = get_carbon_intensity("us-west-2")
        ohio = get_carbon_intensity("us-east-2")
        assert oregon["carbon_intensity_gco2_kwh"] < ohio["carbon_intensity_gco2_kwh"]


# ─────────────────────────────────────────────────────────────────────────────
# TESTES: integração entre os módulos (sem chamada de rede)
# ─────────────────────────────────────────────────────────────────────────────

class TestIntegration:

    def test_sci_components_combine_correctly(self):
        """
        Verifica que E × I + M produz resultado razoável.
        Não testa o SCICalculator (que precisa de rede), mas valida
        que as duas fontes offline produzem valores compatíveis.
        """
        energy = get_instance_energy_kwh("t3.medium", cpu_utilization=0.5)
        carbon = get_carbon_intensity("us-east-1")

        E = energy["energy_kwh_hour_with_pue"]
        I = carbon["carbon_intensity_gco2_kwh"]

        operational_carbon = E * I  # gCO2eq/hora

        # Para t3.medium em us-east-1, esperamos algo entre 5 e 50 gCO2/hora
        assert 1.0 < operational_carbon < 100.0, (
            f"Carbono operacional fora do esperado: {operational_carbon:.2f} gCO2/h"
        )

    def test_cleaner_region_produces_lower_carbon(self):
        """
        Mesma instância em região mais limpa deve produzir menos carbono.
        """
        energy = get_instance_energy_kwh("m5.large", cpu_utilization=0.5)
        E = energy["energy_kwh_hour_with_pue"]

        dirty = get_carbon_intensity("us-east-1")
        clean = get_carbon_intensity("eu-north-1")

        carbon_dirty = E * dirty["carbon_intensity_gco2_kwh"]
        carbon_clean = E * clean["carbon_intensity_gco2_kwh"]

        assert carbon_clean < carbon_dirty

    def test_graviton_has_lower_sci_than_intel_same_region(self):
        """
        t4g (Graviton, mais eficiente) deve ter SCI menor que t3 (Intel)
        na mesma região, assumindo utilização igual.
        """
        graviton_energy = get_instance_energy_kwh("t4g.medium", 0.5)
        intel_energy = get_instance_energy_kwh("t3.medium", 0.5)
        carbon = get_carbon_intensity("us-east-1")

        I = carbon["carbon_intensity_gco2_kwh"]
        sci_graviton = graviton_energy["energy_kwh_hour_with_pue"] * I
        sci_intel = intel_energy["energy_kwh_hour_with_pue"] * I

        assert sci_graviton < sci_intel, (
            f"Graviton ({sci_graviton:.2f}) deveria ter SCI menor que Intel ({sci_intel:.2f})"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TESTE LIVE: aws_pricing.py (requer internet)
# Marcado com @pytest.mark.live — pule com: pytest -m "not live"
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.live
class TestAWSPricingLive:
    """
    Testes que fazem chamada real à AWS Pricing Bulk API.
    Requerem internet mas NÃO requerem conta AWS.
    """

    def test_t3_medium_us_east_1_returns_price(self):
        """Deve retornar um preço positivo para t3.medium em us-east-1."""
        from core.data_sources.aws_pricing import get_ec2_ondemand_price
        result = get_ec2_ondemand_price("t3.medium", "us-east-1")
        assert result["price_usd_hour"] > 0
        assert result["price_usd_month"] > 0
        assert result["vcpu"] is not None

    def test_price_structure_complete(self):
        """Verifica todos os campos do retorno."""
        from core.data_sources.aws_pricing import get_ec2_ondemand_price
        result = get_ec2_ondemand_price("m5.large", "us-east-1")
        required_keys = [
            "instance_type", "region", "region_name",
            "os", "price_usd_hour", "price_usd_month",
            "vcpu", "memory_gib"
        ]
        for key in required_keys:
            assert key in result, f"Campo '{key}' ausente no retorno"

    def test_t3_medium_price_in_expected_range(self):
        """t3.medium Linux on-demand deve custar entre $0.03 e $0.06/hora."""
        from core.data_sources.aws_pricing import get_ec2_ondemand_price
        result = get_ec2_ondemand_price("t3.medium", "us-east-1")
        price = result["price_usd_hour"]
        assert 0.03 <= price <= 0.06, (
            f"Preço fora do esperado: ${price}/hora "
            "(esperado entre $0.03 e $0.06 — verifique se a tabela da AWS mudou)"
        )

    def test_invalid_instance_raises_error(self):
        """Instância inexistente deve lançar ValueError."""
        from core.data_sources.aws_pricing import get_ec2_ondemand_price
        with pytest.raises(ValueError):
            get_ec2_ondemand_price("z99.supermega", "us-east-1")

    def test_invalid_region_raises_error(self):
        """Região inválida deve lançar ValueError."""
        from core.data_sources.aws_pricing import get_ec2_ondemand_price
        with pytest.raises(ValueError, match="não reconhecida"):
            get_ec2_ondemand_price("t3.medium", "br-south-99")
