import pytest
from pathlib import Path
from load_orchestrator.configuration import Config


VALID_YAML = """
adapter:
  type: locust
  test_file: tests/load_tests/locustfile.py
strategy:
  type: degradation_search
  initial_users: 10
  step_multiplier: 1.5
  threshold_count: 3
  window_size: 5
orchestrator:
  spawn_rate: 5
  max_users: 200
"""

MISSING_ORCHESTRATOR_YAML = """
adapter:
  type: locust
  test_file: tests/load_tests/locustfile.py
strategy:
  type: degradation_search
  initial_users: 10
  step_multiplier: 1.5
  threshold_count: 3
  window_size: 5
"""

MISSING_ADAPTER_YAML = """
strategy:
  type: degradation_search
"""

MISSING_STRATEGY_YAML = """
adapter:
  type: locust
  test_file: tests/load_tests/locustfile.py
"""


class TestConfigFromYaml:
    def test_loads_valid_config(self, tmp_path):
        # создаём фиктивный test_file чтобы валидация пути прошла
        locust_file = tmp_path / "locustfile.py"
        locust_file.write_text("")
        yaml_text = VALID_YAML.replace(
            "tests/load_tests/locustfile.py", str(locust_file)
        )
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml_text)

        config = Config.from_yaml(config_file)

        assert config.adapter.type == "locust"
        assert config.strategy.type == "degradation_search"
        assert config.strategy.params.get("initial_users") == 10
        assert config.strategy.params.get("step_multiplier") == 1.5
        assert config.strategy.params.get("threshold_count") == 3
        assert config.strategy.params.get("window_size") == 5
        assert config.orchestrator.max_users == 200

    def test_raises_when_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            Config.from_yaml("/nonexistent/path/config.yaml")

    def test_raises_when_adapter_section_missing(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(MISSING_ADAPTER_YAML)
        with pytest.raises(ValueError, match="adapter"):
            Config.from_yaml(config_file)

    def test_raises_when_strategy_section_missing(self, tmp_path):
        locust_file = tmp_path / "locustfile.py"
        locust_file.write_text("")
        yaml_text = MISSING_STRATEGY_YAML.replace(
            "tests/load_tests/locustfile.py", str(locust_file)
        )
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml_text)
        with pytest.raises(ValueError, match="strategy"):
            Config.from_yaml(config_file)

    def test_raises_when_test_file_does_not_exist(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(MISSING_STRATEGY_YAML)
        with pytest.raises(AttributeError):
            Config.from_yaml(config_file)

    def test_orchestrator_section_is_optional_with_defaults(self, tmp_path):
        locust_file = tmp_path / "locustfile.py"
        locust_file.write_text("")
        yaml_text = MISSING_ORCHESTRATOR_YAML.replace(
            "tests/load_tests/locustfile.py", str(locust_file)
        )
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml_text)

        config = Config.from_yaml(config_file)
        assert config.adapter.type == "locust"
        assert config.strategy.type == "degradation_search"
        assert config.orchestrator.spawn_rate == 10
        assert config.orchestrator.max_users is None
        assert config.orchestrator.monitoring_interval == 5
        assert config.orchestrator.max_wait_time is None

class TestConfigRoundTrip:
    def test_to_dict_and_back(self, tmp_path):
        locust_file = tmp_path / "locustfile.py"
        locust_file.write_text("")
        yaml_text = VALID_YAML.replace(
            "tests/load_tests/locustfile.py", str(locust_file)
        )
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml_text)
        config = Config.from_yaml(config_file)

        d = config.to_dict()

        assert d["adapter"]["type"] == config.adapter.type
        assert d["strategy"]["type"] == config.strategy.type

    def test_to_yaml_and_back(self, tmp_path):
        locust_file = tmp_path / "locustfile.py"
        locust_file.write_text("")
        yaml_text = VALID_YAML.replace(
            "tests/load_tests/locustfile.py", str(locust_file)
        )
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml_text)
        original = Config.from_yaml(config_file)

        saved_path = tmp_path / "saved.yaml"
        original.to_yaml(saved_path)
        restored = Config.from_yaml(saved_path)

        assert restored.adapter.type == original.adapter.type
        assert restored.adapter.port == original.adapter.port
        assert restored.strategy.type == original.strategy.type
        assert restored.strategy.params == original.strategy.params
        assert restored.orchestrator.spawn_rate == original.orchestrator.spawn_rate
        assert restored.orchestrator.max_users == original.orchestrator.max_users