import pytest

from imbh_nuclei.config import (
    ClusterConfig,
    IntegrationConfig,
    PopulationConfig,
    SimulationConfig,
)


def test_defaults_match_paper_fiducial_run():
    cfg = SimulationConfig()
    assert cfg.cluster.m_smbh == 4.0e6
    assert cfg.cluster.alpha_star == 1.25
    assert cfg.cluster.alpha_bh == 1.83
    assert cfg.population.n_bh == 1000
    assert cfg.integration.t_max_gyr == 10.0


def test_invalid_initial_distribution_rejected():
    with pytest.raises(ValueError):
        PopulationConfig(initial_mass_distribution="not-a-real-distribution")


def test_roundtrip_through_yaml(tmp_path):
    cfg = SimulationConfig(
        cluster=ClusterConfig(m_smbh=1.0e5),
        population=PopulationConfig(initial_mass_distribution="K20", n_bh=500),
        integration=IntegrationConfig(seed=42),
    )
    path = tmp_path / "run.yaml"
    cfg.to_yaml(path)
    loaded = SimulationConfig.from_yaml(path)

    assert loaded == cfg


def test_default_yaml_file_loads(tmp_path):
    # config/default.yaml lives two levels up from tests/
    default_path = (
        __file__.rsplit("/tests/", 1)[0] + "/config/default.yaml"
    )
    cfg = SimulationConfig.from_yaml(default_path)
    assert cfg.cluster.m_smbh == 4.0e6
    assert cfg.population.initial_mass_distribution == "H18+M"
