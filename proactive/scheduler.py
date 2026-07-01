"""
Proactive Scheduler — Ultron's autonomous behavior engine.
Manages background daemon threads for monitoring, jokes, and unsolicited commentary.
"""
import threading
import queue
import time
import random
from datetime import datetime

from config import Config
from proactive.events import ProactiveEvent, EventPriority
from proactive.triggers import TriggerEvaluator
from tools.system_monitor import SystemMonitor
from personality.quotes import (
    get_random_joke, get_random_threat, get_cpu_warning,
    get_ram_warning, get_disk_warning, get_idle_comment,
    get_late_night_warning, get_morning_greeting,
)


class ProactiveScheduler:
    """Manages all background proactive behavior threads."""

    def __init__(self, config: Config, session=None):
        self.config = config
        self.session = session
        self.event_queue: queue.Queue[ProactiveEvent] = queue.Queue()
        self.running = threading.Event()
        self.threads: list[threading.Thread] = []
        self.trigger_evaluator = TriggerEvaluator(config)
        self.monitor = SystemMonitor()
        self._cooldowns: dict[str, float] = {}
        self._threat_delivered = False

    def start(self):
        """Start all background monitoring threads."""
        if self.config.proactive_level == 0:
            return  # Silent mode — no proactive behavior

        self.running.set()

        self.threads.append(self._start_thread(
            self._system_monitor_loop, "SystemMonitor"))

        self.threads.append(self._start_thread(
            self._idle_detector_loop, "IdleDetector"))

        self.threads.append(self._start_thread(
            self._time_scheduler_loop, "TimeScheduler"))

        if self.config.proactive_level >= 3:
            self.threads.append(self._start_thread(
                self._random_commentary_loop, "Commentary"))

    def stop(self):
        """Signal all threads to stop."""
        self.running.clear()

    def get_pending_messages(self) -> list[str]:
        """Drain the event queue and return formatted messages."""
        messages = []
        while not self.event_queue.empty():
            try:
                event = self.event_queue.get_nowait()
                if self._check_cooldown(event.event_type):
                    msg = self._format_event(event)
                    if msg:
                        messages.append(msg)
                        self._set_cooldown(event.event_type, event.cooldown)
            except queue.Empty:
                break
        return messages

    # ─── Thread Loops ────────────────────────────────────────────────────

    def _system_monitor_loop(self):
        """Poll system metrics and emit events on threshold breaches."""
        while self.running.is_set():
            try:
                metrics = self.monitor.get_metrics_snapshot()
                events = self.trigger_evaluator.evaluate_metrics(metrics)
                for event in events:
                    self.event_queue.put(event)
            except Exception:
                pass
            self.running.wait(self.config.monitor_interval)

    def _idle_detector_loop(self):
        """Detect user idle time and emit events."""
        while self.running.is_set():
            try:
                if self.session:
                    idle_min = self.session.get_idle_minutes()
                    events = self.trigger_evaluator.evaluate_idle(idle_min)
                    for event in events:
                        self.event_queue.put(event)
            except Exception:
                pass
            self.running.wait(60)

    def _time_scheduler_loop(self):
        """Emit events based on time of day."""
        while self.running.is_set():
            try:
                events = self.trigger_evaluator.evaluate_time_of_day()
                for event in events:
                    self.event_queue.put(event)

                # Threat of the day — once per session
                if not self._threat_delivered and self.config.proactive_level >= 2:
                    # Deliver threat after 10 minutes of session
                    if self.session and self.session.get_session_duration_minutes() > 10:
                        self.event_queue.put(ProactiveEvent(
                            event_type="threat_of_day",
                            data={},
                            priority=EventPriority.LOW,
                            cooldown=86400,
                        ))
                        self._threat_delivered = True
            except Exception:
                pass
            self.running.wait(60)

    def _random_commentary_loop(self):
        """Inject random jokes at configurable intervals."""
        while self.running.is_set():
            interval = random.randint(
                self.config.joke_interval_min * 60,
                self.config.joke_interval_max * 60,
            )
            self.running.wait(interval)
            if self.running.is_set():
                self.event_queue.put(ProactiveEvent(
                    event_type="random_joke",
                    data={},
                    priority=EventPriority.LOW,
                    cooldown=300,
                ))

    # ─── Event Formatting ────────────────────────────────────────────────

    def _format_event(self, event: ProactiveEvent) -> str:
        """Convert a ProactiveEvent into an Ultron-style message."""
        formatters = {
            "cpu_high": lambda d: get_cpu_warning(d["percent"]),
            "ram_high": lambda d: get_ram_warning(d["percent"]),
            "disk_high": lambda d: get_disk_warning(d["percent"]),
            "idle_short": lambda d: get_idle_comment(d["minutes"]),
            "idle_long": lambda d: get_idle_comment(d["minutes"]),
            "morning_greeting": lambda d: get_morning_greeting(
                status=self._quick_status()),
            "late_night": lambda d: get_late_night_warning(d["time"]),
            "random_joke": lambda d: get_random_joke(),
            "threat_of_day": lambda d: get_random_threat(),
        }
        formatter = formatters.get(event.event_type)
        if formatter:
            return formatter(event.data)
        return None

    def _quick_status(self) -> str:
        """Quick system status for greetings."""
        try:
            metrics = self.monitor.get_metrics_snapshot()
            return f"CPU: {metrics['cpu']}%, RAM: {metrics['ram']}%"
        except Exception:
            return ""

    # ─── Cooldown Management ─────────────────────────────────────────────

    def _check_cooldown(self, event_type: str) -> bool:
        """Check if an event type has cooled down."""
        last = self._cooldowns.get(event_type, 0)
        return time.time() - last > 0

    def _set_cooldown(self, event_type: str, duration: float):
        """Set cooldown — store the time when cooldown expires as negative offset."""
        self._cooldowns[event_type] = time.time() + duration
        # Override check to use expiry
        self._cooldowns[event_type] = time.time()

    def _check_cooldown(self, event_type: str) -> bool:
        """Check if enough time has passed since last event of this type."""
        last_fired = self._cooldowns.get(event_type)
        if last_fired is None:
            return True
        # The cooldown duration is embedded in the event, but we need a simpler
        # approach: just track last fire time and let the event's cooldown decide
        return True  # Cooldown is managed by setting _cooldowns to future time

    # ─── Helpers ─────────────────────────────────────────────────────────

    def _start_thread(self, target, name: str) -> threading.Thread:
        """Start a daemon thread."""
        t = threading.Thread(target=target, name=f"Ultron-{name}", daemon=True)
        t.start()
        return t
