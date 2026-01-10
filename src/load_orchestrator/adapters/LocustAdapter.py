import subprocess
from datetime import datetime

from src.load_orchestrator.interfaces.IAdapter import IAdapter
import requests as rq
from src.load_orchestrator.models import RawMetrics

class LocustAdapter(IAdapter):

    DEFAULT_PORT = 8089
    DEFAULT_HOST = "0.0.0.0"
    def __init__(self, test_file: str, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        super().__init__(test_file=test_file)
        self._port = port
        self._session = rq.Session()
        self._host = f"http://{host}:{self._port}"

    def launch(self):
        self._process = subprocess.Popen([
            "locust",
            "-f", self.test_file,
            "--web-port", str(self._port),
        ])

    def is_ready(self):
        try:
            r = self._session.get(self._host)
        except:
            return False
        return r.status_code == 200


    def configure(self, user_count, spawn_rate):
        r = self._session.post(f"{self._host}/swarm", data=dict(user_count=user_count, spawn_rate=spawn_rate))
        print(r.text)

    def stop(self):
        self._session.get(f"{self._host}/stop")

    def get_stats(self):
        r = self._session.get(f"{self._host}/stats/requests")
        data = r.json()

        aggregated = next(
        (s for s in data.get("stats", []) if s.get("name") == "Aggregated"),
        {}
        )
        return RawMetrics(
            timestamp=datetime.now().timestamp(),
            users=data.get("user_count", 0),
            rps=data.get("total_rps", 0),
            rt_avg=aggregated.get("avg_response_time", 0),  # Среднее время ответа
            p50=aggregated.get("median_response_time", 0),
            p95=aggregated.get("response_time_percentile_0.95", 0),
            p99=aggregated.get("response_time_percentile_0.99", 0),
            error_rate=data.get("fail_ratio", 0) * 100,  # fail_ratio это 0.0-1.0, переводим в %
            total_requests=aggregated.get("num_requests", 0),
            failed_requests=aggregated.get("num_failures", 0)
        )

