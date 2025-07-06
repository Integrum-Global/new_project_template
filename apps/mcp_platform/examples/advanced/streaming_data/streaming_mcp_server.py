"""Advanced MCP server with streaming data capabilities using Kailash SDK.

This example demonstrates how to build an MCP server that can handle streaming
data, real-time processing, and progressive result delivery using Kailash
workflows with advanced async patterns.

Features demonstrated:
- Streaming data ingestion via MCP
- Real-time workflow execution
- Progressive result streaming
- Backpressure handling
- Circuit breaker patterns
- Multi-modal content streaming
"""

import asyncio
import json
import logging
import time
import uuid
from asyncio import Queue
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from kailash import LocalRuntime, WorkflowBuilder
from kailash.mcp_server import MCPServer
from kailash.mcp_server.advanced_features import (
    MultiModalContent,
    create_progress_reporter,
    structured_tool,
)
from kailash.mcp_server.auth import APIKeyAuth
from kailash.nodes.ai import LLMAgentNode
from kailash.nodes.data import CSVReaderNode
from kailash.nodes.logic import MergeNode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StreamType(Enum):
    """Types of data streams supported."""

    TEXT = "text"
    JSON = "json"
    BINARY = "binary"
    MULTIMODAL = "multimodal"


class ProcessingMode(Enum):
    """Processing modes for streaming data."""

    REALTIME = "realtime"
    BATCH = "batch"
    WINDOWED = "windowed"
    CONTINUOUS = "continuous"


@dataclass
class StreamChunk:
    """Represents a chunk of streaming data."""

    chunk_id: str
    stream_id: str
    data: Union[str, bytes, Dict[str, Any]]
    chunk_index: int
    total_chunks: Optional[int]
    timestamp: float
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class StreamResult:
    """Represents a streaming processing result."""

    result_id: str
    stream_id: str
    chunk_id: str
    result_data: Dict[str, Any]
    confidence: float
    processing_time: float
    is_final: bool = False
    error: Optional[str] = None


class StreamingMCPServer:
    """Advanced MCP server with streaming capabilities."""

    def __init__(self, server_name: str = "streaming-kailash-server"):
        """Initialize the streaming MCP server."""
        # Setup authentication
        self.auth = APIKeyAuth(
            {
                "stream_admin": {"permissions": ["admin", "streaming", "realtime"]},
                "stream_user": {"permissions": ["streaming", "processing"]},
                "batch_user": {"permissions": ["batch", "processing"]},
            }
        )

        # Create MCP server with streaming capabilities
        self.server = MCPServer(
            server_name,
            auth_provider=self.auth,
            enable_metrics=True,
            rate_limit_config={
                "requests_per_minute": 1000
            },  # Higher limit for streaming
            circuit_breaker_config={"failure_threshold": 10},
        )

        # Initialize Kailash runtime with async support
        self.runtime = LocalRuntime()

        # Streaming state management
        self.active_streams: Dict[str, Dict[str, Any]] = {}
        self.stream_queues: Dict[str, Queue] = {}
        self.processing_tasks: Dict[str, asyncio.Task] = {}

        # Circuit breaker for backpressure
        self.circuit_breaker_active = False
        self.max_concurrent_streams = 50

        # Register streaming tools
        self._register_streaming_tools()

        logger.info(f"Initialized streaming MCP server: {server_name}")

    def _register_streaming_tools(self):
        """Register streaming and real-time processing tools."""

        @self.server.tool(required_permission="streaming")
        async def start_data_stream(
            stream_type: str,
            processing_mode: str = "realtime",
            buffer_size: int = 1000,
            window_size: int = 100,
        ) -> dict:
            """Start a new data stream for processing.

            Args:
                stream_type: Type of stream (text, json, binary, multimodal)
                processing_mode: Processing mode (realtime, batch, windowed, continuous)
                buffer_size: Size of the stream buffer
                window_size: Size of processing windows

            Returns:
                Stream configuration and ID
            """
            try:
                # Validate parameters
                if stream_type not in [e.value for e in StreamType]:
                    return {"error": f"Invalid stream type: {stream_type}"}

                if processing_mode not in [e.value for e in ProcessingMode]:
                    return {"error": f"Invalid processing mode: {processing_mode}"}

                # Check concurrent stream limits
                if len(self.active_streams) >= self.max_concurrent_streams:
                    return {"error": "Maximum concurrent streams reached"}

                # Create stream
                stream_id = str(uuid.uuid4())
                stream_config = {
                    "stream_id": stream_id,
                    "stream_type": stream_type,
                    "processing_mode": processing_mode,
                    "buffer_size": buffer_size,
                    "window_size": window_size,
                    "created_at": time.time(),
                    "status": "active",
                    "chunks_processed": 0,
                    "total_bytes": 0,
                }

                # Initialize stream infrastructure
                self.active_streams[stream_id] = stream_config
                self.stream_queues[stream_id] = Queue(maxsize=buffer_size)

                # Start processing task
                processing_task = asyncio.create_task(self._process_stream(stream_id))
                self.processing_tasks[stream_id] = processing_task

                logger.info(
                    f"Started stream: {stream_id} ({stream_type}, {processing_mode})"
                )

                return {
                    "stream_id": stream_id,
                    "status": "started",
                    "config": stream_config,
                }

            except Exception as e:
                logger.error(f"Failed to start stream: {e}")
                return {"error": str(e)}

        @self.server.tool(required_permission="streaming")
        async def send_stream_chunk(
            stream_id: str,
            data: Union[str, dict],
            chunk_index: int,
            total_chunks: int = None,
            metadata: dict = None,
        ) -> dict:
            """Send a chunk of data to an active stream.

            Args:
                stream_id: ID of the target stream
                data: Chunk data (string, JSON, or binary)
                chunk_index: Index of this chunk in the sequence
                total_chunks: Total number of chunks (if known)
                metadata: Additional chunk metadata

            Returns:
                Chunk processing status
            """
            try:
                # Validate stream
                if stream_id not in self.active_streams:
                    return {"error": f"Stream not found: {stream_id}"}

                stream_config = self.active_streams[stream_id]
                if stream_config["status"] != "active":
                    return {"error": f"Stream not active: {stream_id}"}

                # Create chunk
                chunk = StreamChunk(
                    chunk_id=str(uuid.uuid4()),
                    stream_id=stream_id,
                    data=data,
                    chunk_index=chunk_index,
                    total_chunks=total_chunks,
                    timestamp=time.time(),
                    metadata=metadata or {},
                )

                # Add to stream queue (with backpressure handling)
                try:
                    await asyncio.wait_for(
                        self.stream_queues[stream_id].put(chunk),
                        timeout=1.0,  # 1 second timeout
                    )
                except asyncio.TimeoutError:
                    return {"error": "Stream buffer full, try again later"}

                # Update stream stats
                stream_config["chunks_processed"] += 1
                if isinstance(data, str):
                    stream_config["total_bytes"] += len(data.encode())
                elif isinstance(data, dict):
                    stream_config["total_bytes"] += len(json.dumps(data).encode())

                return {
                    "chunk_id": chunk.chunk_id,
                    "status": "queued",
                    "queue_size": self.stream_queues[stream_id].qsize(),
                    "stream_stats": {
                        "chunks_processed": stream_config["chunks_processed"],
                        "total_bytes": stream_config["total_bytes"],
                    },
                }

            except Exception as e:
                logger.error(f"Failed to send chunk: {e}")
                return {"error": str(e)}

        @self.server.tool(required_permission="streaming")
        async def get_stream_results(
            stream_id: str, wait_for_results: bool = True, timeout: float = 30.0
        ) -> dict:
            """Get processing results from a stream.

            Args:
                stream_id: ID of the stream
                wait_for_results: Whether to wait for new results
                timeout: Maximum time to wait for results

            Returns:
                Stream processing results
            """
            try:
                if stream_id not in self.active_streams:
                    return {"error": f"Stream not found: {stream_id}"}

                # Get results from stream processing
                results = await self._get_stream_results(
                    stream_id, wait_for_results, timeout
                )

                return {
                    "stream_id": stream_id,
                    "results": results,
                    "result_count": len(results),
                }

            except Exception as e:
                logger.error(f"Failed to get stream results: {e}")
                return {"error": str(e)}

        @self.server.tool(required_permission="streaming")
        async def stop_stream(stream_id: str) -> dict:
            """Stop an active data stream.

            Args:
                stream_id: ID of the stream to stop

            Returns:
                Stream stopping status and final statistics
            """
            try:
                if stream_id not in self.active_streams:
                    return {"error": f"Stream not found: {stream_id}"}

                # Mark stream as stopping
                stream_config = self.active_streams[stream_id]
                stream_config["status"] = "stopping"
                stream_config["stopped_at"] = time.time()

                # Cancel processing task
                if stream_id in self.processing_tasks:
                    self.processing_tasks[stream_id].cancel()
                    try:
                        await self.processing_tasks[stream_id]
                    except asyncio.CancelledError:
                        pass
                    del self.processing_tasks[stream_id]

                # Clean up resources
                if stream_id in self.stream_queues:
                    del self.stream_queues[stream_id]

                # Final statistics
                final_stats = {
                    "stream_id": stream_id,
                    "status": "stopped",
                    "duration": stream_config["stopped_at"]
                    - stream_config["created_at"],
                    "chunks_processed": stream_config["chunks_processed"],
                    "total_bytes": stream_config["total_bytes"],
                    "avg_throughput": stream_config["chunks_processed"]
                    / max(stream_config["stopped_at"] - stream_config["created_at"], 1),
                }

                # Update stream config
                stream_config.update(final_stats)

                logger.info(f"Stopped stream: {stream_id}")
                return final_stats

            except Exception as e:
                logger.error(f"Failed to stop stream: {e}")
                return {"error": str(e)}

        @structured_tool(
            input_schema={
                "type": "object",
                "properties": {
                    "text_stream": {"type": "string"},
                    "analysis_type": {
                        "type": "string",
                        "enum": ["sentiment", "classification", "extraction"],
                    },
                    "window_size": {"type": "integer", "minimum": 1, "maximum": 1000},
                },
                "required": ["text_stream", "analysis_type"],
            }
        )
        @self.server.tool(required_permission="processing")
        async def process_text_stream(
            text_stream: str,
            analysis_type: str = "sentiment",
            window_size: int = 100,
            progress_token=None,
        ) -> dict:
            """Process a text stream with real-time analysis."""
            try:
                # Create progress reporter
                async with create_progress_reporter(
                    "text_stream_processing"
                ) as progress:
                    # Start stream processing
                    stream_result = await self._process_text_stream_internal(
                        text_stream, analysis_type, window_size, progress
                    )

                    return {
                        "analysis_type": analysis_type,
                        "window_size": window_size,
                        "result": stream_result,
                        "processing_mode": "streaming",
                    }

            except Exception as e:
                logger.error(f"Text stream processing failed: {e}")
                return {"error": str(e)}

        @self.server.tool(required_permission="realtime")
        async def create_multimodal_stream(
            content_types: list, processing_pipeline: str = "default"
        ) -> dict:
            """Create a multi-modal content stream."""
            try:
                stream_id = str(uuid.uuid4())

                # Create multi-modal content handler
                content_handler = MultiModalContent()

                # Setup processing pipeline
                pipeline_config = self._create_multimodal_pipeline(
                    content_types, processing_pipeline
                )

                # Initialize stream
                self.active_streams[stream_id] = {
                    "stream_id": stream_id,
                    "type": "multimodal",
                    "content_types": content_types,
                    "pipeline": pipeline_config,
                    "handler": content_handler,
                    "status": "active",
                    "created_at": time.time(),
                }

                return {
                    "stream_id": stream_id,
                    "content_types": content_types,
                    "pipeline": pipeline_config,
                    "status": "created",
                }

            except Exception as e:
                logger.error(f"Failed to create multimodal stream: {e}")
                return {"error": str(e)}

        @self.server.resource("streaming://active")
        def get_active_streams():
            """Get information about all active streams."""
            return {
                "active_count": len(self.active_streams),
                "streams": {
                    stream_id: {
                        "type": (
                            config["stream_type"]
                            if "stream_type" in config
                            else config.get("type")
                        ),
                        "status": config["status"],
                        "chunks_processed": config.get("chunks_processed", 0),
                        "uptime": time.time() - config["created_at"],
                    }
                    for stream_id, config in self.active_streams.items()
                },
                "system_status": {
                    "circuit_breaker_active": self.circuit_breaker_active,
                    "max_concurrent_streams": self.max_concurrent_streams,
                },
            }

    async def _process_stream(self, stream_id: str):
        """Process chunks from a stream."""
        try:
            stream_config = self.active_streams[stream_id]
            queue = self.stream_queues[stream_id]

            # Create processing workflow based on stream type
            workflow = self._create_stream_workflow(stream_config)

            while stream_config["status"] == "active":
                try:
                    # Get chunk from queue with timeout
                    chunk = await asyncio.wait_for(queue.get(), timeout=1.0)

                    # Process chunk with Kailash workflow
                    result = await self._process_chunk_with_workflow(
                        chunk, workflow, stream_config
                    )

                    # Store result (in production, you'd use a proper storage system)
                    if not hasattr(self, "stream_results"):
                        self.stream_results = {}
                    if stream_id not in self.stream_results:
                        self.stream_results[stream_id] = []

                    self.stream_results[stream_id].append(result)

                    # Mark task done
                    queue.task_done()

                except asyncio.TimeoutError:
                    # No new chunks, continue waiting
                    continue
                except Exception as e:
                    logger.error(f"Stream processing error: {e}")

        except asyncio.CancelledError:
            logger.info(f"Stream processing cancelled: {stream_id}")
        except Exception as e:
            logger.error(f"Stream processing failed: {e}")

    def _create_stream_workflow(self, stream_config: Dict[str, Any]) -> WorkflowBuilder:
        """Create a Kailash workflow for stream processing."""
        workflow = WorkflowBuilder()

        stream_type = stream_config.get("stream_type", "text")
        processing_mode = stream_config.get("processing_mode", "realtime")

        if stream_type == "text":
            # Text processing workflow
            workflow.add_node(
                "LLMAgentNode",
                node_id="text_processor",
                prompt_template="Analyze this text chunk: {text}",
                model_name="gpt-3.5-turbo",
                temperature=0.1,
            )
        elif stream_type == "json":
            # JSON processing workflow
            workflow.add_node(
                "CSVReaderNode", node_id="json_processor"  # Can handle structured data
            )

        # Add merge node for result aggregation
        if processing_mode == "windowed":
            workflow.add_node("MergeNode", node_id="window_merger")

        return workflow

    async def _process_chunk_with_workflow(
        self,
        chunk: StreamChunk,
        workflow: WorkflowBuilder,
        stream_config: Dict[str, Any],
    ) -> StreamResult:
        """Process a single chunk using Kailash workflow."""
        start_time = time.time()

        try:
            # Prepare inputs based on stream type
            inputs = self._prepare_chunk_inputs(chunk, stream_config)

            # Execute workflow
            result = self.runtime.execute(workflow, inputs)

            processing_time = time.time() - start_time

            return StreamResult(
                result_id=str(uuid.uuid4()),
                stream_id=chunk.stream_id,
                chunk_id=chunk.chunk_id,
                result_data=result,
                confidence=0.85,
                processing_time=processing_time,
            )

        except Exception as e:
            processing_time = time.time() - start_time

            return StreamResult(
                result_id=str(uuid.uuid4()),
                stream_id=chunk.stream_id,
                chunk_id=chunk.chunk_id,
                result_data={},
                confidence=0.0,
                processing_time=processing_time,
                error=str(e),
            )

    def _prepare_chunk_inputs(
        self, chunk: StreamChunk, stream_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare inputs for workflow execution."""
        base_inputs = {
            "chunk_id": chunk.chunk_id,
            "chunk_index": chunk.chunk_index,
            "timestamp": chunk.timestamp,
        }

        stream_type = stream_config.get("stream_type", "text")

        if stream_type == "text":
            base_inputs["text"] = chunk.data
        elif stream_type == "json":
            base_inputs["data"] = chunk.data
        else:
            base_inputs["raw_data"] = chunk.data

        return base_inputs

    async def _get_stream_results(
        self, stream_id: str, wait_for_results: bool, timeout: float
    ) -> List[Dict[str, Any]]:
        """Get results from a stream."""
        if not hasattr(self, "stream_results"):
            return []

        if stream_id not in self.stream_results:
            return []

        # Return available results
        results = self.stream_results[stream_id]
        return [asdict(result) for result in results]

    async def _process_text_stream_internal(
        self, text_stream: str, analysis_type: str, window_size: int, progress
    ) -> Dict[str, Any]:
        """Internal text stream processing with progress reporting."""
        # Split text into windows
        words = text_stream.split()
        windows = [
            " ".join(words[i : i + window_size])
            for i in range(0, len(words), window_size)
        ]

        results = []
        total_windows = len(windows)

        # Process each window
        for i, window_text in enumerate(windows):
            # Update progress
            await progress.update(
                progress=int((i / total_windows) * 100),
                status=f"Processing window {i + 1}/{total_windows}",
            )

            # Create workflow for this window
            workflow = WorkflowBuilder()
            workflow.add_node(
                "LLMAgentNode",
                node_id="window_analyzer",
                prompt_template=f"Perform {analysis_type} analysis on: {{text}}",
                model_name="gpt-3.5-turbo",
            )

            # Process window
            try:
                result = self.runtime.execute(workflow, {"text": window_text})
                results.append(
                    {
                        "window_index": i,
                        "window_text": (
                            window_text[:100] + "..."
                            if len(window_text) > 100
                            else window_text
                        ),
                        "analysis_result": result,
                        "confidence": 0.8
                        + (i % 3) * 0.05,  # Simulated confidence variation
                    }
                )
            except Exception as e:
                results.append({"window_index": i, "error": str(e)})

        return {
            "total_windows": total_windows,
            "successful_windows": len([r for r in results if "error" not in r]),
            "results": results,
        }

    def _create_multimodal_pipeline(
        self, content_types: List[str], processing_pipeline: str
    ) -> Dict[str, Any]:
        """Create a multi-modal processing pipeline configuration."""
        return {
            "pipeline_name": processing_pipeline,
            "content_types": content_types,
            "stages": [
                {"name": "ingestion", "processors": content_types},
                {"name": "analysis", "processors": ["content_analyzer"]},
                {"name": "fusion", "processors": ["multimodal_fusion"]},
                {"name": "output", "processors": ["result_formatter"]},
            ],
        }

    async def run(self, host: str = "localhost", port: int = 8080):
        """Run the streaming MCP server."""
        logger.info(f"Starting streaming MCP server on {host}:{port}")

        # Run with HTTP and SSE transport for streaming
        self.server.run(
            enable_http_transport=True, enable_sse_transport=True, host=host, port=port
        )


async def main():
    """Main function to run the streaming server."""
    server = StreamingMCPServer("streaming-demo-server")
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
