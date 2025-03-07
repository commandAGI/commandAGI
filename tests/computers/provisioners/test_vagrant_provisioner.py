# import unittest
# from unittest.mock import patch, MagicMock, call
# import time
# import os
# import subprocess
# from pathlib import Path

# from commandAGI.computers.provisioners.vagrant_provisioner import VagrantProvisioner


# class TestVagrantProvisioner(unittest.TestCase):
#     def setUp(self):
#         # Create a VagrantProvisioner with default parameters
#         self.provisioner = VagrantProvisioner(
#             port=8000,
#             box_name="test-box",
#             vagrant_file_path="test-path",
#             max_retries=2,
#             timeout=10
#         )

#     def test_init(self):
#         # Test that the provisioner initializes with the correct attributes
#         self.assertEqual(self.provisioner.port, 8000)
#         self.assertEqual(self.provisioner.box_name, "test-box")
#         self.assertEqual(self.provisioner.vagrant_file_path, "test-path")
#         self.assertEqual(self.provisioner.max_retries, 2)
#         self.assertEqual(self.provisioner.timeout, 10)
#         self.assertEqual(self.provisioner._status, "not_started")

#     def test_init_with_custom_params(self):
#         # Test initialization with custom parameters
#         provisioner = VagrantProvisioner(
#             port=9000,
#             box_name="custom-box",
#             vagrant_file_path="custom-path",
#             provider="virtualbox",
#             memory_mb=4096,
#             cpus=4,
#             max_retries=3,
#             timeout=20
#         )

#         self.assertEqual(provisioner.port, 9000)
#         self.assertEqual(provisioner.box_name, "custom-box")
#         self.assertEqual(provisioner.vagrant_file_path, "custom-path")
#         self.assertEqual(provisioner.provider, "virtualbox")
#         self.assertEqual(provisioner.memory_mb, 4096)
#         self.assertEqual(provisioner.cpus, 4)
#         self.assertEqual(provisioner.max_retries, 3)
#         self.assertEqual(provisioner.timeout, 20)

#     @patch('subprocess.run')
#     def test_vagrant_command_success(self, mock_run):
#         # Mock subprocess.run to return a successful result
#         mock_process = MagicMock()
#         mock_process.returncode = 0
#         mock_process.stdout = "Vagrant output"
#         mock_run.return_value = mock_process

#         # Call _vagrant_command
#         result = self.provisioner._vagrant_command(["status"])

#         # Check that subprocess.run was called with the right arguments
#         mock_run.assert_called_once()
#         call_args = mock_run.call_args[0][0]
#         self.assertEqual(call_args[0], "vagrant")
#         self.assertEqual(call_args[1], "status")

#         # Check that cwd was set correctly
#         self.assertEqual(mock_run.call_args[1]["cwd"], "test-path")

#         # Check that the result is correct
#         self.assertEqual(result, "Vagrant output")

#     @patch('subprocess.run')
#     def test_vagrant_command_error(self, mock_run):
#         # Mock subprocess.run to raise a subprocess.CalledProcessError
#         mock_run.side_effect = subprocess.CalledProcessError(
#             returncode=1,
#             cmd=["vagrant", "status"],
#             output="Error output"
#         )

#         # Call _vagrant_command and check that it raises the error
#         with self.assertRaises(subprocess.CalledProcessError):
#             self.provisioner._vagrant_command(["status"])

#     @patch.object(VagrantProvisioner, '_vagrant_command')
#     @patch.object(VagrantProvisioner, '_create_vagrantfile')
#     @patch.object(VagrantProvisioner, 'is_running')
#     @patch('time.sleep')
#     def test_setup_success(self, mock_sleep, mock_is_running, mock_create_vagrantfile, mock_vagrant):
#         # Mock _vagrant_command to return success for each call
#         mock_vagrant.side_effect = [
#             # up
#             ""
#         ]

#         # Mock is_running to return True
#         mock_is_running.return_value = True

#         # Call setup
#         self.provisioner.setup()

#         # Check that _create_vagrantfile was called
#         mock_create_vagrantfile.assert_called_once()

#         # Check that _vagrant_command was called with the right arguments
#         mock_vagrant.assert_called_once_with(["up", "--provider", "docker"])

#         # Check that status was updated
#         self.assertEqual(self.provisioner._status, "running")

#     @patch.object(VagrantProvisioner, '_vagrant_command')
#     @patch.object(VagrantProvisioner, '_create_vagrantfile')
#     @patch.object(VagrantProvisioner, 'is_running')
#     @patch('time.sleep')
#     def test_setup_with_custom_provider(self, mock_sleep, mock_is_running, mock_create_vagrantfile, mock_vagrant):
#         # Create a provisioner with a custom provider
#         provisioner = VagrantProvisioner(
#             port=8000,
#             box_name="test-box",
#             vagrant_file_path="test-path",
#             provider="virtualbox"
#         )

#         # Mock _vagrant_command to return success
#         mock_vagrant.return_value = ""

#         # Mock is_running to return True
#         mock_is_running.return_value = True

#         # Call setup
#         provisioner.setup()

#         # Check that _vagrant_command was called with the right provider
#         mock_vagrant.assert_called_once_with(["up", "--provider", "virtualbox"])

#     @patch.object(VagrantProvisioner, '_vagrant_command')
#     @patch.object(VagrantProvisioner, '_create_vagrantfile')
#     @patch.object(VagrantProvisioner, 'is_running')
#     @patch('time.sleep')
#     def test_setup_up_error(self, mock_sleep, mock_is_running, mock_create_vagrantfile, mock_vagrant):
#         # Mock _vagrant_command to raise an error on up
#         mock_vagrant.side_effect = subprocess.CalledProcessError(
#             returncode=1,
#             cmd=["vagrant", "up", "--provider", "docker"],
#             output="Error starting VM"
#         )

#         # Call setup and check that it raises the error
#         with self.assertRaises(subprocess.CalledProcessError):
#             self.provisioner.setup()

#         # Check that _vagrant_command was called once
#         mock_vagrant.assert_called_once()

#         # Check that status was updated to error
#         self.assertEqual(self.provisioner._status, "error")

#     @patch.object(VagrantProvisioner, '_vagrant_command')
#     @patch.object(VagrantProvisioner, '_create_vagrantfile')
#     @patch.object(VagrantProvisioner, 'is_running')
#     @patch('time.sleep')
#     def test_setup_is_running_timeout(self, mock_sleep, mock_is_running, mock_create_vagrantfile, mock_vagrant):
#         # Mock _vagrant_command to return success
#         mock_vagrant.return_value = ""

#         # Mock is_running to always return False (timeout)
#         mock_is_running.return_value = False

#         # Call setup and check that it raises TimeoutError
#         with self.assertRaises(TimeoutError):
#             self.provisioner.setup()

#         # Check that _vagrant_command was called once
#         mock_vagrant.assert_called_once()

#         # Check that status was updated to error
#         self.assertEqual(self.provisioner._status, "error")

#     @patch.object(VagrantProvisioner, '_vagrant_command')
#     @patch.object(VagrantProvisioner, '_create_vagrantfile')
#     @patch.object(VagrantProvisioner, 'is_running')
#     @patch('time.sleep')
#     def test_setup_retry_success(self, mock_sleep, mock_is_running, mock_create_vagrantfile, mock_vagrant):
#         # Mock _vagrant_command to fail once, then succeed
#         mock_vagrant.side_effect = [
#             # First attempt - up fails
#             subprocess.CalledProcessError(
#                 returncode=1,
#                 cmd=["vagrant", "up", "--provider", "docker"],
#                 output="Error starting VM"
#             ),
#             # Second attempt - up succeeds
#             ""
#         ]

#         # Mock is_running to return True
#         mock_is_running.return_value = True

#         # Call setup
#         self.provisioner.setup()

#         # Check that _vagrant_command was called twice
#         self.assertEqual(mock_vagrant.call_count, 2)

#         # Check that sleep was called for retry backoff
#         mock_sleep.assert_called_once_with(2)  # 2^1

#         # Check that status was updated
#         self.assertEqual(self.provisioner._status, "running")

#     @patch.object(VagrantProvisioner, '_vagrant_command')
#     @patch.object(VagrantProvisioner, '_create_vagrantfile')
#     @patch.object(VagrantProvisioner, 'is_running')
#     @patch('time.sleep')
#     def test_setup_max_retries_exceeded(self, mock_sleep, mock_is_running, mock_create_vagrantfile, mock_vagrant):
#         # Mock _vagrant_command to always fail
#         mock_vagrant.side_effect = subprocess.CalledProcessError(
#             returncode=1,
#             cmd=["vagrant", "up", "--provider", "docker"],
#             output="Error starting VM"
#         )

#         # Call setup and check that it raises the error
#         with self.assertRaises(subprocess.CalledProcessError):
#             self.provisioner.setup()

#         # Check that _vagrant_command was called max_retries times
#         self.assertEqual(mock_vagrant.call_count, 2)  # max_retries=2

#         # Check that sleep was called for retry backoff
#         mock_sleep.assert_has_calls([call(2), call(4)])  # 2^1, 2^2

#         # Check that status was updated to error
#         self.assertEqual(self.provisioner._status, "error")

#     @patch.object(VagrantProvisioner, '_vagrant_command')
#     def test_teardown_success(self, mock_vagrant):
#         # Set status to running
#         self.provisioner._status = "running"

#         # Mock _vagrant_command to return success
#         mock_vagrant.return_value = ""

#         # Call teardown
#         self.provisioner.teardown()

#         # Check that _vagrant_command was called with the right arguments
#         mock_vagrant.assert_called_once_with(["destroy", "-f"])

#         # Check that status was updated
#         self.assertEqual(self.provisioner._status, "stopped")

#     @patch.object(VagrantProvisioner, '_vagrant_command')
#     def test_teardown_error(self, mock_vagrant):
#         # Set status to running
#         self.provisioner._status = "running"

#         # Mock _vagrant_command to raise an error
#         mock_vagrant.side_effect = subprocess.CalledProcessError(
#             returncode=1,
#             cmd=["vagrant", "destroy", "-f"],
#             output="Error destroying VM"
#         )

#         # Call teardown
#         self.provisioner.teardown()

#         # Check that _vagrant_command was called once
#         mock_vagrant.assert_called_once()

#         # Check that status was updated to error
#         self.assertEqual(self.provisioner._status, "error")

#     @patch.object(VagrantProvisioner, '_vagrant_command')
#     def test_is_running_true(self, mock_vagrant):
#         # Mock _vagrant_command to return a running VM
#         mock_vagrant.return_value = "Current machine states:\n\ndefault                   running (docker)"

#         # Check that is_running returns True
#         self.assertTrue(self.provisioner.is_running())

#         # Check that _vagrant_command was called with the right arguments
#         mock_vagrant.assert_called_once_with(["status"])

#     @patch.object(VagrantProvisioner, '_vagrant_command')
#     def test_is_running_false(self, mock_vagrant):
#         # Mock _vagrant_command to return a powered off VM
#         mock_vagrant.return_value = "Current machine states:\n\ndefault                   poweroff (docker)"

#         # Check that is_running returns False
#         self.assertFalse(self.provisioner.is_running())

#     @patch.object(VagrantProvisioner, '_vagrant_command')
#     def test_is_running_not_created(self, mock_vagrant):
#         # Mock _vagrant_command to return a not created VM
#         mock_vagrant.return_value = "Current machine states:\n\ndefault                   not created (docker)"

#         # Check that is_running returns False
#         self.assertFalse(self.provisioner.is_running())

#     @patch.object(VagrantProvisioner, '_vagrant_command')
#     def test_is_running_error(self, mock_vagrant):
#         # Mock _vagrant_command to raise an error
#         mock_vagrant.side_effect = subprocess.CalledProcessError(
#             returncode=1,
#             cmd=["vagrant", "status"],
#             output="Error getting VM status"
#         )

#         # Check that is_running returns False on error
#         self.assertFalse(self.provisioner.is_running())

#     @patch('os.path.exists')
#     @patch('builtins.open', new_callable=unittest.mock.mock_open)
#     def test_create_vagrantfile(self, mock_open, mock_exists):
#         # Mock os.path.exists to return False (file doesn't exist)
#         mock_exists.return_value = False

#         # Call _create_vagrantfile
#         self.provisioner._create_vagrantfile()

#         # Check that open was called with the right arguments
#         mock_open.assert_called_once_with(Path("test-path") / "Vagrantfile", "w")

#         # Check that the Vagrantfile content was written
#         handle = mock_open()
#         write_calls = handle.write.call_args_list

#         # Check that the Vagrantfile contains the box name
#         self.assertTrue(any("test-box" in str(call) for call in write_calls))

#         # Check that the Vagrantfile contains the port forwarding
#         self.assertTrue(any("8000" in str(call) for call in write_calls))

#     @patch('os.path.exists')
#     def test_create_vagrantfile_already_exists(self, mock_exists):
#         # Mock os.path.exists to return True (file exists)
#         mock_exists.return_value = True

#         # Call _create_vagrantfile
#         self.provisioner._create_vagrantfile()

#         # Check that os.path.exists was called with the right arguments
#         mock_exists.assert_called_once_with(Path("test-path") / "Vagrantfile")

#     def test_get_status(self):
#         # Test that get_status returns the current status
#         self.assertEqual(self.provisioner.get_status(), "not_started")

#         # Change status and check again
#         self.provisioner._status = "running"
#         self.assertEqual(self.provisioner.get_status(), "running")


# if __name__ == '__main__':
#     unittest.main()
