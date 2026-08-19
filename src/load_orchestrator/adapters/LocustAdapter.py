import signal
import subprocess
from datetime import datetime
from pathlib import Path

import requests as rq
import time

from load_orchestrator.adapters.IAdapter import IAdapter
from ..configuration import _resolve_test_file
from ..models import RawMetrics


class LocustAdapter(IAdapter):
    DEFAULT_PORT = 8089
    DEFAULT_HOST = "0.0.0.0"

    def __init__(
            self, test_file: str, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
            locust_args: list[str] | None = None,
    ):
        resolved = str(_resolve_test_file(Path.cwd(), test_file))
        print(resolved)
        super().__init__(test_file=resolved)
        self._port = port
        self._session = rq.Session()
        self._web_host = host
        self._host = f"http://{host}:{self._port}"
        self._log_path = Path("logs.txt")
        self._log_path.write_text("")
        self._log_file = open(self._log_path, "a")
        self._locust_args = locust_args or []

    def update_locust_args(self, args: list[str]) -> None:
        self._locust_args = args

    def launch(self, debug, extra_args: list[str] | None = None) -> None:
        if extra_args:
            self._locust_args = extra_args

        cmd = [
            "locust",
            "-f",
            self.test_file,
            "--web-host",
            str(self._web_host),
            "--web-port",
            str(self._port),
        ]
        cmd.extend(self._locust_args)
        try:
            if debug:
                self._process = subprocess.Popen(cmd)
            else:
                self._process = subprocess.Popen(
                    cmd,
                    stdout=self._log_file,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    close_fds=True,
                    start_new_session=True,
                )
        except OSError as e:
            raise RuntimeError(
                f"Failed to start locust: {e}"
            ) from e
        time.sleep(1)
        self._check_crashed()

    def _read_logs(self, lines: int = 30) -> str:
        try:
            self._log_file.flush()
            with open(self._log_path) as f:
                all_lines = f.readlines()
                return ''.join(all_lines[-lines:]) if all_lines else "empty log"
        except Exception as e:
            return f"unreadable: {e}"

    def _check_crashed(self) -> None:
        """Проверяет, не упал ли процесс. Выбрасывает RuntimeError если упал."""
        if self._process is None:
            return

        code = self._process.poll()
        if code is not None:
            logs = self._read_logs()
            raise RuntimeError(
                f"Locust crashed (exit code {code}).\n"
                f"--- Last logs ---\n{logs}\n"
                f"-----------------"
            )

    def is_ready(self):
        self._check_crashed()
        try:
            r = self._session.get(self._host)
        except:
            print(f"⚠️ Locust не отвечает на {self._host}")
            return
        return r.status_code == 200

    def configure(self, **kwargs):
        self._check_crashed()
        try:
            r = self._session.post(f"{self._host}/swarm", data=kwargs, timeout=5)
            if not r.ok:
                raise RuntimeError(f"Failed to configure locust: {r.status_code} {r.text}")
        except rq.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to connect to locust for configuration: {e}")

    def stop(self):
        """Останавливает locust. Не выбрасывает исключения при ошибках подключения."""
        # Если процесс уже мёртв — нечего останавливать
        if self._process is None:
            return

        # Пытаемся мягко остановить через API
        if self._process.poll() is None:
            try:
                self._session.get(f"{self._host}/stop", timeout=5)
            except rq.exceptions.RequestException:
                pass  # Уже упал или не отвечает — не важно

        try:
            if self._process.poll() is None:
                self._process.send_signal(signal.SIGINT)
                try:
                    self._process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait(timeout=2)
        except Exception:
            pass  # Уже мёртв или нет прав — не важно

        # Закрываем лог
        try:
            self._log_file.close()
        except Exception:
            pass

    def get_stats(self):
        self._check_crashed()
        try:
            r = self._session.get(f"{self._host}/stats/requests", timeout=5)
            r.raise_for_status()
        except rq.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to get stats from locust: {e}")
        data = r.json()

        aggregated = next(
            (s for s in data.get("stats", []) if s.get("name") == "Aggregated"), {}
        )
        return RawMetrics(
            timestamp=datetime.now().timestamp(),
            users=data.get("user_count", 0),
            rps=data.get("total_rps", 0),
            rt_avg=aggregated.get("avg_response_time", 0),  # Среднее время ответа
            p50=aggregated.get("median_response_time", 0),
            p95=aggregated.get("response_time_percentile_0.95", 0),
            p99=aggregated.get("response_time_percentile_0.99", 0),
            error_rate=data.get("fail_ratio", 0)
                       * 100,  # fail_ratio это 0.0-1.0, переводим в %
            total_requests=aggregated.get("num_requests", 0),
            failed_requests=aggregated.get("num_failures", 0),
        )
