from enum import Enum
from kubernetes import client, config
from typing import Optional
import time
import logging
from .base_provisioner import BaseComputerProvisioner
from commandLAB.version import get_container_version

logger = logging.getLogger(__name__)

class KubernetesPlatform(str, Enum):
    LOCAL = "local"  # local k8s cluster or minikube
    AWS_EKS = "aws_eks"
    AZURE_AKS = "azure_aks"
    GCP_GKE = "gcp_gke"


class KubernetesProvisioner(BaseComputerProvisioner):
    def __init__(
        self,
        port: int = 8000,
        platform: KubernetesPlatform = KubernetesPlatform.LOCAL,
        namespace: str = "default",
        # Cloud-specific parameters
        cluster_name: Optional[str] = None,
        region: Optional[str] = None,
        resource_group: Optional[str] = None,
        project_id: Optional[str] = None,
        version: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 300  # 5 minutes
    ):
        super().__init__(port)
        self.platform = platform
        self.namespace = namespace
        self.deployment_name = "commandlab-daemon"
        self.service_name = "commandlab-daemon-svc"
        self.version = version or get_container_version()
        self.max_retries = max_retries
        self.timeout = timeout
        self._status = "not_started"
        
        # Validate required parameters based on platform
        if platform != KubernetesPlatform.LOCAL:
            if not cluster_name:
                raise ValueError(f"cluster_name is required for {platform}")
            if platform in [KubernetesPlatform.AWS_EKS, KubernetesPlatform.GCP_GKE] and not region:
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
                config.load_kube_config(context=f"gke_{project_id}_{region}_{cluster_name}")
            
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            logger.info("Kubernetes client configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Kubernetes client: {e}")
            raise

    def setup(self) -> None:
        """Create Kubernetes deployment and service"""
        self._status = "starting"
        self.resources_created = False
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                logger.info(f"Creating Kubernetes deployment {self.deployment_name} in namespace {self.namespace}")
                
                # Create deployment
                deployment = client.V1Deployment(
                    metadata=client.V1ObjectMeta(name=self.deployment_name),
                    spec=client.V1DeploymentSpec(
                        replicas=1,
                        selector=client.V1LabelSelector(
                            match_labels={"app": "commandlab-daemon"}
                        ),
                        template=client.V1PodTemplateSpec(
                            metadata=client.V1ObjectMeta(
                                labels={"app": "commandlab-daemon"}
                            ),
                            spec=client.V1PodSpec(
                                containers=[
                                    client.V1Container(
                                        name="commandlab-daemon",
                                        image=f"commandlab-daemon:{self.version}",
                                        ports=[client.V1ContainerPort(container_port=self.port)],
                                        args=["--port", str(self.port), "--backend", "pynput"]
                                    )
                                ]
                            )
                        )
                    )
                )
                
                # Create service
                service = client.V1Service(
                    metadata=client.V1ObjectMeta(name=self.service_name),
                    spec=client.V1ServiceSpec(
                        selector={"app": "commandlab-daemon"},
                        ports=[client.V1ServicePort(port=self.port)],
                        type="LoadBalancer"  # Use LoadBalancer for cloud platforms
                    )
                )

                # Create deployment
                logger.info(f"Creating deployment {self.deployment_name}")
                self.apps_v1.create_namespaced_deployment(
                    namespace=self.namespace,
                    body=deployment
                )
                
                # Create service
                logger.info(f"Creating service {self.service_name}")
                self.core_v1.create_namespaced_service(
                    namespace=self.namespace,
                    body=service
                )
                
                self.resources_created = True
                
                # Wait for deployment to be available
                logger.info(f"Waiting for deployment {self.deployment_name} to be available")
                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    if self.is_running():
                        self._status = "running"
                        logger.info(f"Deployment {self.deployment_name} is now available")
                        return
                    time.sleep(5)
                
                # If we get here, the deployment didn't become available in time
                self._status = "error"
                logger.error(f"Timeout waiting for deployment {self.deployment_name} to be available")
                raise TimeoutError(f"Timeout waiting for deployment {self.deployment_name} to be available")
                
            except Exception as e:
                retry_count += 1
                if retry_count >= self.max_retries:
                    self._status = "error"
                    logger.error(f"Failed to create Kubernetes resources after {self.max_retries} attempts: {e}")
                    # Attempt cleanup if partial creation occurred
                    if self.resources_created:
                        logger.info("Attempting to clean up partially created resources")
                        self.teardown()
                    raise
                logger.warning(f"Error creating Kubernetes resources, retrying ({retry_count}/{self.max_retries}): {e}")
                time.sleep(2 ** retry_count)  # Exponential backoff

    def teardown(self) -> None:
        self._status = "stopping"
        
        try:
            # Delete deployment
            logger.info(f"Deleting deployment {self.deployment_name}")
            try:
                self.apps_v1.delete_namespaced_deployment(
                    name=self.deployment_name,
                    namespace=self.namespace
                )
                logger.info(f"Deployment {self.deployment_name} deleted successfully")
            except Exception as e:
                logger.error(f"Error deleting deployment {self.deployment_name}: {e}")
            
            # Delete service
            logger.info(f"Deleting service {self.service_name}")
            try:
                self.core_v1.delete_namespaced_service(
                    name=self.service_name,
                    namespace=self.namespace
                )
                logger.info(f"Service {self.service_name} deleted successfully")
            except Exception as e:
                logger.error(f"Error deleting service {self.service_name}: {e}")
            
            # Wait for resources to be deleted
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                deployment_exists = True
                service_exists = True
                
                try:
                    self.apps_v1.read_namespaced_deployment(
                        name=self.deployment_name,
                        namespace=self.namespace
                    )
                except client.exceptions.ApiException as e:
                    if e.status == 404:
                        deployment_exists = False
                
                try:
                    self.core_v1.read_namespaced_service(
                        name=self.service_name,
                        namespace=self.namespace
                    )
                except client.exceptions.ApiException as e:
                    if e.status == 404:
                        service_exists = False
                
                if not deployment_exists and not service_exists:
                    logger.info("All Kubernetes resources deleted successfully")
                    break
                
                logger.debug(f"Waiting for resources to be deleted: deployment={deployment_exists}, service={service_exists}")
                time.sleep(5)
            
            self._status = "stopped"
        except Exception as e:
            self._status = "error"
            logger.error(f"Error during teardown: {e}")

    def is_running(self) -> bool:
        try:
            deployment = self.apps_v1.read_namespaced_deployment_status(
                name=self.deployment_name,
                namespace=self.namespace
            )
            is_running = (
                deployment.status.available_replicas is not None
                and deployment.status.available_replicas > 0
            )
            logger.debug(f"Deployment {self.deployment_name} running status: {is_running}")
            return is_running
        except Exception as e:
            logger.error(f"Error checking deployment status: {e}")
            return False
            
    def get_status(self) -> str:
        """Get the current status of the provisioner."""
        return self._status 