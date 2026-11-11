"""
TameerAI - In-Memory Login Rate Limiter (Phase 02A)

Provides a lightweight, thread-safe sliding window rate limiter
to prevent brute-force credential stuffing and password spraying attacks
against the login endpoint.
"""

import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List, Tuple


class LoginRateLimiter:
    """
    Dual-layer sliding window rate limiter for authentication endpoints:
    1. Account-level threshold: Max failed attempts against a specific account from an IP.
    2. IP-level threshold: Max failed attempts from a single IP across all accounts (spraying defense).
    """

    def __init__(
        self,
        max_attempts: int = 5,
        ip_max_attempts: int = 20,
        window_seconds: int = 300,
    ):
        self.max_attempts = max_attempts
        self.ip_max_attempts = ip_max_attempts
        self.window_seconds = window_seconds
        self._failures: Dict[str, List[float]] = defaultdict(list)
        self._lock = Lock()

    def is_rate_limited(self, key_or_ip: str, email: str = "") -> Tuple[bool, int]:
        """
        Checks if the request has exceeded rate limits.
        If email is provided, checks both per-account key and per-IP key.
        If email is empty, checks key_or_ip directly.
        Returns (is_limited, retry_after_seconds).
        """
        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            if email:
                ip_clean = key_or_ip.strip()
                email_clean = email.strip().lower()
                acc_key = f"acc:{ip_clean}:{email_clean}"
                ip_key = f"ip:{ip_clean}"

                # 1. Check account-level attempts
                valid_acc = [t for t in self._failures[acc_key] if t > cutoff]
                self._failures[acc_key] = valid_acc
                if len(valid_acc) >= self.max_attempts:
                    retry_after = int(self.window_seconds - (now - valid_acc[0])) + 1
                    return True, max(1, retry_after)

                # 2. Check IP-wide spraying attempts
                valid_ip = [t for t in self._failures[ip_key] if t > cutoff]
                self._failures[ip_key] = valid_ip
                if len(valid_ip) >= self.ip_max_attempts:
                    retry_after = int(self.window_seconds - (now - valid_ip[0])) + 1
                    return True, max(1, retry_after)

                return False, 0

            # Single-key fallback
            valid_timestamps = [t for t in self._failures[key_or_ip] if t > cutoff]
            self._failures[key_or_ip] = valid_timestamps
            if len(valid_timestamps) >= self.max_attempts:
                oldest_in_window = valid_timestamps[0]
                retry_after = int(self.window_seconds - (now - oldest_in_window)) + 1
                return True, max(1, retry_after)

            return False, 0

    def record_failure(self, key_or_ip: str, email: str = "") -> None:
        """Records a failed authentication attempt."""
        now = time.monotonic()
        with self._lock:
            if email:
                ip_clean = key_or_ip.strip()
                email_clean = email.strip().lower()
                self._failures[f"acc:{ip_clean}:{email_clean}"].append(now)
                self._failures[f"ip:{ip_clean}"].append(now)
            else:
                self._failures[key_or_ip].append(now)

    def record_success(self, key_or_ip: str, email: str = "") -> None:
        """Clears recorded failures for the specific account upon successful authentication."""
        with self._lock:
            if email:
                ip_clean = key_or_ip.strip()
                email_clean = email.strip().lower()
                self._failures.pop(f"acc:{ip_clean}:{email_clean}", None)
            else:
                self._failures.pop(key_or_ip, None)

    def reset(self) -> None:
        """Resets all tracked rate limiting state (useful for test isolation)."""
        with self._lock:
            self._failures.clear()


# Global singleton instance for login endpoint
login_limiter = LoginRateLimiter(max_attempts=5, ip_max_attempts=20, window_seconds=300)
