# import unittest
# from unittest.mock import patch, MagicMock, call
# import time
# import os
# import subprocess
# from pathlib import Path

# from commandAGI.computers.provisioners.virtualbox_provisioner import VirtualBoxProvisioner


# class TestVirtualBoxProvisioner(unittest.TestCase):
#     def setUp(self):
#         # Create a VirtualBoxProvisioner with default parameters
#         self.provisioner = VirtualBoxProvisioner(
#             port=8000,
#             vm_name="test-vm",
#             vm_image="test-image.ova",
#             max_retries=2,
#             timeout=10
#         )

#     def test_init(self):
#         # Test that the provisioner initializes with the correct attributes
#         self.assertEqual(self.provisioner.port, 8000)
#         self.assertEqual(self.provisioner.vm_name, "test-vm")
#         self.assertEqual(self.provisioner.vm_image, "test-image.ova")
#         self.assertEqual(self.provisioner.max_retries, 2)
#         self.assertEqual(self.provisioner.timeout, 10)
#         self.assertEqual(self.provisioner._status, "not_started")
#         self.assertIsNone(self.provisioner._vm_id)

#     def test_init_with_custom_params(self):
#         # Test initialization with custom parameters
#         provisioner = VirtualBoxProvisioner(
#             port=9000,
#             vm_name="custom-vm",
#             vm_image="custom-image.ova",
#             memory_mb=4096,
#             cpus=4,
#             headless=False,
#             max_retries=3,
#             timeout=20
#         )

#         self.assertEqual(provisioner.port, 9000)
#         self.assertEqual(provisioner.vm_name, "custom-vm")
#         self.assertEqual(provisioner.vm_image, "custom-image.ova")
#         self.assertEqual(provisioner.memory_mb, 4096)
#         self.assertEqual(provisioner.cpus, 4)
#         self.assertFalse(provisioner.headless)
#         self.assertEqual(provisioner.max_retries, 3)
#         self.assertEqual(provisioner.timeout, 20)

#     @patch('subprocess.run')
#     def test_vboxmanage_command_success(self, mock_run):
#         # Mock subprocess.run to return a successful result
#         mock_process = MagicMock()
#         mock_process.returncode = 0
#         mock_process.stdout = "VBoxManage output"
#         mock_run.return_value = mock_process

#         # Call _vboxmanage_command
#         result = self.provisioner._vboxmanage_command(["list", "vms"])

#         # Check that subprocess.run was called with the right arguments
#         mock_run.assert_called_once()
#         call_args = mock_run.call_args[0][0]
#         self.assertEqual(call_args[0], "VBoxManage")
#         self.assertEqual(call_args[1], "list")
#         self.assertEqual(call_args[2], "vms")

#         # Check that the result is correct
#         self.assertEqual(result, "VBoxManage output")

#     @patch('subprocess.run')
#     def test_vboxmanage_command_error(self, mock_run):
#         # Mock subprocess.run to raise a subprocess.CalledProcessError
#         mock_run.side_effect = subprocess.CalledProcessError(
#             returncode=1,
#             cmd=["VBoxManage", "list", "vms"],
#             output="Error output"
#         )

#         # Call _vboxmanage_command and check that it raises the error
#         with self.assertRaises(subprocess.CalledProcessError):
#             self.provisioner._vboxmanage_command(["list", "vms"])

#     @patch.object(VirtualBoxProvisioner, '_vboxmanage_command')
#     @patch.object(VirtualBoxProvisioner, 'is_running')
#     @patch('time.sleep')
#     def test_setup_success(self, mock_sleep, mock_is_running, mock_vboxmanage):
#         # Mock _vboxmanage_command to return success for each call
#         mock_vboxmanage.side_effect = [
#             # import
#             "VM imported with UUID: 12345678-1234-1234-1234-123456789abc",
#             # modifyvm
#             "",
#             # modifyvm (memory)
#             "",
#             # modifyvm (cpus)
#             "",
#             # startvm
#             ""
#         ]

#         # Mock is_running to return True
#         mock_is_running.return_value = True

#         # Call setup
#         self.provisioner.setup()

#         # Check that _vboxmanage_command was called with the right arguments
#         self.assertEqual(mock_vboxmanage.call_count, 5)

#         # Check import call
#         import_call = mock_vboxmanage.call_args_list[0]
#         self.assertEqual(import_call[0][0][0], "import")
#         self.assertEqual(import_call[0][0][1], "test-image.ova")

#         # Check modifyvm calls
#         modifyvm_call = mock_vboxmanage.call_args_list[1]
#         self.assertEqual(modifyvm_call[0][0][0], "modifyvm")
#         self.assertEqual(modifyvm_call[0][0][1], "12345678-1234-1234-1234-123456789abc")
#         self.assertEqual(modifyvm_call[0][0][2], "--name")
#         self.assertEqual(modifyvm_call[0][0][3], "test-vm")

#         # Check startvm call
#         startvm_call = mock_vboxmanage.call_args_list[4]
#         self.assertEqual(startvm_call[0][0][0], "startvm")
#         self.assertEqual(startvm_call[0][0][1], "12345678-1234-1234-1234-123456789abc")
#         self.assertEqual(startvm_call[0][0][2], "--type")
#         self.assertEqual(startvm_call[0][0][3], "headless")

#         # Check that _vm_id was set
#         self.assertEqual(self.provisioner._vm_id, "12345678-1234-1234-1234-123456789abc")

#         # Check that status was updated
#         self.assertEqual(self.provisioner._status, "running")

#     @patch.object(VirtualBoxProvisioner, '_vboxmanage_command')
#     @patch.object(VirtualBoxProvisioner, 'is_running')
#     @patch('time.sleep')
#     def test_setup_import_error(self, mock_sleep, mock_is_running, mock_vboxmanage):
#         # Mock _vboxmanage_command to raise an error on import
#         mock_vboxmanage.side_effect = subprocess.CalledProcessError(
#             returncode=1,
#             cmd=["VBoxManage", "import", "test-image.ova"],
#             output="Error importing VM"
#         )

#         # Call setup and check that it raises the error
#         with self.assertRaises(subprocess.CalledProcessError):
#             self.provisioner.setup()

#         # Check that _vboxmanage_command was called once
#         mock_vboxmanage.assert_called_once()

#         # Check that status was updated to error
#         self.assertEqual(self.provisioner._status, "error")

#     @patch.object(VirtualBoxProvisioner, '_vboxmanage_command')
#     @patch.object(VirtualBoxProvisioner, 'is_running')
#     @patch('time.sleep')
#     def test_setup_is_running_timeout(self, mock_sleep, mock_is_running, mock_vboxmanage):
#         # Mock _vboxmanage_command to return success for each call
#         mock_vboxmanage.side_effect = [
#             # import
#             "VM imported with UUID: 12345678-1234-1234-1234-123456789abc",
#             # modifyvm
#             "",
#             # modifyvm (memory)
#             "",
#             # modifyvm (cpus)
#             "",
#             # startvm
#             ""
#         ]

#         # Mock is_running to always return False (timeout)
#         mock_is_running.return_value = False

#         # Call setup and check that it raises TimeoutError
#         with self.assertRaises(TimeoutError):
#             self.provisioner.setup()

#         # Check that _vboxmanage_command was called 5 times
#         self.assertEqual(mock_vboxmanage.call_count, 5)

#         # Check that status was updated to error
#         self.assertEqual(self.provisioner._status, "error")

#     @patch.object(VirtualBoxProvisioner, '_vboxmanage_command')
#     @patch.object(VirtualBoxProvisioner, 'is_running')
#     @patch('time.sleep')
#     def test_setup_retry_success(self, mock_sleep, mock_is_running, mock_vboxmanage):
#         # Mock _vboxmanage_command to fail once, then succeed
#         mock_vboxmanage.side_effect = [
#             # First attempt - import fails
#             subprocess.CalledProcessError(
#                 returncode=1,
#                 cmd=["VBoxManage", "import", "test-image.ova"],
#                 output="Error importing VM"
#             ),
#             # Second attempt - import succeeds
#             "VM imported with UUID: 12345678-1234-1234-1234-123456789abc",
#             # modifyvm
#             "",
#             # modifyvm (memory)
#             "",
#             # modifyvm (cpus)
#             "",
#             # startvm
#             ""
#         ]

#         # Mock is_running to return True
#         mock_is_running.return_value = True

#         # Call setup
#         self.provisioner.setup()

#         # Check that _vboxmanage_command was called 6 times (1 failed + 5 successful)
#         self.assertEqual(mock_vboxmanage.call_count, 6)

#         # Check that sleep was called for retry backoff
#         mock_sleep.assert_called_once_with(2)  # 2^1

#         # Check that status was updated
#         self.assertEqual(self.provisioner._status, "running")

#     @patch.object(VirtualBoxProvisioner, '_vboxmanage_command')
#     @patch.object(VirtualBoxProvisioner, 'is_running')
#     @patch('time.sleep')
#     def test_setup_max_retries_exceeded(self, mock_sleep, mock_is_running, mock_vboxmanage):
#         # Mock _vboxmanage_command to always fail
#         mock_vboxmanage.side_effect = subprocess.CalledProcessError(
#             returncode=1,
#             cmd=["VBoxManage", "import", "test-image.ova"],
#             output="Error importing VM"
#         )

#         # Call setup and check that it raises the error
#         with self.assertRaises(subprocess.CalledProcessError):
#             self.provisioner.setup()

#         # Check that _vboxmanage_command was called max_retries times
#         self.assertEqual(mock_vboxmanage.call_count, 2)  # max_retries=2

#         # Check that sleep was called for retry backoff
#         mock_sleep.assert_has_calls([call(2), call(4)])  # 2^1, 2^2

#         # Check that status was updated to error
#         self.assertEqual(self.provisioner._status, "error")

#     @patch.object(VirtualBoxProvisioner, '_vboxmanage_command')
#     def test_teardown_success(self, mock_vboxmanage):
#         # Set _vm_id
#         self.provisioner._vm_id = "12345678-1234-1234-1234-123456789abc"
#         self.provisioner._status = "running"

#         # Mock _vboxmanage_command to return success for each call
#         mock_vboxmanage.side_effect = [
#             # controlvm
#             "",
#             # unregistervm
#             ""
#         ]

#         # Call teardown
#         self.provisioner.teardown()

#         # Check that _vboxmanage_command was called with the right arguments
#         self.assertEqual(mock_vboxmanage.call_count, 2)

#         # Check controlvm call
#         controlvm_call = mock_vboxmanage.call_args_list[0]
#         self.assertEqual(controlvm_call[0][0][0], "controlvm")
#         self.assertEqual(controlvm_call[0][0][1], "12345678-1234-1234-1234-123456789abc")
#         self.assertEqual(controlvm_call[0][0][2], "poweroff")

#         # Check unregistervm call
#         unregistervm_call = mock_vboxmanage.call_args_list[1]
#         self.assertEqual(unregistervm_call[0][0][0], "unregistervm")
#         self.assertEqual(unregistervm_call[0][0][1], "12345678-1234-1234-1234-123456789abc")
#         self.assertEqual(unregistervm_call[0][0][2], "--delete")

#         # Check that status was updated
#         self.assertEqual(self.provisioner._status, "stopped")

#     @patch.object(VirtualBoxProvisioner, '_vboxmanage_command')
#     def test_teardown_no_vm_id(self, mock_vboxmanage):
#         # Don't set _vm_id
#         self.provisioner._vm_id = None

#         # Call teardown
#         self.provisioner.teardown()

#         # Check that _vboxmanage_command was not called
#         mock_vboxmanage.assert_not_called()

#         # Check that status was updated
#         self.assertEqual(self.provisioner._status, "stopped")

#     @patch.object(VirtualBoxProvisioner, '_vboxmanage_command')
#     def test_teardown_error(self, mock_vboxmanage):
#         # Set _vm_id
#         self.provisioner._vm_id = "12345678-1234-1234-1234-123456789abc"
#         self.provisioner._status = "running"

#         # Mock _vboxmanage_command to raise an error
#         mock_vboxmanage.side_effect = subprocess.CalledProcessError(
#             returncode=1,
#             cmd=["VBoxManage", "controlvm", "12345678-1234-1234-1234-123456789abc", "poweroff"],
#             output="Error stopping VM"
#         )

#         # Call teardown
#         self.provisioner.teardown()

#         # Check that _vboxmanage_command was called once
#         mock_vboxmanage.assert_called_once()

#         # Check that status was updated to error
#         self.assertEqual(self.provisioner._status, "error")

#     @patch.object(VirtualBoxProvisioner, '_vboxmanage_command')
#     def test_is_running_true(self, mock_vboxmanage):
#         # Set _vm_id
#         self.provisioner._vm_id = "12345678-1234-1234-1234-123456789abc"

#         # Mock _vboxmanage_command to return a running VM
#         mock_vboxmanage.return_value = "State:           running"

#         # Check that is_running returns True
#         self.assertTrue(self.provisioner.is_running())

#         # Check that _vboxmanage_command was called with the right arguments
#         mock_vboxmanage.assert_called_once_with([
#             "showvminfo", "12345678-1234-1234-1234-123456789abc", "--machinereadable"
#         ])

#     @patch.object(VirtualBoxProvisioner, '_vboxmanage_command')
#     def test_is_running_false(self, mock_vboxmanage):
#         # Set _vm_id
#         self.provisioner._vm_id = "12345678-1234-1234-1234-123456789abc"

#         # Mock _vboxmanage_command to return a powered off VM
#         mock_vboxmanage.return_value = "State:           poweroff"

#         # Check that is_running returns False
#         self.assertFalse(self.provisioner.is_running())

#     @patch.object(VirtualBoxProvisioner, '_vboxmanage_command')
#     def test_is_running_no_vm_id(self, mock_vboxmanage):
#         # Don't set _vm_id
#         self.provisioner._vm_id = None

#         # Check that is_running returns False
#         self.assertFalse(self.provisioner.is_running())

#         # Check that _vboxmanage_command was not called
#         mock_vboxmanage.assert_not_called()

#     @patch.object(VirtualBoxProvisioner, '_vboxmanage_command')
#     def test_is_running_error(self, mock_vboxmanage):
#         # Set _vm_id
#         self.provisioner._vm_id = "12345678-1234-1234-1234-123456789abc"

#         # Mock _vboxmanage_command to raise an error
#         mock_vboxmanage.side_effect = subprocess.CalledProcessError(
#             returncode=1,
#             cmd=["VBoxManage", "showvminfo", "12345678-1234-1234-1234-123456789abc", "--machinereadable"],
#             output="Error getting VM info"
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
