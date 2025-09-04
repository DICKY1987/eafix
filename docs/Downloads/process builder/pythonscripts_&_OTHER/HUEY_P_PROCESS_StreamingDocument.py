#!/usr/bin/env python3
"""
Streaming Documentation Processor

Processes large specification documents without loading everything into memory.
Provides incremental processing, progress tracking, and memory-efficient handling.
"""

import io
import logging
import mmap
import queue
import re
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional

logger = logging.getLogger(__name__)


class ChunkType(Enum):
    """Enumeration for the types of document chunks."""

    SECTION_HEADER = "section_header"
    SECTION_CONTENT = "section_content"
    COMPONENT_DEFINITION = "component_definition"
    TABLE = "table"
    CODE_BLOCK = "code_block"
    METADATA = "metadata"


@dataclass
class DocumentChunk:
    """
    Represents a chunk of document content.

    Attributes:
        chunk_type: The type of the content chunk.
        section_id: The identifier of the section this chunk belongs to.
        line_number: The starting line number of the chunk in the document.
        content: The string content of the chunk.
        metadata: A dictionary for any additional metadata.
    """

    chunk_type: ChunkType
    section_id: Optional[str]
    line_number: int
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingProgress:
    """
    Tracks processing progress for large documents.

    Attributes:
        total_bytes: The total size of the document in bytes.
        processed_bytes: The number of bytes processed so far.
        current_section: The ID of the section currently being processed.
        sections_completed: The number of sections fully processed.
        total_sections: The total number of sections in the document.
        chunks_processed: The number of chunks yielded so far.
    """

    total_bytes: int
    processed_bytes: int
    current_section: str
    sections_completed: int
    total_sections: int
    chunks_processed: int

    @property
    def percentage(self) -> float:
        """Calculates the processing completion percentage."""
        if self.total_bytes == 0:
            return 100.0
        return (self.processed_bytes / self.total_bytes) * 100.0


class StreamingDocumentProcessor:
    """
    A memory-efficient streaming processor for large documents.

    This class reads and processes large files in chunks, using memory-mapped
    files to avoid loading the entire document into memory. It identifies
    different parts of the document (headers, content, components) and yields
    them as structured DocumentChunk objects.
    """

    def __init__(self, chunk_size: int = 64 * 1024):
        """
        Initializes the streaming processor.

        Args:
            chunk_size: The size of intermediate content chunks in bytes.
        """
        self.chunk_size = chunk_size
        self.section_pattern = re.compile(r"^## (\d+\.[\d\.]*)\s+(.+)$")
        self.component_pattern = re.compile(r"")
        self.component_end_pattern = re.compile(r"")
        self.progress_callbacks: List[Callable[[ProcessingProgress], None]] = []
        self.cancel_event = threading.Event()

    def add_progress_callback(self, callback: Callable[[ProcessingProgress], None]):
        """
        Adds a callback function for progress updates.

        Args:
            callback: A callable that accepts a ProcessingProgress object.
        """
        self.progress_callbacks.append(callback)

    def cancel_processing(self):
        """Signals to cancel the ongoing processing."""
        self.cancel_event.set()

    def stream_process_file(self, file_path: str) -> Iterator[DocumentChunk]:
        """
        Stream-processes a file, yielding document chunks.

        Args:
            file_path: The path to the document file.

        Yields:
            DocumentChunk objects as they are processed from the file.

        Raises:
            FileNotFoundError: If the specified file does not exist.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = path.stat().st_size
        try:
            with open(path, "r", encoding="utf-8") as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                    yield from self._stream_process_mmap(mmapped_file, file_size)
        except (IOError, OSError) as e:
            logger.error(f"Could not open or map file {file_path}: {e}")
            raise

    def _stream_process_mmap(
        self, mmapped_file: mmap.mmap, total_size: int
    ) -> Iterator[DocumentChunk]:
        """
        Processes a memory-mapped file and yields document chunks.

        Args:
            mmapped_file: The memory-mapped file object.
            total_size: The total size of the file in bytes.

        Yields:
            DocumentChunk objects.
        """
        buffer = io.StringIO()
        current_section = None
        line_number, chunks_yielded = 0, 0
        total_sections = self._count_sections(mmapped_file)
        mmapped_file.seek(0)

        progress = ProcessingProgress(
            total_bytes=total_size,
            processed_bytes=0,
            current_section="",
            sections_completed=0,
            total_sections=total_sections,
            chunks_processed=0,
        )

        try:
            for line_bytes in iter(mmapped_file.readline, b""):
                if self.cancel_event.is_set():
                    logger.info("Processing cancelled by user.")
                    return

                line = line_bytes.decode("utf-8")
                line_number += 1
                progress.processed_bytes += len(line_bytes)
                progress.chunks_processed = chunks_yielded

                section_match = self.section_pattern.match(line.strip())
                if section_match:
                    if current_section and buffer.tell() > 0:
                        yield DocumentChunk(
                            chunk_type=ChunkType.SECTION_CONTENT,
                            section_id=current_section,
                            line_number=line_number - 1,
                            content=buffer.getvalue(),
                            metadata={"size_bytes": buffer.tell()},
                        )
                        chunks_yielded += 1
                        progress.sections_completed += 1

                    current_section = section_match.group(1)
                    progress.current_section = current_section
                    yield DocumentChunk(
                        chunk_type=ChunkType.SECTION_HEADER,
                        section_id=current_section,
                        line_number=line_number,
                        content=line.strip(),
                        metadata={
                            "section_title": section_match.group(2),
                            "section_number": current_section,
                        },
                    )
                    chunks_yielded += 1
                    buffer = io.StringIO()
                    self._report_progress(progress)
                    continue

                buffer.write(line)

            if buffer.tell() > 0:
                yield DocumentChunk(
                    chunk_type=ChunkType.SECTION_CONTENT,
                    section_id=current_section,
                    line_number=line_number,
                    content=buffer.getvalue(),
                    metadata={"final": True, "size_bytes": buffer.tell()},
                )
                chunks_yielded += 1
                progress.sections_completed += 1

            progress.processed_bytes = total_size
            self._report_progress(progress)

        except (ValueError, TypeError) as e:
            logger.error(f"Streaming processing error at line {line_number}: {e}")
            raise

    def _count_sections(self, mmapped_file: mmap.mmap) -> int:
        """Counts the total number of sections for progress tracking."""
        count = 0
        current_pos = mmapped_file.tell()
        mmapped_file.seek(0)
        for line_bytes in iter(mmapped_file.readline, b""):
            try:
                line = line_bytes.decode("utf-8")
                if self.section_pattern.match(line.strip()):
                    count += 1
            except UnicodeDecodeError:
                continue
        mmapped_file.seek(current_pos)
        return count

    def _report_progress(self, progress: ProcessingProgress):
        """Reports progress to all registered callbacks."""
        for callback in self.progress_callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")


class IncrementalDocumentationProcessor:
    """
    Processes documentation incrementally using a pool of worker threads.

    This class orchestrates the streaming processor and distributes document chunks
    to worker threads for parallel processing, aggregating the results.
    """

    def __init__(self, streaming_processor: StreamingDocumentProcessor):
        """
        Initializes the incremental processor.

        Args:
            streaming_processor: An instance of StreamingDocumentProcessor.
        """
        self.streaming_processor = streaming_processor
        self.processing_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.worker_threads: List[threading.Thread] = []
        self.is_processing = False

    def start_workers(self, num_workers: int = 2):
        """
        Starts the worker threads for parallel chunk processing.

        Args:
            num_workers: The number of worker threads to start.
        """
        self.is_processing = True
        for i in range(num_workers):
            worker = threading.Thread(
                target=self._worker_loop, name=f"DocWorker-{i}", daemon=True
            )
            worker.start()
            self.worker_threads.append(worker)
        logger.info(f"Started {num_workers} documentation workers.")

    def stop_workers(self):
        """Stops all active worker threads."""
        self.is_processing = False
        for _ in self.worker_threads:
            self.processing_queue.put(None)  # Poison pill
        for worker in self.worker_threads:
            worker.join(timeout=5)
        self.worker_threads.clear()
        logger.info("Stopped all documentation workers.")

    def process_file_incrementally(self, file_path: str) -> Dict[str, Any]:
        """
        Processes a file incrementally with parallel chunk processing.

        Args:
            file_path: The path to the document file.

        Returns:
            A dictionary containing the aggregated processing results.
        """
        if not self.is_processing:
            self.start_workers()

        chunk_count = 0
        for chunk in self.streaming_processor.stream_process_file(file_path):
            self.processing_queue.put(chunk)
            chunk_count += 1

        for _ in self.worker_threads:
            self.processing_queue.put("END")

        results: Dict[str, Dict] = {}
        completed_workers = 0
        while completed_workers < len(self.worker_threads):
            try:
                result = self.result_queue.get(timeout=1.0)
                if result is None:
                    completed_workers += 1
                    continue

                section_id, section_data = result
                if section_id not in results:
                    results[section_id] = {
                        "chunks": [],
                        "components": [],
                        "tables": [],
                        "metadata": {},
                    }
                for key, value in section_data.items():
                    if isinstance(value, list):
                        results[section_id][key].extend(value)
                    else:
                        results[section_id][key] = value

            except queue.Empty:
                continue

        return {
            "sections": results,
            "summary": {
                "total_chunks_processed": chunk_count,
                "sections_found": len(results),
                "processing_method": "incremental_streaming",
            },
        }

    def _worker_loop(self):
        """The main loop for a worker thread."""
        while self.is_processing:
            try:
                chunk = self.processing_queue.get(timeout=1.0)
                if chunk is None or chunk == "END":
                    break
                result = self._process_chunk(chunk)
                if result:
                    self.result_queue.put(result)
                self.processing_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker thread error: {e}")
        self.result_queue.put(None)

    def _process_chunk(self, chunk: DocumentChunk) -> Optional[tuple]:
        """
        Processes an individual document chunk.

        Args:
            chunk: The DocumentChunk to process.

        Returns:
            A tuple containing the section ID and processed data, or None.
        """
        if not chunk.section_id:
            return None

        section_data: Dict[str, Any] = {
            "chunks": [chunk],
            "components": [],
            "tables": [],
            "metadata": chunk.metadata,
        }

        if chunk.chunk_type == ChunkType.COMPONENT_DEFINITION:
            component_data = self._extract_component_data(chunk.content)
            if component_data:
                section_data["components"].append(component_data)
        elif chunk.chunk_type == ChunkType.TABLE:
            table_data = self._extract_table_data(chunk.content)
            if table_data:
                section_data["tables"].append(table_data)

        return (chunk.section_id, section_data)

    def _extract_component_data(self, content: str) -> Dict:
        """Extracts component data from content."""
        lines = content.split("\n")
        component_data = {"type": "unknown", "properties": [], "dependencies": []}
        for line in lines:
            line = line.strip()
            if line.startswith("**Type:**"):
                component_data["type"] = line.split(":", 1)[1].strip()
            elif line.startswith("- "):
                component_data["properties"].append(line[2:].strip())
        return component_data

    def _extract_table_data(self, content: str) -> Dict:
        """Extracts table data from content."""
        lines = content.split("\n")
        if len(lines) < 2:
            return {}

        headers = [cell.strip() for cell in lines[0].split("|") if cell.strip()]
        rows = []
        for line in lines[2:]:
            if line.strip():
                row = [cell.strip() for cell in line.split("|") if cell.strip()]
                if len(row) == len(headers):
                    rows.append(dict(zip(headers, row)))

        return {"headers": headers, "rows": rows, "row_count": len(rows)}


if __name__ == "__main__":
    import tempfile

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    test_content = """# Test Document

## 1.1 First Section

This is the first section with some content.

**Type:** Service
**Description:** Test component
- Property 1: Value 1
- Property 2: Value 2
## 1.2 Second Section

| Column 1 | Column 2 | Column 3 |
|:---------|:---------|:---------|
| Row 1 Col 1 | Row 1 Col 2 | Row 1 Col 3 |
| Row 2 Col 1 | Row 2 Col 2 | Row 2 Col 3 |

More content here.
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(test_content)
        test_file_path = f.name

    try:
        streaming_proc = StreamingDocumentProcessor(chunk_size=1024)
        incremental_proc = IncrementalDocumentationProcessor(streaming_proc)

        def progress_callback(p: ProcessingProgress):
            logger.info(
                f"Progress: {p.percentage:.1f}% - Section: {p.current_section}"
            )

        streaming_proc.add_progress_callback(progress_callback)
        logger.info("Processing file incrementally...")
        final_result = incremental_proc.process_file_incrementally(test_file_path)

        logger.info("\nProcessing completed!")
        logger.info(f"Sections found: {final_result['summary']['sections_found']}")

        for sec_id, sec_data in final_result["sections"].items():
            logger.info(f"\nSection {sec_id}:")
            logger.info(f"  Components: {len(sec_data['components'])}")
            logger.info(f"  Tables: {len(sec_data['tables'])}")

        incremental_proc.stop_workers()

    finally:
        Path(test_file_path).unlink()