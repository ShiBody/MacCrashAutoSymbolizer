import asyncio.subprocess
import asyncio


__author__  = "Cindy Shi <body1992218@gmail.com>"
__status__  = "production"
__version__ = "1.0"
__date__    = "3 May 2024"


class SubProcessCmd:
    @classmethod
    def execute(cls, cmd: str, args_list: list, **kwargs):
        process = cls(cmd, **kwargs)
        process.result = asyncio.run(process.start(args_list))
        return process

    def __init__(self, cmd:str, **kwargs):
        self._program = cmd
        self._kwargs = kwargs

        self._stdin = kwargs.pop(r'stdin') if r'stdin' in kwargs else None
        self._stdout = kwargs.pop(r'stdout') if r'stdout' in kwargs else asyncio.subprocess.PIPE
        self._stderr = kwargs.pop(r'stderr') if r'stderr' in kwargs else asyncio.subprocess.PIPE
        self._timeout = kwargs.pop(r'timeout') if r'timeout' in kwargs else None

    @property
    def stdin(self):
        return self._stdin

    @property
    def stdout(self):
        return self._stdout

    @property
    def stderr(self):
        return self._stderr

    async def cmd(self, *args):
        process = await asyncio.create_subprocess_exec(
            self._program,
            *args,
            stdin=self._stdin,
            stdout=self._stdout,
            stderr=self._stderr,
            **self._kwargs
        )
        stdout, stderr = await process.communicate()
        return process.returncode, stdout.decode(), stderr.decode()

    async def start(self, args_list):
        tasks = [self.cmd(*x) for x in args_list]
        return await asyncio.gather(*tasks)
