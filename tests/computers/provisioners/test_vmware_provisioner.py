# import unittest
# from unittest.mock import patch, MagicMock, call
# import time
# import os
# import subprocess
# from pathlib import Path

# from commandAGI.computers.provisioners.vmware_provisioner import VMwareProvisioner


# class TestVMwareProvisioner(unittest.TestCase):
#     def setUp(self):
#         # Create a VMwareProvisioner with default parameters
#         self.provisioner = VMwareProvisioner(
#             port=8000,
#             vm_name="test-vm",
#             vm_image="test-image.vmx",
#             max_retries=2,
#             timeout=10
#         )

#     def test_init(self):
#         # Test that the provisioner initializes with the correct attributes
#         self.assertEqual(self.provisioner.port, 8000)
#         self.assertEqual(self.provisioner.vm_name, "test-vm")
#         self.assertEqual(self.provisioner.vm_image, "test-image.vmx")
#         self.assertEqual(self.provisioner.max_retries, 2)
#         self.assertEqual(self.provisioner.timeout, 10)
#         self.assertEqual(self.provisioner._status, "not_started")
#         self.assertIsNone(self.provisioner._vm_id)

#     def test_init_with_custom_params(self):
#         # Test initialization with custom parameters
#         provisioner = VMwareProvisioner(
#             port=9000,
#             vm_name="custom-vm",
#             vm_image="custom-image.vmx",
#             memory_mb=4096,
#             cpus=4,
#             headless=False,
#             max_retries=3,
#             timeout=20
#         )

#         self.assertEqual(provisioner.port, 9000)
#         self.assertEqual(provisioner.vm_name, "custom-vm")
#         self.assertEqual(provisioner.vm_image, "custom-image.vmx")
#         self.assertEqual(provisioner.memory_mb, 4096)
#         self.assertEqual(provisioner.cpus, 4)
#         self.assertFalse(provisioner.headless)
#         self.assertEqual(provisioner.max_retries, 3)
#         self.assertEqual(provisioner.timeout, 20)

#     @patch('subprocess.run')
#     def test_vmrun_command_success(self, mock_run):
#         # Mock subprocess.run to return a successful result
#         mock_process = MagicMock()
#         mock_process.returncode = 0
#         mock_process.stdout = "VMware output"
#         mock_run.return_value = mock_process

#         # Call _vmrun_command
#         result = self.provisioner._vmrun_command(["list"])

#         # Check that subprocess.run was called with the right arguments
#         mock_run.assert_called_once()
#         call_args = mock_run.call_args[0][0]
#         self.assertEqual(call_args[0], "vmrun")
#         self.assertEqual(call_args[1], "-T")
#         self.assertEqual(call_args[2], "ws")  # Default provider is Workstation
#         self.assertEqual(call_args[3], "list")

#         # Check that the result is correct
#         self.assertEqual(result, "VMware output")

#     @patch('subprocess.run')
#     def test_vmrun_command_with_fusion(self, mock_run):
#         # Create a provisioner with Fusion provider
#         provisioner = VMwareProvisioner(
#             port=8000,
#             vm_name="test-vm",
#             vm_image="test-image.vmx",
#             provider="fusion"
#         )

#         # Mock subprocess.run to return a successful result
#         mock_process = MagicMock()
#         mock_process.returncode = 0
#         mock_process.stdout = "VMware output"
#         mock_run.return_value = mock_process

#         # Call _vmrun_command
#         result = provisioner._vmrun_command(["list"])

#         # Check that subprocess.run was called with the right arguments
#         mock_run.assert_called_once()
#         call_args = mock_run.call_args[0][0]
#         self.assertEqual(call_args[0], "vmrun")
#         self.assertEqual(call_args[1], "-T")
#         self.assertEqual(call_args[2], "fusion")
#         self.assertEqual(call_args[3], "list")

#     @patch('subprocess.run')
#     def test_vmrun_command_error(self, mock_run):
#         # Mock subprocess.run to raise a subprocess.CalledProcessError
#         mock_run.side_effect = subprocess.CalledProcessError(
#             returncode=1,
#             cmd=["vmrun", "-T", "ws", "list"],
#             output="Error output"
#         )

#         # Call _vmrun_command and check that it raises the error
#         with self.assertRaises(subprocess.CalledProcessError):
#             self.provisioner._vmrun_command(["list"])

#     @patch.object(VMwareProvisioner, '_vmrun_command')
#     @patch.object(VMwareProvisioner, 'is_running')
#     @patch('time.sleep')
#     def test_setup_success(self, mock_sleep, mock_is_running, mock_vmrun):
#         # Mock _vmrun_command to return success for each call
#         mock_vmrun.side_effect = [
#             # clone
#             "",
#             # start
#             ""
#         ]

#         # Mock is_running to return True
#         mock_is_running.return_value = True

#         # Call setup
#         self.provisioner.setup()

#         # Check that _vmrun_command was called with the right arguments
#         self.assertEqual(mock_vmrun.call_count, 2)

#         # Check clone call
#         clone_call = mock_vmrun.call_args_list[0]
#         self.assertEqual(clone_call[0][0][0], "clone")
#         self.assertEqual(clone_call[0][0][1], "test-image.vmx")
#         self.assertEqual(clone_call[0][0][2], str(Path("test-vm") / "test-vm.vmx"))
#         self.assertEqual(clone_call[0][0][3], "linked")

#         # Check start call
#         start_call = mock_vmrun.call_args_list[1]
#         self.assertEqual(start_call[0][0][0], "start")
#         self.assertEqual(start_call[0][0][1], str(Path("test-vm") / "test-vm.vmx"))
#         if self.provisioner.headless:
#             self.assertEqual(start_call[0][0][2], "nogui")

#         # Check that _vm_id was set
#         self.assertEqual(self.provisioner._vm_id, str(Path("test-vm") / "test-vm.vmx"))

#         # Check that status was updated
#         self.assertEqual(self.provisioner._status, "running")

#     @patch.object(VMwareProvisioner, '_vmrun_command')
#     @patch.object(VMwareProvisioner, 'is_running')
#     @patch('time.sleep')
#     def test_setup_clone_error(self, mock_sleep, mock_is_running, mock_vmrun):
#         # Mock _vmrun_command to raise an error on clone
#         mock_vmrun.side_effect = subprocess.CalledProcessError(
#             returncode=1,
#             cmd=["vmrun", "-T", "ws", "clone", "test-image.vmx", "test-vm/test-vm.vmx", "linked"],
#             output="Error cloning VM"
#         )

#         # Call setup and check that it raises the error
#         with self.assertRaises(subprocess.CalledProcessError):
#             self.provisioner.setup()

#         # Check that _vmrun_command was called once
#         mock_vmrun.assert_called_once()

#         # Check that status was updated to error
#         self.assertEqual(self.provisioner._status, "error")

#     @patch.object(VMwareProvisioner, '_vmrun_command')
#     @patch.object(VMwareProvisioner, 'is_running')
#     @patch('time.sleep')
#     def test_setup_start_error(self, mock_sleep, mock_is_running, mock_vmrun):
#         # Mock _vmrun_command to succeed on clone but fail on start
#         mock_vmrun.side_effect = [
#             # clone succeeds
#             "",
#             # start fails
#             subprocess.CalledProcessError(
#                 returncode=1,
#                 cmd=["vmrun", "-T", "ws", "start", "test-vm/test-vm.vmx", "nogui"],
#                 output="Error starting VM"
#             )
#         ]

#         # Call setup and check that it raises the error
#         with self.assertRaises(subprocess.CalledProcessError):
#             self.provisioner.setup()

#         # Check that _vmrun_command was called twice
#         self.assertEqual(mock_vmrun.call_count, 2)

#         # Check that status was updated to error
#         self.assertEqual(self.provisioner._status, "error")

#     @patch.object(VMwareProvisioner, '_vmrun_command')
#     @patch.object(VMwareProvisioner, 'is_running')
#     @patch('time.sleep')
#     def test_setup_is_running_timeout(self, mock_sleep, mock_is_running, mock_vmrun):
#         # Mock _vmrun_command to return success for each call
#         mock_vmrun.side_effect = [
#             # clone
#             "",
#             # start
#             ""
#         ]

#         # Mock is_running to always return False (timeout)
#         mock_is_running.return_value = False

#         # Call setup and check that it raises TimeoutError
#         with self.assertRaises(TimeoutError):
#             self.provisioner.setup()

#         # Check that _vmrun_command was called twice
#         self.assertEqual(mock_vmrun.call_count, 2)

#         # Check that status was updated to error
#         self.assertEqual(self.provisioner._status, "error")

#     @patch.object(VMwareProvisioner, '_vmrun_command')
#     @patch.object(VMwareProvisioner, 'is_running')
#     @patch('time.sleep')
#     def test_setup_retry_success(self, mock_sleep, mock_is_running, mock_vmrun):
#         # Mock _vmrun_command to fail once, then succeed
#         mock_vmrun.side_effect = [
#             # First attempt - clone fails
#             subprocess.CalledProcessError(
#                 returncode=1,
#                 cmd=["vmrun", "-T", "ws", "clone", "test-image.vmx", "test-vm/test-vm.vmx", "linked"],
#                 output="Error cloning VM"
#             ),
#             # Second attempt - clone succeeds
#             "",
#             # start
#             ""
#         ]

#         # Mock is_running to return True
#         mock_is_running.return_value = True

#         # Call setup
#         self.provisioner.setup()

#         # Check that _vmrun_command was called 3 times (1 failed + 2 successful)
#         self.assertEqual(mock_vmrun.call_count, 3)

#         # Check that sleep was called for retry backoff
#         mock_sleep.assert_called_once_with(2)  # 2^1

#         # Check that status was updated
#         self.assertEqual(self.provisioner._status, "running")

#     @patch.object(VMwareProvisioner, '_vmrun_command')
#     @patch.object(VMwareProvisioner, 'is_running')
#     @patch('time.sleep')
#     def test_setup_max_retries_exceeded(self, mock_sleep, mock_is_running, mock_vmrun):
#         # Mock _vmrun_command to always fail
#         mock_vmrun.side_effect = subprocess.CalledProcessError(
#             returncode=1,
#             cmd=["vmrun", "-T", "ws", "clone", "test-image.vmx", "test-vm/test-vm.vmx", "linked"],
#             output="Error cloning VM"
#         )

#         # Call setup and check that it raises the error
#         with self.assertRaises(subprocess.CalledProcessError):
#             self.provisioner.setup()

#         # Check that _vmrun_command was called max_retries times
#         self.assertEqual(mock_vmrun.call_count, 2)  # max_retries=2

#         # Check that sleep was called for retry backoff
#         mock_sleep.assert_has_calls([call(2), call(4)])  # 2^1, 2^2

#         # Check that status was updated to error
#         self.assertEqual(self.provisioner._status, "error")

#     @patch.object(VMwareProvisioner, '_vmrun_command')
#     @patch('shutil.rmtree')
#     def test_teardown_success(self, mock_rmtree, mock_vmrun):
#         # Set _vm_id
#         self.provisioner._vm_id = "test-vm/test-vm.vmx"
#         self.provisioner._status = "running"

#         # Mock _vmrun_command to return success for each call
#         mock_vmrun.side_effect = [
#             # stop
#             "",
#             # list (to check if VM is still running)
#             "Total running VMs: 0"
#         ]

#         # Call teardown
#         self.provisioner.teardown()

#         # Check that _vmrun_command was called with the right arguments
#         self.assertEqual(mock_vmrun.call_count, 2)

#         # Check stop call
#         stop_call = mock_vmrun.call_args_list[0]
#         self.assertEqual(stop_call[0][0][0], "stop")
#         self.assertEqual(stop_call[0][0][1], "test-vm/test-vm.vmx")
#         self.assertEqual(stop_call[0][0][2], "hard")

#         # Check list call
#         list_call = mock_vmrun.call_args_list[1]
#         self.assertEqual(list_call[0][0][0], "list")

#         # Check that rmtree was called with the right arguments
#         mock_rmtree.assert_called_once_with(Path("test-vm"), ignore_errors=True)

#         # Check that status was updated
#         self.assertEqual(self.provisioner._status, "stopped")

#     @patch.object(VMwareProvisioner, '_vmrun_command')
#     @patch('shutil.rmtree')
#     def test_teardown_no_vm_id(self, mock_rmtree, mock_vmrun):
#         # Don't set _vm_id
#         self.provisioner._vm_id = None

#         # Call teardown
#         self.provisioner.teardown()

#         # Check that _vmrun_command was not called
#         mock_vmrun.assert_not_called()

#         # Check that rmtree was not called
#         mock_rmtree.assert_not_called()

#         # Check that status was updated
#         self.assertEqual(self.provisioner._status, "stopped")

#     @patch.object(VMwareProvisioner, '_vmrun_command')
#     @patch('shutil.rmtree')
#     def test_teardown_stop_error(self, mock_rmtree, mock_vmrun):
#         # Set _vm_id
#         self.provisioner._vm_id = "test-vm/test-vm.vmx"
#         self.provisioner._status = "running"

#         # Mock _vmrun_command to raise an error on stop
#         mock_vmrun.side_effect = subprocess.CalledProcessError(
#             returncode=1,
#             cmd=["vmrun", "-T", "ws", "stop", "test-vm/test-vm.vmx", "hard"],
#             output="Error stopping VM"
#         )

#         # Call teardown
#         self.provisioner.teardown()

#         # Check that _vmrun_command was called once
#         mock_vmrun.assert_called_once()

#         # Check that rmtree was still called (cleanup attempt)
#         mock_rmtree.assert_called_once_with(Path("test-vm"), ignore_errors=True)

#         # Check that status was updated to error
#         self.assertEqual(self.provisioner._status, "error")

#     @patch.object(VMwareProvisioner, '_vmrun_command')
#     def test_is_running_true(self, mock_vmrun):
#         # Set _vm_id
#         self.provisioner._vm_id = "test-vm/test-vm.vmx"

#         # Mock _vmrun_command to return a list with the VM
#         mock_vmrun.return_value = "Total running VMs: 1\ntest-vm/test-vm.vmx"

#         # Check that is_running returns True
#         self.assertTrue(self.provisioner.is_running())

#         # Check that _vmrun_command was called with the right arguments
#         mock_vmrun.assert_called_once_with(["list"])

#     @patch.object(VMwareProvisioner, '_vmrun_command')
#     def test_is_running_false(self, mock_vmrun):
#         # Set _vm_id
#         self.provisioner._vm_id = "test-vm/test-vm.vmx"

#         # Mock _vmrun_command to return an empty list
#         mock_vmrun.return_value = "Total running VMs: 0"

#         # Check that is_running returns False
#         self.assertFalse(self.provisioner.is_running())

#     @patch.object(VMwareProvisioner, '_vmrun_command')
#     def test_is_running_no_vm_id(self, mock_vmrun):
#         # Don't set _vm_id
#         self.provisioner._vm_id = None

#         # Check that is_running returns False
#         self.assertFalse(self.provisioner.is_running())

#         # Check that _vmrun_command was not called
#         mock_vmrun.assert_not_called()

#     @patch.object(VMwareProvisioner, '_vmrun_command')
#     def test_is_running_error(self, mock_vmrun):
#         # Set _vm_id
#         self.provisioner._vm_id = "test-vm/test-vm.vmx"

#         # Mock _vmrun_command to raise an error
#         mock_vmrun.side_effect = subprocess.CalledProcessError(
#             returncode=1,
#             cmd=["vmrun", "-T", "ws", "list"],
#             output="Error listing VMs"
#         )

#         # Check that is_running returns False on error
#         self.assertFalse(self.provisioner.is_running())

#     def test_get_status(self):
#         # Test that get_status returns the current status
#         self.assertEqual(self.provisioner.get_status(), "not_started")

#         # Change status and check again
#         self.provisioner._status = "running"
#         self.assertEqual(self.provisioner.get_status(), "running")


# if __name__ == '__main__':
#     unittest.main()
