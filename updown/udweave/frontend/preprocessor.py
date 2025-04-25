from __future__ import annotations
from Weave.debug import debugMsg, errorMsg

import subprocess
import os


class WeavePreprocessor:
    def __init__(self, path: str, input_file: str, args: list[str]):
        self.path = path
        self.input_file = input_file
        self.include_paths = []
        self.args = args
        pass

    def setIncludePaths(self, paths: list):
        self.include_paths = paths
        for p in self.include_paths:
            if not os.path.isdir(p):
                errorMsg(f"Include path {p} not found")

    def preprocess(self) -> str:
        debugMsg(1, "Preprocessing source code with " + self.path + " ...")

        command = [
            self.path,
            "-undef",
            "-nostdinc",
            "-CC",
            "-I./",
            "-D__udweave"]
        command.extend(self.args)
        command.append(self.input_file)

        if not self.isPreprocessorClang():
            command.append("-fno-canonical-system-headers")

        command[-1:-1] = [f"-I{p}" for p in self.include_paths]
        p = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        debugMsg(1, "Preprocessing command: " + " ".join(command))
        out, err = p.communicate()
        if p.returncode != 0:
            errorMsg("Preprocessor error:\n" + err.decode("utf-8"))
        source = out.decode("utf-8")
        debugMsg(1, "Preprocessing done.")

        return source

    def isPreprocessorClang(self) -> bool:
        p = subprocess.Popen([self.path, "--version"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
            errorMsg("Preprocessor error:\n" + err.decode("utf-8"))
        if "clang" in out.decode("utf-8").lower():
            debugMsg(1, "Clang detected")
            return True
        return False
