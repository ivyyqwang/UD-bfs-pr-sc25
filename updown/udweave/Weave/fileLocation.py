import os
import re

from typing import Union


class FileContent:
    def __init__(self, fileContent: str):
        self._fileContent = fileContent
        self._files = {}
        numLines = len(self._fileContent.split("\n"))

        # Example of a preprocessor line:
        # 1 "UDKVMSR.udwh" 1
        # The format is
        # line_number "file_name" flag
        # flag = 1 indicates the start of a new file
        # flag = 2 indicates returning to a file after a #include
        # flag = 3 indicates the following text comes from a system header file
        # flag = 4 indicates that the following text should be treated as being wrapped in an implicit extern "C" block

        curFileName = None
        curLineNumber = 0
        count = 0

        for line in self._fileContent.split("\n"):
            new_line = {}
            if len(line) > 1 and line[0] == "#":
                vals = line.split()
                if len(vals) > 3 and (vals[3] == "1" or vals[3] == "2"):
                    curFileName = vals[2].replace('"', "")
                if len(vals) > 2:
                    curLineNumber = int(vals[1])
                count += len(line) + 1
                continue
            new_line["content"] = line
            new_line["file_name"] = curFileName
            new_line["line_number"] = curLineNumber
            new_line["firstLoc"] = count
            curLineNumber += 1
            count += len(line) + 1
            if curFileName not in self._files:
                self._files[curFileName] = []
            while len(self._files[curFileName]) <= curLineNumber:
                self._files[curFileName].append({"content": "", "file_name": "", "line_number": len(self._files[curFileName]), "firstLoc": 0})
            self._files[curFileName][curLineNumber] = new_line

    def getFileContent(self):
        """Returns the file content"""
        return self._fileContent

    def getLine(self, file: str, lineNum: int) -> dict:
        """Returns the line of the given file"""
        if file in self._files:
            if lineNum < len(self._files[file]):
                return self._files[file][lineNum]
        return {"content": "", "file_name": "", "line_number": lineNum, "firstLoc": 0}


class FileManager:
    def __init__(self, fileName: str, fileContent: FileContent):
        self._fileName = fileName
        self._fileContent = fileContent

    def getFileContent(self) -> FileContent:
        """Returns the file content"""
        return self._fileContent

    def getFileName(self, fullPath: bool = False):
        """Returns the file name"""
        return self._fileName if fullPath else os.path.basename(self._fileName)

    def getFileNameLoc(self, line: int, cur: int = None, fullPath: bool = True):
        """Print the filename with line and column number

        Using the cursor (cur), calculate the column, and based on the column
        create a string that contains the order: filename:lineNumber:columnNumber

        Args:
            line (int): _description_
            cur (int): _description_

        Returns:
            _type_: _description_
        """
        lineDict = self._fileContent.getLine(self._fileName, line)
        col = cur - lineDict["firstLoc"] + 1 if cur is not None else 0
        name = self._fileName if fullPath else os.path.basename(self._fileName)

        return f"{name}:{line}:{col}" if cur is not None else f"{name}:{line}"

    def getLine(self, line: int) -> str:
        """Returns a dictionary for the given line number

        It calculates the offset from the original source code to the one with the preprocessor

        Args:
            line (int): Line number to return

        Returns:
            str: Line content
        """
        return self._fileContent.getLine(self._fileName, line)

    def getLineWithCursor(self, line: int, cur: int, indent: int = 0):
        """Print the line where the error is reported with a cursor below

            This is to improve error handling
        Args:
            line (int): Line where error occurred
            cur (int): location in file where error happened
        """
        lineDict = self._fileContent.getLine(self._fileName, line)
        lineCont = lineDict["content"]
        col = cur - lineDict["firstLoc"]
        lenWord = len(lineCont[col:].split(" ")[0])
        retStr = f"{' '*indent}{lineCont}\n"
        retStr += f"{' '*indent}{' '*col}{'^'*lenWord}"
        return retStr


class FileLocation:
    def __init__(self, line: int, loc: int, fileMgr: FileManager = None):
        self._line = line
        self._loc = loc
        self._fileMgr = fileMgr

    def __str__(self):
        return f"({self._fileMgr.getFileNameLoc(self._line, self._loc, False)})"

    def getLineHighlighted(self, indent: int = 0):
        return self._fileMgr.getLineWithCursor(self._line, self._loc, indent)

    def getLine(self):
        return (
            self._fileMgr.getFileNameLoc(self._line)
            + " => "
            + self._fileMgr.getLine(self._line)["content"]
        )

    def sameLine(self, other: Union["FileLocation", None]):
        if other is None:
            return False
        return self._fileMgr == other._fileMgr and self._line == other._line

    @property
    def fileName(self):
        return self._fileMgr.getFileName()

    @property
    def line(self):
        return self._line
