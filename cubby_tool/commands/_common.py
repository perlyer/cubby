import os
import re
from datetime import datetime, timedelta, timezone

from cubby_tool import config


def _resolve(args):
    """Return (home, cfg, namespace, reason)."""
    home = config.get_home()
    cfg = config.load_config(home)
    ns, reason = config.resolve_namespace(
        cfg,
        flag=getattr(args, "namespace", None),
        env=os.environ.get("CUBBY_NS"),
        cwd=os.getcwd(),
    )
    return home, cfg, ns, reason


def _env_var_name(secret_name: str) -> str:
    """Default environment-variable name for a secret: UPPER_SNAKE, no prefix."""
    return secret_name.upper().replace("-", "_")


_DURATION_RE = re.compile(r"^(\d+)([hdw])$")
_DURATION_UNITS = {"h": "hours", "d": "days", "w": "weeks"}


def _parse_duration(text: str) -> timedelta:
    """Parse a TTL duration like '12h', '30d', '2w' into a timedelta.
    Raises ValueError on anything else."""
    match = _DURATION_RE.match(text.strip())
    if not match:
        raise ValueError(
            f"invalid duration '{text}' — use <int><unit>, unit h/d/w (e.g. 30d)")
    amount = int(match.group(1))
    if amount <= 0:
        raise ValueError(f"invalid duration '{text}' — must be a positive amount")
    return timedelta(**{_DURATION_UNITS[match.group(2)]: amount})


def _ttl_to_expires(ttl: str) -> str:
    """Absolute ISO-8601 expiry for a duration string, measured from now."""
    return (datetime.now(timezone.utc) + _parse_duration(ttl)).isoformat()


def _format_relative(iso_timestamp: str) -> str:
    """Render an ISO-8601 timestamp as a human phrase relative to now, with no
    surrounding parentheses: 'in 89 days', 'in 5 hours', 'expired 3 days ago',
    'expires today', 'expired today'."""
    when = datetime.fromisoformat(iso_timestamp)
    secs = (when - datetime.now(timezone.utc)).total_seconds()
    future = secs >= 0
    secs = abs(secs)
    if secs < 3600:
        return "expires today" if future else "expired today"
    if secs < 86400:
        n, unit = round(secs / 3600), "hour"
        if n >= 24:
            n, unit = 1, "day"
    else:
        n, unit = round(secs / 86400), "day"
    plural = "" if n == 1 else "s"
    return f"in {n} {unit}{plural}" if future else f"expired {n} {unit}{plural} ago"


def _is_expired(entry: dict) -> bool:
    """True when the entry has an 'expires' timestamp that is in the past."""
    exp = entry.get("expires")
    if not exp:
        return False
    return datetime.fromisoformat(exp) < datetime.now(timezone.utc)


def _resolve_env_var(env_map: dict, secret_name: str) -> str:
    """The environment variable a secret is injected as: its env_map override,
    or the upper_snake default."""
    return env_map.get(secret_name, _env_var_name(secret_name))


def _env_var_clash(env_map: dict, secret_names, target_var: str, this_secret: str):
    """If a secret other than this_secret already resolves to target_var,
    return that secret's name; else None."""
    for name in secret_names:
        if name == this_secret:
            continue
        if _resolve_env_var(env_map, name) == target_var:
            return name
    return None
