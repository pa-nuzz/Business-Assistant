"""
Circuit Breaker for AI Providers.

Prevents cascading failures when an AI provider is down or slow.
Uses a simple state machine: CLOSED -> OPEN -> HALF_OPEN
"""
import time
import logging
from enum import Enum
from threading import Lock
from typing import Callable, Any, Optional, TypeVar
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation, requests pass through
    OPEN = "open"          # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5          # Number of failures before opening
    success_threshold: int = 2          # Successes in half-open before closing
    timeout: float = 30.0               # Seconds before trying half-open
    excluded_exceptions: tuple = ()     # Exception types that don't count as failures


@dataclass
class CircuitBreakerStats:
    """Runtime statistics for monitoring."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changes: int = 0


class CircuitBreaker:
    """
    Circuit breaker implementation for AI provider calls.
    
    States:
    - CLOSED: Normal operation, requests pass through. On failure, increment counter.
              If failures reach threshold, transition to OPEN.
    - OPEN: Requests fail immediately without calling the provider.
            After timeout, transition to HALF_OPEN.
    - HALF_OPEN: Allow a test request. If successful, transition to CLOSED.
                 If failed, transition back to OPEN.
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._stats = CircuitBreakerStats()
        self._lock = Lock()
        self._last_state_change = time.time()
    
    @property
    def state(self) -> CircuitState:
        with self._lock:
            # Check if we should transition from OPEN to HALF_OPEN
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_state_change >= self.config.timeout:
                    self._transition_to(CircuitState.HALF_OPEN)
            return self._state
    
    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state."""
        old_state = self._state
        self._state = new_state
        self._last_state_change = time.time()
        self._stats.state_changes += 1
        
        if new_state == CircuitState.HALF_OPEN:
            self._stats.consecutive_successes = 0
        elif new_state == CircuitState.CLOSED:
            self._stats.consecutive_failures = 0
        elif new_state == CircuitState.OPEN:
            self._stats.consecutive_successes = 0
        
        logger.info(
            f"Circuit breaker '{self.name}' transitioned: {old_state.value} -> {new_state.value}"
        )
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            func: The function to call
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            The result of the function call
            
        Raises:
            CircuitBreakerOpenError: If circuit is OPEN
            Exception: Any exception raised by the function
        """
        # Check state and potentially transition
        current_state = self.state
        
        if current_state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Try again after {self.config.timeout}s."
            )
        
        # Execute the function
        start_time = time.time()
        self._stats.total_calls += 1
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.excluded_exceptions:
            # Excluded exceptions don't count as failures
            self._on_success()
            raise
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self) -> None:
        with self._lock:
            self._stats.successful_calls += 1
            self._stats.consecutive_failures = 0
            self._stats.consecutive_successes += 1
            self._stats.last_success_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                if self._stats.consecutive_successes >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
    
    def _on_failure(self) -> None:
        with self._lock:
            self._stats.failed_calls += 1
            self._stats.consecutive_failures += 1
            self._stats.consecutive_successes = 0
            self._stats.last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open goes back to open
                self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                if self._stats.consecutive_failures >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)
    
    def get_stats(self) -> dict:
        """Get current statistics for monitoring."""
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "total_calls": self._stats.total_calls,
                "successful_calls": self._stats.successful_calls,
                "failed_calls": self._stats.failed_calls,
                "consecutive_failures": self._stats.consecutive_failures,
                "consecutive_successes": self._stats.consecutive_successes,
                "success_rate": (
                    self._stats.successful_calls / self._stats.total_calls
                    if self._stats.total_calls > 0 else 0
                ),
                "last_failure_time": self._stats.last_failure_time,
                "last_success_time": self._stats.last_success_time,
                "state_changes": self._stats.state_changes,
            }
    
    def reset(self) -> None:
        """Manually reset the circuit breaker to CLOSED state."""
        with self._lock:
            self._transition_to(CircuitState.CLOSED)
            self._stats = CircuitBreakerStats()
            logger.info(f"Circuit breaker '{self.name}' manually reset")


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is OPEN and request is blocked."""
    pass


# Global registry for circuit breakers
_circuit_breakers: dict[str, CircuitBreaker] = {}
_registry_lock = Lock()


def get_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None,
) -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    with _registry_lock:
        if name not in _circuit_breakers:
            _circuit_breakers[name] = CircuitBreaker(name, config)
        return _circuit_breakers[name]


def get_all_circuit_breaker_stats() -> dict[str, dict]:
    """Get stats for all registered circuit breakers."""
    with _registry_lock:
        return {name: cb.get_stats() for name, cb in _circuit_breakers.items()}


def reset_all_circuit_breakers() -> None:
    """Reset all circuit breakers to CLOSED state."""
    with _registry_lock:
        for cb in _circuit_breakers.values():
            cb.reset()