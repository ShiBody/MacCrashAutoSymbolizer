#!/usr/bin/env python3
"""
Example usage of the new advanced IPS converter

This example demonstrates how to use the IPSConverter class to convert
Mac crash reports from JSON format to human-readable text format
exactly matching Mac Console output.
"""

import sys
import os

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'MacAutoSymbolizer', 'src'))

from ips_converter_new import IPSConverter, convert_ips_file


def example_basic_usage():
    """Basic example of converting an IPS file"""
    print("=== Basic Usage Example ===")
    
    # Method 1: Using the convenience function
    input_file = "crash_files/example.ips"
    output_file = "converted_crash_report.txt"
    
    try:
        result = convert_ips_file(input_file, output_file)
        print(f"✅ Successfully converted {input_file} to {output_file}")
        
        # Display first few lines
        lines = result.split('\n')
        print("\nFirst 10 lines of output:")
        for i, line in enumerate(lines[:10]):
            print(f"{i+1:2}: {line}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def example_advanced_usage():
    """Advanced example using the IPSConverter class directly"""
    print("\n=== Advanced Usage Example ===")
    
    # Method 2: Using the IPSConverter class directly
    converter = IPSConverter()
    
    input_file = "crash_files/example.ips"
    
    try:
        # Convert the file
        result = converter.convert(json_file_path=input_file)
        
        # Save to file manually
        output_file = "advanced_converted_report.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        
        print(f"✅ Successfully converted using IPSConverter class")
        print(f"📄 Output saved to: {output_file}")
        
        # Show some statistics
        lines = result.split('\n')
        threads_count = len([line for line in lines if line.startswith('Thread ')])
        binary_images_count = len([line for line in lines if '0x' in line and ' - ' in line])
        
        print(f"📊 Statistics:")
        print(f"   Total lines: {len(lines)}")
        print(f"   Threads: {threads_count}")
        print(f"   Binary images: {binary_images_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_string_input():
    """Example of converting from string input"""
    print("\n=== String Input Example ===")
    
    # Read file content as string
    input_file = "crash_files/example.ips"
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            ips_content = f.read()
        
        # Convert from string
        converter = IPSConverter()
        result = converter.convert(ips_content=ips_content)
        
        print(f"✅ Successfully converted from string input")
        print(f"📏 Input size: {len(ips_content)} characters")
        print(f"📏 Output size: {len(result)} characters")
        
        # Show header section only
        lines = result.split('\n')
        header_end = next((i for i, line in enumerate(lines) if line.startswith('Thread')), 20)
        
        print(f"\nHeader section (first {header_end} lines):")
        for i, line in enumerate(lines[:header_end]):
            print(f"{i+1:2}: {line}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🚀 IPS Converter New - Example Usage")
    print("=====================================")
    
    # Change to examples directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Run examples
    example_basic_usage()
    example_advanced_usage()
    example_string_input()
    
    print("\n✨ All examples completed!")
    print("\nGenerated files:")
    print("  - converted_crash_report.txt")
    print("  - advanced_converted_report.txt")
    
    print("\n💡 Tips:")
    print("  - The converter produces output identical to Mac Console")
    print("  - It supports both file paths and string input")
    print("  - Error handling provides detailed feedback")
    print("  - The output format includes proper spacing and symbols")
