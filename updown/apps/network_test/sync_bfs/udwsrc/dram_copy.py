from linker.EFAProgram import efaProgram

@efaProgram
def EFA_dram_copy(efa):
    efa.code_level = 'machine'
    state0 = efa.State("udweave_init") #Only one state code 
    efa.add_initId(state0.state_id)

    '''
    X8: DRAM Addr read
    X9: length
    X10: DRAM Addr write
    X11: FLAG_OFFSET
    '''

    ADDR = "X16"
    END_ADDR = "X17"
    WRITE_ADDR = "X18"
    FLAG_OFFSET = "X19"
    START_ADDR = "X20"
    TIMES = "X21"
    EV = "X22"
    TMP = "X23"
    EV2 = "X24"
    ADDR_OFFSET = "X25"
    ACCESS_TIMES = "X26"


    tran0 = efa.writeEvent('dram_copy::send_reads')
    tran0.writeAction("print 'START COPY'")
    tran0.writeAction(f"addi X8 {ADDR} 0")                  # ADDR = DRAM read addr
    tran0.writeAction(f"add X8 X9 {END_ADDR}")              # END_ADDR = DRAM read addr + length
    tran0.writeAction(f"addi X10 {WRITE_ADDR} 0")           # WRITE_ADDR 
    tran0.writeAction(f"addi X11 {FLAG_OFFSET} 0")
    tran0.writeAction(f"addi X8 {START_ADDR} 0")            # START_ADDR = DRAM fetch addr
    tran0.writeAction(f"movir {TIMES} 0")  

    tran0.writeAction(f'movir {EV} 0')
    tran0.writeAction(f'evi X2 {EV} dram_copy::read_returns 1')
    tran0.writeAction(f"send_loop: sendm {ADDR} {EV} {TMP} 8 0")
    # tran0.writeAction("print 'Send'")
    tran0.writeAction(f"addi {ADDR} {ADDR} 64")
    tran0.writeAction(f"addi {TIMES} {TIMES} 1")
    tran0.writeAction(f"blt {ADDR} {END_ADDR} send_loop")      
    tran0.writeAction("print 'Send finished'")
    tran0.writeAction("yield")                                        

    tran1 = efa.writeEvent('dram_copy::read_returns')
    # tran1.writeAction("print 'read_returns'")
    tran1.writeAction(f'sub X3 {START_ADDR} {ADDR_OFFSET}')
    tran1.writeAction(f'add {ADDR_OFFSET} {WRITE_ADDR} {ADDR_OFFSET}')
    tran1.writeAction(f'movir {EV2} 0')
    tran1.writeAction(f'evi X2 {EV2} dram_copy::write_returns 1')
    tran1.writeAction(f"sendmops {ADDR_OFFSET} {EV2} X8 8 1")
    tran1.writeAction("yield")        


    tran2 = efa.writeEvent('dram_copy::write_returns')
    # tran2.writeAction("print 'write_returns'")
    tran2.writeAction(f"subi {TIMES} {TIMES} 1")
    tran2.writeAction(f"beqi {TIMES} 0 all_done")                          
    tran2.writeAction("yield")                                        
    tran2.writeAction(f"all_done: movir {TMP} 1")                           
    tran2.writeAction(f"add X7 {FLAG_OFFSET} {FLAG_OFFSET}")
    tran2.writeAction("print 'NWID:%d COPY DONE' X0")
    tran2.writeAction(f"movrl {TMP} 0({FLAG_OFFSET}) 0 8")                    
    tran2.writeAction("yieldt")                              

