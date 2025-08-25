#!/usr/bin/env python3
"""
Advanced IPS Converter - Convert JSON .ips crash report to human-readable text format
exactly matching Mac Console output.

This converter produces output that precisely matches the Mac Console application,
including proper formatting, spacing, and symbol information.
"""

import json
import re
from typing import Dict, List, Optional, Union, Any
from MacAutoSymbolizer.src.utilities import safe_read_file


class IPSConverter:
    """Advanced IPS file converter that produces Mac Console-compatible output"""
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.used_images: List[Dict[str, Any]] = []
        self.threads: List[Dict[str, Any]] = []
        
    def convert(self, ips_content: Optional[str] = None, 
                json_file_path: Optional[str] = None) -> str:
        """
        Convert IPS JSON to Mac Console format
        
        Args:
            ips_content: Raw IPS file content as string
            json_file_path: Path to IPS JSON file
            
        Returns:
            Formatted crash report text
        """
        self._load_data(ips_content, json_file_path)
        return self._format_report()
    
    def _load_data(self, ips_content: Optional[str], json_file_path: Optional[str]):
        """Load and parse IPS data"""
        json_content = None
        
        if json_file_path:
            # 使用安全读取文件
            file_content = safe_read_file(json_file_path)
            lines = file_content.splitlines()
            
            # 检查第一行是否包含元数据
            if lines and lines[0].strip().startswith('{"app_name"'):
                # 第一行是元数据，从第二行开始是实际JSON
                json_content = '\n'.join(lines[1:])
            else:
                # 整个文件都是JSON内容
                json_content = file_content
        elif ips_content:
            lines = ips_content.strip().split('\n', 1)
            if len(lines) > 1 and lines[0].startswith('{"app_name"'):
                # Skip metadata line
                json_content = lines[1]
            else:
                json_content = ips_content
        else:
            raise ValueError("No content provided for conversion")
            
        if not json_content:
            raise ValueError("No JSON content found")
            
        try:
            self.data = json.loads(json_content)
            self.used_images = self.data.get('usedImages', [])
            self.threads = self.data.get('threads', [])
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
    
    def _format_report(self) -> str:
        """Format the complete crash report"""
        sections = []
        
        # Header section
        sections.append(self._format_header())
        
        # Exception information
        exception_info = self._format_exception()
        if exception_info:
            sections.append(exception_info + "\n")
        
        # Application specific information
        app_info = self._format_application_specific_info()
        if app_info:
            sections.append(app_info + "\n")
        
        # Application Specific Backtrace
        asi_backtraces = self._format_asi_backtraces()
        if asi_backtraces:
            sections.append(asi_backtraces)
        
        # Thread information
        thread_info = self._format_threads()
        if thread_info:
            sections.append(thread_info)
        
        # Binary images
        binary_info = self._format_binary_images()
        if binary_info:
            sections.append(binary_info)
        
        return '\n\n'.join(sections) + '\n'
    
    def _format_header(self) -> str:
        """Format the crash report header exactly like Mac Console"""
        lines = []
        
        # Header banner
        lines.extend([
            "-------------------------------------",
            "Translated Report (Full Report Below)",
            "-------------------------------------",
            ""
        ])
        
        # Process information
        proc_name = self.data.get('procName', 'Unknown')
        pid = self.data.get('pid', 'Unknown')
        lines.append(f"Process:               {proc_name} [{pid}]")
        
        proc_path = self.data.get('procPath', '')
        if proc_path:
            lines.append(f"Path:                  {proc_path}")
        
        # Bundle information
        bundle_info = self.data.get('bundleInfo', {})
        if bundle_info:
            bundle_id = bundle_info.get('CFBundleIdentifier', '')
            if bundle_id:
                lines.append(f"Identifier:            {bundle_id}")
            
            version = bundle_info.get('CFBundleShortVersionString', '')
            build = bundle_info.get('CFBundleVersion', '')
            if version and build:
                lines.append(f"Version:               {version} ({build})")
        
        # Code type - add "(Native)" for ARM-64
        cpu_type = self.data.get('cpuType', '')
        if cpu_type:
            if cpu_type == 'ARM-64':
                cpu_type = 'ARM-64 (Native)'
            lines.append(f"Code Type:             {cpu_type}")
        
        # Parent process
        parent_proc = self.data.get('parentProc', '')
        parent_pid = self.data.get('parentPid', '')
        if parent_proc and parent_pid:
            lines.append(f"Parent Process:        {parent_proc} [{parent_pid}]")
        
        # User ID
        user_id = self.data.get('userID', '')
        if user_id:
            lines.append(f"User ID:               {user_id}")
        
        lines.append("")
        
        # Date/Time
        capture_time = self.data.get('captureTime', '')
        if capture_time:
            lines.append(f"Date/Time:             {capture_time}")
        
        # OS Version
        os_version = self.data.get('osVersion', {})
        if os_version:
            train = os_version.get('train', '')
            build = os_version.get('build', '')
            if train and build:
                lines.append(f"OS Version:            {train} ({build})")
        
        lines.append("Report Version:        12")
        
        # Anonymous UUID (this is the incident ID)
        incident = self.data.get('incident', '')
        if incident:
            lines.append(f"Anonymous UUID:        {incident}")
        
        lines.append("")
        
        # Sleep/Wake UUID
        sleep_wake_uuid = self.data.get('sleepWakeUUID', '')
        if sleep_wake_uuid:
            lines.append(f"Sleep/Wake UUID:       {sleep_wake_uuid}")
            lines.append("")
        else:
            lines.append("")
        
        # Time information
        uptime = self.data.get('uptime', '')
        wake_time = self.data.get('wakeTime', '')
        if uptime:
            lines.append(f"Time Awake Since Boot: {uptime} seconds")
        if wake_time:
            lines.append(f"Time Since Wake:       {wake_time} seconds")
        
        lines.append("")
        
        # System Integrity Protection
        sip_enabled = self.data.get('sip', 'enabled')  # Default to enabled
        lines.append(f"System Integrity Protection: {sip_enabled}")
        lines.append("")
        
        # Crashed thread information
        faulting_thread = self.data.get('faultingThread')
        if faulting_thread is not None:
            # Find the crashed thread to get its name and queue
            crashed_thread_name = ""
            crashed_thread_queue = ""
            
            if faulting_thread < len(self.threads):
                thread = self.threads[faulting_thread]
                crashed_thread_name = thread.get('name', '')
                crashed_thread_queue = thread.get('queue', '')
            
            crashed_line = f"Crashed Thread:        {faulting_thread}"
            if crashed_thread_name:
                crashed_line += f"  {crashed_thread_name}"
            if crashed_thread_queue:
                crashed_line += f"  Dispatch queue: {crashed_thread_queue}"
            
            lines.append(crashed_line)
        
        return '\n'.join(lines)
    
    def _format_exception(self) -> str:
        """Format exception information exactly like Mac Console"""
        exception_data = self.data.get('exception', {})
        if not exception_data:
            return ""
        
        lines = []
        
        # Exception Type and Signal on same line if both exist
        exc_type = exception_data.get('type', '')
        signal = exception_data.get('signal', '')
        
        if exc_type and signal:
            lines.append(f"Exception Type:        {exc_type} ({signal})")
        elif exc_type:
            lines.append(f"Exception Type:        {exc_type}")
        
        # Exception Codes
        codes = exception_data.get('codes', '')
        if codes:
            lines.append(f"Exception Codes:       {codes}")
        
        # Termination information
        termination = self.data.get('termination', {})
        if termination:
            namespace = termination.get('namespace', '')
            code = termination.get('code', '')
            indicator = termination.get('indicator', '')
            by_proc = termination.get('byProc', '')
            by_pid = termination.get('byPid', '')
            
            if namespace and code is not None and indicator:
                lines.append(f"Termination Reason:    Namespace {namespace}, Code {code} {indicator}")
            
            if by_proc and by_pid:
                lines.append(f"Terminating Process:   {by_proc} [{by_pid}]")
        
        return '\n'.join(lines)
    
    def _format_application_specific_info(self) -> str:
        """Format application specific information"""
        # Look for termination reason or other app-specific info
        termination = self.data.get('termination', {})
        if termination:
            namespace = termination.get('namespace', '')
            code = termination.get('code', '')
            
            if namespace == 'SIGNAL' and code == 6:  # SIGABRT
                return "Application Specific Information:\nabort() called"
        
        # Check exception for SIGABRT signal
        exception = self.data.get('exception', {})
        if exception:
            signal = exception.get('signal', '')
            if signal == 'SIGABRT':
                return "Application Specific Information:\nabort() called"
        
        # Check for other application specific info
        app_specific = self.data.get('applicationSpecificInformation', '')
        if app_specific:
            return f"Application Specific Information:\n{app_specific}"
        
        return ""
    
    def _format_asi_backtraces(self) -> str:
        """Format Application Specific Backtrace information"""
        asi_backtraces = self.data.get('asiBacktraces', [])
        if not asi_backtraces:
            return ""
        
        lines = []
        for i, backtrace in enumerate(asi_backtraces):
            lines.append(f"Application Specific Backtrace {i}:")
            if isinstance(backtrace, str):
                # Split the backtrace string into individual lines
                backtrace_lines = backtrace.split('\n')
                for line in backtrace_lines:
                    if line.strip():  # Skip empty lines
                        lines.append(line)
            lines.append("")  # Empty line after each backtrace
        
        return '\n'.join(lines)
    
    def _format_threads(self) -> str:
        """Format thread information exactly like Mac Console"""
        if not self.threads:
            return ""
        
        formatted_threads = []
        faulting_thread = self.data.get('faultingThread')
        
        for thread_idx, thread in enumerate(self.threads):
            thread_lines = []
            
            # Thread header
            thread_header = f"Thread {thread_idx}"
            
            # Check if this is the crashed thread
            if thread_idx == faulting_thread:
                thread_header += " Crashed"
            
            # Add thread name if available
            thread_name = thread.get('name', '')
            if thread_name:
                thread_header += f":: {thread_name}"
            
            # Add dispatch queue if available
            queue = thread.get('queue', '')
            if queue:
                thread_header += f" Dispatch queue: {queue}"
            
            # If no additional info, add colon at the end
            if not thread_name and not queue and thread_idx != faulting_thread:
                thread_header += ":"
            
            thread_lines.append(thread_header)
            
            # Format stack frames
            frames = thread.get('frames', [])
            for frame_idx, frame in enumerate(frames):
                frame_line = self._format_frame(frame_idx, frame)
                thread_lines.append(frame_line)
            
            formatted_threads.append('\n'.join(thread_lines))
        
        return '\n\n'.join(formatted_threads)
    
    def _format_frame(self, frame_idx: int, frame: Dict[str, Any]) -> str:
        """Format a single stack frame exactly like Mac Console"""
        # Get frame information
        image_index = frame.get('imageIndex')
        image_offset = frame.get('imageOffset', 0)
        symbol = frame.get('symbol', '')
        symbol_location = frame.get('symbolLocation', 0)
        
        # Get image information
        image_name = ''
        image_base = 0
        if image_index is not None and image_index < len(self.used_images):
            image_info = self.used_images[image_index]
            image_name = image_info.get('name', '')
            image_base = image_info.get('base', 0)
        
        # Format frame number (left-aligned, followed by spaces)
        frame_num = f"{frame_idx}"
        
        # Format image name (left-aligned in 30-character field)
        image_col = f"{image_name:<30}"
        
        # Calculate absolute address
        if isinstance(image_offset, int) and isinstance(image_base, int):
            absolute_addr = image_base + image_offset
            addr_hex = f"0x{absolute_addr:x}"
        else:
            addr_hex = str(image_offset)
        
        # Determine if this is a system library
        is_system = self._is_system_library(image_name)
        
        # Format the frame line based on whether we have symbol information
        if symbol:
            if symbol_location and symbol_location > 0:
                symbol_part = f"{symbol} + {symbol_location}"
            else:
                symbol_part = symbol
            
            frame_line = f"{frame_num}   {image_col}\t       {addr_hex} {symbol_part}"
        else:
            # No symbol - show base + offset for non-system libraries
            if not is_system and isinstance(image_base, int) and isinstance(image_offset, int):
                base_hex = f"0x{image_base:x}"
                frame_line = f"{frame_num}   {image_col}\t       {addr_hex} {base_hex} + {image_offset}"
            else:
                frame_line = f"{frame_num}   {image_col}\t       {addr_hex}"
        
        return frame_line
    
    def _is_system_library(self, image_name: str) -> bool:
        """Determine if an image is a system library"""
        if not image_name:
            return False
        
        system_patterns = [
            'libsystem_',
            'libc++',
            'libobjc',
            'libdispatch',
            'CoreFoundation',
            'AppKit',
            'HIToolbox',
            'dyld',
            'Foundation',
            'CFNetwork',
            'JavaScriptCore',
            'SkyLight',
            'LaunchServices',
            'MetalPerformanceShadersGraph'
        ]
        
        return any(image_name.startswith(pattern) for pattern in system_patterns)
    
    def _format_binary_images(self) -> str:
        """Format binary images section exactly like Mac Console"""
        if not self.used_images:
            return ""
        
        lines = ["Binary Images:"]
        
        for image in self.used_images:
            base = image.get('base', 0)
            size = image.get('size', 0)
            name = image.get('name', '')
            uuid = image.get('uuid', '').lower()
            path = image.get('path', '')
            
            # Calculate end address
            end_address = base + size - 1 if size > 0 else base
            
            # Format addresses
            base_hex = f"0x{base:x}" if base else "0x0"
            end_hex = f"0x{end_address:x}" if end_address else "0x0"
            
            # Pad addresses for alignment
            base_padded = f"{base_hex:>16}"
            end_padded = f"{end_hex:>16}"
            
            # Get version information
            version_info = ""
            if 'CFBundleShortVersionString' in image:
                version_info = f" ({image['CFBundleShortVersionString']})"
            elif 'CFBundleVersion' in image:
                version_info = f" ({image['CFBundleVersion']})"
            
            # Get identifier
            identifier = image.get('CFBundleIdentifier', name)
            if not identifier:
                identifier = "*"
            
            # Format UUID
            if uuid and uuid != "00000000-0000-0000-0000-000000000000":
                uuid_formatted = f"<{uuid}>"
            else:
                uuid_formatted = "<*>"
            
            # Build the line
            image_line = f"{base_padded} -        {end_padded} {identifier}{version_info} {uuid_formatted} {path}"
            lines.append(image_line)
        
        return '\n'.join(lines)


def convert_ips_file(input_file: str, output_file: Optional[str] = None) -> str:
    """
    Convenient function to convert IPS file
    
    Args:
        input_file: Path to input IPS JSON file
        output_file: Optional path to output text file
        
    Returns:
        Formatted crash report text
    """
    converter = IPSConverter()
    result = converter.convert(json_file_path=input_file)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"Converted crash report saved to: {output_file}")
    
    return result


if __name__ == "__main__":
    input_file = 'examples/crash_files/Webex Relay-2025-08-20-145611.ips'
    output_file = 'examples/crash_files/Webex Relay-2025-08-20-145611_ips.txt'

    try:
        convert_ips_file(input_file, output_file)
        print("Conversion completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
