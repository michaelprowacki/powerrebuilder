"""Docker Builder - Containerize pipeline and generated applications.

This module handles Docker containerization for the PowerRebuilder pipeline,
including multi-stage builds, optimization, and orchestration.
"""

import logging
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ContainerType(str, Enum):
    """Types of containers."""

    PIPELINE = "pipeline"
    WEB_APP = "web_app"
    API = "api"
    DATABASE = "database"
    WORKER = "worker"
    FULL_STACK = "full_stack"


class BaseImage(str, Enum):
    """Base Docker images."""

    PYTHON_SLIM = "python:3.11-slim"
    PYTHON_ALPINE = "python:3.11-alpine"
    NODE_ALPINE = "node:20-alpine"
    NODE_SLIM = "node:20-slim"
    NGINX = "nginx:alpine"
    POSTGRES = "postgres:15-alpine"
    REDIS = "redis:7-alpine"
    UBUNTU = "ubuntu:22.04"


@dataclass
class DockerConfig:
    """Docker configuration."""

    name: str
    base_image: str
    container_type: ContainerType
    ports: List[int] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    volumes: List[str] = field(default_factory=list)
    build_args: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    healthcheck: Optional[Dict[str, Any]] = None
    multi_stage: bool = False
    optimize_size: bool = True


@dataclass
class ComposeService:
    """Docker Compose service definition."""

    name: str
    image: str
    build: Optional[Dict[str, str]] = None
    ports: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    volumes: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    networks: List[str] = field(default_factory=list)
    restart: str = "unless-stopped"
    healthcheck: Optional[Dict[str, Any]] = None


class DockerBuilder:
    """Build Docker containers for PowerRebuilder."""

    def __init__(self):
        """Initialize Docker builder."""
        self.dockerfiles: Dict[str, str] = {}
        self.compose_services: Dict[str, ComposeService] = {}

    def create_pipeline_container(
        self,
        output_dir: Path,
        stages: Optional[List[str]] = None,
    ) -> DockerConfig:
        """Create container for pipeline execution.

        Args:
            output_dir: Output directory
            stages: Pipeline stages to include

        Returns:
            Docker configuration
        """
        if not stages:
            stages = ["extract", "decompile", "parse", "model", "generate"]

        config = DockerConfig(
            name="powerrebuilder-pipeline",
            base_image=BaseImage.PYTHON_SLIM,
            container_type=ContainerType.PIPELINE,
            ports=[8080],
            environment={
                "PYTHONPATH": "/app",
                "PIPELINE_STAGES": ",".join(stages),
            },
            volumes=[
                "/input:/input",
                "/output:/output",
            ],
            multi_stage=True,
            optimize_size=True,
        )

        # Generate Dockerfile
        dockerfile = self._generate_pipeline_dockerfile(config, stages)
        self._write_dockerfile(output_dir, "Dockerfile.pipeline", dockerfile)

        # Generate entrypoint script
        entrypoint = self._generate_pipeline_entrypoint(stages)
        self._write_file(output_dir, "entrypoint.sh", entrypoint)

        return config

    def _generate_pipeline_dockerfile(
        self,
        config: DockerConfig,
        stages: List[str],
    ) -> str:
        """Generate Dockerfile for pipeline.

        Args:
            config: Docker configuration
            stages: Pipeline stages

        Returns:
            Dockerfile content
        """
        dockerfile = f"""# Multi-stage build for PowerRebuilder pipeline
# Stage 1: Builder
FROM {config.base_image} AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM {config.base_image}

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \\
    libgomp1 \\
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src_new/ /app/

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set environment variables
ENV PYTHONPATH=/app
ENV PIPELINE_STAGES="{",".join(stages)}"

# Create directories
RUN mkdir -p /input /output /tmp/cache

# Labels
LABEL maintainer="PowerRebuilder"
LABEL version="1.0.0"
LABEL description="PowerRebuilder pipeline container"

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD python -c "import sys; sys.exit(0)"

# Ports
EXPOSE 8080

# Volume mount points
VOLUME ["/input", "/output"]

# Entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["pipeline", "run"]"""

        return dockerfile

    def _generate_pipeline_entrypoint(self, stages: List[str]) -> str:
        """Generate entrypoint script for pipeline.

        Args:
            stages: Pipeline stages

        Returns:
            Entrypoint script
        """
        return """#!/bin/bash
set -e

# Function to handle shutdown
cleanup() {
    echo "Shutting down pipeline..."
    exit 0
}

trap cleanup SIGTERM SIGINT

# Parse command
COMMAND=$1
shift

case "$COMMAND" in
    pipeline)
        echo "Running PowerRebuilder pipeline..."
        python -m cli all /input /output --stages $PIPELINE_STAGES "$@"
        ;;

    webui)
        echo "Starting Web UI..."
        python -m webui.app
        ;;

    worker)
        echo "Starting worker..."
        python -m worker --queue "$@"
        ;;

    test)
        echo "Running tests..."
        pytest /app/tests
        ;;

    shell)
        echo "Starting shell..."
        /bin/bash
        ;;

    *)
        echo "Unknown command: $COMMAND"
        echo "Available commands: pipeline, webui, worker, test, shell"
        exit 1
        ;;
esac

# Keep container running if needed
if [ "$KEEP_RUNNING" = "true" ]; then
    tail -f /dev/null
fi"""

    def create_app_container(
        self,
        app_type: str,
        app_path: Path,
        output_dir: Path,
        framework: Optional[str] = None,
    ) -> DockerConfig:
        """Create container for generated application.

        Args:
            app_type: Type of application (web, api, etc.)
            app_path: Path to application code
            output_dir: Output directory
            framework: Framework used

        Returns:
            Docker configuration
        """
        # Determine base image and ports based on app type
        if app_type == "web":
            if framework in ["react", "vue", "svelte"]:
                base_image = BaseImage.NODE_ALPINE
                ports = [3000]
            else:
                base_image = BaseImage.NGINX
                ports = [80]
        elif app_type == "api":
            if framework == "python":
                base_image = BaseImage.PYTHON_SLIM
                ports = [8000]
            else:
                base_image = BaseImage.NODE_SLIM
                ports = [3000]
        else:
            base_image = BaseImage.UBUNTU
            ports = [8080]

        config = DockerConfig(
            name=f"powerrebuilder-{app_type}",
            base_image=base_image,
            container_type=ContainerType.WEB_APP
            if app_type == "web"
            else ContainerType.API,
            ports=ports,
            environment={
                "NODE_ENV": "production" if "node" in base_image else "",
                "PORT": str(ports[0]),
            },
            multi_stage=True,
            optimize_size=True,
        )

        # Generate appropriate Dockerfile
        if framework in ["react", "vue", "svelte", "next"]:
            dockerfile = self._generate_node_app_dockerfile(config, framework)
        elif framework == "flutter":
            dockerfile = self._generate_flutter_dockerfile(config)
        elif framework == "python":
            dockerfile = self._generate_python_app_dockerfile(config)
        else:
            dockerfile = self._generate_generic_dockerfile(config)

        self._write_dockerfile(output_dir, f"Dockerfile.{app_type}", dockerfile)

        return config

    def _generate_node_app_dockerfile(
        self,
        config: DockerConfig,
        framework: str,
    ) -> str:
        """Generate Dockerfile for Node.js application.

        Args:
            config: Docker configuration
            framework: Framework name

        Returns:
            Dockerfile content
        """
        return f"""# Multi-stage build for {framework} application
# Stage 1: Builder
FROM {config.base_image} AS builder

WORKDIR /build

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Build application
RUN npm run build

# Stage 2: Runtime
FROM {config.base_image}

WORKDIR /app

# Install production dependencies
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Copy built application
COPY --from=builder /build/dist ./dist
COPY --from=builder /build/public ./public

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \\
    adduser -S nodejs -u 1001

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE {config.ports[0] if config.ports else 3000}

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD node -e "require('http').get('http://localhost:{config.ports[0] if config.ports else 3000}/health', (r) => {{process.exit(r.statusCode === 200 ? 0 : 1)}})"

# Start application
CMD ["node", "dist/index.js"]"""

    def _generate_python_app_dockerfile(self, config: DockerConfig) -> str:
        """Generate Dockerfile for Python application.

        Args:
            config: Docker configuration

        Returns:
            Dockerfile content
        """
        return f"""# Multi-stage build for Python application
FROM {config.base_image}

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT={config.ports[0] if config.ports else 8000}

# Expose port
EXPOSE $PORT

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:$PORT/health || exit 1

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]"""

    def _generate_flutter_dockerfile(self, config: DockerConfig) -> str:
        """Generate Dockerfile for Flutter web application.

        Args:
            config: Docker configuration

        Returns:
            Dockerfile content
        """
        return """# Flutter web application
FROM ubuntu:22.04 AS builder

# Install dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    git \\
    unzip \\
    xz-utils \\
    zip \\
    && rm -rf /var/lib/apt/lists/*

# Install Flutter
RUN git clone https://github.com/flutter/flutter.git /flutter
ENV PATH="/flutter/bin:$PATH"
RUN flutter channel stable && flutter upgrade
RUN flutter config --enable-web

WORKDIR /app

# Copy and build
COPY . .
RUN flutter pub get
RUN flutter build web --release

# Stage 2: Serve with nginx
FROM nginx:alpine

COPY --from=builder /app/build/web /usr/share/nginx/html

# Nginx configuration
RUN echo 'server { \\
    listen 80; \\
    location / { \\
        root /usr/share/nginx/html; \\
        try_files $uri $uri/ /index.html; \\
    } \\
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]"""

    def _generate_generic_dockerfile(self, config: DockerConfig) -> str:
        """Generate generic Dockerfile.

        Args:
            config: Docker configuration

        Returns:
            Dockerfile content
        """
        return f"""# Generic application container
FROM {config.base_image}

WORKDIR /app

# Copy application
COPY . .

# Expose port
EXPOSE {config.ports[0] if config.ports else 8080}

# Start application
CMD ["/bin/sh"]"""

    def create_compose_file(
        self,
        services: List[DockerConfig],
        output_dir: Path,
    ) -> None:
        """Create Docker Compose file for multiple services.

        Args:
            services: List of service configurations
            output_dir: Output directory
        """
        compose = {
            "version": "3.9",
            "services": {},
            "networks": {
                "powerrebuilder": {
                    "driver": "bridge",
                },
            },
            "volumes": {},
        }

        for config in services:
            service = {
                "image": f"{config.name}:latest",
                "build": {
                    "context": ".",
                    "dockerfile": f"Dockerfile.{config.container_type.value}",
                },
                "ports": [f"{p}:{p}" for p in config.ports],
                "environment": config.environment,
                "volumes": config.volumes,
                "networks": ["powerrebuilder"],
                "restart": "unless-stopped",
            }

            if config.healthcheck:
                service["healthcheck"] = config.healthcheck

            compose["services"][config.name] = service

        # Add standard services
        compose["services"].update(self._get_standard_services())

        # Write compose file
        compose_path = output_dir / "docker-compose.yml"
        with compose_path.open("w") as f:
            import yaml

            yaml.dump(compose, f, default_flow_style=False)

        logger.info("Created Docker Compose file: %s", compose_path)

    def _get_standard_services(self) -> Dict[str, Any]:
        """Get standard services for compose file.

        Returns:
            Standard services configuration
        """
        return {
            "postgres": {
                "image": "postgres:15-alpine",
                "environment": {
                    "POSTGRES_DB": "powerrebuilder",
                    "POSTGRES_USER": "powerrebuilder",
                    "POSTGRES_PASSWORD": "changeme",
                },
                "volumes": [
                    "postgres_data:/var/lib/postgresql/data",
                ],
                "networks": ["powerrebuilder"],
                "restart": "unless-stopped",
                "healthcheck": {
                    "test": ["CMD-SHELL", "pg_isready -U powerrebuilder"],
                    "interval": "10s",
                    "timeout": "5s",
                    "retries": 5,
                },
            },
            "redis": {
                "image": "redis:7-alpine",
                "volumes": [
                    "redis_data:/data",
                ],
                "networks": ["powerrebuilder"],
                "restart": "unless-stopped",
                "healthcheck": {
                    "test": ["CMD", "redis-cli", "ping"],
                    "interval": "10s",
                    "timeout": "5s",
                    "retries": 5,
                },
            },
        }

    def create_kubernetes_manifests(
        self,
        config: DockerConfig,
        output_dir: Path,
    ) -> None:
        """Create Kubernetes manifests for deployment.

        Args:
            config: Docker configuration
            output_dir: Output directory
        """
        # Deployment manifest
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": config.name,
                "labels": config.labels,
            },
            "spec": {
                "replicas": 3,
                "selector": {
                    "matchLabels": {
                        "app": config.name,
                    },
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": config.name,
                        },
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": config.name,
                                "image": f"{config.name}:latest",
                                "ports": [{"containerPort": p} for p in config.ports],
                                "env": [
                                    {"name": k, "value": v}
                                    for k, v in config.environment.items()
                                ],
                            }
                        ],
                    },
                },
            },
        }

        # Service manifest
        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": config.name,
            },
            "spec": {
                "selector": {
                    "app": config.name,
                },
                "ports": [
                    {
                        "port": p,
                        "targetPort": p,
                    }
                    for p in config.ports
                ],
                "type": "LoadBalancer",
            },
        }

        # Write manifests
        import yaml

        deployment_path = output_dir / f"{config.name}-deployment.yaml"
        with deployment_path.open("w") as f:
            yaml.dump(deployment, f, default_flow_style=False)

        service_path = output_dir / f"{config.name}-service.yaml"
        with service_path.open("w") as f:
            yaml.dump(service, f, default_flow_style=False)

        logger.info("Created Kubernetes manifests in %s", output_dir)

    def optimize_dockerfile(self, dockerfile: str) -> str:
        """Optimize Dockerfile for size and security.

        Args:
            dockerfile: Original Dockerfile content

        Returns:
            Optimized Dockerfile
        """
        optimizations = []

        # Add --no-cache-dir to pip installs
        dockerfile = dockerfile.replace("pip install", "pip install --no-cache-dir")

        # Combine RUN commands
        lines = dockerfile.split("\n")
        new_lines = []
        run_commands = []

        for line in lines:
            if line.strip().startswith("RUN "):
                run_commands.append(line.replace("RUN ", "").strip())
            else:
                if run_commands:
                    # Combine RUN commands
                    combined = "RUN " + " && \\\n    ".join(run_commands)
                    new_lines.append(combined)
                    run_commands = []
                new_lines.append(line)

        if run_commands:
            combined = "RUN " + " && \\\n    ".join(run_commands)
            new_lines.append(combined)

        optimized = "\n".join(new_lines)

        return optimized

    def build_image(
        self,
        dockerfile_path: Path,
        image_name: str,
        build_args: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Build Docker image.

        Args:
            dockerfile_path: Path to Dockerfile
            image_name: Image name and tag
            build_args: Build arguments

        Returns:
            True if build successful
        """
        cmd = ["docker", "build", "-t", image_name, "-f", str(dockerfile_path)]

        if build_args:
            for key, value in build_args.items():
                cmd.extend(["--build-arg", f"{key}={value}"])

        cmd.append(str(dockerfile_path.parent))

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Successfully built image: %s", image_name)
                return True
            else:
                logger.error("Failed to build image: %s", result.stderr)
                return False
        except Exception as e:
            logger.error("Error building image: %s", e)
            return False

    def _write_dockerfile(
        self,
        output_dir: Path,
        filename: str,
        content: str,
    ) -> None:
        """Write Dockerfile to disk.

        Args:
            output_dir: Output directory
            filename: Dockerfile name
            content: Dockerfile content
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        dockerfile_path = output_dir / filename

        # Optimize before writing
        optimized = self.optimize_dockerfile(content)

        with dockerfile_path.open("w") as f:
            f.write(optimized)

        logger.info("Created Dockerfile: %s", dockerfile_path)

    def _write_file(
        self,
        output_dir: Path,
        filename: str,
        content: str,
    ) -> None:
        """Write file to disk.

        Args:
            output_dir: Output directory
            filename: File name
            content: File content
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / filename

        with file_path.open("w") as f:
            f.write(content)

        # Make executable if shell script
        if filename.endswith(".sh"):
            file_path.chmod(0o755)

        logger.info("Created file: %s", file_path)
