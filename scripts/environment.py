"""Registra o ambiente de execução (CPU, RAM, SO, versões e flags). Funciona em Linux, WSL e macOS."""

import argparse
import json
import platform
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def command_output(command: list[str]) -> str:
    try:
        return subprocess.run(command, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def cpu_model() -> str:
    if sys.platform == "darwin":
        return command_output(["sysctl", "-n", "machdep.cpu.brand_string"]) or platform.processor()
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "desconhecido"


def ram_gib() -> float | None:
    if sys.platform == "darwin":
        value = command_output(["sysctl", "-n", "hw.memsize"])
        return round(int(value) / 2**30, 1) if value.isdigit() else None
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                return round(int(line.split()[1]) / 2**20, 1)
    except OSError:
        pass
    return None


def os_description() -> str:
    if sys.platform == "darwin":
        return f"macOS {platform.mac_ver()[0]} ({platform.machine()})"
    name = platform.platform()
    try:
        release = dict(line.split("=", 1) for line in Path("/etc/os-release").read_text().splitlines() if "=" in line)
        name = release.get("PRETTY_NAME", name).strip('"')
    except OSError:
        pass
    if "microsoft" in platform.release().lower():
        name += " (WSL2, Windows)"
    return f"{name}, kernel {platform.release()}"


def cflags() -> str:
    try:
        match = re.search(r"^CFLAGS\s*\?=\s*(.+)$", (ROOT / "Makefile").read_text(), re.MULTILINE)
        return match.group(1).strip() if match else ""
    except OSError:
        return ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results/environment.json")
    args = parser.parse_args()
    info = {
        "data": datetime.now().isoformat(timespec="seconds"),
        "cpu": cpu_model(),
        "nucleos_logicos": __import__("os").cpu_count(),
        "ram_gib": ram_gib(),
        "sistema": os_description(),
        "python": f"{platform.python_implementation()} {platform.python_version()}",
        "compilador": command_output(["cc", "--version"]).splitlines()[0] if command_output(["cc", "--version"]) else "",
        "cflags": cflags(),
        "commit": command_output(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"]),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for key, value in info.items():
        print(f"{key:16} {value}")


if __name__ == "__main__":
    main()
