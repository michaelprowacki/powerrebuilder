"""Web UI Dashboard - Browser-based pipeline management interface.

This module provides a modern web dashboard for PowerRebuilder with real-time
monitoring, pipeline control, and visual analytics.
"""

import asyncio
import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

try:
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse, HTMLResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    FastAPI = None
    BaseModel = object

from src_new._patterns.observability import get_metrics
from src_new.analyze.complexity import ComplexityAnalyzer
from src_new.analyze.database import SchemaExtractor

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================


class PipelineRequest(BaseModel):
    """Pipeline execution request."""

    input_path: str
    output_path: str
    stages: List[str] = ["all"]
    options: Dict[str, Any] = {}


class PipelineStatus(BaseModel):
    """Pipeline execution status."""

    id: str
    status: str  # pending, running, completed, failed
    stage: Optional[str] = None
    progress: float = 0.0
    message: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metrics: Dict[str, Any] = {}


class ProjectInfo(BaseModel):
    """Project information."""

    name: str
    path: str
    last_modified: datetime
    size_bytes: int
    file_count: int
    stages_completed: List[str] = []


# ============================================================================
# WEB UI APPLICATION
# ============================================================================


class WebUIApp:
    """Web UI Dashboard application."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        pipeline_executor: Optional[Any] = None,
    ):
        """Initialize Web UI application.

        Args:
            host: Host to bind to
            port: Port to listen on
            pipeline_executor: Pipeline executor instance
        """
        if not FASTAPI_AVAILABLE:
            raise ImportError(
                "FastAPI is required for Web UI. Install with: pip install fastapi uvicorn"
            )

        self.host = host
        self.port = port
        self.pipeline_executor = pipeline_executor
        self.app = FastAPI(title="PowerRebuilder Dashboard", version="1.0.0")
        self.active_pipelines: Dict[str, PipelineStatus] = {}
        self.projects: Dict[str, ProjectInfo] = {}
        self.websocket_clients: List[WebSocket] = []

        # Setup routes and middleware
        self._setup_middleware()
        self._setup_routes()
        self._setup_websocket()

    def _setup_middleware(self):
        """Setup FastAPI middleware."""
        # CORS middleware for frontend
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        """Setup API routes."""

        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            """Serve dashboard HTML."""
            return self._get_dashboard_html()

        @self.app.get("/api/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": datetime.now()}

        @self.app.get("/api/projects")
        async def get_projects():
            """Get all projects."""
            return list(self.projects.values())

        @self.app.post("/api/projects")
        async def create_project(name: str, path: str):
            """Create new project."""
            project_id = str(uuid4())
            project = ProjectInfo(
                name=name,
                path=path,
                last_modified=datetime.now(),
                size_bytes=0,
                file_count=0,
            )
            self.projects[project_id] = project
            return {"id": project_id, "project": project}

        @self.app.post("/api/pipeline/start")
        async def start_pipeline(request: PipelineRequest):
            """Start pipeline execution."""
            pipeline_id = str(uuid4())
            status = PipelineStatus(
                id=pipeline_id,
                status="pending",
                started_at=datetime.now(),
            )
            self.active_pipelines[pipeline_id] = status

            # Start pipeline execution in background
            asyncio.create_task(self._execute_pipeline(pipeline_id, request))

            return status

        @self.app.get("/api/pipeline/status/{pipeline_id}")
        async def get_pipeline_status(pipeline_id: str):
            """Get pipeline execution status."""
            if pipeline_id not in self.active_pipelines:
                raise HTTPException(status_code=404, detail="Pipeline not found")
            return self.active_pipelines[pipeline_id]

        @self.app.post("/api/pipeline/cancel/{pipeline_id}")
        async def cancel_pipeline(pipeline_id: str):
            """Cancel pipeline execution."""
            if pipeline_id not in self.active_pipelines:
                raise HTTPException(status_code=404, detail="Pipeline not found")

            status = self.active_pipelines[pipeline_id]
            status.status = "cancelled"
            status.completed_at = datetime.now()
            return status

        @self.app.get("/api/metrics")
        async def get_metrics_data():
            """Get current metrics."""
            metrics = get_metrics()
            return metrics.get_summary()

        @self.app.post("/api/analyze/complexity")
        async def analyze_complexity(file_path: str):
            """Analyze code complexity."""
            analyzer = ComplexityAnalyzer()
            path = Path(file_path)

            if not path.exists():
                raise HTTPException(status_code=404, detail="File not found")

            metrics = analyzer.analyze_file(path)
            return asdict(metrics)

        @self.app.post("/api/analyze/schema")
        async def extract_schema(directory: str):
            """Extract database schema."""
            extractor = SchemaExtractor()
            path = Path(directory)

            if not path.exists():
                raise HTTPException(status_code=404, detail="Directory not found")

            schema = extractor.extract_from_directory(path)
            return {
                "name": schema.name,
                "tables": len(schema.tables),
                "procedures": len(schema.stored_procedures),
                "statements": len(schema.sql_statements),
            }

    def _setup_websocket(self):
        """Setup WebSocket for real-time updates."""

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.websocket_clients.append(websocket)

            try:
                while True:
                    # Keep connection alive and handle messages
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    if message.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    elif message.get("type") == "subscribe":
                        # Subscribe to pipeline updates
                        pipeline_id = message.get("pipeline_id")
                        if pipeline_id in self.active_pipelines:
                            await websocket.send_json(
                                {
                                    "type": "status",
                                    "data": asdict(self.active_pipelines[pipeline_id]),
                                }
                            )
            except WebSocketDisconnect:
                self.websocket_clients.remove(websocket)

    async def _execute_pipeline(self, pipeline_id: str, request: PipelineRequest):
        """Execute pipeline in background.

        Args:
            pipeline_id: Pipeline ID
            request: Pipeline request
        """
        status = self.active_pipelines[pipeline_id]
        status.status = "running"

        try:
            # Broadcast status update
            await self._broadcast_status(pipeline_id)

            # Execute each stage
            stages = (
                request.stages
                if request.stages != ["all"]
                else ["extract", "decompile", "parse", "model", "generate"]
            )

            for i, stage in enumerate(stages):
                status.stage = stage
                status.progress = (i / len(stages)) * 100
                status.message = f"Running {stage} stage..."

                await self._broadcast_status(pipeline_id)

                # Simulate stage execution (replace with actual executor)
                await asyncio.sleep(2)

                # Update metrics
                status.metrics[stage] = {
                    "files_processed": 10,
                    "duration_seconds": 2.0,
                    "success_rate": 1.0,
                }

            status.status = "completed"
            status.progress = 100
            status.message = "Pipeline completed successfully"
            status.completed_at = datetime.now()

        except Exception as e:
            status.status = "failed"
            status.message = str(e)
            status.completed_at = datetime.now()
            logger.error("Pipeline execution failed: %s", e)

        await self._broadcast_status(pipeline_id)

    async def _broadcast_status(self, pipeline_id: str):
        """Broadcast pipeline status to WebSocket clients.

        Args:
            pipeline_id: Pipeline ID
        """
        if pipeline_id not in self.active_pipelines:
            return

        status = self.active_pipelines[pipeline_id]
        message = {"type": "pipeline_update", "data": asdict(status)}

        # Broadcast to all connected clients
        for client in self.websocket_clients[:]:
            try:
                await client.send_json(message)
            except:
                self.websocket_clients.remove(client)

    def _get_dashboard_html(self) -> str:
        """Get dashboard HTML."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PowerRebuilder Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div id="app" class="min-h-screen bg-gray-100">
        <!-- Header -->
        <header class="bg-white shadow">
            <div class="mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between h-16">
                    <div class="flex items-center">
                        <h1 class="text-2xl font-bold text-gray-900">
                            PowerRebuilder Dashboard
                        </h1>
                    </div>
                    <div class="flex items-center space-x-4">
                        <span class="text-sm text-gray-500">
                            Status: <span class="text-green-600">● Connected</span>
                        </span>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <!-- Stats Cards -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <div class="bg-white overflow-hidden shadow rounded-lg">
                    <div class="px-4 py-5 sm:p-6">
                        <dt class="text-sm font-medium text-gray-500 truncate">
                            Active Pipelines
                        </dt>
                        <dd class="mt-1 text-3xl font-semibold text-gray-900">
                            {{ activePipelines }}
                        </dd>
                    </div>
                </div>
                <div class="bg-white overflow-hidden shadow rounded-lg">
                    <div class="px-4 py-5 sm:p-6">
                        <dt class="text-sm font-medium text-gray-500 truncate">
                            Files Processed
                        </dt>
                        <dd class="mt-1 text-3xl font-semibold text-gray-900">
                            {{ filesProcessed }}
                        </dd>
                    </div>
                </div>
                <div class="bg-white overflow-hidden shadow rounded-lg">
                    <div class="px-4 py-5 sm:p-6">
                        <dt class="text-sm font-medium text-gray-500 truncate">
                            Success Rate
                        </dt>
                        <dd class="mt-1 text-3xl font-semibold text-gray-900">
                            {{ successRate }}%
                        </dd>
                    </div>
                </div>
                <div class="bg-white overflow-hidden shadow rounded-lg">
                    <div class="px-4 py-5 sm:p-6">
                        <dt class="text-sm font-medium text-gray-500 truncate">
                            Avg Duration
                        </dt>
                        <dd class="mt-1 text-3xl font-semibold text-gray-900">
                            {{ avgDuration }}s
                        </dd>
                    </div>
                </div>
            </div>

            <!-- Pipeline Control -->
            <div class="bg-white shadow sm:rounded-lg mb-8">
                <div class="px-4 py-5 sm:p-6">
                    <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">
                        Start New Pipeline
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">
                                Input Path
                            </label>
                            <input v-model="inputPath" type="text"
                                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">
                                Output Path
                            </label>
                            <input v-model="outputPath" type="text"
                                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm">
                        </div>
                        <div class="flex items-end">
                            <button @click="startPipeline"
                                class="w-full bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700">
                                Start Pipeline
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Active Pipelines -->
            <div class="bg-white shadow sm:rounded-lg">
                <div class="px-4 py-5 sm:p-6">
                    <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">
                        Active Pipelines
                    </h3>
                    <div v-if="pipelines.length === 0" class="text-gray-500">
                        No active pipelines
                    </div>
                    <div v-else class="space-y-4">
                        <div v-for="pipeline in pipelines" :key="pipeline.id"
                            class="border rounded-lg p-4">
                            <div class="flex justify-between items-center mb-2">
                                <span class="font-medium">{{ pipeline.id.slice(0, 8) }}</span>
                                <span :class="getStatusClass(pipeline.status)">
                                    {{ pipeline.status }}
                                </span>
                            </div>
                            <div class="text-sm text-gray-600 mb-2">
                                Stage: {{ pipeline.stage || 'N/A' }}
                            </div>
                            <div class="w-full bg-gray-200 rounded-full h-2">
                                <div class="bg-indigo-600 h-2 rounded-full"
                                    :style="{width: pipeline.progress + '%'}">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        const { createApp } = Vue;

        createApp({
            data() {
                return {
                    ws: null,
                    pipelines: [],
                    activePipelines: 0,
                    filesProcessed: 0,
                    successRate: 100,
                    avgDuration: 0,
                    inputPath: '/input',
                    outputPath: '/output'
                }
            },
            mounted() {
                this.connectWebSocket();
                this.loadStats();
            },
            methods: {
                connectWebSocket() {
                    this.ws = new WebSocket('ws://localhost:8080/ws');

                    this.ws.onmessage = (event) => {
                        const message = JSON.parse(event.data);

                        if (message.type === 'pipeline_update') {
                            this.updatePipeline(message.data);
                        }
                    };

                    this.ws.onopen = () => {
                        console.log('WebSocket connected');
                        setInterval(() => {
                            this.ws.send(JSON.stringify({type: 'ping'}));
                        }, 30000);
                    };
                },

                async startPipeline() {
                    const response = await fetch('/api/pipeline/start', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            input_path: this.inputPath,
                            output_path: this.outputPath,
                            stages: ['all']
                        })
                    });

                    const pipeline = await response.json();
                    this.pipelines.push(pipeline);
                    this.updateStats();
                },

                updatePipeline(data) {
                    const index = this.pipelines.findIndex(p => p.id === data.id);
                    if (index >= 0) {
                        this.pipelines[index] = data;
                    } else {
                        this.pipelines.push(data);
                    }
                    this.updateStats();
                },

                updateStats() {
                    this.activePipelines = this.pipelines.filter(
                        p => p.status === 'running'
                    ).length;

                    const completed = this.pipelines.filter(
                        p => p.status === 'completed'
                    );

                    if (completed.length > 0) {
                        this.filesProcessed = completed.reduce(
                            (sum, p) => sum + (p.metrics.files_processed || 0), 0
                        );
                    }
                },

                async loadStats() {
                    try {
                        const response = await fetch('/api/metrics');
                        const metrics = await response.json();
                        // Update stats from metrics
                    } catch (error) {
                        console.error('Failed to load stats:', error);
                    }
                },

                getStatusClass(status) {
                    const classes = {
                        'pending': 'text-yellow-600',
                        'running': 'text-blue-600',
                        'completed': 'text-green-600',
                        'failed': 'text-red-600',
                        'cancelled': 'text-gray-600'
                    };
                    return classes[status] || 'text-gray-600';
                }
            }
        }).mount('#app');
    </script>
</body>
</html>"""

    def run(self):
        """Run the Web UI application."""
        import uvicorn

        logger.info("Starting Web UI Dashboard on http://%s:%d", self.host, self.port)
        uvicorn.run(self.app, host=self.host, port=self.port)


# ============================================================================
# CLI INTEGRATION
# ============================================================================


def start_webui(host: str = "0.0.0.0", port: int = 8080):
    """Start the Web UI dashboard.

    Args:
        host: Host to bind to
        port: Port to listen on
    """
    app = WebUIApp(host=host, port=port)
    app.run()


if __name__ == "__main__":
    # Run standalone for testing
    start_webui()
