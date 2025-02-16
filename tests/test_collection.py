import pytest
from commandagi_j2.utils.collection import DataCollector, Episode
import json
from pathlib import Path


class TestDataCollector:
    @pytest.fixture
    def collector(self, tmp_path):
        return DataCollector(save_dir=str(tmp_path))

    def test_reset(self, collector):
        collector.reset()
        assert isinstance(collector.current_episode, Episode)
        assert len(collector.current_episode.observations) == 0
        assert len(collector.current_episode.actions) == 0
        assert len(collector.current_episode.rewards) == 0
        assert len(collector.current_episode.infos) == 0
        assert collector.current_episode.total_reward == 0.0

    def test_add_step(self, collector):
        collector.add_step(
            observation="test.png",
            action="click 100,100",
            reward=1.0,
            info={"success": True},
        )

        assert len(collector.current_episode.observations) == 1
        assert len(collector.current_episode.actions) == 1
        assert len(collector.current_episode.rewards) == 1
        assert len(collector.current_episode.infos) == 1
        assert collector.current_episode.total_reward == 1.0

    def test_save_episode(self, collector):
        collector.add_step("test.png", "click 100,100", 1.0, {"success": True})
        collector.save_episode(0)

        saved_file = Path(collector.save_dir) / "episode_0.json"
        assert saved_file.exists()

        with open(saved_file) as f:
            data = json.load(f)
            assert "observations" in data
            assert "actions" in data
            assert "rewards" in data
            assert "infos" in data
            assert "total_reward" in data
