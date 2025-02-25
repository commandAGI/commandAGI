# Provisioners API

This section contains documentation for the provisioners that manage computer environments. Provisioners handle the creation, configuration, and cleanup of environments where computers run.

## Base Classes

- **[Base Provisioner](base_provisioner.md)** - Abstract base class defining the provisioner interface
- **[Manual Provisioner](manual_provisioner.md)** - Simple provisioner for manually managed environments

## Container Provisioners

- **[Docker Provisioner](docker_provisioner.md)** - Provision environments using Docker containers
- **[Kubernetes Provisioner](kubernetes_provisioner.md)** - Provision environments using Kubernetes pods

## Cloud Provisioners

- **[AWS Provisioner](aws_provisioner.md)** - Provision environments on Amazon Web Services
- **[Azure Provisioner](azure_provisioner.md)** - Provision environments on Microsoft Azure
- **[GCP Provisioner](gcp_provisioner.md)** - Provision environments on Google Cloud Platform

## Virtual Machine Provisioners

- **[VirtualBox Provisioner](virtualbox_provisioner.md)** - Provision environments using VirtualBox VMs
- **[VMware Provisioner](vmware_provisioner.md)** - Provision environments using VMware VMs
- **[Vagrant Provisioner](vagrant_provisioner.md)** - Provision environments using Vagrant
