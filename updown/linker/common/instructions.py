class UpDownInstFormat:
    def __init__(self, instruction: str):
        """Create an UpDown instruction

        Args:
            instruction (str): Instruction
        """

        ## Check if variable length instruction with <opcode>
        if instruction.find("<") != -1:
            self._variableLength = True
            ## For now remove the variable length part
            instruction = instruction.split("<")[0].strip()
        opcode = instruction.split()[0].strip()
        operands = instruction.split(opcode)[1].strip().split(",")
        operands = [operand.strip() for operand in operands]

        self._opCode = opcode
        self._operands = operands

        ## Get index of operands that are immediate values
        self._immOperands = [
            i
            for i, _ in enumerate(operands)
            if len(operands) > 0 and operands[i].startswith("$imm")
        ]
        ## Get index of operands that are registers
        self._registerOperands = [
            i
            for i, _ in enumerate(operands)
            if len(operands) > 0 and operands[i].lower().startswith("x")
        ]
        ## TODO: Other encodings here

    @property
    def opcode(self) -> str:
        """Get the opcode of the instruction

        Returns:
            str: Opcode of the instruction
        """
        return self._opCode

    @property
    def operands(self) -> list:
        """Get the operands of the instruction

        Returns:
            list: Operands of the instruction
        """
        return self._operands

    def getRegisterIndexList(self) -> list:
        """Returns the index of the operands that are registers

        Returns:
            list: _description_
        """
        return self._registerOperands

    def getPossibleSymbols(self) -> list:
        """Returns the index of the operands that could be possible symbols

        Returns:
            list: _description_
        """
        return self._immOperands

    def __str__(self) -> str:
        return (
            f"{self.opcode} {','.join(self._operands)} \n"
            f"- OpCode: {self._opCode}\n"
            f"- Operands: {self._operands}\n"
            f"- REG: {self._registerOperands}\n"
            f"- IMM: {self._immOperands}"
        )

    @classmethod
    def readInstructions(cls, inputFile: str) -> dict:
        """Reads the instructions from the input file

        Args:
            inputFile (str): The path to the input file

        Returns:
            list: The list of instructions
        """
        instructions = {}
        try:
            with open(inputFile, "r") as file:
                for line in file:
                    line = line.strip()
                    if len(line) > 0 and line[0] != "#":
                        inst = UpDownInstFormat(line)
                        instructions[inst.opcode] = inst
        except FileNotFoundError:
            print(f"File {inputFile} not found")
            exit(1)

        return instructions
