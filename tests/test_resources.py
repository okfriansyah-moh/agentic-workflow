import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from agent_workflow import process_runner, resources

GIB = resources.GIB


def healthy():
    return {'platform': 'fixture', 'architecture': 'test', 'cpu_count': 8,
            'memory_total_bytes': 16 * GIB, 'memory_available_bytes': 12 * GIB,
            'disk_total_bytes': 100 * GIB, 'disk_free_bytes': 20 * GIB,
            'load_1m': 0, 'pressure': 'normal', 'thermal': 'unknown'}


class BudgetTests(unittest.TestCase):
    def test_small_large_and_fractional_container_capacity(self):
        for cpu, memory, workers, budget in [(2, 2, 1, GIB // 2), (8, 16, 2, 4 * GIB), (32, 128, 2, 4 * GIB), (0.5, 2, 1, GIB // 2)]:
            reading = dict(healthy(), cpu_count=cpu, memory_total_bytes=memory * GIB, memory_available_bytes=memory * GIB * 3 // 4)
            limits = resources.budgets(reading)
            self.assertEqual((limits['workers'], limits['memory_bytes']), (workers, budget))

    def test_unknown_elevated_load_and_command_minimum_block(self):
        for changes in [{'pressure': 'unknown'}, {'pressure': 'warning'}, {'cpu_count': None}, {'load_1m': 9}, {'memory_available_bytes': GIB}]:
            reading = dict(healthy(), **changes)
            self.assertIsNotNone(resources.admission_reason(reading, resources.budgets(reading)))
        self.assertIsNotNone(resources.admission_reason(healthy(), resources.budgets(healthy()), {'minimum_memory_bytes': 5 * GIB}))

    def test_tightening_and_authorized_increase_cannot_create_headroom(self):
        self.assertEqual(resources.budgets(healthy(), {'workers': 1})['workers'], 1)
        with self.assertRaises(ValueError):
            resources.budgets(healthy(), {'workers': 4})
        self.assertEqual(resources.budgets(healthy(), {'workers': 4, 'increase_authorized': True})['workers'], 4)
        reading = dict(healthy(), memory_available_bytes=5 * GIB)
        self.assertEqual(resources.budgets(reading, {'memory_bytes': 10 * GIB, 'increase_authorized': True})['memory_bytes'], GIB)
        for value in [True, -1, 0, '2']:
            with self.assertRaises(ValueError):
                resources.budgets(healthy(), {'workers': value})

    def test_critical_pressure_cannot_be_overridden(self):
        reading = dict(healthy(), pressure='critical')
        self.assertIsNotNone(resources.admission_reason(reading, resources.budgets(reading, {'increase_authorized': True})))

    def test_two_healthy_samples_are_required(self):
        with patch.object(resources.resource_system, 'snapshot', side_effect=[healthy(), dict(healthy(), pressure='warning')]), patch.object(resources.time, 'sleep') as sleep:
            result = resources.confirm_health('.')
        self.assertEqual(result['status'], 'blocked')
        sleep.assert_called_once_with(5)

    def test_process_and_reserve_limits(self):
        limits = resources.budgets(healthy())
        tree = {'known': True, 'rss_bytes': 1, 'descendants': 1}
        for changed in [{'pressure': 'critical'}, {'memory_available_bytes': 1}, {'disk_free_bytes': 1}]:
            self.assertIsNotNone(resources.active_reason(dict(healthy(), **changed), limits, tree))
        for changed in [{'known': False}, {'rss_bytes': 5 * GIB}, {'descendants': 65}]:
            self.assertIsNotNone(resources.active_reason(healthy(), limits, dict(tree, **changed)))

    def test_installer_inventory_preserves_resource_preferences(self):
        from agent_workflow import installer
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); state = root / '.ai'; state.mkdir()
            (state / 'config.json').write_text(json.dumps({'resources': {'workers': 1}}))
            with patch.object(installer, 'validate_source', return_value={'version': '1.3.0'}), patch.object(installer, 'bundle_files', return_value={}), patch.object(installer, 'adapter_files', return_value={}), patch.object(installer, 'skill_links', return_value={}):
                _, files = installer.inventory(root, root, state, False, 'general')
            self.assertEqual(json.loads(files['.ai/config.json']['data'])['resources'], {'workers': 1})

    def test_project_configuration_wins_over_global(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / '.ai').mkdir()
            (root / '.ai/config.json').write_text(json.dumps({'resources': {'workers': 1}}))
            (root / 'nested').mkdir()
            self.assertEqual(resources.configuration(root / 'nested'), {'workers': 1})


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.original_state_directory = resources.state_directory
        self.start_patch(resources, 'state_directory', return_value=self.root / 'machine')
        self.start_patch(resources.resource_system, 'snapshot', side_effect=lambda *a: healthy())
        self.original_tree = resources.resource_system.process_tree
        self.start_patch(resources.resource_system, 'process_tree', return_value={'known': True, 'rss_bytes': 1, 'descendants': 0, 'pids': []})
        self.start_patch(resources, 'INTERVAL', 0)

    def start_patch(self, target, name, *args, **kwargs):
        mock = patch.object(target, name, *args, **kwargs); self.addCleanup(mock.stop); return mock.start()

    def test_tiny_process_capture_and_slot_release(self):
        result = process_runner.run_process([sys.executable, '-c', 'print("ok")'], self.root, 2)
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(result['stdout'].strip(), b'ok')
        self.assertTrue(result['cleanup_verified'])
        self.assertFalse((self.root / 'machine/active.json').exists())

    def test_output_memory_is_bounded(self):
        (self.root / '.ai').mkdir()
        (self.root / '.ai/config.json').write_text(json.dumps({'resources': {'output_bytes': 64}}))
        result = process_runner.run_process([sys.executable, '-c', 'print("x" * 1024)'], self.root, 2)
        self.assertTrue(result['truncated'])
        self.assertLessEqual(len(result['stdout']) + len(result['stderr']), 64)
        self.assertEqual(result['status'], 'blocked')

    def test_resource_stop_blocks_next_work_until_explicit_recovery(self):
        with patch.object(resources.resource_system, 'process_tree', return_value={'known': True, 'rss_bytes': 5 * GIB, 'descendants': 0, 'pids': []}):
            result = process_runner.run_process([sys.executable, '-c', 'import time; time.sleep(2)'], self.root, 3)
        self.assertTrue(result['resources']['stopped'])
        with patch.object(process_runner.subprocess, 'Popen') as spawn:
            blocked = process_runner.run_process([sys.executable, '-c', 'print(1)'], self.root, 2)
            spawn.assert_not_called()
        self.assertEqual(blocked['status'], 'blocked')
        self.assertEqual(resources.inspect_resources(self.root, resume=True)['status'], 'healthy')

    def test_another_owner_and_failed_recovery_do_not_unlock(self):
        lease = resources.Lease(self.root)
        self.assertTrue(lease.acquire())
        other = resources.Lease(self.root)
        self.assertFalse(other.acquire())
        other.release()
        self.assertTrue(lease.lock.exists())
        self.assertEqual(resources.inspect_resources(self.root, resume=True)['status'], 'blocked')
        self.assertTrue(lease.lock.exists())
        lease.release()

    def test_timeout_terminates_owned_process(self):
        result = process_runner.run_process([sys.executable, '-c', 'import time; time.sleep(2)'], self.root, 0.05)
        self.assertTrue(result['timed_out'])
        self.assertTrue(result['cleanup_verified'])

    def test_unavailable_containment_launches_nothing(self):
        with patch.object(process_runner.os, 'name', 'nt'), patch.object(process_runner.subprocess, 'Popen') as spawn:
            result = process_runner.run_process(['fixture'], self.root)
        self.assertEqual(result['status'], 'blocked')
        spawn.assert_not_called()

    def test_machine_state_ignores_client_temp_directory(self):
        before = self.original_state_directory()
        with patch.dict(os.environ, {'TMPDIR': '/different-client-temp'}):
            self.assertEqual(self.original_state_directory(), before)
        self.assertTrue(before.is_relative_to(Path.home() / '.local/state/agent-workflow'))

    def test_recovery_refuses_recorded_surviving_descendant(self):
        folder = self.root / 'machine'; folder.mkdir()
        (folder / 'stopped.json').write_text(json.dumps({'identities': {'123': {'started': 'fixture', 'pgid': 123}}}))
        with patch.object(resources.resource_system, 'living_owned', return_value={'123': {'started': 'fixture', 'pgid': 123}}):
            result = resources.inspect_resources(self.root, resume=True)
        self.assertEqual(result['status'], 'blocked')
        self.assertTrue((folder / 'stopped.json').exists())

    def test_known_npm_workspace_vitest_is_bounded(self):
        from agent_workflow.command_resources import npm_workers
        folder = self.root / 'web'; folder.mkdir()
        (folder / 'package.json').write_text(json.dumps({'scripts': {'test:coverage': 'vitest run --coverage', 'test': 'npm run hidden'}}))
        argv = npm_workers(['npm', 'run', 'test:coverage', '--workspace', 'web'], self.root, '1')
        self.assertEqual(argv[-3:], ['--', '--maxWorkers=1', '--no-file-parallelism'])
        with self.assertRaises(ValueError):
            npm_workers(['npm', 'test', '--workspace', 'web'], self.root, '1')

    @unittest.skipUnless(os.name == 'posix', 'POSIX process-group fixture')
    def test_tiny_detached_child_does_not_survive_cleanup(self):
        import signal
        code = "import subprocess,sys,time,pathlib; child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(3)'],start_new_session=True); pathlib.Path('child.pid').write_text(str(child.pid)); time.sleep(3)"
        with patch.object(resources.resource_system, 'process_tree', self.original_tree):
            result = process_runner.run_process([sys.executable, '-c', code], self.root, 0.3)
        child = int((self.root / 'child.pid').read_text())
        try:
            os.kill(child, 0)
        except ProcessLookupError:
            gone = True
        else:
            gone = False
            os.kill(child, signal.SIGKILL)
        self.assertTrue(gone)
        self.assertTrue(result['cleanup_verified'])

    def test_cooperative_workers_preserve_lower_user_values(self):
        with patch.dict(os.environ, {'OMP_NUM_THREADS': '1'}):
            argv, env = process_runner.command_limits(['gradlew', 'test'], resources.budgets(healthy()))
        self.assertEqual(env['OMP_NUM_THREADS'], '1')
        self.assertIn('--max-workers=2', argv)
        self.assertIn('--no-daemon', argv)
