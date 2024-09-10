from setuptools import setup

setup(
    name='MacCrashAutoSymbolizer',
    version='1.0.0',
    packages=['MacAutoSymbolizer', 'MacAutoSymbolizer.tools', 'MacAutoSymbolizer.tools.libMap', 'MacAutoSymbolizer.tools.scanner', 'MacAutoSymbolizer.tools.symbolize', 'MacAutoSymbolizer.tools.downloader', 'MacAutoSymbolizer.mac_symbolize'],
    url='https://github.com/ShiBody/MacCrashAutoSymbolizer',
    license='MIT',
    author='CindyShi',
    author_email='body1992218@gmail.com',
    description='',
    install_requires=[
        'aiofiles==23.2.1',
        'aiohttp==3.9.5',
        'aiosignal==1.3.1',
        'async-timeout==4.0.3',
        'attrs==23.2.0',
        'frozenlist==1.4.1',
        'idna==3.7',
        'multidict==6.0.5',
        'uvloop==0.19.0',
        'yarl==1.9.4',
    ],
    python_requires=">=3.9"
)
