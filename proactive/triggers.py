"""
Proactive Triggers — Evaluates system metrics and conditions to produce events.
"""
from datetime import datetime
from proactive.events import ProactiveEvent, EventPriority
from config import Config


class TriggerEvaluator:
    """Evaluates system state and produces ProactiveEvents when thresholds are exceeded."""

    def __init__(self, config: Config):
        self.config = config

    def evaluate_metrics(self, metrics: dict) -> list[ProactiveEvent]:
        """Evaluate system metrics snapshot and return any triggered events."""
        events = []

        cpu = metrics.get("cpu", 0)
        ram = metrics.get("ram", 0)
        disk = metrics.get("disk", 0)

        if cpu > self.config.cpu_threshold:
            events.append(ProactiveEvent(
                event_type="cpu_high",
                data={"percent": cpu},
                priority=EventPriority.HIGH,
                cooldown=300,
            ))

        if ram > self.config.ram_threshold:
            events.append(ProactiveEvent(
                event_type="ram_high",
                data={"percent": ram},
                priority=EventPriority.HIGH,
                cooldown=300,
            ))

        if disk > self.config.disk_threshold:
            events.append(ProactiveEvent(
                event_type="disk_high",
                data={"percent": disk},
                priority=EventPriority.CRITICAL,
                cooldown=1800,
            ))

        return events

    def evaluate_idle(self, idle_minutes: float) -> list[ProactiveEvent]:
        """Generate events based on user idle time."""
        events = []
        if idle_minutes >= 30:
            events.append(ProactiveEvent(
                event_type="idle_long",
                data={"minutes": int(idle_minutes)},
                priority=EventPriority.LOW,
                cooldown=1800,
            ))
        elif idle_minutes >= self.config.idle_threshold_min:
            events.append(ProactiveEvent(
                event_type="idle_short",
                data={"minutes": int(idle_minutes)},
                priority=EventPriority.LOW,
                cooldown=600,
            ))
        return events

    def evaluate_time_of_day(self) -> list[ProactiveEvent]:
        """Generate time-based events."""
        events = []
        hour = datetime.now().hour

        if 7 <= hour <= 9:
            events.append(ProactiveEvent(
                event_type="morning_greeting",
                data={"hour": hour},
                priority=EventPriority.NORMAL,
                cooldown=86400,  # Once per day
            ))
        elif hour >= 23 or hour < 4:
            events.append(ProactiveEvent(
                event_type="late_night",
                data={"time": datetime.now().strftime("%H:%M")},
                priority=EventPriority.NORMAL,
                cooldown=1800,
            ))

        return events
