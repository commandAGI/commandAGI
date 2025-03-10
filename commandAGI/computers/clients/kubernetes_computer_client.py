import logging
import re
import time
from enum import Enum
from typing import Optional

from kubernetes import client, config

from commandAGI.version import get_container_version

from commandAGI.computers.clients.base_computer_client import BaseComputerComputerClient

logger = logging.getLogger(__name__)


class KubernetesPlatform(str, Enum):
    LOCAL = "local"  # local k8s cluster or minikube
    AWS_EKS = "aws_eks"
    AZURE_AKS = "azure_aks"
    GCP_GKE = "gcp_gke"


class KubernetesComputerClient(BaseComputerComputerClient):
    """Kubernetes-based computer computer_client.

    This computer_client creates and manages Kubernetes deployments and services for running the commandAGI daemon.
    It supports both local Kubernetes clusters and cloud-based Kubernetes services.

    Args:
        daemon_base_url: Base URL for the daemon service
        daemon_port: Port for the daemon service
        platform: Kubernetes platform to use (LOCAL, AWS_EKS, AZURE_AKS, GCP_GKE)
        namespace: Kubernetes namespace to use
        deployment_name: Optional name for the deployment. If not provided, a name will be generated
                        based on deployment_prefix
        service_name: Optional name for the service. If not provided, a name will be generated
                     based on service_prefix
        deployment_prefix: Prefix to use when generating deployment names (default: "commandagi-daemon")
        service_prefix: Prefix to use when generating service names (default: "commandagi-daemon-svc")
        cluster_name: Name of the Kubernetes cluster (required for cloud platforms)
        region: Cloud region (required for AWS_EKS and GCP_GKE)
        resource_group: Resource group (required for AZURE_AKS)
        project_id: Project ID (required for GCP_GKE)
        version: Container image version to use
        max_retries: Maximum number of retries for setup operations
        timeout: Timeout in seconds for operations
    """

    def __init__(
        self,
        daemon_base_url: str = "http://localhost",
        daemon_port: Optional[int] = None,
        platform: KubernetesPlatform = KubernetesPlatform.LOCAL,
        namespace: str = "default",
        deployment_name: Optional[str] = None,
        service_name: Optional[str] = None,
        deployment_prefix: str = "commandagi-daemon",
        service_prefix: str = "commandagi-daemon-svc",
        # Cloud-specific parameters
        cluster_name: Optional[str] = None,
        region: Optional[str] = None,
        resource_group: Optional[str] = None,
        project_id: Optional[str] = None,
        version: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 300,  # 5 minutes
    ):
        # Initialize the base class with daemon URL and port
        super().__init__(
            daemon_base_url=daemon_base_url,
            daemon_port=daemon_port,
        )

        self.platform = platform
        self.namespace = namespace
        self.deployment_prefix = deployment_prefix
        self.service_prefix = service_prefix
        self.deployment_name = deployment_name
        self.service_name = service_name
        self.version = version or get_container_version()
        self.max_retries = max_retries
        self.timeout = timeout
        self._status = "not_started"

        # Validate required parameters based on platform
        if platform != KubernetesPlatform.LOCAL:
            if not cluster_name:
                raise ValueError(f"cluster_name is required for {platform}")
            if (
                platform in [KubernetesPlatform.AWS_EKS, KubernetesPlatform.GCP_GKE]
                and not region
            ):
                raise ValueError(f"region is required for {platform}")
            if platform == KubernetesPlatform.AZURE_AKS and not resource_group:
                raise ValueError(f"resource_group is required for {platform}")
            if platform == KubernetesPlatform.GCP_GKE and not project_id:
                raise ValueError(f"project_id is required for {platform}")

        # Configure kubernetes client based on platform
        try:
            logger.info(f"Configuring Kubernetes client for platform {platform}")
            if platform == KubernetesPlatform.LOCAL:
                config.load_kube_config()
            elif platform == KubernetesPlatform.AWS_EKS:
                config.load_kube_config(context=f"arn:aws:eks:{region}:{cluster_name}")
            elif platform == KubernetesPlatform.AZURE_AKS:
                config.load_kube_config(context=f"{resource_group}_{cluster_name}")
            elif platform == KubernetesPlatform.GCP_GKE:
                config.load_kube_config(
                    context=f"gke_{project_id}_{region}_{cluster_name}"
                )

            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            logger.info("Kubernetes client configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Kubernetes client: {e}")
            raise

    def _find_next_available_name(self, resource_type: str, prefix: str) -> str:
        """Find the next available name for a Kubernetes resource with the given prefix.

        This method checks for existing resources with the prefix and finds the next
        available name by incrementing a numeric suffix. For example, if deployments
        'commandagi-daemon' and 'commandagi-daemon-1' exist, it will return 'commandagi-daemon-2'.

        Args:
            resource_type: Type of resource ('deployment' or 'service')
            prefix: Prefix to use for the resource name

        Returns:
            str: The next available resource name
        """
        try:
            existing_names = []

            if resource_type == "deployment":
                # List all deployments in the namespace
                deployments = self.apps_v1.list_namespaced_deployment(
                    namespace=self.namespace
                )
                existing_names = [d.metadata.name for d in deployments.items]
            elif resource_type == "service":
                # List all services in the namespace
                services = self.core_v1.list_namespaced_service(
                    namespace=self.namespace
                )
                existing_names = [s.metadata.name for s in services.items]
            else:
                raise ValueError(f"Unsupported resource type: {resource_type}")

            # Filter names that match our prefix pattern
            prefix_pattern = f"^{re.escape(prefix)}(-\\d+)?$"
            matching_names = [
                name for name in existing_names if re.match(prefix_pattern, name)
            ]

            if not matching_names:
                # No matching resources found, use the prefix as is
                return prefix

            # Find the highest suffix number
            highest_suffix = 0
            for name in matching_names:
                # Extract the suffix number if it exists
                suffix_match = re.search(f"^{re.escape(prefix)}-(\\d+)$", name)
                if suffix_match:
                    suffix_num = int(suffix_match.group(1))
                    highest_suffix = max(highest_suffix, suffix_num)
                elif name == prefix:
                    # The base prefix exists without a number
                    highest_suffix = max(highest_suffix, 0)

            # Create the next available name
            if highest_suffix == 0 and prefix not in matching_names:
                return prefix
            else:
                return f"{prefix}-{highest_suffix + 1}"

        except Exception as e:
            logger.error(f"Error finding next available {resource_type} name: {e}")
            # In case of error, generate a name with a timestamp to avoid
            # conflicts
            import datetime

            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            return f"{prefix}-{timestamp}"

    def setup(self) -> None:
        """Create Kubernetes deployment and service"""
        self._status = "starting"
        self.resources_created = False
        retry_count = 0

        # Use default port 8000 if not specified
        if self.daemon_port is None:
            self.daemon_port = 8000
            logger.info(
                f"Using default port {
                    self.daemon_port} for daemon service"
            )
        else:
            logger.info(
                f"Using specified port {
                    self.daemon_port} for daemon service"
            )

        # If deployment_name is not provided, find the next available name
        if self.deployment_name is None:
            self.deployment_name = self._find_next_available_name(
                "deployment", self.deployment_prefix
            )
            logger.info(f"Using deployment name: {self.deployment_name}")

        # If service_name is not provided, find the next available name
        if self.service_name is None:
            self.service_name = self._find_next_available_name(
                "service", self.service_prefix
            )
            logger.info(f"Using service name: {self.service_name}")

        while retry_count < self.max_retries:
            try:
                logger.info(
                    f"Creating Kubernetes deployment {
                        self.deployment_name} in namespace {
                        self.namespace}"
                )

                # Create deployment
                deployment = client.V1Deployment(
                    metadata=client.V1ObjectMeta(name=self.deployment_name),
                    spec=client.V1DeploymentSpec(
                        replicas=1,
                        selector=client.V1LabelSelector(
                            match_labels={"app": "commandagi-daemon"}
                        ),
                        template=client.V1PodTemplateSpec(
                            metadata=client.V1ObjectMeta(
                                labels={"app": "commandagi-daemon"}
                            ),
                            spec=client.V1PodSpec(
                                containers=[
                                    client.V1Container(
                                        name="commandagi-daemon",
                                        image=f"commandagi-daemon:{self.version}",
                                        ports=[
                                            client.V1ContainerPort(
                                                container_port=self.daemon_port
                                            )
                                        ],
                                        env=[
                                            client.V1EnvVar(
                                                name="DAEMON_PORT",
                                                value=str(self.daemon_port),
                                            ),
                                            # Add token if it exists
                                            (
                                                client.V1EnvVar(
                                                    name="DAEMON_TOKEN",
                                                    value=getattr(
                                                        self, "daemon_token", ""
                                                    ),
                                                )
                                                if hasattr(self, "daemon_token")
                                                and self.daemon_token
                                                else None
                                            ),
                                        ],
                                        args=[
                                            "--port",
                                            str(self.daemon_port),
                                            "--backend",
                                            "pynput",
                                        ],
                                    )
                                ]
                            ),
                        ),
                    ),
                )

                # Filter out None values from env list
                if deployment.spec.template.spec.containers[0].env:
                    deployment.spec.template.spec.containers[0].env = [
                        env
                        for env in deployment.spec.template.spec.containers[0].env
                        if env is not None
                    ]

                # Create service
                service = client.V1Service(
                    metadata=client.V1ObjectMeta(name=self.service_name),
                    spec=client.V1ServiceSpec(
                        selector={"app": "commandagi-daemon"},
                        ports=[client.V1ServicePort(port=self.daemon_port)],
                        type="LoadBalancer",  # Use LoadBalancer for cloud platforms
                    ),
                )

                # Create deployment
                logger.info(f"Creating deployment {self.deployment_name}")
                self.apps_v1.create_namespaced_deployment(
                    namespace=self.namespace, body=deployment
                )

                # Create service
                logger.info(f"Creating service {self.service_name}")
                self.core_v1.create_namespaced_service(
                    namespace=self.namespace, body=service
                )

                self.resources_created = True

                # Wait for deployment to be available
                logger.info(
                    f"Waiting for deployment {
                        self.deployment_name} to be available"
                )
                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    if self.is_running():
                        self._status = "running"
                        logger.info(
                            f"Deployment {
                                self.deployment_name} is now available"
                        )
                        return
                    time.sleep(5)

                # If we get here, the deployment didn't become available in
                # time
                self._status = "error"
                logger.error(
                    f"Timeout waiting for deployment {
                        self.deployment_name} to be available"
                )
                raise TimeoutError(
                    f"Timeout waiting for deployment {
                        self.deployment_name} to be available"
                )

            except Exception as e:
                retry_count += 1
                if retry_count >= self.max_retries:
                    self._status = "error"
                    logger.error(
                        f"Failed to create Kubernetes resources after {
                            self.max_retries} attempts: {e}"
                    )
                    # Attempt cleanup if partial creation occurred
                    if self.resources_created:
                        logger.info(
                            "Attempting to clean up partially created resources"
                        )
                        self.teardown()
                    raise
                logger.warning(
                    f"Error creating Kubernetes resources, retrying ({retry_count}/{self.max_retries}): {e}"
                )
                time.sleep(2**retry_count)  # Exponential backoff

    def teardown(self) -> None:
        """Tear down Kubernetes deployment and service"""
        self._status = "stopping"

        try:
            # Delete deployment
            logger.info(f"Deleting deployment {self.deployment_name}")
            try:
                self.apps_v1.delete_namespaced_deployment(
                    name=self.deployment_name, namespace=self.namespace
                )
                logger.info(
                    f"Deployment {
                        self.deployment_name} deleted successfully"
                )
            except Exception as e:
                logger.error(
                    f"Error deleting deployment {
                        self.deployment_name}: {e}"
                )

            # Delete service
            logger.info(f"Deleting service {self.service_name}")
            try:
                self.core_v1.delete_namespaced_service(
                    name=self.service_name, namespace=self.namespace
                )
                logger.info(
                    f"Service {
                        self.service_name} deleted successfully"
                )
            except Exception as e:
                logger.error(
                    f"Error deleting service {
                        self.service_name}: {e}"
                )

            # Wait for resources to be deleted
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                deployment_exists = True
                service_exists = True

                try:
                    self.apps_v1.read_namespaced_deployment(
                        name=self.deployment_name, namespace=self.namespace
                    )
                except client.exceptions.ApiException as e:
                    if e.status == 404:
                        deployment_exists = False

                try:
                    self.core_v1.read_namespaced_service(
                        name=self.service_name, namespace=self.namespace
                    )
                except client.exceptions.ApiException as e:
                    if e.status == 404:
                        service_exists = False

                if not deployment_exists and not service_exists:
                    logger.info("All Kubernetes resources deleted successfully")
                    break

                logger.debug(
                    f"Waiting for resources to be deleted: deployment={deployment_exists}, service={service_exists}"
                )
                time.sleep(5)

            self._status = "stopped"
        except Exception as e:
            self._status = "error"
            logger.error(f"Error during teardown: {e}")

    def is_running(self) -> bool:
        """Check if the Kubernetes deployment is running and available"""
        try:
            deployment = self.apps_v1.read_namespaced_deployment_status(
                name=self.deployment_name, namespace=self.namespace
            )
            is_running = (
                deployment.status.available_replicas is not None
                and deployment.status.available_replicas > 0
            )
            logger.debug(
                f"Deployment {
                    self.deployment_name} running status: {is_running}"
            )
            return is_running
        except Exception as e:
            logger.error(f"Error checking deployment status: {e}")
            return False

    def get_status(self) -> str:
        """Get the current status of the computer_client."""
        return self._status
