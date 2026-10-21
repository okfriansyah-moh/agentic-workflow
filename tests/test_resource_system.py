"""Capacity adapters use mocked OS data and never stress the machine."""
import types
import io
import subprocess
import unittest
from unittest.mock import Mock, patch

from agent_workflow import resource_system as system


class ResourceSystemTests(unittest.TestCase):
    def base(self):
        return {"cpu_count": 8.0, "memory_total_bytes": None, "memory_available_bytes": None, "pressure": "unknown", "measurement_notes": []}

    def test_mac_pages_and_warning(self):
        values = {"hw.memsize": str(16 * system.GIB), "kern.memorystatus_vm_pressure_level": "2"}
        def command(args):
            if args[-1] in values:
                return values[args[-1]]
            return 'Mach Virtual Memory Statistics: (page size of 16384 bytes)\nPages free: 10.\nPages inactive: 20.\nPages speculative: 2.\n'
        info = self.base()
        with patch.object(system, "_command", side_effect=command):
            system._mac(info)
        self.assertEqual(info["memory_available_bytes"], 32 * 16384)
        self.assertEqual(info["pressure"], "warning")

    def test_mac_unknown_does_not_claim_healthy(self):
        info = self.base()
        with patch.object(system, "_command", return_value=""):
            system._mac(info)
        self.assertIsNone(info["memory_available_bytes"])
        self.assertEqual(info["pressure"], "unknown")

    def test_cgroup_mount_resolution_and_ancestors(self):
        data = {"/proc/self/cgroup": "0::/tenant/work\n", "/proc/self/mountinfo": "1 0 0:1 /tenant /sys/fs/cgroup rw - cgroup2 cgroup rw\n"}
        with patch.object(system, "_read", side_effect=lambda path: data.get(str(path), "")):
            result = system._cgroups()
        self.assertEqual([str(path) for _, path in result], ["/sys/fs/cgroup/work", "/sys/fs/cgroup"])

    def test_linux_nested_limits_and_pressure(self):
        from pathlib import Path
        data = {"/proc/meminfo": "MemTotal: 16777216 kB\nMemAvailable: 8388608 kB\n", "/proc/pressure/memory": "some avg10=0.00 avg60=0\nfull avg10=0.00 avg60=0\n", "/cg/work/cpu.max": "150000 100000", "/cg/work/memory.max": str(4 * system.GIB), "/cg/work/memory.current": str(system.GIB), "/cg/work/cpuset.cpus.effective": "1-3", "/cg/cpu.max": "100000 100000", "/cg/memory.max": str(8 * system.GIB), "/cg/memory.current": str(6 * system.GIB)}
        info = self.base()
        with patch.object(system, "_read", side_effect=lambda path: data.get(str(path), "")), patch.object(system, "_cgroups", return_value=[("cgroup2", Path("/cg/work")), ("cgroup2", Path("/cg"))]), patch.object(system.os, "sched_getaffinity", return_value=set(range(8)), create=True):
            system._linux(info)
        self.assertEqual(info["cpu_count"], 1.0)
        self.assertEqual(info["memory_total_bytes"], 4 * system.GIB)
        self.assertEqual(info["memory_available_bytes"], 2 * system.GIB)
        self.assertEqual(info["pressure"], "normal")

    def test_linux_v1_missing_usage_unknown(self):
        from pathlib import Path
        data = {"/proc/meminfo": "MemTotal: 16777216 kB\nMemAvailable: 8388608 kB\n", "/cg/memory.limit_in_bytes": str(2 * system.GIB), "/cg/cpu.cfs_quota_us": "50000", "/cg/cpu.cfs_period_us": "100000", "/proc/pressure/memory": "some avg10=1.0\nfull avg10=0.1\n"}
        info = self.base()
        with patch.object(system, "_read", side_effect=lambda path: data.get(str(path), "")), patch.object(system, "_cgroups", return_value=[("cgroup", Path("/cg"))]):
            system._linux(info)
        self.assertEqual(info["cpu_count"], 0.5)
        self.assertIsNone(info["memory_available_bytes"])
        self.assertEqual(info["pressure"], "critical")

    def test_windows_mock_and_job_unknown(self):
        def memory(pointer):
            pointer._obj.total = 8 * system.GIB
            pointer._obj.available = 4 * system.GIB
            return 1
        def job(_process, _job, pointer):
            pointer._obj.value = 1
            return 1
        kernel = types.SimpleNamespace(GlobalMemoryStatusEx=memory, GetActiveProcessorCount=lambda _: 8, GetCurrentProcess=lambda: -1, GetProcessAffinityMask=lambda *args: 0, IsProcessInJob=job)
        info = self.base()
        with patch.object(system.ctypes, "windll", types.SimpleNamespace(kernel32=kernel), create=True):
            system._windows(info)
        self.assertIsNone(info["memory_total_bytes"])
        self.assertIsNone(info["cpu_count"])

    def test_windows_unavailable(self):
        info = self.base()
        with patch.object(system.ctypes, "windll", None, create=True):
            system._windows(info)
        self.assertIn("Windows capacity API unavailable", info["measurement_notes"])

    def test_tree_includes_group_and_descendants(self):
        with patch.object(system.platform, "system", return_value="Darwin"), patch.object(system, "_command", return_value="10 1 10 100 Wed Oct 21 12:34:56 2026\n11 10 10 20 Wed Oct 21 12:34:56 2026\n12 11 12 30 Wed Oct 21 12:34:57 2026\n13 1 13 999 Wed Oct 21 12:34:58 2026\n14 1 10 40 Wed Oct 21 12:34:59 2026\n"):
            result = system.process_tree(10, 10)
        self.assertEqual(result["pids"], [10, 11, 12, 14])
        self.assertEqual(result["rss_bytes"], 190 * 1024)
        self.assertEqual(result["descendants"], 3)
        self.assertEqual(result["outside_group"], [12])
        self.assertEqual(result["identities"]["12"], {"started": "Wed Oct 21 12:34:57 2026", "pgid": 12})

    def test_tree_incomplete_is_unknown(self):
        with patch.object(system.platform, "system", return_value="Linux"), patch.object(system, "_command", return_value="malformed"):
            self.assertFalse(system.process_tree(10)["known"])

    def test_snapshot_unsupported_and_disk_failure(self):
        with patch.object(system.platform, "system", return_value="Other"), patch.object(system.shutil, "disk_usage", side_effect=OSError), patch.object(system.os, "getloadavg", side_effect=OSError):
            info = system.snapshot("/missing")
        self.assertIsNone(info["disk_free_bytes"])
        self.assertEqual(info["pressure"], "unknown")
        self.assertEqual(info["thermal"], "unknown")

    def test_helper_output_is_bounded(self):
        proc = Mock(stdout=io.BytesIO(b"x" * 8192), returncode=0, pid=123456789)
        with patch.object(system.subprocess, "Popen", return_value=proc), patch.object(system.os, "killpg", create=True) as kill:
            self.assertEqual(system._command(["fake"], limit=1024), "")
        if system.os.name == "posix":
            kill.assert_called_once()
        self.assertTrue(proc.stdout.closed)

    def test_helper_timeout_is_unknown(self):
        proc = Mock(stdout=io.BytesIO(b"partial"), returncode=0, pid=123456789)
        proc.wait.side_effect = [subprocess.TimeoutExpired("fake", 3), 0]
        with patch.object(system.subprocess, "Popen", return_value=proc), patch.object(system.os, "killpg", create=True):
            self.assertEqual(system._command(["fake"]), "")

    def test_unresolved_container_is_unknown(self):
        info = self.base()
        data = {"/proc/meminfo": "MemTotal: 16777216 kB\nMemAvailable: 8388608 kB\n", "/proc/self/cgroup": "0::/hidden"}
        with patch.object(system, "_read", side_effect=lambda path: data.get(str(path), "")), patch.object(system, "_cgroups", return_value=[]):
            system._linux(info)
        self.assertIsNone(info["cpu_count"])
        self.assertIsNone(info["memory_total_bytes"])
        self.assertIsNone(info["memory_available_bytes"])

    def test_linux_start_identity_accepts_spacing(self):
        output = "  10   1 10 100 Wed Oct  7 01:02:03 2026\n"
        with patch.object(system.platform, "system", return_value="Linux"), patch.object(system, "_command", return_value=output):
            result = system.process_tree(10, 10)
        self.assertEqual(result["identities"]["10"]["started"], "Wed Oct 7 01:02:03 2026")
        self.assertEqual(result["outside_group"], [])

    def test_living_owned_rejects_reused_pid_and_preserves_group_change(self):
        identities = {"10": {"started": "Wed Oct 21 12:34:56 2026", "pgid": 10},
                      "11": {"started": "Wed Oct 21 12:34:56 2026", "pgid": 10},
                      "12": {"started": "Wed Oct 21 12:34:56 2026", "pgid": 10}}
        output = "10 1 10 1 Wed Oct 21 12:34:59 2026\n11 1 11 1 Wed Oct 21 12:34:56 2026\n"
        with patch.object(system.platform, "system", return_value="Darwin"), patch.object(system, "_command", return_value=output):
            living = system.living_owned(identities)
        self.assertEqual(living, {"11": {"started": "Wed Oct 21 12:34:56 2026", "pgid": 11}})

    def test_living_owned_distinguishes_empty_from_unknown(self):
        with patch.object(system.platform, "system", return_value="Linux"), patch.object(system, "_command", return_value="10 1 10 1 Wed Oct 21 12:34:56 2026\n"):
            self.assertEqual(system.living_owned({}), {})
        with patch.object(system.platform, "system", return_value="Linux"), patch.object(system, "_command", return_value=""):
            self.assertIsNone(system.living_owned({}))
        with patch.object(system.platform, "system", return_value="Windows"):
            self.assertIsNone(system.living_owned({}))

    def test_cpu_set(self):
        self.assertEqual(system._cpu_set("1-3,5"), 4)
        self.assertIsNone(system._cpu_set("broken"))


if __name__ == "__main__":
    unittest.main()
