from dataclasses import dataclass
import math


@dataclass
class Progress:
    stage: str = "Scanning sources"
    completed: int = 0
    total: int = 0
    probe_started: float = 0
    probe_finished: float = 0

    def update(self, stage: str, completed: int, total: int, timestamp: float) -> None:
        if stage == "Probing media":
            if self.stage != stage:
                self.probe_started = timestamp
            self.probe_finished = timestamp
        self.stage, self.completed, self.total = stage, completed, total

    @property
    def maximum(self) -> int:
        return 0 if self.stage in ("Preparing sources", "Scanning sources") else self.total + 2

    @property
    def value(self) -> int:
        extra = {"Writing Lua script": 1, "Complete": 2}.get(self.stage, 0)
        return self.completed + extra

    def status(self, now: float) -> str:
        if self.stage == "Scanning sources":
            return f"Scanning sources: {self.completed}/{self.total}  |  — items/s  |  ETA —"
        metrics = "— items/s  |  ETA —"
        if self.completed:
            end = now if self.stage == "Probing media" else self.probe_finished
            rate = self.completed / (end - self.probe_started)
            seconds = math.ceil((self.total - self.completed) / rate)
            eta = f"{seconds // 60}:{seconds % 60:02d}"
            if self.stage in ("Grouping clips", "Writing Lua script"):
                eta = "finalizing"
            metrics = f"{rate:.2f} items/s  |  ETA {eta}"
        label = "Lua script created" if self.stage == "Complete" else self.stage
        return f"{label}: {self.completed}/{self.total} items  |  {metrics}"
