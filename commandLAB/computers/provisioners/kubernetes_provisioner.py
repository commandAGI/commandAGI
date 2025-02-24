from enum import Enum
from kubernetes import client, config
from typing import Optional
from .base_provisioner import BaseComputerProvisioner
from commandLAB.version import get_container_version


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
        version: Optional[str] = None
    ):
        super().__init__(port)
        self.platform = platform
        self.namespace = namespace
        self.deployment_name = "commandlab-daemon"
        self.service_name = "commandlab-daemon-svc"
        self.version = version or get_container_version()
        
        # Configure kubernetes client based on platform
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

    def setup(self) -> None:
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

        self.apps_v1.create_namespaced_deployment(
            namespace=self.namespace,
            body=deployment
        )
        self.core_v1.create_namespaced_service(
            namespace=self.namespace,
            body=service
        )

    def teardown(self) -> None:
        self.apps_v1.delete_namespaced_deployment(
            name=self.deployment_name,
            namespace=self.namespace
        )
        self.core_v1.delete_namespaced_service(
            name=self.service_name,
            namespace=self.namespace
        )

    def is_running(self) -> bool:
        try:
            deployment = self.apps_v1.read_namespaced_deployment_status(
                name=self.deployment_name,
                namespace=self.namespace
            )
            return (
                deployment.status.available_replicas is not None
                and deployment.status.available_replicas > 0
            )
        except Exception:
            return False 