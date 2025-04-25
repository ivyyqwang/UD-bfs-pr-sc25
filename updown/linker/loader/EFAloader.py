## EFAloader.py
## This represents the loader into EFA emulator. It takes a linkableModule that has already been fully
## linked and loads it into the EFA emulator by calling the right methods for each state, transition and action

from linker.LinkableModule import LinkableModule

class EFAloader:
    def __init__(self, efa: "EFA"):
        self.efa = efa
        pass

    def relocateStaticData(self, baseAddress: int):
        ## Iterate over the static data, assign a value, and
        ## replace all the references with the value
        pass

    def load(self, linkableModule: LinkableModule):
        ## Iterate over the sates and create all the states

        ## iterate over the transitions and create all the transitions
        ## with its corresponding actions

        ## iterate over the shared blocks and create all the shared blocks

        ## iterate over the actions and create all the actions

        pass


def efaMain():
    pass