from MacAutoSymbolizer.src.ips_converter import convert_ips_json_to_text
import sys


if __name__ == "__main__":
    try:
        input_path = 'examples/crash_files/Webex-2025-08-12-113051.ips'
        output_path = 'examples/crash_files/Webex-2025-08-12-113051_ips.txt'
        result = convert_ips_json_to_text(
            json_file_path=input_path,
            output_file_path=output_path
        )
        if not output_path:
            print(result)
    except Exception as e:
        print(f"Error: {e}")
