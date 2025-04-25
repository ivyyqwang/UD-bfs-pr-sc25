import os, sys
import math
#sys.path.append(f"{os.getcwd()}/../efas/")
from EFA_v2 import *
from isa_encodings import *

INPUT_TERM_OFFSET = 0 
INPUT_TERM_MAX = 60
SB_REFILL_OFFSET = INPUT_TERM_MAX + 1
SB_REFILL_MAX = 10


general_purpose_register_enc = {
    "X16": "10000",
    "X17": "10001",
    "X18": "10010",
    "X19": "10011",
    "X20": "10100",
    "X21": "10101",
    "X22": "10110",
    "X23": "10111",
    "X24": "11000",
    "X25": "11001",
    "X26": "11010",
    "X27": "11011",
    "X28": "11100",
    "X29": "11101",
    "X30": "11110",
    "X31": "11111",
    "UDPR_0": "10000",
    "UDPR_1": "10001",
    "UDPR_2": "10010",
    "UDPR_3": "10011",
    "UDPR_4": "10100",
    "UDPR_5": "10101",
    "UDPR_6": "10110",
    "UDPR_7": "10111",
    "UDPR_8": "11000",
    "UDPR_9": "11001",
    "UDPR_10": "11010",
    "UDPR_11": "11011",
    "UDPR_12": "11100",
    "UDPR_13": "11101",
    "UDPR_14": "11110",
    "UDPR_15": "11111",
}

class MemoryManager:
    def __init__(self, word_count):
        self.word_count = word_count
        self.mem_bitmap = [0] * word_count  # Initialize memory usage bitmap
        self.block_bitmap = [0] * word_count  # Initialize block bitmap
        self.memory = [""] * word_count

    
    def print_block_bitmap(self, init_address):
        printing=[]
        for i in range (self.word_count):
            if self.block_bitmap[i] == 1:
                printing.append((init_address + (i<<2)) )
        print(f"block_bitmap: {printing}")

    def print_mem_bitmap(self, init_address):
        printing=[]
        for i in range (self.word_count):
            if self.mem_bitmap[i] == 1:
                printing.append((init_address + (i<<2)) )
        print(f"mem_bitmap: {printing}")

    def set_memory(self, address, value):
        address = address & 0xFFF
        if 0 <= address < self.word_count:
            self.memory[address] = value
        else:
            raise ValueError("Invalid memory address")

    def get_memory(self, address):
        address = address & 0xFFF
        if 0 <= address < self.word_count:
            return self.memory[address]
        else:
            raise ValueError("Invalid memory address")

    def is_allocation_valid(self, block_start, block_end):
        block_start = block_start & 0xFFF
        block_end = block_end & 0xFFF
        for i in range(block_start, block_end):
            if self.mem_bitmap[i] & self.block_bitmap[i] != 0:
                # An overlap is detected, indicating an invalid allocation
                return False
        return True
    
    def reset_block_bitmap(self):
        self.block_bitmap = [0] * self.word_count
    
    def set_block_bitmap(self, addr):
        addr = addr & 0xFFF
        self.block_bitmap[addr] = 1

    def set_memory_bitmap(self,start_addr,end_addr):
        start_addr = start_addr & 0xFFF
        end_addr = end_addr & 0xFFF
        if self.is_allocation_valid(start_addr, end_addr):
            for i in range (start_addr,end_addr):
                if (self.block_bitmap[i] == 1):
                    self.mem_bitmap[i] = 1
        else:
            return False

    def shift_block_bitmap(self, shift_distance, start_addr, end_addr):
        start_addr = start_addr & 0xFFF
        end_addr = end_addr & 0xFFF
        if shift_distance < 0:
            raise ValueError("Shift distance must be non-negative.")
        if shift_distance >= self.word_count:
            raise ValueError("Shift distance exceeds word count.")

        new_block_bitmap = [0] * self.word_count

        for i in range(start_addr, end_addr - shift_distance):
            new_block_bitmap[i + shift_distance] = self.block_bitmap[i]

        self.block_bitmap = new_block_bitmap

    def find_consecutive_inst(self):
        start = None
        length = 0
        consecutive_blocks = []

        for i, bit in enumerate(self.mem_bitmap):
            if bit == 1:
                if start is None:
                    start = i
                length += 1
            else:
                if start is not None:
                    consecutive_blocks.append((start, length))
                    start = None
                    length = 0

        # Check for consecutive 1s at the end of the mem_bitmap
        if start is not None:
            consecutive_blocks.append((start, length))

        return consecutive_blocks


## compact to instruction word
##   takes a list of strings
##   produces a 32-bit binary word
def pack(fields):
    instruction_word = ""
    for f in fields:
    #    print(f"field: {f}")
        instruction_word = instruction_word + f
    if len(instruction_word)==32:
        return instruction_word
    else:
        print("Instruction word error: ", fields)
        return ""

def pack_print(fields):
    instruction_word = ""
    for f in fields:
    #    print(f"field: {f}")
        instruction_word = instruction_word + f
    if len(instruction_word) % 32 == 0:
        return instruction_word
    else:
        print("Instruction word error: ", fields)
        return ""

# assign an EFA id to each EFA states (non-EFA states id will remain UNDEFINED)
def color_EFAs(efa):
    efa_counter = 0
    init_state = efa.states[efa.init_state_id[0]]
    #traverse each non-event-driven destination state of the initial state
    for idx, tr in enumerate(init_state.trans):
        if tr.dst.state_id != efa.init_state_id[0]: #TODO: make sure this condition identifies the states that drives events in all cases
            if tr.dst.marked == 0:
                traversed_states = []
                traversed_states.append(tr.dst)
                tr.dst.marked = 1
                traversed_states = traverse_EFA_states(tr.dst,traversed_states)
                #print(f'the traversed size is: {len(traversed_states)}')
                has_color, color = states_color_check(traversed_states)
                if has_color:
                    color_remaining_states(traversed_states, color)
                else:
                    color_states(traversed_states, efa_counter)
                    efa_counter = efa_counter + 1
        #unmark all states
        for state in efa.states:
            state.marked = 0

    return efa_counter

def traverse_EFA_states(state,state_list):
    for tr in state.trans:
        if tr.dst.marked == 0:
            state_list.append(tr.dst)
            tr.dst.marked = 1
            state_list = traverse_EFA_states(tr.dst , state_list)
            if tr.anno_type == "eventCarry":
                sys.exit("a transition from an EFA state to a state driving events is illigal!!!")
    return state_list

#checked whether any of the states in list are colored (i.e. assigned a EFA ID) and returns the flag and the EFA_id that was found
def states_color_check(traversed_states):
    for state in traversed_states:
        if state.EFA_id != UNDEFINED :
            return True , state.EFA_id
    return False , UNDEFINED

def color_remaining_states(traversed_states, color):
    for state in traversed_states:
        if state.EFA_id == UNDEFINED:
            state.EFA_id = color
        elif state.EFA_id != color :
            sys.exit('different EFA colors detected in one EFA state set!!')

    return None

def color_states(traversed_states, color):
    for state in traversed_states:
        if state.EFA_id == UNDEFINED:
            state.EFA_id = color
        else:
            sys.exit('EFA states should not have color at this stage!!')
    return None

def make_efa_states_dict(efa):
    efa_states = dict()
    for state in efa.states:
        if state.EFA_id not in efa_states:
            efa_states[state.EFA_id] = []
            efa_states[state.EFA_id].append(state)
        else:
            efa_states[state.EFA_id].append(state)
    return efa_states

# associate color (EFA_id) to each of the shared blocks to distinguish between different EFA shared blocks
def color_sharedblocks(efa):
    #color shared blocks that are referenced in EFA programms
    for state in efa.states:
        for tr in state.trans:
            for action in tr.actions:
                if action.opcode == "branch" or action.opcode == "jmp":     #TODO: support TransCarry_goto
                    if action.dst in efa.sharedBlock:                   #the branch should be to a shared block target
                        if state.EFA_id not in efa.EFA_sharedblocks:
                            efa.EFA_sharedblocks[state.EFA_id] = [action.dst]
                        else:
                            efa.EFA_sharedblocks[state.EFA_id].append(action.dst)
    #color shared blocks that are supposed to be automatically called by the hw (sb_refill and input_termination)
    for label in efa.sharedBlock_state_links:
        for state in efa.sharedBlock_state_links[label]:
            efa_id = state.EFA_id
            if efa_id not in efa.EFA_sharedblocks:
                efa.EFA_sharedblocks[efa_id] = [label]
            else:
                efa.EFA_sharedblocks[efa_id].append(label)

    #make sure all shared blocks are colored
    uncolored_block_found = 0
    for label in efa.sharedBlock:
        if is_sharedblock_colored(efa,label) == False:
            print(f"sharedblock {label} is not referenced in the program, or attached to an EFA for automatic HW call!")

    #make sure shared blocks are not used for event driven program
    for efa_id in efa.EFA_sharedblocks:
        if efa_id == UNDEFINED:
            print(f"event driven program should not use shared blocks!")

    return None

def is_sharedblock_colored(efa,sb_label):
    for efa_id in efa.EFA_sharedblocks:
        for label in efa.EFA_sharedblocks[efa_id]:
            if label == sb_label:
                return True
    return False

def get_potential_actions_size(action_list):
    size = 0
    for action in action_list:
        if (action.opcode == "evi" or action.opcode == "ev_update_1"):
            size += 2
        else:
            size += 1
    return size

# resolve the address for input_term (mandatory) and sb_refill (optional) shared blocks
def assign_sharedblock_addr(efa, base_addr, efa_id, sharedB_symbols, manager):
    #input_term is placed first, sb_refill is placed next
    sb_refill_label =""
    input_term_label = ""
    # --- resolve input_term and update bitmap block---
    offset = INPUT_TERM_OFFSET
    #find the label used in the program for this EFA's input_term shared block
    input_term_label = find_input_term_label(efa,efa_id)
    add_resolved_symbol(sharedB_symbols, input_term_label, base_addr + (offset << 2))

    action_list = efa.sharedBlock[input_term_label]
    for i in range ( (base_addr>>2) + offset , (base_addr>>2) + offset + len(action_list)):
        manager.set_block_bitmap(i)
    offset += INPUT_TERM_MAX

    # --- resolve sb_refill and update bitmap block---
    flag, sb_refill_label = find_sb_refill_label(efa,efa_id)
    if flag:
        offset = SB_REFILL_OFFSET 
        add_resolved_symbol(sharedB_symbols, sb_refill_label, base_addr + (offset << 2))

        action_list = efa.sharedBlock[sb_refill_label]
        for i in range ( (base_addr>>2) + offset , (base_addr>>2) + offset + len(action_list)):
            manager.set_block_bitmap(i)

        offset +=SB_REFILL_MAX

    address = base_addr + (offset << 2)
    offset = 0
    # --- resolve remaining shared blocks and update bitmap block---
    for label in efa.EFA_sharedblocks[efa_id]:
        if label != sb_refill_label and label != input_term_label:
            add_resolved_symbol(sharedB_symbols, label, address)
            action_list = efa.sharedBlock[label]
            
            for i in range ((address>>2), (address>>2) + len(action_list)):
                manager.set_block_bitmap(i)

            address = allocate_actions_addresses(action_list, address, True)
    
    # ---  update memory bitmap with bitmap block and reset bitmap block---
    if (manager.set_memory_bitmap( min(INPUT_TERM_OFFSET, SB_REFILL_OFFSET), (address>>2) ) == False):
        sys.exit(f"memory bitmap allocation failed for shared blocks of EFA{efa_id}!")
    manager.reset_block_bitmap()
    return sharedB_symbols, address

def add_resolved_symbol(symbols, label, address):
    if label not in symbols:
        symbols[label] = address
    else:
        print(f"{label} is already resolved!!!")

def allocate_actions_addresses(action_list, address, after_resolve):
    instruction_counter = 0
    # at the very beginning pseudo instructions are changed, so no need for reserving 2 instructions
    #for action in action_list:
        #each action gets 1 slot, event_updates take 2 slots
        #if (action.opcode == "evi" or action.opcode == "ev_update_1" or action.opcode == "evii" or action.opcode == "ev_update_2"):
        #    instruction_counter +=2
        #else:
        #    instruction_counter +=1
    if after_resolve == True:
        instruction_counter = len(action_list)
    else:
        instruction_counter = get_potential_actions_size(action_list)

    address += (instruction_counter <<2)
    return address

def find_input_term_label(efa,efa_id):
    #print(f"\n\nefa.sharedBlock_state_links=> {efa.sharedBlock_state_links} \n efa.EFA_sharedblocks=> {efa.EFA_sharedblocks}")
    automated_blocks = list(efa.sharedBlock_state_links.keys())
    intersection = list(set(efa.EFA_sharedblocks[efa_id]) & set(automated_blocks))
    if len(intersection) < 1:
        sys.exit(f"sb_refill(optional) and input_term(mandatory) not detected for efa {efa_id}!")
    elif len(intersection) == 1:
        if is_sb_refill_block(intersection[0],efa) :
            sys.exit(f"input_term not detected for efa {efa_id}!")
        else:
            return intersection[0]
    elif len(intersection) == 2:
        if is_sb_refill_block(intersection[0],efa) :
            return intersection[1]
        else:
            return intersection[0]
    else:
        sys.exit(f"maximum number of automatically referenbced shared blocks exceeded 2 for efa {efa_id}!")

def find_sb_refill_label(efa,efa_id):
    automated_blocks = list(efa.sharedBlock_state_links.keys())
    intersection = list(set(efa.EFA_sharedblocks[efa_id]) & set(automated_blocks))
    if len(intersection) == 2:
        if is_sb_refill_block(intersection[0],efa) :
            return True, intersection[0]
        else:
            return True, intersection[1]
    else:
        return False, ""

def is_sb_refill_block(label, efa):
    action_list = efa.sharedBlock[label]
    for action in action_list:
        if action.opcode == "mov_lm2sb" or action.opcode == "movlsb":
            return True
    return False

def assign_efa_state_addr(efa_states, allstates_symbols, address,efa, manager,do_print):
    max_last_addr = 0
    starting_address = address
    incoming = ConstructIncoming(efa)
    for state in efa_states:
        address , last_address = set_state_bitmap(state, incoming, manager,starting_address,do_print)
        if (last_address > max_last_addr):
            max_last_addr = last_address
        add_resolved_symbol(allstates_symbols, state.state_id, address)
    print(f"max_last_addr = {max_last_addr}") if do_print else None
    return None


#set state's instructions (transitions and actions) location in EFA's bitmap
#first fill all outgoing transition and actions of the state in a block bitmap starting offset starting_address
#then shift the blockbitmap (i.e, increment block offset) and compare with EFA's bitmap to resolve the state address when there is not conflict between EFA bitmap and shifted block
def set_state_bitmap(state, incomings,manager, starting_address, do_print):
    state_addr = starting_address
    last_addr = starting_address
    if len(state.trans) == 0:
        return state_addr, last_addr

    state_type = identify_carried_dispatch_type(incomings[state.state_id][0])

    if state_type == "basic" or state_type == "flag" or state_type == "majority" or state_type == "flagmajority" or state_type == "default" or state_type == "flagdefault":
        #First fills the state block bitmap with labeled transition and actions instructions
        #Second, resolve the address of majority or default tx and action and fill them into the memory

        #set up a bitmaps for  majority and default tx and actions (will be used to resolve the maj/default tx address)
        state_bitmap = 0
        majdef_bitmap = 0
        # measure base and scalar fields (to be filled in transitions attach filed)
        # Note:majority or default transition are ignored in these steps
        base = get_baseINattach(state)
        base_tx_count = 2** (base+1)
        if (get_max_action_count(state,True) != 0):
            scalar = get_scalarINattach(state)
            scalar_action_count = 2**scalar
        else:
            scalar = 0
            scalar_action_count = 0
      #  print(f"{state_type} state {state.state_id}[addr:NEXT] ==>  base={base} base_tx_count={base_tx_count} scalar={scalar} scalar_action_count={scalar_action_count}")    if do_print else None
        # ----fill labeled txs in block bitmap------
        for label in range (base_tx_count):
            if len(state.get_tran_byLabel(label))>0 :
                manager.set_block_bitmap( (state_addr>>2)+label)
                state_bitmap = (1 << label) | state_bitmap
        last_addr = state_addr + (base_tx_count<<2)
        # ----fill labeled tx actions in block bitmap------
        action_addr = 0
        for tr in state.trans:
            # if tr has action and is labeled (i.e., not majority or default transition)
            if ( len(tr.anno_type.split('_')) > 1) and (tr.name[:1] in {"9","8","7","6","5","4","3","2","1","0"}):
                action_addr = get_action_address(state, tr, incomings, state_addr)
                for i in range ( (action_addr>>2), (action_addr>>2) + len(tr.actions)):
                    manager.set_block_bitmap(i)
                    state_bitmap = (1 << i) | state_bitmap
                action_addr += (len(tr.actions) <<2)
            if action_addr > last_addr:
                last_addr = action_addr
        # ----fill majority (and its actions) or default txs in block bitmap------
        if state_type == "majority" or state_type == "flagmajority" or state_type == "default" or state_type == "flagdefault":
            majdef_bitmap = 1 #the transition it self
            #fill majdef_bitmap bitmap
            majdef_tr = get_majdef_tx(state)
            if majdef_tr.actions:
                if state_type == "default" or state_type == "flagdefault":
                    sys.exit(f"The default transition should not have any actions!(src state {state.state_id})")
                else:
                    for i in range( 1 , len(majdef_tr.actions)+1 ):
                        majdef_bitmap = (1 << i) | majdef_bitmap
            #find majdef address
            majdef_offset = 0
            while (majdef_bitmap & state_bitmap) != 0 :
                majdef_offset = majdef_offset +1 
                majdef_bitmap = majdef_bitmap << 1
            #store the majdef_offset from the state addr to be used as carried value (either as attach of incoming tx s or value of ssprop)
            majdef_tr.label = majdef_offset
            #resolve value of ssprop of any incoming tx
            ssprop_actions = [action for tr in incomings[state.state_id] for action in tr.actions if action.opcode in {"ssprop", "set_state_property"}]
            for action in ssprop_actions:
                action.dst = str(majdef_offset)

            #fill majdef into state block bitmap
            majdef_addr = ((state_addr>>2) + majdef_offset) <<2
            for i in range ( majdef_addr>>2 , (majdef_addr>>2) + 1 + len(majdef_tr.actions) ):
                manager.set_block_bitmap(i)
            last_majdef_addr =  majdef_addr + ( (1+ len(majdef_tr.actions))<<2)
            if last_majdef_addr > last_addr :
                last_addr = last_majdef_addr 

    elif state_type == "common" or state_type == "epsilon":
     #   print(f"{state_type} state {state.state_id}[addr:NEXT] ")    if do_print else None
        # ----fill txs in block bitmap------
        if len(state.trans) == 1:
            manager.set_block_bitmap(state_addr>>2)
        elif len(state.trans) > 1:
            sys.exit(f"{state_type} state {state.state_id} has more than 1 transition!")
        last_addr = state_addr + 4
        # ----fill actions in block bitmap------
        tr = state.trans[0]
        if len(tr.anno_type.split('_')) > 1:
            for i in range (last_addr>>2, (last_addr>>2) + len(tr.actions)):
                manager.set_block_bitmap(i)
            last_addr += (len(tr.actions)<<2)
    else:
        sys.exit(f"{state_type} state {state.state_id} is not supported for bitmap generation!")

    # ----find the state_addr that is free to allocate------
    found_free_slot = manager.is_allocation_valid((state_addr>>2),(last_addr>>2))
    while(found_free_slot == False):
        manager.shift_block_bitmap(1,(state_addr>>2), (last_addr>>2)+1)
        #if state.state_id==108:
        #    print(f"------------------------------------------------------------------- startaddr:{state_addr} last addr:{((last_addr>>2)+1)<<2} ({((last_addr>>2) & 0xFFF)})")
        #    manager.print_block_bitmap(0)
        state_addr += 4
        last_addr += 4
        if((last_addr>>2) & 0xFFF) == (2**12)-1:
            sys.exit(f"memory bitmap allocation grows beyond limit for state {state.state_id}!")

        found_free_slot = manager.is_allocation_valid((state_addr>>2),(last_addr>>2))

    #print(f"****** {state_type} state {state.state_id} ******** [addr:{state_addr}] ")    if do_print else None
    #manager.print_block_bitmap(0)
    # ---  update memory bitmap with bitmap block and reset bitmap block---
    if (manager.set_memory_bitmap( (state_addr>>2), (last_addr>>2) ) == False):
        sys.exit(f"memory bitmap allocation failed for state {state.state_id}!")
    manager.reset_block_bitmap()
    return state_addr, last_addr

def get_action_address(state, tr, incomings, state_addr):
    state_type = identify_carried_dispatch_type(incomings[state.state_id][0])
    if state_type == "basic" or state_type == "flag" or state_type == "majority" or state_type == "flagmajority" or state_type == "default" or state_type == "flagdefault":
        if tr.name[:1] not in {"9", "8", "7", "6", "5", "4", "3", "2", "1", "0"}:
            address = state_addr + (tr.label <<2) + (1 <<2)     #majority's actions are placed right after the transition
        else:
            base = get_baseINattach(state)
            base_tx_count = 2** (base+1)
            scalar = get_scalarINattach(state)
            address = state_addr + ((base_tx_count + (tr.label << scalar)) <<2)
    elif state_type == "common" or state_type == "epsilon":
         address = state_addr + (1<<2)
    else:
        sys.exit(f"state type {state_type} not supported!")
    return address

def encode_EFAstate_actions(state, incomings,allstates_symbols,myprogram):
    l = []
    state_type = identify_carried_dispatch_type(incomings[state][0])

    return myprogram

def get_baseINattach(state):
    max_tx_label = get_max_label(state)
    max_tx_label += 1 #if max is 255, log2 256 should be taken
    base = math.ceil(math.log2(max_tx_label))
    base = base -1  #base can be between 0 to 7 but transition # can be upto 256
    if (2** (base+1) ) > 256:
        sys.exit (f"base of {base} for transitions attach filed is not supported!")
    return base

def get_scalarINattach(state):
    max_action_count = get_max_action_count(state,True)
    scalar = math.ceil(math.log2(max_action_count))
    return scalar

def get_max_label(state):
    max_label = 0
    for tr in state.trans:
        if tr.name[:1] in {"9","8","7","6","5","4","3","2","1","0"}:
            if (tr.label > max_label):
                max_label = tr.label
    return max_label

def get_max_action_count(state, count_lastact):
    max_action_count = 0
    for tr in state.trans:
        if tr.name[:1] in {"9","8","7","6","5","4","3","2","1","0"}:
            if(count_lastact):
                if len(tr.actions) == 0:
                    continue
                if tr.actions[-1].opcode == "lastact" and (len(tr.actions)-1) > max_action_count:
                    max_action_count = len(tr.actions) -1
                elif tr.actions[-1].opcode != "lastact" and (len(tr.actions)) > max_action_count:
                    max_action_count = len(tr.actions)
            else:
                if (len(tr.actions)) > max_action_count:
                    max_action_count = len(tr.actions)

    return max_action_count

# Define the dispatch type of transitions's dst state
# Note: All incoming txs should carry same dispatch type either by tx's anno_type or by ssprop's type
def identify_carried_dispatch_type(tr):
    # check if transition has ssprop action
    result = next((action.imm for action in reversed(tr.actions) if action.opcode in {"ssprop", "set_state_property"}), None)
    if result is not None and (result[:1] in {"9","8","7","6","5","4","3","2","1","0"}):
        result = int(result) & 0b1111
        if result == state_property_enc["BASIC"]:
            return "basic"
        elif result == state_property_enc["COMMON"]:
            return "common"
        elif result == state_property_enc["EPSILON"]:
            return "epsilon"
        elif result == state_property_enc["DEFAULT"]:
            return "default"
        elif result == state_property_enc["MAJORITY"]:
            return "majority"
        elif result == state_property_enc["FLAG_DEFAULT"]:
            return "flagdefault"
        elif result == state_property_enc["FLAG_MAJORITY"]:
            return "flagmajority"
        elif result == state_property_enc["FLAG"]:
            return "flag"
    elif result is not None:
        if result == "basic":
            return "basic"
        elif result == "common":
            return "common"
        elif result == "epsilon":
            return "epsilon"
        elif result == "default":
            return "default"
        elif result == "majority":
            return "majority"
        elif result == "flag_default":
            return "flagdefault"
        elif result == "flag_majority":
            return "flagmajority"
        elif result == "flag":
            return "flag"
        else:
            sys.exit(f" ssprop type {result} is not supported!")
    elif tr.anno_type[:4] == "basic"[:4]:
        return "basic"
    elif tr.anno_type[:4] == "common"[:4]:
        return "common"
    elif tr.anno_type[:4] == "epsilon"[:4]:
        return "epsilon"
    elif tr.anno_type[:4] == "refill"[:4]:
        return "basic"
    elif tr.anno_type[:4] == "majority"[:4]:
        return "majority"
    elif tr.anno_type[:4] == "default"[:4]:
        return "default"
    elif tr.anno_type[:7] == "flagmajority"[:7]:
        return "flagmajority"
    elif tr.anno_type[:7] == "flagdefault"[:7]:
        return "flagdefault"
    elif tr.anno_type[:4] == "flag"[:4]:
        return "flag"
    else:
        sys.exit(f"Transition type {tr.anno_type} is not supported!")

def ConstructIncoming(efa):
    lookup = dict()
    for state in efa.states:
        for tr in state.trans:
            if tr.dst.state_id not in lookup:
                if(tr.anno_type != "event"):
                    lookup[tr.dst.state_id] = [tr]
            else:
                if(tr.anno_type != "event"):
                    lookup[tr.dst.state_id].append(tr)
    for state in efa.states:
        if (state.state_id not in lookup) and state.state_id!= efa.init_state_id[0]:
            #lookup[state] = []
            sys.exit(f"state {state.state_id} do not have incoming transitions!!")
    return lookup

def update_event_labels(actions, myprogram):
    idx = 0
    while idx < len(actions):
        #print(f"opcode is {actions[idx].opcode}")
        #set the label of first instr.
        if actions[idx].label is not None:
            label = actions[idx].label
        else:
            label = ""
        if (actions[idx].opcode == "evi" and int(actions[idx].imm2) & 0b0001 == 1) or (actions[idx].opcode == "ev_update_1" and int(actions[idx].imm2) & 0b0001 == 1) or actions[idx].opcode == "evlb":
            #resolve the label
            if int(actions[idx].imm) not in myprogram.symbols:
                sys.exit(f"(opcode:{actions[idx].opcode}) event label {actions[idx].imm} is not resolved!")
            else:
                actions[idx].imm= myprogram.symbols[int(actions[idx].imm)]
            #change evi in case of large resolved event label
            if actions[idx].opcode == "evi" or actions[idx].opcode == "ev_update_1":
                if (int(actions[idx].imm)>0xFFF):
                    action1, maxudp, maxop = GetAction(f"{label}: addi {actions[idx].src} {actions[idx].dst} 0")
                    action2, maxudp, maxop = GetAction(f"evlb {actions[idx].dst} {actions[idx].imm}")
                    actions.pop(idx)
                    actions.insert(idx, action1)
                    actions.insert(idx + 1, action2)
                    idx += 2
                else:
                    idx += 1
            else:
                idx += 1
        else:
            idx += 1

    return actions

def get_majdef_tx(state):
    majdef_trs = [tr for tr in state.trans if tr.name[:1] not in {"9", "8", "7", "6", "5", "4", "3", "2", "1", "0"}]
    if len(majdef_trs) != 1:
        sys.exit(f" State {state.state_id} has {len(majdef_trs)} majority or default transitions!")
    return majdef_trs[0]

#This function assumes that state dispatch type is def maj
def calculate_defmaj_offset(state):
    # a bitmap showing state transitions and actions
    state_bitmap = 0
    #get base and scalar
    base = get_baseINattach(state)
    base_tx_count = 2** (base+1)
    if (get_max_action_count(state,True) != 0):
        scalar = get_scalarINattach(state)
        scalar_action_count = 2**scalar
    else:
        scalar = 0
        scalar_action_count = 0
    # ----fill labeled txs in state bitmap------
    for label in range (base_tx_count):
        if len(state.get_tran_byLabel(label))>0 :
            state_bitmap = (1 << label) | state_bitmap
    # ----fill labeled tx actions in state bitmap-----
    for tr in state.trans:
        # if tr has action and is labeled (i.e., not majority or default transition)
        if ( len(tr.anno_type.split('_')) > 1) and (tr.name[:1] in {"9","8","7","6","5","4","3","2","1","0"}):
            action_addr = get_action_address(state, tr, incomings, state_addr)
            for i in range ( (action_addr>>2), (action_addr>>2) + len(tr.actions)):
                state_bitmap = (1 << i) | state_bitmap
    # ----fill majority (and its actions) or default txs in def maj bitmap------
    majdef_bitmap = 1 #the transition it self
    majdef_tr = get_majdef_tx(state)
    if majdef_tr.actions:
        for i in range( 1 , len(majdef_tr.actions)+1 ):
            majdef_bitmap = (1 << i) | majdef_bitmap
    # ----find majdef offset------
    majdef_offset = 0
    while (majdef_bitmap & state_bitmap) != 0 :
        majdef_offset = majdef_offset +1
        majdef_bitmap = majdef_bitmap << 1

    return majdef_offset

#change maj/flagmaj/def/flagdef carry annotation to a _with_action annotation to enable the attach part of the transition to be used for addressing the actions
#add ssprop to the end of action block to enable transition carry maj/flagmaj/def/flagdef dispatch type and the value (i.e. offset of maj/def transitions for addressing)
def change_majoritydefault(tr):
    #set the label of ssprop
    if tr.actions and tr.actions[-1].opcode == "lastact":
        if(tr.actions[-1].label) is not None:
            label = tr.actions[-1].label
        else:
            label = ""
    else:
        label = ""

    if tr.anno_type[:5] == 'majorityCarry'[:5]:
        annotype = 'basic_with_action'
        ssprop_type = 'majority'
    elif tr.anno_type[:5] == 'defaultCarry'[:5]:
        annotype = 'basic_with_action'
        ssprop_type = 'default'
    elif tr.anno_type[:5] == 'flagmajorityCarry'[:5]:
        annotype = 'flagCarry_with_action'
        ssprop_type = 'flag_majority'
    elif tr.anno_type[:5] == 'flagdefaultCarry'[:5]:
        annotype = 'flagCarry_with_action'
        ssprop_type = 'flag_default'

    ssprop_action, maxudp, maxop = GetAction(f"{label}: ssprop {ssprop_type}")
    #print(f" state{tr.src.state_id} tr label {tr.label} added ssprop action ({label}: ssprop {ssprop_type}) in which imm is {ssprop_action.imm}")
    #add ssprop to actions list
    if tr.actions and (tr.actions[-1].opcode == "lastact" or tr.actions[-1].opcode == "yield" or tr.actions[-1].opcode == "yieldt"):
        tr.actions.insert(-1, ssprop_action)  # Insert ssprop_action before the lastact
    elif not tr.actions:
        tr.actions.append(ssprop_action)  # Add ssprop_action to the end of the list
        lastact_action, maxudp, maxop = GetAction(f"{label}: lastact")
        tr.actions.append(lastact_action)  # Add lastact_action to the end of the list
    else:       #in case change_majoritydefault is called after lastact removal
        tr.actions.append(ssprop_action)  # Add ssprop_action to the end of the list

    #change the transition annotatation
    tr.anno_type = annotype

    return

#remove the lastact instructions of outgoing transitions of basic or flag states
#lastact is removed in cases that the lastact dont fall within max_tx_action_count defined using the scalar filed in attach, so its not encoded
def remove_lastact(state,incomings):
    if not state.trans:
        return
    state_type = identify_carried_dispatch_type(incomings[state.state_id][0])
    if state_type == "basic" or state_type == "flag" or state_type == "majority" or state_type == "flagmajority" or state_type == "default" or state_type == "flagdefault":
        # measure base and scalar fields (to be filled in transitions attach filed)
        # Note:majority or default transition are ignored in these steps
        base = get_baseINattach(state)
        base_tx_count = 2** (base+1)
        if (get_max_action_count(state,True) != 0):
            scalar = get_scalarINattach(state)
            scalar_action_count = 2**scalar
        else:
            scalar = 0
            scalar_action_count = 0
        #remove the lastact of transitions with lastact that dont fall within max_tx_action_count
        for label in range (base_tx_count):
            if len(state.get_tran_byLabel(label))>0:
                tr = state.get_tran_byLabel(label)[0]
                if tr.actions:
                    if len(tr.actions) > scalar_action_count and tr.actions[-1].opcode == "lastact":
                        tr.actions.pop()
    else:
        return

    return

def change_pseudo_instr(actions):
    idx = 0
    while idx < len(actions):
        #set the label of first instr.
        if actions[idx].label is not None:
            label = actions[idx].label
        else:
            label = ""

        if (actions[idx].opcode == "evii" or actions[idx].opcode == "ev_update_2"):
            if int(actions[idx].op3) == 1 or int(actions[idx].op3) == 2 or int(actions[idx].op3) == 4 or int(actions[idx].op3) == 8:
                action1, maxudp, maxop = GetAction(f"{label}: evi X2 {actions[idx].dst} {actions[idx].op1} {int(actions[idx].op3) & 0b1111}")
                actions.pop(idx)
                actions.insert(idx, action1)
                idx += 1
            else: 
                num_tmp = 0
                mask_bit = 0b0001
                action1 = 0
                action2 = 0
                for i in range(0,4):
                    if (int(actions[idx].op3) & mask_bit) == mask_bit:
                        if(num_tmp == 0):
                            # print(f"{label}: evi X2 {actions[idx].dst} {actions[idx].op1} {mask_bit}")
                            action1, maxudp, maxop = GetAction(f"{label}: evi X2 {actions[idx].dst} {actions[idx].op1} {mask_bit}")
                            num_tmp += 1
                        else:
                            action2, maxudp, maxop = GetAction(f"evi {actions[idx].dst} {actions[idx].dst} {actions[idx].op2} {mask_bit}")
                            num_tmp += 1
                    mask_bit = mask_bit << 1
                if num_tmp != 2:
                    sys.exit(f"evii mask {actions[idx].op3} wrong!")
                actions.pop(idx)
                actions.insert(idx, action1)
                actions.insert(idx + 1, action2)
                idx += 2

            # if int(actions[idx].op3) & 0b0001 == 1:
            #     action1, maxudp, maxop = GetAction(f"{label}: evi X2 {actions[idx].dst} {actions[idx].op2} {int(actions[idx].op3) & 0b1110}")
            #     action2, maxudp, maxop = GetAction(f"evlb {actions[idx].dst} {actions[idx].op1}")
            #     #print(f"action1: {actions[idx].label}: evi X2 {actions[idx].dst} {actions[idx].op2} {int(actions[idx].op3) & 0b1110}")
            #     #print(f"action2: evlb {actions[idx].dst} {actions[idx].op1}")
            # else :
            #     position = 0
            #     number = int(actions[idx].op3)
            #     while number % 2 == 0:
            #         number >>= 1
            #         position += 1
            #     number = (1 << position) ^ 0b1111
            #     action1, maxudp, maxop = GetAction(f"{label}: evi X2 {actions[idx].dst} {actions[idx].op2} {int(actions[idx].op3) & number}")
            #     action2, maxudp, maxop = GetAction(f"evi {actions[idx].dst} {actions[idx].dst} {actions[idx].op1} {1 << position}")
            #     #print (f"action1: {actions[idx].label}: evi X2 {actions[idx].dst} {actions[idx].op2} {int(actions[idx].op3) & number}")
            #     #print (f"action2: evi {actions[idx].dst} {actions[idx].dst} {actions[idx].op1} {1 << position}")
            # actions.pop(idx)
            # actions.insert(idx, action1)
            # actions.insert(idx + 1, action2)
            # idx += 2
        elif (actions[idx].opcode == "mov_ob2reg" or actions[idx].opcode == "mov_reg2reg"):            #resolve the event or continueation label
            if actions[idx].dst not in general_purpose_register_enc:
                sys.exit(f"writing to an unauthorized register {actions[idx].dst} using mov_ob2reg and mov_reg2reg! The assembler do not support this")
            else:
               # print(f"{actions[idx].opcode} {actions[idx].src} {actions[idx].dst}")
               # print(f" CHANGED TO: addi {actions[idx].src} {actions[idx].dst} 0")
                action1, maxudp, maxop = GetAction(f"{label}: addi {actions[idx].src} {actions[idx].dst} 0")
                actions.pop(idx)
                actions.insert(idx, action1)
            idx += 1
        elif (actions[idx].opcode == "branch" and actions[idx].op1 not in register_enc):      #since some old bge and blts accepted immidates
            action1, maxudp, maxop = GetAction(f"{label}: {actions[idx].funct}i {actions[idx].op2} {actions[idx].op1} {actions[idx].dst}")
            actions.pop(idx)
            actions.insert(idx, action1)
            idx += 1
        elif actions[idx].opcode == "branch" and actions[idx].funct == "bge":
            action1, maxudp, maxop = GetAction(f"{label}: ble {actions[idx].op2} {actions[idx].op1} {actions[idx].dst}")
            actions.pop(idx)
            actions.insert(idx, action1)
            idx += 1 
        elif actions[idx].opcode == "branch" and actions[idx].funct == "blt":
            action1, maxudp, maxop = GetAction(f"{label}: bgt {actions[idx].op2} {actions[idx].op1} {actions[idx].dst}")
            actions.pop(idx)
            actions.insert(idx, action1)
            idx += 1 
        elif actions[idx].opcode == "send_wcont":
            # PSEUDO:   send_wcont    Xe      Xc      Xptr    $len
            # HERE:     send_wcont    event   cont    op1     op2
            # AFTER:    send    event   cont    op1     op2     0
            # ISA:      send    Xe      Xc      Xptr    $len    $mode[1]
            action1, maxudp, maxop = GetAction(f"{label}: send {actions[idx].event} {actions[idx].cont} {actions[idx].op1} {actions[idx].op2} 0")
            actions.pop(idx)
            actions.insert(idx, action1)
            idx += 1
        elif actions[idx].opcode == "sendr_wcont":
            # PSEUDO:   sendr_wcont   Xe      Xc      X1      X2
            # HERE:     sendr_wcont   event   cont    op1     op2
            # AFTER:    sendr   event   cont    op1     op2
            # ISA:      sendr   Xe      Xc      X1      X2
            action1, maxudp, maxop = GetAction(f"{label}: sendr {actions[idx].event} {actions[idx].cont} {actions[idx].op1} {actions[idx].op2} ")
            actions.pop(idx)
            actions.insert(idx, action1)
            idx += 1
        elif actions[idx].opcode == "sendr3_wcont":
            # PSEUDO:   sendr3_wcont  Xe      Xc      X1      X2      X3
            # HERE:     sendr3_wcont  event   cont    op1     op2     op3
            # AFTER:    sendr3  event   cont    op1     op2     op3
            # ISA:      sendr3  Xe      Xc      X1      X2      X3
            action1, maxudp, maxop = GetAction(f"{label}: sendr3 {actions[idx].event} {actions[idx].cont} {actions[idx].op1} {actions[idx].op2} {actions[idx].op3} ")
            actions.pop(idx)
            actions.insert(idx, action1)
            idx += 1
        elif actions[idx].opcode == "sendops_wcont":
            # PSEUDO:   sendops_wcont     Xe      Xc      Xop     $numops
            # HERE:     sendops_wcont     event   cont    op1     op2
            # AFTER:    sendops     event   cont    op1     op2         0
            # ISA:      sendops     Xe      Xc      Xop     $numops     $mode[1]
            action1, maxudp, maxop = GetAction(f"{label}: sendops {actions[idx].event} {actions[idx].cont} {actions[idx].op1} {actions[idx].op2} 0")
            actions.pop(idx)
            actions.insert(idx, action1)
            idx += 1
        elif actions[idx].opcode == "send_wret":
            # PSEUDO:   send_wret     Xe        $cont_label     Xptr    $len    Xtmp1
            # HERE:     send_wret     event     cont            op1     op2     tmp_reg1
            # AFTER:    send    event   tmp_reg1    op1     op2     0
            # ISA:      send    Xe      Xc          Xptr    $len    $mode[1]
            action1, maxudp, maxop = GetAction(f"{label}: addi X2 {actions[idx].tmp_reg1} 0")
            action2, maxudp, maxop = GetAction(f"evlb {actions[idx].tmp_reg1} {actions[idx].cont}")
            action3, maxudp, maxop = GetAction(f"send {actions[idx].event} {actions[idx].tmp_reg1} {actions[idx].op1} {actions[idx].op2} 0 ")
            actions.pop(idx)
            actions.insert(idx, action1)
            actions.insert(idx + 1, action2)
            actions.insert(idx + 2, action3)
            idx += 3
        elif actions[idx].opcode == "sendr_wret":
            # PSEUDO:   sendr_wret    Xe      $cont_label     X1      X2      Xtmp1
            # HERE:     sendr_wret    event   cont            op1     op2     tmp_reg1
            # AFTER:    sendr   event   tmp_reg1    op1     op2
            # ISA:      sendr   Xe      Xc          X1      X2
            action1, maxudp, maxop = GetAction(f"{label}: addi X2 {actions[idx].tmp_reg1} 0")
            action2, maxudp, maxop = GetAction(f"evlb {actions[idx].tmp_reg1} {actions[idx].cont}")
            action3, maxudp, maxop = GetAction(f"sendr {actions[idx].event} {actions[idx].tmp_reg1} {actions[idx].op1} {actions[idx].op2} ")
            actions.pop(idx)
            actions.insert(idx, action1)
            actions.insert(idx + 1, action2)
            actions.insert(idx + 2, action3)
            idx += 3
        elif actions[idx].opcode == "sendr3_wret":
            # PSEUDO:   sendr3_wret   Xe      $cont_label     X1      X2      X3      Xtmp1
            # HERE:     sendr3_wret   event   cont            op1     op2     op3     tmp_reg1
            # AFTER:    sendr3  event   tmp_reg1    op1     op2     op3
            # ISA:      sendr3  Xe      Xc          X1      X2      X3
            action1, maxudp, maxop = GetAction(f"{label}: addi X2 {actions[idx].tmp_reg1} 0")
            action2, maxudp, maxop = GetAction(f"evlb {actions[idx].tmp_reg1} {actions[idx].cont}")
            action3, maxudp, maxop = GetAction(f"sendr3 {actions[idx].event} {actions[idx].tmp_reg1} {actions[idx].op1} {actions[idx].op2} {actions[idx].op3} ")
            actions.pop(idx)
            actions.insert(idx, action1)
            actions.insert(idx + 1, action2)
            actions.insert(idx + 2, action3)
            idx += 3
        elif actions[idx].opcode == "sendops_wret":
            # PSEUDO:   sendops_wret  Xe      $cont_label     Xop     $numops     Xtmp1
            # HERE:     sendops_wret  event   cont            op1     op2         tmp_reg1
            # AFTER:    sendops     event   tmp_reg1    op1     op2         0
            # ISA:      sendops     Xe      Xc          Xop     $numops     $mode[1]
            action1, maxudp, maxop = GetAction(f"{label}: addi X2 {actions[idx].tmp_reg1} 0")
            action2, maxudp, maxop = GetAction(f"evlb {actions[idx].tmp_reg1} {actions[idx].cont}")
            action3, maxudp, maxop = GetAction(f"sendops {actions[idx].event} {actions[idx].tmp_reg1} {actions[idx].op1} {actions[idx].op2} 0 ")
            actions.pop(idx)
            actions.insert(idx, action1)
            actions.insert(idx + 1, action2)
            actions.insert(idx + 2, action3)
            idx += 3
        elif actions[idx].opcode == "send_dmlm_ld":
            # PSEUDO:   send_dmlm_ld  Xd      Xc      $len
            # HERE:     send_dmlm_ld  dst     cont    op1
            # AFTER:    sendm   dst     cont    X0      op1     0
            # ISA:      sendm   Xd      Xc      Xptr    $len    $mode[1:0]
            action1, maxudp, maxop = GetAction(f"{label}: sendm {actions[idx].dst} {actions[idx].cont} X0 {actions[idx].op1} 0")
            actions.pop(idx)
            actions.insert(idx, action1)
            idx += 1
        elif actions[idx].opcode == "send_dmlm_ld_wret":
            # PSEUDO:   send_dmlm_ld_wret     Xd      $cont_label     $len    Xtmp1
            # HERE:     send_dmlm_ld_wret     dst     cont            op1     tmp_reg1
            # AFTER:    sendm   dst     tmp_reg1    X0      op1     0
            # ISA:      sendm   Xd      Xc          Xptr    $len    $mode[1:0]
            action1, maxudp, maxop = GetAction(f"{label}: addi X2 {actions[idx].tmp_reg1} 0")
            action2, maxudp, maxop = GetAction(f"evlb {actions[idx].tmp_reg1} {actions[idx].cont}")
            action3, maxudp, maxop = GetAction(f"sendm {actions[idx].dst} {actions[idx].tmp_reg1} X0 {actions[idx].op1} 0")
            actions.pop(idx)
            actions.insert(idx, action1)
            actions.insert(idx + 1, action2)
            actions.insert(idx + 2, action3)
            idx += 3
        elif actions[idx].opcode == "send_dmlm":
            # PSEUDO:   send_dmlm     Xd      Xc      Xptr        $len
            # HERE:     send_dmlm     dst     cont    op1         op2
            # AFTER:    sendm   dst     cont    op1     op2     1
            # ISA:      sendm   Xd      Xc      Xptr    $len    $mode[1:0]
            action1, maxudp, maxop = GetAction(f"{label}: sendm {actions[idx].dst} {actions[idx].cont} {actions[idx].op1} {actions[idx].op2} 1 ")
            actions.pop(idx)
            actions.insert(idx, action1)
            idx += 1
        elif actions[idx].opcode == "sendr_dmlm":
            # PSEUDO:   sendr_dmlm    Xd      Xc      Xop1
            # HERE:     sendr_dmlm    dst     cont    op1
            # AFTER:    sendmr  dst     cont    op1
            # ISA:      sendmr  Xd      Xc      X1
            action1, maxudp, maxop = GetAction(f"{label}: sendmr {actions[idx].dst} {actions[idx].cont} {actions[idx].op1} ")
            actions.pop(idx)
            actions.insert(idx, action1)
            idx += 1
        elif actions[idx].opcode == "sendr2_dmlm":
            # PSEUDO:   sendr2_dmlm   Xd      Xc      Xop1    Xop2
            # HERE:     sendr2_dmlm   dst     cont    op1     op2
            # AFTER:    sendmr2     dst     cont    op1     op2
            # ISA:      sendmr2     Xd      Xc      X1      X2
            action1, maxudp, maxop = GetAction(f"{label}: sendmr2 {actions[idx].dst} {actions[idx].cont} {actions[idx].op1} {actions[idx].op2} ")
            actions.pop(idx)
            actions.insert(idx, action1)
            idx += 1
        elif actions[idx].opcode == "send_dmlm_wret":
            # PSEUDO:   send_dmlm_wret    Xd      $cont_label     Xptr    $len    Xtmp1
            # HERE:     send_dmlm_wret    dst     cont            op1     op2     tmp_reg1
            # AFTER:    sendm   dst     tmp_reg1    op1     op2     1
            # ISA:      sendm   Xd      Xc          Xptr    $len    $mode[1:0]
            action1, maxudp, maxop = GetAction(f"{label}: addi X2 {actions[idx].tmp_reg1} 0")
            action2, maxudp, maxop = GetAction(f"evlb {actions[idx].tmp_reg1} {actions[idx].cont}")
            action3, maxudp, maxop = GetAction(f"sendm {actions[idx].dst} {actions[idx].tmp_reg1} {actions[idx].op1} {actions[idx].op2} 1")
            actions.pop(idx)
            actions.insert(idx, action1)
            actions.insert(idx + 1, action2)
            actions.insert(idx + 2, action3)
            idx += 3
        elif actions[idx].opcode == "sendr_dmlm_wret":
            # PSEUDO:   sendr_dmlm_wret   Xd      $cont_label     Xop1    Xtmp1
            # HERE:     sendr_dmlm_wret   dst     cont            op1     tmp_reg1
            # AFTER:    sendmr  dst     tmp_reg1    op1
            # ISA:      sendmr  Xd      Xc          X1
            action1, maxudp, maxop = GetAction(f"{label}: addi X2 {actions[idx].tmp_reg1} 0")
            action2, maxudp, maxop = GetAction(f"evlb {actions[idx].tmp_reg1} {actions[idx].cont}")
            action3, maxudp, maxop = GetAction(f"sendmr {actions[idx].dst} {actions[idx].tmp_reg1} {actions[idx].op1} ")
            actions.pop(idx)
            actions.insert(idx, action1)
            actions.insert(idx + 1, action2)
            actions.insert(idx + 2, action3)
            idx += 3
        elif actions[idx].opcode == "sendr2_dmlm_wret":
            # PSEUDO:   sendr2_dmlm_wret  Xd      $cont_label     Xop1    Xop2    Xtmp1
            # HERE:     sendr2_dmlm_wret  dst     cont            op1     op2     tmp_reg1
            # AFTER:    sendmr2     dst     tmp_reg1    op1     op2
            # ISA:      sendmr2     Xd      Xc          X1      X2
            action1, maxudp, maxop = GetAction(f"{label}: addi X2 {actions[idx].tmp_reg1} 0")
            action2, maxudp, maxop = GetAction(f"evlb {actions[idx].tmp_reg1} {actions[idx].cont}")
            action3, maxudp, maxop = GetAction(f"sendmr2 {actions[idx].dst} {actions[idx].tmp_reg1} {actions[idx].op1} {actions[idx].op2} ")
            actions.pop(idx)
            actions.insert(idx, action1)
            actions.insert(idx + 1, action2)
            actions.insert(idx + 2, action3)
            idx += 3
        elif actions[idx].opcode == "sendops_dmlm_wret":
            # PSEUDO:   sendops_dmlm_wret     Xd      $cont_label     Xop     $numops     Xtmp1
            # HERE:     sendops_dmlm_wret     dst     cont            op1     op2         tmp_reg1
            # AFTER:    sendmops    dst     tmp_reg1    op1     op2         0
            # ISA:      sendmops    Xd      Xc          Xop     $numops     $mode[1]
            action1, maxudp, maxop = GetAction(f"{label}: addi X2 {actions[idx].tmp_reg1} 0")
            action2, maxudp, maxop = GetAction(f"evlb {actions[idx].tmp_reg1} {actions[idx].cont}")
            action3, maxudp, maxop = GetAction(f"sendmops {actions[idx].dst} {actions[idx].tmp_reg1} {actions[idx].op1} {actions[idx].op2} 0")
            actions.pop(idx)
            actions.insert(idx, action1)
            actions.insert(idx + 1, action2)
            actions.insert(idx + 2, action3)
            idx += 3
        elif actions[idx].opcode == "send_reply":
            # PSEUDO:   send_reply    Xptr    $len    Xtmp1
            # HERE:     send_reply    op1     op2     tmp_reg1
            # AFTER:    send    X1      tmp_reg1    op1     op2     0
            # ISA:      send    Xe      Xc          Xptr    $len    $mode[1]
            action1, maxudp, maxop = GetAction(f"{label}: movir {actions[idx].tmp_reg1} 0") #0x0000000000000000
            action2, maxudp, maxop = GetAction(f"subi {actions[idx].tmp_reg1} {actions[idx].tmp_reg1} 1") #0xFFFFFFFFFFFFFFFF
            action3, maxudp, maxop = GetAction(f"sri {actions[idx].tmp_reg1} {actions[idx].tmp_reg1} 1") #0x7FFFFFFFFFFFFFFF
            action4, maxudp, maxop = GetAction(f"send X1 {actions[idx].tmp_reg1} {actions[idx].op1} {actions[idx].op2} 0")
            actions.pop(idx)
            actions.insert(idx, action1)
            actions.insert(idx + 1, action2)
            actions.insert(idx + 2, action3)
            actions.insert(idx + 3, action4)
            idx += 4
        elif actions[idx].opcode == "sendr_reply" or actions[idx].opcode == "send4_reply":
            # PSEUDO:   sendr_reply   Xop1    Xop2    Xtmp1
            # HERE:     sendr_reply   op1     op2     tmp_reg1
            # AFTER:    sendr   X1      tmp_reg1    op1     op2
            # ISA:      sendr   Xe      Xc          X1      X2
            action1, maxudp, maxop = GetAction(f"{label}: movir {actions[idx].tmp_reg1} 0") #0x0000000000000000
            action2, maxudp, maxop = GetAction(f"subi {actions[idx].tmp_reg1} {actions[idx].tmp_reg1} 1") #0xFFFFFFFFFFFFFFFF
            action3, maxudp, maxop = GetAction(f"sri {actions[idx].tmp_reg1} {actions[idx].tmp_reg1} 1") #0x7FFFFFFFFFFFFFFF
            action4, maxudp, maxop = GetAction(f"sendr X1 {actions[idx].tmp_reg1} {actions[idx].op1} {actions[idx].op2} ")
            actions.pop(idx)
            actions.insert(idx, action1)
            actions.insert(idx + 1, action2)
            actions.insert(idx + 2, action3)
            actions.insert(idx + 3, action4)
            idx += 4
        elif actions[idx].opcode == "sendr3_reply":
            # PSEUDO:   sendr3_reply  Xop1    Xop2    Xop3    Xtmp1
            # HERE:     sendr3_reply  op1     op2     op3     tmp_reg1
            # AFTER:    sendr3  X1      tmp_reg1    op1     op2     op3
            # ISA:      sendr3  Xe      Xc          X1      X2      X3
            action1, maxudp, maxop = GetAction(f"{label}: movir {actions[idx].tmp_reg1} 0") #0x0000000000000000
            action2, maxudp, maxop = GetAction(f"subi {actions[idx].tmp_reg1} {actions[idx].tmp_reg1} 1") #0xFFFFFFFFFFFFFFFF
            action3, maxudp, maxop = GetAction(f"sri {actions[idx].tmp_reg1} {actions[idx].tmp_reg1} 1") #0x7FFFFFFFFFFFFFFF
            action4, maxudp, maxop = GetAction(f"sendr3 X1 {actions[idx].tmp_reg1} {actions[idx].op1} {actions[idx].op2} {actions[idx].op3} ")
            actions.pop(idx)
            actions.insert(idx, action1)
            actions.insert(idx + 1, action2)
            actions.insert(idx + 2, action3)
            actions.insert(idx + 3, action4)
            idx += 4
        elif actions[idx].opcode == "send_any_wcont":
            # PSEUDO:   send_any_wcont    Xe      Xc      Xptr    <X1, X2… Xn>    Xtmp1
            # HERE:     send_any_wcont    event   cont    op1     reglist         tmp_reg1
            # AFTER:    send    event   cont    op1     len(reglist)    0
            # ISA:      send    Xe      Xc      Xptr    $len            $mode[1]
            tmp_reg1    = actions[idx].tmp_reg1
            op1         = actions[idx].op1
            reglist     = actions[idx].reglist
            cont        = actions[idx].cont
            event       = actions[idx].event
            actions.pop(idx)
            action, maxudp, maxop = GetAction(f"{label}: movir {tmp_reg1} 0")
            actions.insert(idx, action)
            action, maxudp, maxop = GetAction(f"add {op1} {tmp_reg1} {tmp_reg1}")
            actions.insert(idx + 1, action)
            for i in range (len(reglist)):
                action, maxudp, maxop = GetAction(f"movrl {reglist[i]} 0({tmp_reg1}) 1 8")
                actions.insert(idx + 2 + i, action)
            action, maxudp, maxop = GetAction(f"send {event} {cont} {op1} {len(reglist)} 0")
            actions.insert(idx + 2 + len(reglist), action)
            idx += 3+len(reglist)
        elif actions[idx].opcode == "send_any_wret":
            # PSEUDO:   send_any_wret     Xe      $cont       Xptr    <X1, X2… Xn>    Xtmp1
            # HERE:     send_any_wret     event   cont        op1     reglist         tmp_reg1
            # AFTER:    send    event   tmp_reg1    op1     len(reglist)    0
            # ISA:      send    Xe      Xc          Xptr    $len            $mode[1]
            tmp_reg1    = actions[idx].tmp_reg1
            op1         = actions[idx].op1
            reglist     = actions[idx].reglist
            cont        = actions[idx].cont
            event       = actions[idx].event
            actions.pop(idx)
            action, maxudp, maxop = GetAction(f"{label}: movir {tmp_reg1} 0")
            actions.insert(idx, action)
            action, maxudp, maxop = GetAction(f"add {op1} {tmp_reg1} {tmp_reg1}")
            actions.insert(idx + 1, action)
            for i in range (len(reglist)):
                action, maxudp, maxop = GetAction(f"movrl {reglist[i]} 0({tmp_reg1}) 1 8")
                actions.insert(idx + 2 + i, action)
            action, maxudp, maxop = GetAction(f"addi X2 {tmp_reg1} 0")
            actions.insert(idx + 2 + len(reglist), action)
            action, maxudp, maxop = GetAction(f"evlb {tmp_reg1} {cont}")
            actions.insert(idx + 3 + len(reglist), action)
            action, maxudp, maxop = GetAction(f"send {event} {tmp_reg1} {op1} {len(reglist)} 0")
            actions.insert(idx + 4 + len(reglist), action)
            idx += 5+len(reglist)
        else:#-------------------------------
            idx += 1

    return actions
