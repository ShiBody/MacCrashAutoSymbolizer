"""
Advanced File Downloader - Supports chunked download, progress display
Specially optimized for large file (.7z etc.) download experience
"""

import asyncio
import aiohttp
import aiofiles
import hashlib
import os
import time
import base64

from pathlib import Path
from typing import Optional, Dict, List, Callable, Tuple
from dataclasses import dataclass, asdict
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DownloadProgress:
    url: str
    filename: str
    total_size: int
    downloaded_size: int
    chunks_completed: int
    total_chunks: int
    speed: float  # bytes/second
    eta: float    # seconds
    start_time: float

    @property
    def progress_percent(self) -> float:
        if self.total_size == 0:
            return 0.0
        return (self.downloaded_size / self.total_size) * 100

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class ChunkInfo:
    index: int
    start: int
    end: int
    size: int
    completed: bool = False
    temp_file: Optional[str] = None

class AdvancedDownloader:
    def __init__(self,
                 chunk_size: int = 1024 * 1024,  # 1MB per chunk
                 max_concurrent_chunks: int = 8,
                 timeout: int = 300,
                 max_retries: int = 3,
                 progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
                 headers: Optional[Dict[str, str]] = None,
                 basic_token: Optional[str] = None):
        """
        Initialize downloader

        Args:
            chunk_size: Size of each chunk (in bytes)
            max_concurrent_chunks: Maximum number of concurrent chunks
            timeout: Request timeout (in seconds)
            max_retries: Maximum number of retries
            progress_callback: Progress callback function
            headers: Custom HTTP headers
            basic_token: Basic authentication token (encoded base64 string)
        """
        self.chunk_size = chunk_size
        self.max_concurrent_chunks = max_concurrent_chunks
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.progress_callback = progress_callback
        self.semaphore = asyncio.Semaphore(max_concurrent_chunks)

        # Set request headers
        self.headers = headers or {}
        if basic_token:
            self.headers['Authorization'] = f'Basic {basic_token}'

    async def get_file_info(self, url: str) -> Tuple[int, bool]:
        """
        Get file information

        Returns:
            (file_size, supports_range)
        """
        async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
            async with session.head(url) as response:
                if response.status == 401:
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=401,
                        message="HTTP 401: Unauthorized - Check your Basic token"
                    )
                if response.status == 404:
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=404,
                        message="HTTP 404: Could not find resource"
                    )

                response.raise_for_status()

                # Get file size
                content_length = response.headers.get('Content-Length')
                file_size = int(content_length) if content_length else 0

                # Check if range requests are supported
                accept_ranges = response.headers.get('Accept-Ranges', '').lower()
                supports_range = accept_ranges == 'bytes'

                return file_size, supports_range

    def _create_chunks(self, file_size: int) -> List[ChunkInfo]:
        """Create download chunks"""
        chunks = []
        for i in range(0, file_size, self.chunk_size):
            start = i
            end = min(i + self.chunk_size - 1, file_size - 1)
            size = end - start + 1

            chunk = ChunkInfo(
                index=len(chunks),
                start=start,
                end=end,
                size=size
            )
            chunks.append(chunk)

        return chunks

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _download_chunk(self, session: aiohttp.ClientSession, url: str,
                            chunk: ChunkInfo, temp_dir: str) -> ChunkInfo:
        """Download a single chunk"""
        async with self.semaphore:
            chunk.temp_file = os.path.join(temp_dir, f"chunk_{chunk.index:06d}.tmp")

            # Merge Range header and Authorization header
            request_headers = self.headers.copy()
            request_headers['Range'] = f'bytes={chunk.start}-{chunk.end}'

            async with session.get(url, headers=request_headers) as response:
                if response.status not in (206, 200):  # 206 Partial Content or 200 OK
                    raise aiohttp.ClientError(f"HTTP {response.status}")

                async with aiofiles.open(chunk.temp_file, 'wb') as f:
                    async for data in response.content.iter_chunked(8192):
                        await f.write(data)

                chunk.completed = True
                return chunk

    def _merge_chunks(self, chunks: List[ChunkInfo], output_file: str):
        """Merge chunk files"""
        logger.info(f"Merging {len(chunks)} chunks...")

        with open(output_file, 'wb') as outfile:
            for chunk in sorted(chunks, key=lambda x: x.index):
                if chunk.temp_file and os.path.exists(chunk.temp_file):
                    with open(chunk.temp_file, 'rb') as infile:
                        outfile.write(infile.read())
                    # Delete temp file
                    os.remove(chunk.temp_file)

    def _cleanup_temp_files(self, temp_dir: str):
        """Clean up temp files"""
        if os.path.exists(temp_dir):
            for file in os.listdir(temp_dir):
                if file.endswith('.tmp'):
                    os.remove(os.path.join(temp_dir, file))
            try:
                os.rmdir(temp_dir)
            except OSError:
                pass

    def _calculate_speed_and_eta(self, downloaded: int, total: int, elapsed: float) -> Tuple[float, float]:
        """Calculate download speed and estimated time remaining"""
        if elapsed == 0:
            return 0.0, 0.0

        speed = downloaded / elapsed
        if speed == 0:
            return 0.0, 0.0

        remaining = total - downloaded
        eta = remaining / speed

        return speed, eta

    async def download_file(self, url: str, filepath: str) -> bool:
        """
        Download file

        Args:
            url: Download link
            filepath: Save path

        Returns:
            Download success or not
        """
        try:
            # Create directory
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)

            # Check if file already exists
            if os.path.exists(filepath):
                logger.info("File already exists, skipping download")
                return True

            # Get file information
            logger.info(f"Getting file information: {url}")
            file_size, supports_range = await self.get_file_info(url)

            if file_size == 0:
                logger.warning("Unable to get file size, using simple download mode")
                return await self._simple_download(url, filepath)

            logger.info(f"File size: {self._format_size(file_size)}")
            logger.info(f"Supports chunked download: {supports_range}")

            # Create chunks
            chunks = self._create_chunks(file_size)

            # Create temp directory
            temp_dir = f"{filepath}.tmp"
            os.makedirs(temp_dir, exist_ok=True)

            # Initialize progress
            progress = DownloadProgress(
                url=url,
                filename=os.path.basename(filepath),
                total_size=file_size,
                downloaded_size=0,
                chunks_completed=0,
                total_chunks=len(chunks),
                speed=0.0,
                eta=0.0,
                start_time=time.time()
            )

            logger.info(f"Starting download of {len(chunks)} chunks...")

            # Download chunks
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                # Create download tasks
                tasks = []
                for chunk in chunks:
                    task = self._download_chunk(session, url, chunk, temp_dir)
                    tasks.append(task)

                # Execute download and monitor progress
                completed_chunks = []
                for coro in asyncio.as_completed(tasks):
                    try:
                        chunk = await coro
                        completed_chunks.append(chunk)

                        # Update progress
                        progress.chunks_completed += 1
                        progress.downloaded_size += chunk.size
                        elapsed = time.time() - progress.start_time
                        progress.speed, progress.eta = self._calculate_speed_and_eta(
                            progress.downloaded_size, progress.total_size, elapsed
                        )

                        # Call progress callback
                        if self.progress_callback:
                            self.progress_callback(progress)

                        logger.info(f"Chunk {chunk.index} completed "
                                  f"({progress.chunks_completed}/{progress.total_chunks}) "
                                  f"{progress.progress_percent:.1f}% "
                                  f"Speed: {self._format_size(progress.speed)}/s")

                    except Exception as e:
                        logger.error(f"Chunk download failed: {e}")
                        raise

            # Merge all chunks
            self._merge_chunks(completed_chunks, filepath)

            # Clean up temp files
            self._cleanup_temp_files(temp_dir)

            logger.info(f"Download completed: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False

    async def _simple_download(self, url: str, filepath: str) -> bool:
        """Simple download mode (no chunking)"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.get(url) as response:
                    response.raise_for_status()

                    async with aiofiles.open(filepath, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)

            logger.info(f"Simple download completed: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Simple download failed: {e}")
            return False

    @staticmethod
    def _format_size(size_bytes: float) -> str:
        """Format file size"""
        if size_bytes == 0:
            return "0B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"

    @staticmethod
    def create_basic_token(username: str, password: str) -> str:
        """
        Create Basic authentication token

        Args:
            username: Username
            password: Password

        Returns:
            Encoded Basic token eGlhb3hzaGg6Y21WbWRHdHVPakF4T2pFM05qTTNNRGswTXpnNlEyWXdNV04zZDAxVVkydHNSSEI0WlhaV1ZYQkxRV3hEY1dGcg==
        """
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        return encoded_credentials

class SevenZipValidator:
    """7z file validator"""

    @staticmethod
    def validate_7z_file(filepath: str) -> bool:
        """
        Validate 7z file integrity

        Args:
            filepath: 7z file path

        Returns:
            Is the file valid
        """
        try:
            # Check file header
            with open(filepath, 'rb') as f:
                header = f.read(6)
                # 7z file header: 37 7A BC AF 27 1C
                if header != b'\x37\x7A\xBC\xAF\x27\x1C':
                    logger.error("7z file header validation failed")
                    return False

            # If py7zr is installed, perform deeper validation
            try:
                import py7zr
                with py7zr.SevenZipFile(filepath, mode='r') as archive:
                    # Try to read file list
                    archive.list()
                logger.info("7z file validation passed")
                return True

            except ImportError:
                logger.warning("py7zr not installed, only basic validation performed")
                return True

        except Exception as e:
            logger.error(f"7z file validation failed: {e}")
            return False

    @staticmethod
    def calculate_file_hash(filepath: str, algorithm: str = 'md5') -> str:
        """
        Calculate file hash value

        Args:
            filepath: File path
            algorithm: Hash algorithm (md5, sha1, sha256)

        Returns:
            Hash value
        """
        hash_obj = hashlib.new(algorithm)

        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                hash_obj.update(chunk)

        return hash_obj.hexdigest()

    @staticmethod
    def extract_7z_file(filepath: str, extract_to: str) -> bool:
        """
        Extract 7z file contents

        Args:
            filepath: 7z file path
            extract_to: Extraction destination directory

        Returns:
            Extraction success or not
        """
        try:
            import py7zr

            # Extract 7z file
            with py7zr.SevenZipFile(filepath, mode='r') as archive:
                archive.extractall(path=extract_to)

            return True

        except ImportError:
            logger.error("py7zr not installed, cannot extract 7z file")
            return False

        except Exception as e:
            logger.error(f"7z file extraction failed: {e}")
            return False

# Progress display callback function
def default_progress_callback(progress: DownloadProgress):
    """Default progress display callback"""
    bar_length = 50
    filled_length = int(bar_length * progress.progress_percent / 100)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    print(f'\rDownload progress: |{bar}| {progress.progress_percent:.1f}% '
          f'{AdvancedDownloader._format_size(progress.downloaded_size)}/'
          f'{AdvancedDownloader._format_size(progress.total_size)} '
          f'Speed: {AdvancedDownloader._format_size(progress.speed)}/s '
          f'Remaining: {progress.eta:.0f}s', end='', flush=True)

