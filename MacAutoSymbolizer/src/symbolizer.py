import asyncio
import logging
import os
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
import time
from typing import Callable
from pathlib import Path
from MacAutoSymbolizer.src.utilities import (
    Arch,
    version_full_match,
    get_dst_information,
    get_download_full_url,
    get_atos_tool_path
)
from MacAutoSymbolizer.src.scanner import (
    CrashScanner,
    ScanResult,
    get_arch,
    ScannedLine,
    SymbolizedLine,
    DiagLine,
    CrashLineType,
    RawLine,
    ImageBinary
)
from MacAutoSymbolizer.src.advanced_downloader import (
    AdvancedDownloader,
    SevenZipValidator
)
from MacAutoSymbolizer.src.subprocess_cmd import SubProcessCmd
from MacAutoSymbolizer.src.resource_config import resource_config


class Symbolizer:
    def __init__(
            self,
            result_processor: Callable | None = None,
            max_concurrent_symbolize: int = None  # 限制并发符号化任务数量，None时使用配置文件
    ):
        self.loop = asyncio.get_event_loop()
        self.scanner = CrashScanner()
        
        # 使用配置文件中的设置，如果未指定参数的话
        if max_concurrent_symbolize is None:
            max_concurrent_symbolize = resource_config.max_concurrent_symbolize
        
        # 添加信号量来控制并发数量，防止创建过多文件句柄
        self.symbolize_semaphore = asyncio.Semaphore(max_concurrent_symbolize)
        self.max_concurrent_symbolize = max_concurrent_symbolize
        
        # 记录资源配置
        logger.info(f"符号化器初始化: 最大并发数={max_concurrent_symbolize}")
        # logger.debug(resource_config.get_config_summary())
        
        username = os.getenv('DOWNLOAD_USER')
        password = os.getenv('DOWNLOAD_PASSWORD')
        basic_token = AdvancedDownloader.create_basic_token(username, password) if username and password else None
        self.downloader = AdvancedDownloader(
            chunk_size=8 * 1024 * 1024,  # 8MB chunks, suitable for large files
            max_concurrent_chunks=10,  # 10 concurrent connections
            timeout=600,  # 10 minutes timeout
            max_retries=5,  # 5 retries
            basic_token=basic_token,
            headers={
                'User-Agent': 'AdvancedDownloader/1.0 (Mac-Auto-Symbols)',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
            }
        )
        self.validator = SevenZipValidator()
        atos_path = get_atos_tool_path()
        self.sub_process_cmd = SubProcessCmd(atos_path)
        logger.debug(f"使用 atos 工具路径: {atos_path}")

    async def symbolize_async(self, thread_block: list, symbol_dir: str, arch: Arch, image_dict: dict | None = None):
        # 提取需要处理的二进制文件
        image_binarys: list[ImageBinary] = [a_line.binary for a_line in thread_block if isinstance(a_line, RawLine) or isinstance(a_line, SymbolizedLine) or isinstance(a_line, DiagLine)]
        
        # 批量更新二进制文件信息，但控制并发数量
        async def update_with_semaphore(binary):
            async with self.symbolize_semaphore:
                return await self._update_image_binary(binary, symbol_dir, arch, image_dict)
        
        tasks1 = [update_with_semaphore(binary) for binary in image_binarys]
        await asyncio.gather(*tasks1)
        
        # 符号化处理也需要控制并发数量
        async def symbolize_with_semaphore(a_line):
            async with self.symbolize_semaphore:
                return await self._symbolize_line(a_line)
        
        tasks2 = [symbolize_with_semaphore(a_line) for a_line in thread_block]
        return await asyncio.gather(*tasks2)

    @staticmethod
    async def _update_image_binary(binary: ImageBinary, symbol_dir: str, arch: Arch, image_dict: dict | None = None):
        if not binary:
            return
        if image_dict and binary.name in image_dict:
            binary_from_dict = image_dict[binary.name]
            if not binary.binaryArc:
                binary.binaryArc = binary_from_dict.binaryArc
            if not binary.pathToDSYMFile:
                binary.pathToDSYMFile = binary_from_dict.pathToDSYMFile
            if not binary.loadAddress:
                binary.loadAddress = binary_from_dict.loadAddress
            if not binary.uuid:
                binary.uuid = binary_from_dict.uuid
        if not binary.binaryArc:
            binary.binaryArc = arch
        if not binary.pathToDSYMFile:
            if os.path.exists(symbol_dir):
                dsym_file = None
                try:
                    # 优化文件搜索：使用生成器表达式减少内存使用，限制搜索结果数量
                    symbol_path = Path(symbol_dir)
                    
                    # 首先尝试搜索primary name，最多搜索5个结果避免过度消耗资源
                    for i, f in enumerate(symbol_path.rglob(f'{binary.name}*')):
                        if i >= 5:  # 限制搜索结果数量
                            break
                        if f.is_dir():
                            dsym_file = str(f)
                            break
                    
                    # 如果没找到且有备用名称，再尝试搜索backup name
                    if not dsym_file and binary.name_from_binary:
                        for i, f in enumerate(symbol_path.rglob(f'{binary.name_from_binary}*')):
                            if i >= 5:  # 限制搜索结果数量
                                break
                            if f.is_dir():
                                dsym_file = str(f)
                                break
                                
                    if dsym_file:
                        binary.pathToDSYMFile = dsym_file
                    else:
                        return
                except (OSError, PermissionError) as e:
                    # 处理文件系统错误，避免程序崩溃
                    logger.warning(f"文件搜索出错: {e}")
                    return

    async def _symbolize_line(self, line: ScannedLine):
        if isinstance(line, RawLine) or isinstance(line, SymbolizedLine) or isinstance(line, DiagLine):
            cmd_args = line.cmd_args()
            if cmd_args:
                return_code, stdout, stderr = await self.sub_process_cmd.cmd(*cmd_args)
                useful_output = max(stdout.split('\n'), key=len)
                line.symbolizedRes = useful_output
                line.isSymbolized = True
        return line


    @staticmethod
    def _cleanup_old_downloads(dst_dir: str, max_folders: int = 10):
        """
        Clean up old download folders, keeping only the most recent ones

        Args:
            dst_dir: The destination directory path (e.g., './test_symbols/45.6.0.32215/arm64')
            max_folders: Maximum number of folders to keep (default: 10)
        """
        try:
            # Get the parent directory that contains all version folders
            # e.g., './test_symbols/45.6.0.32215/arm64' -> './test_symbols'
            parent_dir = Path(dst_dir).parents[1]  # Go up 2 levels to get test_symbols

            if not parent_dir.exists():
                return

            # Get all version folders (e.g., 45.6.0.32215, 45.10.0.32870, etc.)
            version_folders = []
            for item in parent_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    version_folders.append(item)

            # If we have fewer folders than the limit, no cleanup needed
            if len(version_folders) <= max_folders:
                return

            # Sort folders by modification time (newest first)
            version_folders.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Keep only the most recent max_folders, delete the rest
            folders_to_delete = version_folders[max_folders:]

            if folders_to_delete:
                logger.info(f"🧹 Cleaning up {len(folders_to_delete)} old download folders...")

                for folder in folders_to_delete:
                    try:
                        import shutil
                        shutil.rmtree(folder)
                        logger.info(f"🗑️  Deleted old folder: {folder.name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete folder {folder}: {e}")

                logger.info(f"✅ Cleanup completed, kept {len(version_folders) - len(folders_to_delete)} most recent folders")

        except Exception as e:
            logger.warning(f"Failed to cleanup old downloads: {e}")

    async def download_symbols(
            self,
            version: str,
            arch: Arch,
            isBackup: bool = False
    ) -> tuple[bool, str | None]:
        if not version or not arch:
            raise ValueError("Version and architecture must be specified")
        url = get_download_full_url(version, arch, isBackup)
        dst_dir, filepath = get_dst_information(version, arch)
        if os.path.exists(dst_dir):
            dsym_files = list(Path(dst_dir).rglob('*.dSYM'))
            if dsym_files:
                logger.info(f"✅ Symbols already exist in {dst_dir}")
                logger.info(f"📂 Found {len(dsym_files)} .dSYM files, skipping download")
                return True, dst_dir


        # Clean up old downloads before starting new download
        Symbolizer._cleanup_old_downloads(dst_dir, max_folders=10)

        os.makedirs(dst_dir, exist_ok=True)

        logger.info("Starting download...")
        logger.info("💡 Using chunked download for large files")

        max_download_attempts = 2  # Allow one retry

        for attempt in range(max_download_attempts):
            if attempt > 0:
                logger.info(f"🔄 Retry attempt {attempt} due to file validation failure...")
                # Remove corrupted file before retry
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logger.info(f"🗑️  Removed corrupted file: {filepath}")

            start_time = time.time()

            try:
                success = await self.downloader.download_file(url, filepath)
                end_time = time.time()

                # Clear progress display - no logging needed for this

                if success:
                    file_size = os.path.getsize(filepath)
                    duration = end_time - start_time
                    avg_speed = file_size / duration if duration > 0 else 0

                    logger.info("✅ Download completed!")
                    logger.info(f"📊 File size: {AdvancedDownloader._format_size(file_size)}")
                    logger.info(f"⏱️  Total time: {duration:.1f}s")
                    logger.info(f"⚡ Average speed: {AdvancedDownloader._format_size(avg_speed)}/s")

                    # Validate 7z file
                    logger.info("🔍 Validating 7z file integrity...")


                    if self.validator.validate_7z_file(filepath):
                        logger.info("✅ 7z file validation passed")

                        # Calculate file hash
                        logger.info("🔐 Calculating file hash...")
                        md5_hash = self.validator.calculate_file_hash(filepath, 'md5')
                        sha256_hash = self.validator.calculate_file_hash(filepath, 'sha256')

                        logger.info(f"📝 MD5: {md5_hash}")
                        logger.info(f"📝 SHA256: {sha256_hash}")

                        # Extract 7z file contents
                        logger.info("📦 Extracting 7z file contents...")
                        try:
                            extraction_success = SevenZipValidator.extract_7z_file(filepath, dst_dir)
                            if extraction_success:
                                logger.info("✅ 7z file extracted successfully")

                                # Delete the 7z file after successful extraction
                                os.remove(filepath)
                                logger.info(f"🗑️  Deleted 7z file: {filepath}")

                                logger.info(f"🎉 Cisco Webex OSX Symbols download, validation, and extraction completed!")
                                logger.info(f"📂 Extracted to: {os.path.abspath(dst_dir)}")
                            else:
                                logger.error("❌ 7z file extraction failed")
                                logger.info("💡 7z file is valid but extraction failed, keeping the file for manual extraction")
                        except Exception as e:
                            logger.error(f"❌ 7z file extraction error: {e}")
                            logger.info("💡 7z file is valid but extraction failed, keeping the file for manual extraction")

                        return True, dst_dir

                    else:
                        logger.error("❌ 7z file validation failed")
                        if attempt < max_download_attempts - 1:
                            logger.warning("💡 File may be corrupted, will retry download...")
                            continue  # Try again
                        else:
                            logger.error("💡 File validation failed after retry, recommend checking network or server")
                            return False, None

                else:
                    logger.error("❌ Download failed")
                    if attempt < max_download_attempts - 1:
                        logger.warning("💡 Will retry download...")
                        continue  # Try again
                    else:
                        return False, None

            except KeyboardInterrupt:
                logger.warning("⏸️  Download interrupted by user")
                return False, None

            except Exception as e:
                logger.error(f"❌ Download error: {e}")
                if attempt < max_download_attempts - 1:
                    logger.warning("💡 Will retry download due to error...")
                    continue  # Try again
                else:
                    logger.error("💡 Download failed after retry. Please check network connection and authentication credentials")
                    return False, None
        return False, None

    def symbolize(
            self,
            content_or_path: str,
            version: str,
            arch: str,
            isBackup: bool = False
    ):
        if not content_or_path:
            raise Exception("Empty content_or_path provided for symbolization.")
        if not version or not version_full_match(version):
            raise Exception("Invalid or unsupported version format. version should be later than 44.0.0.0000")
        version = version.strip()
        if not arch:
            raise Exception("Empty architecture provided.")
        if os.path.exists(content_or_path):
            scan_res: ScanResult = self.scanner.scan_file(content_or_path)
        else:
            scan_res: ScanResult = self.scanner.scan_crash(content_or_path)

        if scan_res:
            if scan_res.crash_info and scan_res.crash_info.get('version'):
                version = scan_res.crash_info.get('version')

        arch: Arch = get_arch(arch) or Arch.osx
        ok, symbol_dir = self.loop.run_until_complete(self.download_symbols(
            version=version,
            arch=arch,
            isBackup=isBackup
        ))
        if not ok:
            raise Exception("Failed to download or validate symbol files.")
        res: list = []
        for thread_block in scan_res.stack_blocks[:10]:
            res.append(self.loop.run_until_complete(self.symbolize_async(thread_block, symbol_dir, arch, scan_res.images_dict)))

        logger.debug('Symbolization process completed')
        return res



