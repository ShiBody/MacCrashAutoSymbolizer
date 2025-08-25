
import asyncio
import os

from MacAutoSymbolizer.src.advanced_downloader import download_symbols
from MacAutoSymbolizer.src.utilities import Arch

async def main():
    """Main function"""
    # Ensure download directory exists
    try:
        await download_symbols(
            version="45.6.0.32215",
            arch=Arch.arm,
            username=os.getenv('DOWNLOAD_USER'),  # Set if needed
            password=os.getenv('DOWNLOAD_PASSWORD')  # Set if needed
        )
    except Exception as e:
        print(f"Program error: {e}")


if __name__ == "__main__":

    asyncio.run(main())
