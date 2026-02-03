"""Parallel and Streaming Decoders - High-performance P-code decompilation.

This module provides parallel and streaming decompilation capabilities
for handling large codebases and improving performance.
"""

import asyncio
import logging
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Dict, Iterator, List

from src_new._core import DecompileResult
from src_new._patterns import BinaryReader
from .decompiler import PCodeDecoder
from .opcodes import OPCODES

logger = logging.getLogger(__name__)


@dataclass
class StreamingResult:
    """Streaming decompilation result."""

    chunk_id: int
    source: str
    instructions: List[str]
    errors: List[str]


class ParallelDecoder:
    """Parallel P-code decoder using multiprocessing."""

    def __init__(self, workers: int = None):
        """Initialize parallel decoder.

        Args:
            workers: Number of worker processes (None for CPU count)
        """
        self.workers = workers
        self.decoder = PCodeDecoder()

    def decode_batch(self, files: List[Path]) -> Dict[Path, DecompileResult]:
        """Decode multiple files in parallel.

        Args:
            files: Files to decode

        Returns:
            Decompilation results by file
        """
        results = {}

        with ProcessPoolExecutor(max_workers=self.workers) as executor:
            # Submit all files
            futures = {executor.submit(self._decode_file, f): f for f in files}

            # Collect results
            for future in futures:
                file_path = futures[future]
                try:
                    result = future.result(timeout=30.0)
                    results[file_path] = result
                except Exception as e:
                    logger.error(f"Failed to decode {file_path}: {e}")
                    results[file_path] = DecompileResult(
                        success=False,
                        source="",
                        instructions=[],
                        errors=[str(e)],
                    )

        return results

    def decode_batch_async(self, files: List[Path]) -> Dict[Path, DecompileResult]:
        """Decode files using async I/O.

        Args:
            files: Files to decode

        Returns:
            Decompilation results
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            results = loop.run_until_complete(self._async_decode_batch(files))
            return results
        finally:
            loop.close()

    async def _async_decode_batch(
        self, files: List[Path]
    ) -> Dict[Path, DecompileResult]:
        """Async batch decoding.

        Args:
            files: Files to decode

        Returns:
            Results by file
        """
        tasks = [self._async_decode_file(f) for f in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            file: result
            if not isinstance(result, Exception)
            else DecompileResult(
                success=False,
                source="",
                instructions=[],
                errors=[str(result)],
            )
            for file, result in zip(files, results)
        }

    async def _async_decode_file(self, file_path: Path) -> DecompileResult:
        """Async file decoding.

        Args:
            file_path: File to decode

        Returns:
            Decompilation result
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._decode_file, file_path)

    def _decode_file(self, file_path: Path) -> DecompileResult:
        """Decode single file.

        Args:
            file_path: File to decode

        Returns:
            Decompilation result
        """
        try:
            with BinaryReader(file_path) as reader:
                data = reader.read()

            # Decode P-code
            instructions = self.decoder.decode(data)

            # Generate source
            source = self._generate_source(instructions)

            return DecompileResult(
                success=True,
                source=source,
                instructions=instructions,
                errors=[],
            )

        except Exception as e:
            return DecompileResult(
                success=False,
                source="",
                instructions=[],
                errors=[str(e)],
            )

    def _generate_source(self, instructions: List[str]) -> str:
        """Generate source from instructions.

        Args:
            instructions: Decoded instructions

        Returns:
            Generated source code
        """
        lines = []
        indent = 0

        for inst in instructions:
            # Handle indentation
            if inst.startswith(("end", "else", "elseif", "catch", "finally")):
                indent = max(0, indent - 1)

            # Add indented line
            lines.append("    " * indent + inst)

            # Increase indent
            if inst.startswith(("if", "for", "while", "try", "function", "class")):
                indent += 1

        return "\n".join(lines)


class StreamingDecoder:
    """Streaming P-code decoder for large files."""

    def __init__(self, chunk_size: int = 4096):
        """Initialize streaming decoder.

        Args:
            chunk_size: Size of chunks to process
        """
        self.chunk_size = chunk_size
        self.decoder = PCodeDecoder()

    def decode_stream(self, file_path: Path) -> Iterator[StreamingResult]:
        """Stream decode a file.

        Args:
            file_path: File to decode

        Yields:
            Streaming results
        """
        with BinaryReader(file_path) as reader:
            chunk_id = 0

            while reader.tell() < reader.size:
                # Read chunk
                chunk = reader.read(min(self.chunk_size, reader.size - reader.tell()))

                # Decode chunk
                result = self._decode_chunk(chunk_id, chunk)

                yield result
                chunk_id += 1

    async def decode_stream_async(
        self, file_path: Path
    ) -> AsyncIterator[StreamingResult]:
        """Async stream decode.

        Args:
            file_path: File to decode

        Yields:
            Streaming results
        """
        chunk_id = 0

        async with self._async_reader(file_path) as reader:
            async for chunk in reader:
                result = await self._async_decode_chunk(chunk_id, chunk)
                yield result
                chunk_id += 1

    def _decode_chunk(self, chunk_id: int, chunk: bytes) -> StreamingResult:
        """Decode a chunk.

        Args:
            chunk_id: Chunk identifier
            chunk: Data chunk

        Returns:
            Streaming result
        """
        try:
            instructions = self._extract_instructions(chunk)
            source = self._generate_partial_source(instructions)

            return StreamingResult(
                chunk_id=chunk_id,
                source=source,
                instructions=instructions,
                errors=[],
            )

        except Exception as e:
            return StreamingResult(
                chunk_id=chunk_id,
                source="",
                instructions=[],
                errors=[str(e)],
            )

    async def _async_decode_chunk(self, chunk_id: int, chunk: bytes) -> StreamingResult:
        """Async decode chunk.

        Args:
            chunk_id: Chunk identifier
            chunk: Data chunk

        Returns:
            Streaming result
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._decode_chunk, chunk_id, chunk)

    def _extract_instructions(self, chunk: bytes) -> List[str]:
        """Extract instructions from chunk.

        Args:
            chunk: Data chunk

        Returns:
            Extracted instructions
        """
        instructions = []
        i = 0

        while i < len(chunk):
            opcode = chunk[i]

            if opcode in OPCODES:
                inst_name = OPCODES[opcode]

                # Get instruction size
                inst_size = self._get_instruction_size(opcode)

                # Extract operands
                if i + inst_size <= len(chunk):
                    operands = chunk[i + 1 : i + inst_size]
                    inst = self._format_instruction(inst_name, operands)
                    instructions.append(inst)
                    i += inst_size
                else:
                    # Incomplete instruction
                    break
            else:
                i += 1

        return instructions

    def _get_instruction_size(self, opcode: int) -> int:
        """Get instruction size.

        Args:
            opcode: Operation code

        Returns:
            Instruction size in bytes
        """
        # Size map for common opcodes
        size_map = {
            0x00: 1,  # RETURN
            0x02: 5,  # JUMPTRUE
            0x03: 5,  # JUMPFALSE
            0x10: 5,  # PUSH
            0x11: 1,  # POP
            0x20: 5,  # LOAD
            0x21: 5,  # STORE
            0x30: 9,  # CALL
        }

        return size_map.get(opcode, 1)

    def _format_instruction(self, name: str, operands: bytes) -> str:
        """Format instruction.

        Args:
            name: Instruction name
            operands: Operand bytes

        Returns:
            Formatted instruction
        """
        if not operands:
            return name

        # Format operands
        if len(operands) == 4:
            value = int.from_bytes(operands, "little")
            return f"{name} {value}"
        else:
            hex_str = operands.hex()
            return f"{name} {hex_str}"

    def _generate_partial_source(self, instructions: List[str]) -> str:
        """Generate partial source.

        Args:
            instructions: Instructions

        Returns:
            Partial source code
        """
        return "\n".join(instructions)

    async def _async_reader(self, file_path: Path):
        """Async file reader.

        Args:
            file_path: File to read

        Yields:
            Data chunks
        """
        import aiofiles

        async with aiofiles.open(file_path, "rb") as f:
            while True:
                chunk = await f.read(self.chunk_size)
                if not chunk:
                    break
                yield chunk


class HybridDecoder:
    """Hybrid decoder combining parallel and streaming."""

    def __init__(self, threshold: int = 1_000_000):
        """Initialize hybrid decoder.

        Args:
            threshold: Size threshold for streaming (bytes)
        """
        self.threshold = threshold
        self.parallel = ParallelDecoder()
        self.streaming = StreamingDecoder()

    def decode(self, file_path: Path) -> DecompileResult:
        """Decode using appropriate strategy.

        Args:
            file_path: File to decode

        Returns:
            Decompilation result
        """
        file_size = file_path.stat().st_size

        if file_size > self.threshold:
            # Use streaming for large files
            return self._decode_streaming(file_path)
        else:
            # Use parallel for small files
            results = self.parallel.decode_batch([file_path])
            return results[file_path]

    def decode_directory(self, directory: Path) -> Dict[Path, DecompileResult]:
        """Decode all files in directory.

        Args:
            directory: Directory to process

        Returns:
            Results by file
        """
        # Categorize files by size
        small_files = []
        large_files = []

        for file_path in directory.rglob("*.fun"):
            if file_path.stat().st_size > self.threshold:
                large_files.append(file_path)
            else:
                small_files.append(file_path)

        results = {}

        # Process small files in parallel
        if small_files:
            results.update(self.parallel.decode_batch(small_files))

        # Process large files with streaming
        for file_path in large_files:
            results[file_path] = self._decode_streaming(file_path)

        return results

    def _decode_streaming(self, file_path: Path) -> DecompileResult:
        """Decode using streaming.

        Args:
            file_path: File to decode

        Returns:
            Decompilation result
        """
        all_source = []
        all_instructions = []
        errors = []

        for result in self.streaming.decode_stream(file_path):
            if result.source:
                all_source.append(result.source)

            all_instructions.extend(result.instructions)
            errors.extend(result.errors)

        return DecompileResult(
            success=len(errors) == 0,
            source="\n".join(all_source),
            instructions=all_instructions,
            errors=errors,
        )


def parallel_decompile(directory: Path, output_dir: Path, workers: int = None) -> int:
    """Parallel decompile directory.

    Args:
        directory: Input directory
        output_dir: Output directory
        workers: Number of workers

    Returns:
        Number of files processed
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    decoder = HybridDecoder()
    results = decoder.decode_directory(directory)

    processed = 0
    for file_path, result in results.items():
        if result.success:
            # Write output file
            output_file = output_dir / file_path.with_suffix(".sru").name

            with open(output_file, "w") as f:
                f.write(result.source)

            processed += 1
            logger.debug(f"Decompiled {file_path} -> {output_file}")
        else:
            logger.warning(f"Failed to decompile {file_path}: {result.errors}")

    logger.info(f"Decompiled {processed}/{len(results)} files")
    return processed
