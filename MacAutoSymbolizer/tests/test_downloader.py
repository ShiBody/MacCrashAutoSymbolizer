"""
高级下载器测试脚本
用于测试各种下载场景和功能
"""

import asyncio
import os
import tempfile
import time
from unittest.mock import Mock
from MacAutoSymbolizer.src.advanced_downloader import AdvancedDownloader, SevenZipValidator, DownloadProgress


class DownloadTester:
    """下载器测试类"""

    def __init__(self):
        self.test_results = []

    async def test_basic_download(self):
        """测试基本下载功能"""
        print("🧪 测试基本下载功能...")

        downloader = AdvancedDownloader(
            chunk_size=512 * 1024,  # 512KB for testing
            max_concurrent_chunks=4
        )

        # 使用一个小文件进行测试
        test_url = "https://httpbin.org/bytes/1024"  # 1KB test file

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            temp_path = tmp_file.name

        try:
            start_time = time.time()
            success = await downloader.download_file(test_url, temp_path)
            end_time = time.time()

            if success and os.path.exists(temp_path):
                file_size = os.path.getsize(temp_path)
                print(f"  ✅ 基本下载测试通过 - 文件大小: {file_size} bytes, 耗时: {end_time - start_time:.2f}s")
                self.test_results.append(("基本下载", True, f"{file_size} bytes"))
            else:
                print("  ❌ 基本下载测试失败")
                self.test_results.append(("基本下载", False, "下载失败"))

        except Exception as e:
            print(f"  ❌ 基本下载测试异常: {e}")
            self.test_results.append(("基本下载", False, str(e)))
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    async def test_progress_callback(self):
        """测试进度回调功能"""
        print("🧪 测试进度回调功能...")

        progress_calls = []

        def test_progress_callback(progress: DownloadProgress):
            progress_calls.append(progress.progress_percent)

        downloader = AdvancedDownloader(
            chunk_size=256 * 1024,  # 256KB
            max_concurrent_chunks=2,
            progress_callback=test_progress_callback
        )

        test_url = "https://httpbin.org/bytes/2048"  # 2KB test file

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            temp_path = tmp_file.name

        try:
            success = await downloader.download_file(test_url, temp_path)

            if success and len(progress_calls) > 0:
                max_progress = max(progress_calls)
                print(f"  ✅ 进度回调测试通过 - 回调次数: {len(progress_calls)}, 最大进度: {max_progress:.1f}%")
                self.test_results.append(("进度回调", True, f"{len(progress_calls)} 次回调"))
            else:
                print("  ❌ 进度回调测试失败")
                self.test_results.append(("进度回调", False, "无回调或下载失败"))

        except Exception as e:
            print(f"  ❌ 进度回调测试异常: {e}")
            self.test_results.append(("进度回调", False, str(e)))
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    async def test_file_info_retrieval(self):
        """测试文件信息获取"""
        print("🧪 测试文件信息获取...")

        downloader = AdvancedDownloader()

        try:
            # 测试一个已知大小的文件
            test_url = "https://httpbin.org/bytes/5120"  # 5KB
            file_size, supports_range = await downloader.get_file_info(test_url)

            if file_size > 0:
                print(f"  ✅ 文件信息获取测试通过 - 大小: {file_size} bytes, 支持Range: {supports_range}")
                self.test_results.append(("文件信息获取", True, f"{file_size} bytes"))
            else:
                print("  ❌ 文件信息获取测试失败 - 无法获取文件大小")
                self.test_results.append(("文件信息获取", False, "无法获取大小"))

        except Exception as e:
            print(f"  ❌ 文件信息获取测试异常: {e}")
            self.test_results.append(("文件信息获取", False, str(e)))

    def test_7z_validator(self):
        """测试7z验证器"""
        print("🧪 测试7z验证器...")

        validator = SevenZipValidator()

        # 创建一个假的7z文件头进行测试
        with tempfile.NamedTemporaryFile(delete=False, suffix='.7z') as tmp_file:
            # 写入7z文件头
            tmp_file.write(b'\x37\x7A\xBC\xAF\x27\x1C')
            tmp_file.write(b'fake 7z content for testing')
            temp_path = tmp_file.name

        try:
            # 测试基本头部验证
            is_valid = validator.validate_7z_file(temp_path)

            if is_valid:
                print("  ✅ 7z验证器测试通过 - 文件头验证正确")
                self.test_results.append(("7z验证器", True, "头部验证通过"))
            else:
                print("  ❌ 7z验证器测试失败 - 文件头验证失败")
                self.test_results.append(("7z验证器", False, "头部验证失败"))

            # 测试哈希计算
            hash_value = validator.calculate_file_hash(temp_path, 'md5')
            if hash_value and len(hash_value) == 32:  # MD5 is 32 characters
                print(f"  ✅ 哈希计算测试通过 - MD5: {hash_value[:8]}...")
                self.test_results.append(("哈希计算", True, f"MD5: {hash_value[:8]}..."))
            else:
                print("  ❌ 哈希计算测试失败")
                self.test_results.append(("哈希计算", False, "哈希计算失败"))

        except Exception as e:
            print(f"  ❌ 7z验证器测试异常: {e}")
            self.test_results.append(("7z验证器", False, str(e)))
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    async def test_error_handling(self):
        """测试错误处理"""
        print("🧪 测试错误处理...")

        downloader = AdvancedDownloader(
            max_retries=2,
            timeout=5
        )

        # 测试无效URL
        invalid_url = "https://this-domain-does-not-exist-12345.com/file.zip"

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            temp_path = tmp_file.name

        try:
            success = await downloader.download_file(invalid_url, temp_path)

            if not success:
                print("  ✅ 错误处理测试通过 - 正确处理了无效URL")
                self.test_results.append(("错误处理", True, "正确处理无效URL"))
            else:
                print("  ❌ 错误处理测试失败 - 应该失败但成功了")
                self.test_results.append(("错误处理", False, "未正确处理错误"))

        except Exception as e:
            print(f"  ✅ 错误处理测试通过 - 捕获异常: {type(e).__name__}")
            self.test_results.append(("错误处理", True, f"捕获异常: {type(e).__name__}"))
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_chunk_creation(self):
        """测试分片创建"""
        print("🧪 测试分片创建...")

        downloader = AdvancedDownloader(chunk_size=1024)  # 1KB chunks

        try:
            # 测试5KB文件的分片
            file_size = 5120  # 5KB
            chunks = downloader._create_chunks(file_size)

            expected_chunks = 5  # 5KB / 1KB = 5 chunks
            total_size = sum(chunk.size for chunk in chunks)

            if len(chunks) == expected_chunks and total_size == file_size:
                print(f"  ✅ 分片创建测试通过 - 创建了 {len(chunks)} 个分片，总大小: {total_size} bytes")
                self.test_results.append(("分片创建", True, f"{len(chunks)} 个分片"))
            else:
                print(f"  ❌ 分片创建测试失败 - 期望 {expected_chunks} 个分片，实际 {len(chunks)} 个")
                self.test_results.append(("分片创建", False, f"分片数量错误"))

        except Exception as e:
            print(f"  ❌ 分片创建测试异常: {e}")
            self.test_results.append(("分片创建", False, str(e)))

    def test_size_formatting(self):
        """测试大小格式化"""
        print("🧪 测试大小格式化...")

        try:
            test_cases = [
                (0, "0B"),
                (1024, "1.0 KB"),
                (1024 * 1024, "1.0 MB"),
                (1024 * 1024 * 1024, "1.0 GB"),
                (1536, "1.5 KB"),  # 1.5KB
            ]

            all_passed = True
            for size_bytes, expected in test_cases:
                result = AdvancedDownloader._format_size(size_bytes)
                if result != expected:
                    print(f"  ❌ 大小格式化失败: {size_bytes} -> 期望 '{expected}', 实际 '{result}'")
                    all_passed = False

            if all_passed:
                print("  ✅ 大小格式化测试通过")
                self.test_results.append(("大小格式化", True, "所有测试用例通过"))
            else:
                self.test_results.append(("大小格式化", False, "部分测试用例失败"))

        except Exception as e:
            print(f"  ❌ 大小格式化测试异常: {e}")
            self.test_results.append(("大小格式化", False, str(e)))

    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始运行下载器测试套件")
        print("=" * 60)

        # 运行所有测试
        await self.test_basic_download()
        await self.test_progress_callback()
        await self.test_file_info_retrieval()
        self.test_7z_validator()
        await self.test_error_handling()
        self.test_chunk_creation()
        self.test_size_formatting()

        # 显示测试结果汇总
        print("\n" + "=" * 60)
        print("📊 测试结果汇总:")

        passed = 0
        failed = 0

        for test_name, success, details in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status} {test_name:<15} - {details}")

            if success:
                passed += 1
            else:
                failed += 1

        total = passed + failed
        print(f"\n总计: {total} 个测试, {passed} 个通过, {failed} 个失败")

        if failed == 0:
            print("🎉 所有测试通过!")
        else:
            print(f"⚠️  有 {failed} 个测试失败，请检查相关功能")

        return failed == 0


async def main():
    """主测试函数"""
    print("🧪 高级文件下载器 - 测试套件")
    print("=" * 60)

    tester = DownloadTester()

    try:
        success = await tester.run_all_tests()

        if success:
            print("\n🎯 测试套件执行完成 - 所有功能正常!")
        else:
            print("\n⚠️  测试套件执行完成 - 发现问题，请检查失败的测试")

    except KeyboardInterrupt:
        print("\n\n👋 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试套件异常: {e}")


if __name__ == "__main__":
    asyncio.run(main())
