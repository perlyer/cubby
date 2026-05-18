import json
import os
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_HOME = Path("~/.config/cubby").expanduser()


def get_home() -> Path:
    return Path(os.environ.get("CUBBY_HOME", str(DEFAULT_HOME))).expanduser()


@dataclass
class Namespace:
    cwd_prefix: str | None = None
    env_map: dict = field(default_factory=dict)


@dataclass
class Config:
    default_namespace: str = ""
    key_mode: str = "file"
    namespaces: dict = field(default_factory=dict)
    audit: bool = False


def config_path(home: Path) -> Path:
    return home / "config.json"


def load_config(home: Path) -> Config:
    path = config_path(home)
    if not path.exists():
        return Config()
    raw = json.loads(path.read_text())
    namespaces = {
        name: Namespace(cwd_prefix=ns.get("cwd_prefix"), env_map=ns.get("env_map", {}))
        for name, ns in raw.get("namespaces", {}).items()
    }
    return Config(
        default_namespace=raw.get("default_namespace", ""),
        key_mode=raw.get("key_mode", "file"),
        namespaces=namespaces,
        audit=raw.get("audit", False),
    )


def save_config(home: Path, cfg: Config) -> None:
    home.mkdir(parents=True, exist_ok=True)
    data = {
        "default_namespace": cfg.default_namespace,
        "key_mode": cfg.key_mode,
        "audit": cfg.audit,
        "namespaces": {
            name: {"cwd_prefix": ns.cwd_prefix, "env_map": ns.env_map}
            for name, ns in cfg.namespaces.items()
        },
    }
    config_path(home).write_text(json.dumps(data, indent=2) + "\n")


def resolve_namespace(cfg: Config, *, flag=None, env=None, cwd=None):
    """Return (namespace_name, reason). reason: flag|env|cwd|default."""
    if flag:
        return flag, "flag"
    if env:
        return env, "env"
    if cwd:
        matches = [
            (name, ns.cwd_prefix)
            for name, ns in cfg.namespaces.items()
            if ns.cwd_prefix
            and (cwd == ns.cwd_prefix or cwd.startswith(ns.cwd_prefix.rstrip("/") + "/"))
        ]
        if matches:
            name, _ = max(matches, key=lambda m: len(m[1]))
            return name, "cwd"
    if cfg.default_namespace:
        return cfg.default_namespace, "default"
    raise LookupError("no namespace could be resolved")
