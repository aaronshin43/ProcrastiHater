import time
from collections import defaultdict
from shared.protocol import Packet

class SessionStats:
    """
    Records session statistics and distraction events for the Result Dashboard.
    Lives on the Client side to provide full history for the UI.
    """
    def __init__(self):
        # Cooldown to prevent counting the same event multiple times in a short burst (e.g. continuos detection)
        # Assuming Packet events are discrete triggers.
        self.last_event_time = defaultdict(float)
        self.cooldown = 5.0 # Seconds
        self.reset()

    def reset(self):
        """Reset all stats for a new session"""
        self.start_time = time.time()
        self.end_time = None
        self.events = [] # List of {"timestamp": float, "event": str, "data": dict}
        self.counts = defaultdict(int)
        self.last_event_time.clear()
        print("📊 Session Stats Reset")

    def record_event(self, packet: Packet):
        """Record a distraction event"""
        now = time.time()
        event_type = packet.event
        
        # Simple debounce/cooldown logic
        if now - self.last_event_time[event_type] < self.cooldown:
            return

        self.last_event_time[event_type] = now
        self.counts[event_type] += 1
        
        # Add relative time from start
        relative_time = now - self.start_time
        
        event_record = {
            "timestamp": now,
            "relative_time": relative_time,
            "event": event_type,
            "data": packet.data
        }
        self.events.append(event_record)
        
        print(f"📊 Stat Recorded: {event_type} (Total: {self.counts[event_type]})")

    def stop_session(self):
        """Mark session end"""
        self.end_time = time.time()
        print(f"📊 Session Ended. Duration: {self.get_duration():.1f}s")
        print(f"📊 Summary: {dict(self.counts)}")
    
    def get_duration(self) -> float:
        """Get session duration in seconds"""
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time

    def get_summary(self):
        """Return a summary dictionary for the dashboard"""
        duration = self.get_duration()
        total_counts = sum(self.counts.values())
        
        # Calculate 'Focused Time' (Rough estimate: Total Duration - (Distractions * Penalty))
        # Or just return raw duration and let UI decide
        
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": duration,
            "total_distractions": total_counts,
            "counts": dict(self.counts),
            "history": self.events
        }
