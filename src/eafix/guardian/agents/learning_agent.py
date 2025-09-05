"""Learning agent for pattern recognition and adaptive behavior."""

import logging
import sqlite3
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import json


@dataclass
class LearningEvent:
    """Represents a learning event."""
    event_type: str
    data: Dict[str, Any]
    outcome: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)


@dataclass
class Pattern:
    """Represents a learned pattern."""
    pattern_id: str
    pattern_type: str
    conditions: Dict[str, Any]
    success_rate: float
    occurrences: int
    last_seen: datetime
    confidence: float


class LearningAgent:
    """Production learning agent for pattern recognition and system adaptation."""
    
    def __init__(self, db_path: str = "learning_agent.db"):
        self.logger = logging.getLogger(__name__)
        self.db_path = Path(db_path)
        self.events: deque = deque(maxlen=10000)  # Keep recent events in memory
        self.patterns: Dict[str, Pattern] = {}
        self.pattern_stats = defaultdict(lambda: {"success": 0, "failure": 0})
        
        # Learning parameters
        self.min_pattern_occurrences = 5
        self.min_confidence_threshold = 0.6
        self.learning_enabled = True
        
        # Initialize database
        self._init_database()
        self._load_patterns()
    
    def _init_database(self) -> None:
        """Initialize the learning database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS learning_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,
                        data TEXT NOT NULL,
                        outcome TEXT,
                        timestamp TEXT NOT NULL,
                        tags TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS patterns (
                        pattern_id TEXT PRIMARY KEY,
                        pattern_type TEXT NOT NULL,
                        conditions TEXT NOT NULL,
                        success_rate REAL NOT NULL,
                        occurrences INTEGER NOT NULL,
                        last_seen TEXT NOT NULL,
                        confidence REAL NOT NULL
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_events_type_time 
                    ON learning_events(event_type, timestamp)
                """)
                
                conn.commit()
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to initialize learning database: {e}")
    
    def _load_patterns(self) -> None:
        """Load existing patterns from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM patterns")
                
                for row in cursor.fetchall():
                    pattern = Pattern(
                        pattern_id=row[0],
                        pattern_type=row[1],
                        conditions=json.loads(row[2]),
                        success_rate=row[3],
                        occurrences=row[4],
                        last_seen=datetime.fromisoformat(row[5]),
                        confidence=row[6]
                    )
                    self.patterns[pattern.pattern_id] = pattern
                    
        except sqlite3.Error as e:
            self.logger.error(f"Failed to load patterns: {e}")
    
    def record(self, event: dict) -> None:
        """Record a learning event."""
        if not self.learning_enabled:
            return
            
        try:
            learning_event = LearningEvent(
                event_type=event.get("type", "unknown"),
                data=event.get("data", {}),
                outcome=event.get("outcome"),
                tags=event.get("tags", [])
            )
            
            # Add to memory
            self.events.append(learning_event)
            
            # Store in database
            self._store_event(learning_event)
            
            # Update pattern recognition
            self._update_patterns(learning_event)
            
            self.logger.debug(f"Recorded learning event: {learning_event.event_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to record learning event: {e}")
    
    def _store_event(self, event: LearningEvent) -> None:
        """Store event in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO learning_events 
                    (event_type, data, outcome, timestamp, tags)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    event.event_type,
                    json.dumps(event.data),
                    event.outcome,
                    event.timestamp.isoformat(),
                    json.dumps(event.tags)
                ))
                conn.commit()
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to store event: {e}")
    
    def _update_patterns(self, event: LearningEvent) -> None:
        """Update pattern recognition based on new event."""
        try:
            # Simple pattern detection based on event type and outcome
            pattern_key = f"{event.event_type}_{event.outcome}"
            
            if event.outcome:
                stats = self.pattern_stats[pattern_key]
                if event.outcome in ["success", "profit", "completed"]:
                    stats["success"] += 1
                else:
                    stats["failure"] += 1
                
                total = stats["success"] + stats["failure"]
                if total >= self.min_pattern_occurrences:
                    success_rate = stats["success"] / total
                    confidence = min(total / 100.0, 1.0)  # Confidence increases with more data
                    
                    if success_rate >= self.min_confidence_threshold:
                        pattern = Pattern(
                            pattern_id=pattern_key,
                            pattern_type=event.event_type,
                            conditions={"event_type": event.event_type},
                            success_rate=success_rate,
                            occurrences=total,
                            last_seen=event.timestamp,
                            confidence=confidence
                        )
                        self.patterns[pattern_key] = pattern
                        self._store_pattern(pattern)
                        
        except Exception as e:
            self.logger.error(f"Failed to update patterns: {e}")
    
    def _store_pattern(self, pattern: Pattern) -> None:
        """Store pattern in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO patterns 
                    (pattern_id, pattern_type, conditions, success_rate, occurrences, last_seen, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    pattern.pattern_id,
                    pattern.pattern_type,
                    json.dumps(pattern.conditions),
                    pattern.success_rate,
                    pattern.occurrences,
                    pattern.last_seen.isoformat(),
                    pattern.confidence
                ))
                conn.commit()
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to store pattern: {e}")
    
    def get_patterns(self, pattern_type: Optional[str] = None, min_confidence: float = 0.0) -> List[Pattern]:
        """Get learned patterns matching criteria."""
        patterns = []
        for pattern in self.patterns.values():
            if pattern_type and pattern.pattern_type != pattern_type:
                continue
            if pattern.confidence < min_confidence:
                continue
            patterns.append(pattern)
        
        # Sort by confidence descending
        return sorted(patterns, key=lambda p: p.confidence, reverse=True)
    
    def predict_outcome(self, event_type: str, data: Dict[str, Any]) -> Optional[Tuple[str, float]]:
        """Predict outcome based on learned patterns."""
        matching_patterns = self.get_patterns(pattern_type=event_type, min_confidence=self.min_confidence_threshold)
        
        if not matching_patterns:
            return None
        
        # Use the most confident pattern
        best_pattern = matching_patterns[0]
        return ("success" if best_pattern.success_rate > 0.5 else "failure", best_pattern.confidence)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get learning agent statistics."""
        return {
            "total_events": len(self.events),
            "total_patterns": len(self.patterns),
            "high_confidence_patterns": len([p for p in self.patterns.values() if p.confidence > 0.8]),
            "learning_enabled": self.learning_enabled,
            "pattern_types": list(set(p.pattern_type for p in self.patterns.values()))
        }
    
    def cleanup_old_data(self, days: int = 30) -> None:
        """Clean up old learning data."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    DELETE FROM learning_events 
                    WHERE datetime(timestamp) < ?
                """, (cutoff_date.isoformat(),))
                conn.commit()
                
            self.logger.info(f"Cleaned up learning data older than {days} days")
            
        except sqlite3.Error as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
