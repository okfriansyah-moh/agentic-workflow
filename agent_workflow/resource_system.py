"""Inexpensive local capacity readings; unavailable facts remain unknown."""
from __future__ import annotations

import ctypes
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import threading

GIB = 1024 ** 3


def _read(path):
    try:
        with open(path, encoding="utf-8") as stream:
            return stream.read(65536)
    except (OSError, UnicodeError):
        return ""


def _command(args, limit=1024 * 1024):
    """Bound both captured bytes and command duration, without a shell."""
    try:
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, start_new_session=os.name == "posix")
    except OSError:
        return ""
    data = bytearray()
    exceeded = threading.Event()

    def stop():
        try:
            if os.name == "posix":
                os.killpg(proc.pid, signal.SIGKILL)
            else:
                proc.kill()
        except ProcessLookupError:
            pass

    def drain():
        while True:
            chunk = proc.stdout.read(4096)
            if not chunk:
                break
            if len(data) + len(chunk) > limit:
                exceeded.set()
                stop()
                break
            data.extend(chunk)

    reader = threading.Thread(target=drain, daemon=True)
    reader.start()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        stop()
        proc.wait(timeout=3)
        exceeded.set()
    reader.join(timeout=1)
    if reader.is_alive():
        stop()
        reader.join(timeout=1)
    if not reader.is_alive():
        proc.stdout.close()
    if reader.is_alive() or exceeded.is_set() or proc.returncode:
        return ""
    return data.decode("utf-8", errors="replace")


def _cpu_set(value):
    try:
        cpus = set()
        for span in value.strip().split(","):
            ends = [int(part) for part in span.split("-")]
            if len(ends) == 1:
                cpus.add(ends[0])
            elif len(ends) == 2 and 0 <= ends[0] <= ends[1] < 1048576:
                cpus.update(range(ends[0], ends[1] + 1))
            else:
                return None
        return len(cpus) or None
    except ValueError:
        return None


def _cgroups():
    """Resolve mounted cgroup roots, including nested container memberships."""
    memberships = []
    for line in _read("/proc/self/cgroup").splitlines():
        parts = line.split(":", 2)
        if len(parts) == 3:
            memberships.append((set(parts[1].split(",")), parts[2]))
    result = []
    for line in _read("/proc/self/mountinfo").splitlines():
        halves = line.split(" - ", 1)
        if len(halves) != 2:
            continue
        left, right = halves[0].split(), halves[1].split()
        if len(left) < 5 or len(right) < 3 or right[0] not in {"cgroup", "cgroup2"}:
            continue
        root, mount = left[3], Path(left[4].replace("\\040", " "))
        controllers = set(right[2].split(","))
        for owned, member in memberships:
            if right[0] == "cgroup" and not owned.intersection(controllers):
                continue
            if right[0] == "cgroup2" and owned != {""}:
                continue
            if root != "/" and member != root and not member.startswith(root.rstrip("/") + "/"):
                continue
            relative = member[len(root):].lstrip("/") if root != "/" else member.lstrip("/")
            current = mount / relative
            while True:
                result.append((right[0], current))
                if current == mount:
                    break
                current = current.parent
    return list(dict.fromkeys(result))


def _number(value):
    try:
        number = int(value.strip())
        return number if 0 <= number < (1 << 60) else None
    except ValueError:
        return None


def _linux(info):
    values = {}
    for name, amount in re.findall(r"^(\w+):\s+(\d+) kB", _read("/proc/meminfo"), re.M):
        values[name] = int(amount) * 1024
    info["memory_total_bytes"] = values.get("MemTotal")
    info["memory_available_bytes"] = values.get("MemAvailable")
    try:
        info["cpu_count"] = float(len(os.sched_getaffinity(0)))
    except (AttributeError, OSError):
        pass
    groups = _cgroups()
    if _read("/proc/self/cgroup").strip() and not groups:
        info["cpu_count"] = None
        info["memory_total_bytes"] = None
        info["memory_available_bytes"] = None
        info["measurement_notes"].append("Container controller paths unresolved")
    for kind, directory in groups:
        if kind == "cgroup2":
            quota = _read(directory / "cpu.max").split()
            memory = _number(_read(directory / "memory.max"))
            used = _number(_read(directory / "memory.current"))
            cpus = _cpu_set(_read(directory / "cpuset.cpus.effective"))
        else:
            quota = [_read(directory / "cpu.cfs_quota_us"), _read(directory / "cpu.cfs_period_us")]
            memory = _number(_read(directory / "memory.limit_in_bytes"))
            used = _number(_read(directory / "memory.usage_in_bytes"))
            cpus = _cpu_set(_read(directory / "cpuset.cpus"))
        if len(quota) == 2:
            numerator, denominator = _number(quota[0]), _number(quota[1])
            if numerator and denominator:
                info["cpu_count"] = min(info["cpu_count"] or float("inf"), numerator / denominator)
        if cpus:
            info["cpu_count"] = min(info["cpu_count"] or float("inf"), cpus)
        if memory is not None:
            info["memory_total_bytes"] = min(info["memory_total_bytes"] or memory, memory)
            if used is None:
                info["memory_available_bytes"] = None
                info["measurement_notes"].append("Container memory usage unavailable")
            elif info["memory_available_bytes"] is not None:
                info["memory_available_bytes"] = min(info["memory_available_bytes"], max(0, memory - used))
    pressure = _read("/proc/pressure/memory")
    samples = dict(re.findall(r"^(some|full) avg10=([\d.]+)", pressure, re.M))
    if "some" in samples and "full" in samples:
        info["pressure"] = "critical" if float(samples["full"]) > 0 else "warning" if float(samples["some"]) > 0 else "normal"


def _mac(info):
    total = _number(_command(["/usr/sbin/sysctl", "-n", "hw.memsize"]))
    info["memory_total_bytes"] = total
    vm = _command(["/usr/bin/vm_stat"])
    page = re.search(r"page size of (\d+) bytes", vm)
    counts = dict(re.findall(r"^(Pages [^:]+):\s+(\d+)\.", vm, re.M))
    needed = ["Pages free", "Pages inactive", "Pages speculative"]
    if page and all(name in counts for name in needed):
        info["memory_available_bytes"] = min(total or float("inf"), int(page[1]) * sum(int(counts[name]) for name in needed))
        info["measurement_notes"].append("Available memory estimates free and reclaimable pages")
    pressure = _command(["/usr/sbin/sysctl", "-n", "kern.memorystatus_vm_pressure_level"]).strip()
    info["pressure"] = {"1": "normal", "2": "warning", "4": "critical"}.get(pressure, "unknown")
    # Thermal API availability differs by macOS version; do not infer safety.


def _windows(info):
    class Memory(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [(name, ctypes.c_ulonglong) for name in ("total", "available", "page_total", "page_available", "virtual_total", "virtual_available", "extended")]
    try:
        kernel = ctypes.windll.kernel32
        memory = Memory()
        memory.length = ctypes.sizeof(memory)
        if kernel.GlobalMemoryStatusEx(ctypes.byref(memory)):
            info["memory_total_bytes"] = memory.total
            info["memory_available_bytes"] = memory.available
        count = kernel.GetActiveProcessorCount(0xFFFF)
        info["cpu_count"] = float(count) if count else None
        process_mask, system_mask = ctypes.c_size_t(), ctypes.c_size_t()
        if kernel.GetProcessAffinityMask(kernel.GetCurrentProcess(), ctypes.byref(process_mask), ctypes.byref(system_mask)) and process_mask.value:
            info["cpu_count"] = min(info["cpu_count"] or float("inf"), process_mask.value.bit_count())
        else:
            info["cpu_count"] = None
            info["measurement_notes"].append("Windows process affinity unavailable")
        in_job = ctypes.c_int()
        if not kernel.IsProcessInJob(kernel.GetCurrentProcess(), None, ctypes.byref(in_job)) or in_job.value:
            info["cpu_count"] = None
            info["memory_total_bytes"] = None
            info["memory_available_bytes"] = None
            info["measurement_notes"].append("Windows job limits unavailable; effective capacity unknown")
    except (AttributeError, OSError):
        info["measurement_notes"].append("Windows capacity API unavailable")


def snapshot(cwd):
    info = {"platform": platform.system(), "architecture": platform.machine(), "cpu_count": float(os.cpu_count()) if os.cpu_count() else None, "memory_total_bytes": None, "memory_available_bytes": None, "disk_total_bytes": None, "disk_free_bytes": None, "load_1m": None, "pressure": "unknown", "thermal": "unknown", "measurement_notes": []}
    try:
        disk = shutil.disk_usage(cwd)
        info.update(disk_total_bytes=disk.total, disk_free_bytes=disk.free)
    except OSError:
        info["measurement_notes"].append("Disk capacity unavailable")
    try:
        info["load_1m"] = os.getloadavg()[0]
    except (AttributeError, OSError):
        pass
    try:
        {"Linux": _linux, "Darwin": _mac, "Windows": _windows}.get(info["platform"], lambda _: None)(info)
    except (OSError, ValueError, OverflowError):
        info["pressure"] = "unknown"
        info["measurement_notes"].append("Incomplete capacity readings")
    return info


def _process_rows():
    """One bounded POSIX snapshot without command lines or environment data."""
    if platform.system() == "Windows":
        return None
    output = _command(["ps", "-axo", "pid=,ppid=,pgid=,rss=,lstart="])
    if not output.strip():
        return None
    rows = {}
    try:
        for line in output.splitlines():
            fields = line.split()
            if len(fields) != 9:
                return None
            child, parent, group, rss = map(int, fields[:4])
            if child <= 0 or parent < 0 or group <= 0 or rss < 0:
                return None
            started = " ".join(fields[4:])
            rows[child] = (parent, group, rss * 1024, started)
    except ValueError:
        return None
    return rows


def process_tree(pid, group_id=None):
    """Read process ownership and start identities for bounded cleanup."""
    result = {"rss_bytes": None, "descendants": None, "pids": [], "known": False,
              "identities": {}, "outside_group": []}
    rows = _process_rows()
    if rows is None:
        return result
    selected = {pid} if pid in rows else set()
    if group_id is not None:
        selected.update(child for child, row in rows.items() if row[1] == group_id)
    if not selected:
        return result
    while True:
        children = {child for child, row in rows.items() if row[0] in selected}
        if children.issubset(selected):
            break
        selected.update(children)
    return {
        "rss_bytes": sum(rows[child][2] for child in selected),
        "descendants": len(selected - {pid}), "pids": sorted(selected), "known": True,
        "identities": {str(child): {"started": rows[child][3], "pgid": rows[child][1]}
                       for child in sorted(selected)},
        "outside_group": sorted(child for child in selected
                                if group_id is not None and rows[child][1] != group_id),
    }


def living_owned(identities):
    """Return matching live start identities; None means observation failed."""
    rows = _process_rows()
    if rows is None:
        return None
    living = {}
    for raw_pid, identity in identities.items():
        try:
            pid = int(raw_pid)
        except (TypeError, ValueError):
            continue
        row = rows.get(pid)
        if row and isinstance(identity, dict) and row[3] == identity.get("started"):
            living[str(pid)] = {"started": row[3], "pgid": row[1]}
    return living


def group_members(group_id):
    """None means unknown; an empty mapping establishes no observed group members."""
    rows = _process_rows()
    if rows is None:
        return None
    return {str(pid): {'started': row[3], 'pgid': row[1]}
            for pid, row in rows.items() if row[1] == group_id}
