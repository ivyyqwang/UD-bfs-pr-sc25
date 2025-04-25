from linker.EFAProgram import efaProgram

## Global constants

@efaProgram
def EFA_launchers(efa):
  efa.code_level = 'machine'
  state0 = efa.State("udweave_init") #Only one state code 
  efa.add_initId(state0.state_id)
  ## Static declarations
  ## Scoped Variable "num_threads_v" uses Register X16, scope (0)
  ## Scoped Variable "num_threads_split_v" uses Register X17, scope (0)
  ## Scoped Variable "map_dram_ptr" uses Register X18, scope (0)
  ## Scoped Variable "reduce_dram_head_ptr" uses Register X19, scope (0)
  ## Scoped Variable "previous_vid" uses Register X20, scope (0)
  ## Scoped Variable "previous_split_vid" uses Register X21, scope (0)
  ## Scoped Variable "map_count_finish1" uses Register X22, scope (0)
  ## Scoped Variable "map_count_finish2" uses Register X23, scope (0)
  ## Scoped Variable "reduce_count_finish" uses Register X24, scope (0)
  ## Scoped Variable "edges_count" uses Register X25, scope (0)
  ## Param "_gv" uses Register X8, scope (0->16)
  ## Param "_queue_start" uses Register X9, scope (0->16)
  ## Param "_queue_length" uses Register X10, scope (0->16)
  ## Param "_itera" uses Register X11, scope (0->16)
  ## Param "_num_lanes_total" uses Register X12, scope (0->16)
  ## Scoped Variable "lmbuff" uses Register X26, scope (0->16)
  ## Scoped Variable "temp_lmbuff" uses Register X27, scope (0->16)
  ## Scoped Variable "tmp" uses Register X28, scope (0->16->21)
  ## Scoped Variable "i" uses Register X29, scope (0->16->21->22)
  ## Param "length" uses Register X8, scope (0->25)
  ## Scoped Variable "lmbuff" uses Register X26, scope (0->25)
  ## Scoped Variable "queue_length" uses Register X27, scope (0->25)
  ## Scoped Variable "cont" uses Register X28, scope (0->25)
  ## Param "op0" uses Register X8, scope (0->28)
  ## Param "op1" uses Register X9, scope (0->28)
  ## Scoped Variable "lmbuff" uses Register X26, scope (0->28)
  ## Scoped Variable "tid" uses Register X27, scope (0->28)
  ## Scoped Variable "evword" uses Register X28, scope (0->28)
  ## Param "itera" uses Register X8, scope (0->29)
  ## Scoped Variable "lmbuff" uses Register X26, scope (0->29)
  ## Scoped Variable "launch_count" uses Register X27, scope (0->29)
  ## Scoped Variable "map_count" uses Register X28, scope (0->29)
  ## Scoped Variable "cont" uses Register X29, scope (0->29->33)
  ## Param "itera" uses Register X8, scope (0->36)
  ## Scoped Variable "lmbuff" uses Register X26, scope (0->36)
  ## Scoped Variable "launch_count" uses Register X27, scope (0->36)
  ## Scoped Variable "map_count" uses Register X28, scope (0->36)
  ## Scoped Variable "cont" uses Register X29, scope (0->36->40->42)
  ## Param "vid" uses Register X8, scope (0->43)
  ## Param "parent" uses Register X9, scope (0->43)
  ## Scoped Variable "temp_lmbuff" uses Register X26, scope (0->43)
  ## Scoped Variable "evword" uses Register X27, scope (0->43)
  ## Param "vid" uses Register X8, scope (0->44)
  ## Param "parent" uses Register X9, scope (0->44)
  ## Scoped Variable "temp_lmbuff" uses Register X26, scope (0->44)
  ## Scoped Variable "evword" uses Register X27, scope (0->44)
  ## Param "n_v" uses Register X8, scope (0->45)
  ## Param "vid" uses Register X9, scope (0->45)
  ## Scoped Variable "lmbuff" uses Register X26, scope (0->45)
  ## Scoped Variable "map_count" uses Register X27, scope (0->45)
  ## Scoped Variable "launch_count" uses Register X28, scope (0->45->47->49)
  ## Scoped Variable "launch_count" uses Register X28, scope (0->45->52)
  ## Param "n_v" uses Register X8, scope (0->58)
  ## Param "vid" uses Register X9, scope (0->58)
  ## Scoped Variable "lmbuff" uses Register X26, scope (0->58)
  ## Scoped Variable "map_count" uses Register X27, scope (0->58)
  ## Scoped Variable "launch_count" uses Register X28, scope (0->58)
  ## Scoped Variable "cont" uses Register X28, scope (0->58->60->62)
  ## Scoped Variable "lmbuff" uses Register X26, scope (0->65)
  ## Scoped Variable "iter" uses Register X27, scope (0->65)
  ## Scoped Variable "evword" uses Register X28, scope (0->65)
  ## Scoped Variable "lmbuff" uses Register X26, scope (0->66)
  ## Scoped Variable "reduce_count" uses Register X27, scope (0->66)
  ## Scoped Variable "itera" uses Register X28, scope (0->66->68->70)
  ## Scoped Variable "dram_ptr" uses Register X29, scope (0->66->68->70->74)
  ## Scoped Variable "dram_ptr" uses Register X29, scope (0->66->68->70->75)
  ## Scoped Variable "lmbuff" uses Register X26, scope (0->76)
  ## Scoped Variable "cont" uses Register X27, scope (0->76)
  ## Scoped Variable "reduce_count" uses Register X28, scope (0->76)
  ## Param "vid" uses Register X8, scope (0->77)
  ## Param "parent" uses Register X9, scope (0->77)
  ## Scoped Variable "lmbuff" uses Register X26, scope (0->77)
  ## Scoped Variable "hash_id" uses Register X27, scope (0->77)
  ## Scoped Variable "total_lane" uses Register X28, scope (0->77)
  ## Scoped Variable "index" uses Register X29, scope (0->77)
  ## Scoped Variable "dram_ptr" uses Register X30, scope (0->77)
  ## Param "vid" uses Register X8, scope (0->83)
  ## Param "parent" uses Register X9, scope (0->83)
  ## Scoped Variable "lmbuff" uses Register X26, scope (0->83)
  ## Scoped Variable "tid" uses Register X27, scope (0->83)
  ## Scoped Variable "evword0" uses Register X28, scope (0->83)
  ## Scoped Variable "evword" uses Register X29, scope (0->83)
  ## Param "vid" uses Register X8, scope (0->84)
  ## Param "parent" uses Register X9, scope (0->84)
  ## Scoped Variable "lmbuff" uses Register X26, scope (0->84)
  ## Scoped Variable "tid" uses Register X27, scope (0->84)
  ## Scoped Variable "evword0" uses Register X28, scope (0->84)
  ## Scoped Variable "evword" uses Register X29, scope (0->84)
  ## Param "vid" uses Register X8, scope (0->85)
  ## Param "parent" uses Register X9, scope (0->85)
  ## Scoped Variable "lmbuff" uses Register X26, scope (0->85)
  ## Scoped Variable "hash_id" uses Register X27, scope (0->85)
  ## Scoped Variable "tmp" uses Register X28, scope (0->85)
  ## Scoped Variable "cache_vid" uses Register X29, scope (0->85)
  ## Scoped Variable "dram_ptr" uses Register X30, scope (0->85)
  ## Scoped Variable "lmbuff" uses Register X26, scope (0->95)
  ## Scoped Variable "total" uses Register X27, scope (0->95)
  ## Scoped Variable "launch_count" uses Register X28, scope (0->95->97->99)
  ## Scoped Variable "lmbuff" uses Register X26, scope (0->102)
  ## Scoped Variable "reduce_count" uses Register X27, scope (0->102)
  ## Scoped Variable "itera" uses Register X28, scope (0->102->104->106)
  ## Scoped Variable "dram_ptr" uses Register X29, scope (0->102->104->106->110)
  ## Scoped Variable "dram_ptr" uses Register X29, scope (0->102->104->106->111)
  ## This is all metadata information
  ## #define DEBUG
  ## This is all metadata information
  ## Total threads used in BFS
  ## #define NUM_THREADS 245
  ## #define NUM_LANES_PER_MASTER 2048
  ## Each threads in the same lane shared the following scratchpad
  ## send buffer 1 - 17 (16 words)
  ## #define DEBUG
  ## #define LANEID 2023
  
  ################################################
  ###### Writing code for thread map_master ######
  ################################################
  # Writing code for event map_master::init
  tranmap_master__init = efa.writeEvent('map_master::init')
  ## #ifdef DEBUG
  ## print("[DEBUG][NWID %lu] <init> start addr = 0x%lx, len = %lu", NETID, _queue_start, _queue_length);
  ## #endif
  tranmap_master__init.writeAction(f"entry: addi X7 X26 0") 
  tranmap_master__init.writeAction(f"sri X2 X28 24") 
  tranmap_master__init.writeAction(f"andi X28 X28 255") 
  tranmap_master__init.writeAction(f"movrl X28 160(X26) 0 8") 
  tranmap_master__init.writeAction(f"movrl X1 168(X26) 0 8") 
  tranmap_master__init.writeAction(f"andi X11 X27 1") 
  tranmap_master__init.writeAction(f"bneiu X27 0 __if_init_1_false") 
  tranmap_master__init.writeAction(f"__if_init_0_true: addi X9 X18 16") 
  tranmap_master__init.writeAction(f"sli X10 X27 3") 
  tranmap_master__init.writeAction(f"add X18 X27 X19") 
  tranmap_master__init.writeAction(f"send_dmlm_ld_wret X9 map_master::read_length_from_dram 1 X27") 
  tranmap_master__init.writeAction(f"jmp __if_init_2_post") 
  tranmap_master__init.writeAction(f"__if_init_1_false: addi X9 X19 16") 
  tranmap_master__init.writeAction(f"sli X10 X27 3") 
  tranmap_master__init.writeAction(f"add X19 X27 X18") 
  tranmap_master__init.writeAction(f"addi X9 X27 8") 
  tranmap_master__init.writeAction(f"send_dmlm_ld_wret X27 map_master::read_length_from_dram 1 X28") 
  ## lmbuff[GV] = _gv;
  tranmap_master__init.writeAction(f"__if_init_2_post: movrl X10 304(X26) 0 8") 
  tranmap_master__init.writeAction(f"movrl X18 192(X26) 0 8") 
  ## lmbuff[UPDATE_V] = 0;
  tranmap_master__init.writeAction(f"movir X28 0") 
  tranmap_master__init.writeAction(f"movrl X28 224(X26) 0 8") 
  tranmap_master__init.writeAction(f"movrl X11 232(X26) 0 8") 
  tranmap_master__init.writeAction(f"movir X28 0") 
  tranmap_master__init.writeAction(f"movrl X28 240(X26) 0 8") 
  tranmap_master__init.writeAction(f"movir X28 0") 
  tranmap_master__init.writeAction(f"movrl X28 264(X26) 0 8") 
  tranmap_master__init.writeAction(f"movrl X12 320(X26) 0 8") 
  tranmap_master__init.writeAction(f"movir X28 0") 
  tranmap_master__init.writeAction(f"movrl X28 216(X26) 0 8") 
  tranmap_master__init.writeAction(f"movir X16 122") 
  tranmap_master__init.writeAction(f"movir X17 0") 
  tranmap_master__init.writeAction(f"movir X20 -1") 
  tranmap_master__init.writeAction(f"movir X21 -1") 
  tranmap_master__init.writeAction(f"movir X22 0") 
  tranmap_master__init.writeAction(f"movir X23 0") 
  tranmap_master__init.writeAction(f"movir X24 0") 
  tranmap_master__init.writeAction(f"movir X25 0") 
  tranmap_master__init.writeAction(f"addi X7 X28 8") 
  tranmap_master__init.writeAction(f"addi X28 X27 64") 
  tranmap_master__init.writeAction(f"movrl X8 0(X27) 0 8") 
  tranmap_master__init.writeAction(f"movrl X12 24(X27) 0 8") 
  tranmap_master__init.writeAction(f"movrl X11 32(X27) 0 8") 
  tranmap_master__init.writeAction(f"bneiu X11 0 __if_init_5_post") 
  tranmap_master__init.writeAction(f"__if_init_3_true: addi X7 X26 16384") 
  tranmap_master__init.writeAction(f"movir X28 4096") 
  tranmap_master__init.writeAction(f"movir X29 0") 
  tranmap_master__init.writeAction(f"__for_init_6_condition: bleu X28 X29 __if_init_5_post") 
  tranmap_master__init.writeAction(f"__for_init_7_body: movir X31 -1") 
  tranmap_master__init.writeAction(f"movwrl X31 X26(X29,0,0)") 
  tranmap_master__init.writeAction(f"addi X29 X29 1") 
  tranmap_master__init.writeAction(f"jmp __for_init_6_condition") 
  tranmap_master__init.writeAction(f"__if_init_5_post: yield") 
  
  # Writing code for event map_master::read_length_from_dram
  tranmap_master__read_length_from_dram = efa.writeEvent('map_master::read_length_from_dram')
  ## #ifdef DEBUG
  ## print("[DEBUG][NWID %lu] <MASTER read_length_from_dram> length = %lu", NETID, length);
  ## #endif
  tranmap_master__read_length_from_dram.writeAction(f"entry: addi X7 X26 0") 
  tranmap_master__read_length_from_dram.writeAction(f"movlr 304(X26) X27 0 8") 
  tranmap_master__read_length_from_dram.writeAction(f"bleu X8 X27 __if_read_length_from_dram_2_post") 
  tranmap_master__read_length_from_dram.writeAction(f"__if_read_length_from_dram_0_true: print 'Error, queue length not long enough, please increase queue length, current queue length is %lu, need queue length is %lu' X27 X8") 
  tranmap_master__read_length_from_dram.writeAction(f"__if_read_length_from_dram_2_post: movrl X8 200(X26) 0 8") 
  tranmap_master__read_length_from_dram.writeAction(f"movrl X8 208(X26) 0 8") 
  tranmap_master__read_length_from_dram.writeAction(f"movrl X8 248(X26) 0 8") 
  tranmap_master__read_length_from_dram.writeAction(f"movrl X8 256(X26) 0 8") 
  tranmap_master__read_length_from_dram.writeAction(f"movlr 168(X26) X28 0 8") 
  tranmap_master__read_length_from_dram.writeAction(f"movir X29 -1") 
  tranmap_master__read_length_from_dram.writeAction(f"sri X29 X29 1") 
  tranmap_master__read_length_from_dram.writeAction(f"sendr_wcont X28 X29 X0 X0") 
  tranmap_master__read_length_from_dram.writeAction(f"movir X30 1") 
  tranmap_master__read_length_from_dram.writeAction(f"movrl X30 216(X26) 0 8") 
  tranmap_master__read_length_from_dram.writeAction(f"yield") 
  
  # Writing code for event map_master::send_to_map_master_thread
  tranmap_master__send_to_map_master_thread = efa.writeEvent('map_master::send_to_map_master_thread')
  tranmap_master__send_to_map_master_thread.writeAction(f"entry: addi X7 X26 0") 
  tranmap_master__send_to_map_master_thread.writeAction(f"movrl X1 168(X26) 0 8") 
  tranmap_master__send_to_map_master_thread.writeAction(f"movlr 160(X26) X28 0 8") 
  tranmap_master__send_to_map_master_thread.writeAction(f"addi X28 X27 0")  # This is for casting. May be used later on
  ## #ifdef DEBUG
  ##         print("[DEBUG][NWID %lu] <send_to_worker_thread2> tid:%ld, CCONT=%lu", NETID, tid, CCONT);
  ## #endif
  tranmap_master__send_to_map_master_thread.writeAction(f"ev X8 X28 X27 X27 4") 
  tranmap_master__send_to_map_master_thread.writeAction(f"sendr_wcont X28 X1 X9 X9") 
  ## #ifdef DEBUG
  ##         print("[DEBUG][NWID %lu] <send_to_worker_thread2> op1:%lu", NETID, op1);
  ## #endif
  ## if(NETID == LANEID){
  ##     print("[DEBUG][NWID %lu] <send_to_worker_thread2> op1:%lu", NETID, op1);
  ## }
  tranmap_master__send_to_map_master_thread.writeAction(f"yield_terminate") 
  
  # Writing code for event map_master::start
  tranmap_master__start = efa.writeEvent('map_master::start')
  tranmap_master__start.writeAction(f"entry: addi X7 X26 0") 
  tranmap_master__start.writeAction(f"movlr 240(X26) X27 0 8") 
  tranmap_master__start.writeAction(f"movlr 200(X26) X28 0 8") 
  tranmap_master__start.writeAction(f"movir X30 2") 
  tranmap_master__start.writeAction(f"movrl X30 216(X26) 0 8") 
  tranmap_master__start.writeAction(f"__while_start_0_condition: cgti X16 X29 0") 
  tranmap_master__start.writeAction(f"clt X27 X28 X30") 
  tranmap_master__start.writeAction(f"and X29 X30 X31") 
  tranmap_master__start.writeAction(f"beqiu X31 0 __while_start_2_post") 
  ## #ifdef DEBUG
  ## print("[DEBUG][NWID %lu] <launch_v> launch_count = %lu", NETID, launch_count);
  ## #endif
  tranmap_master__start.writeAction(f"__while_start_1_body: send_dmlm_ld_wret X18 map_master::receive_dram 2 X29") 
  tranmap_master__start.writeAction(f"addi X18 X18 16") 
  tranmap_master__start.writeAction(f"addi X27 X27 2") 
  tranmap_master__start.writeAction(f"subi X16 X16 1") 
  tranmap_master__start.writeAction(f"jmp __while_start_0_condition") 
  tranmap_master__start.writeAction(f"__while_start_2_post: bneu X28 X23 __if_start_5_post") 
  tranmap_master__start.writeAction(f"__if_start_3_true: movlr 168(X26) X29 0 8") 
  ## unsigned long update_v = lmbuff[UPDATE_V];
  tranmap_master__start.writeAction(f"movir X30 -1") 
  tranmap_master__start.writeAction(f"sri X30 X30 1") 
  tranmap_master__start.writeAction(f"sendr_wcont X29 X30 X28 X0") 
  ## #ifdef DEBUG
  ## print("[DEBUG][NWID %lu] <start>: cont %lu, map count = %lu, v count finish = %lu", NETID, cont, map_count, map_count_finish2);
  ## #endif
  tranmap_master__start.writeAction(f"movir X31 3") 
  tranmap_master__start.writeAction(f"movrl X31 216(X26) 0 8") 
  tranmap_master__start.writeAction(f"__if_start_5_post: bleiu X16 0 __if_start_8_post") 
  tranmap_master__start.writeAction(f"__if_start_6_true: addi X16 X17 0") 
  tranmap_master__start.writeAction(f"movir X16 0") 
  tranmap_master__start.writeAction(f"__if_start_8_post: movrl X27 240(X26) 0 8") 
  tranmap_master__start.writeAction(f"yield") 
  
  # Writing code for event map_master::start_split_v
  tranmap_master__start_split_v = efa.writeEvent('map_master::start_split_v')
  tranmap_master__start_split_v.writeAction(f"entry: addi X7 X26 0") 
  tranmap_master__start_split_v.writeAction(f"movlr 240(X26) X27 0 8") 
  tranmap_master__start_split_v.writeAction(f"movlr 248(X26) X28 0 8") 
  tranmap_master__start_split_v.writeAction(f"__while_start_split_v_0_condition: cgti X17 X29 0") 
  tranmap_master__start_split_v.writeAction(f"clt X27 X28 X30") 
  tranmap_master__start_split_v.writeAction(f"and X29 X30 X31") 
  tranmap_master__start_split_v.writeAction(f"beqiu X31 0 __while_start_split_v_2_post") 
  ## #ifdef DEBUG
  ## print("[DEBUG][NWID %lu] <launch_v> launch_count = %lu", NETID, launch_count);
  ## #endif
  tranmap_master__start_split_v.writeAction(f"__while_start_split_v_1_body: send_dmlm_ld_wret X18 map_master::receive_dram_split_v 2 X29") 
  tranmap_master__start_split_v.writeAction(f"addi X18 X18 16") 
  tranmap_master__start_split_v.writeAction(f"addi X27 X27 2") 
  tranmap_master__start_split_v.writeAction(f"subi X17 X17 1") 
  tranmap_master__start_split_v.writeAction(f"jmp __while_start_split_v_0_condition") 
  tranmap_master__start_split_v.writeAction(f"__while_start_split_v_2_post: movlr 208(X26) X28 0 8") 
  tranmap_master__start_split_v.writeAction(f"movlr 264(X26) X29 0 8") 
  tranmap_master__start_split_v.writeAction(f"add X28 X29 X28") 
  ## print("[DEBUG][NWID %lu] <start_split_v> map_count = %lu, num_threads = %lu", NETID, map_count, num_threads);
  tranmap_master__start_split_v.writeAction(f"bneu X28 X22 __if_start_split_v_5_post") 
  tranmap_master__start_split_v.writeAction(f"__if_start_split_v_3_true: movlr 216(X26) X29 0 8") 
  tranmap_master__start_split_v.writeAction(f"bneiu X29 4 __if_start_split_v_5_post") 
  tranmap_master__start_split_v.writeAction(f"__if_start_split_v_6_true: movlr 168(X26) X29 0 8") 
  ## unsigned long update_v = lmbuff[UPDATE_V];
  tranmap_master__start_split_v.writeAction(f"movir X30 -1") 
  tranmap_master__start_split_v.writeAction(f"sri X30 X30 1") 
  tranmap_master__start_split_v.writeAction(f"sendr_wcont X29 X30 X28 X0") 
  ## #ifdef DEBUG
  ## print("[DEBUG][NWID %lu] <start>: cont %lu", NETID, cont);
  ## #endif
  tranmap_master__start_split_v.writeAction(f"movir X31 5") 
  tranmap_master__start_split_v.writeAction(f"movrl X31 216(X26) 0 8") 
  tranmap_master__start_split_v.writeAction(f"__if_start_split_v_5_post: movrl X27 240(X26) 0 8") 
  tranmap_master__start_split_v.writeAction(f"yield") 
  
  # Writing code for event map_master::receive_dram
  tranmap_master__receive_dram = efa.writeEvent('map_master::receive_dram')
  tranmap_master__receive_dram.writeAction(f"entry: addi X7 X27 8") 
  tranmap_master__receive_dram.writeAction(f"addi X27 X26 64") 
  ## unsigned long* local lmbuff = LMBASE;
  ## temp_lmbuff[0] = lmbuff[GV];
  tranmap_master__receive_dram.writeAction(f"movrl X8 8(X26) 0 8") 
  tranmap_master__receive_dram.writeAction(f"movrl X9 16(X26) 0 8") 
  ## temp_lmbuff[3] = lmbuff[NUM_LANES_TOTAL];
  ## temp_lmbuff[4] = lmbuff[ITERATION];
  tranmap_master__receive_dram.writeAction(f"movir X28 0") 
  tranmap_master__receive_dram.writeAction(f"movrl X28 40(X26) 0 8") 
  tranmap_master__receive_dram.writeAction(f"movir X27 0") 
  tranmap_master__receive_dram.writeAction(f"evlb X27 vertex_master__launch") 
  tranmap_master__receive_dram.writeAction(f"evi X27 X27 255 4") 
  tranmap_master__receive_dram.writeAction(f"ev X27 X27 X0 X0 8") 
  tranmap_master__receive_dram.writeAction(f"send_wret X27 map_master::vertex_term X26 6 X28") 
  tranmap_master__receive_dram.writeAction(f"yield") 
  
  # Writing code for event map_master::receive_dram_split_v
  tranmap_master__receive_dram_split_v = efa.writeEvent('map_master::receive_dram_split_v')
  tranmap_master__receive_dram_split_v.writeAction(f"entry: addi X7 X27 8") 
  tranmap_master__receive_dram_split_v.writeAction(f"addi X27 X26 64") 
  ## unsigned long* local lmbuff = LMBASE;
  ## temp_lmbuff[0] = lmbuff[GV];
  tranmap_master__receive_dram_split_v.writeAction(f"movrl X8 8(X26) 0 8") 
  tranmap_master__receive_dram_split_v.writeAction(f"movrl X9 16(X26) 0 8") 
  ## temp_lmbuff[3] = lmbuff[NUM_LANES_TOTAL];
  ## temp_lmbuff[4] = lmbuff[ITERATION];
  tranmap_master__receive_dram_split_v.writeAction(f"movir X28 1") 
  tranmap_master__receive_dram_split_v.writeAction(f"movrl X28 40(X26) 0 8") 
  tranmap_master__receive_dram_split_v.writeAction(f"movir X27 0") 
  tranmap_master__receive_dram_split_v.writeAction(f"evlb X27 vertex_master__launch") 
  tranmap_master__receive_dram_split_v.writeAction(f"evi X27 X27 255 4") 
  tranmap_master__receive_dram_split_v.writeAction(f"ev X27 X27 X0 X0 8") 
  tranmap_master__receive_dram_split_v.writeAction(f"send_wret X27 map_master::vertex_term_split_v X26 6 X28") 
  tranmap_master__receive_dram_split_v.writeAction(f"yield") 
  
  # Writing code for event map_master::vertex_term
  tranmap_master__vertex_term = efa.writeEvent('map_master::vertex_term')
  ## vertex thread terminated
  ## #ifdef DEBUG
  ##         print("[DEBUG][NWID %lu] <vertex_term>: nv %lu", NETID, n_v);
  ## #endif
  tranmap_master__vertex_term.writeAction(f"entry: addi X7 X26 0") 
  tranmap_master__vertex_term.writeAction(f"addi X22 X22 2") 
  tranmap_master__vertex_term.writeAction(f"addi X23 X23 2") 
  tranmap_master__vertex_term.writeAction(f"addi X16 X16 1") 
  tranmap_master__vertex_term.writeAction(f"movlr 200(X26) X27 0 8") 
  ## Check if map finished
  tranmap_master__vertex_term.writeAction(f"bneu X23 X27 __if_vertex_term_1_false") 
  tranmap_master__vertex_term.writeAction(f"__if_vertex_term_0_true: movlr 216(X26) X28 0 8") 
  tranmap_master__vertex_term.writeAction(f"bneiu X28 2 __if_vertex_term_5_post") 
  tranmap_master__vertex_term.writeAction(f"__if_vertex_term_3_true: movlr 168(X26) X28 0 8") 
  tranmap_master__vertex_term.writeAction(f"movir X29 -1") 
  tranmap_master__vertex_term.writeAction(f"sri X29 X29 1") 
  tranmap_master__vertex_term.writeAction(f"sendr_wcont X28 X29 X27 X0") 
  tranmap_master__vertex_term.writeAction(f"movir X30 3") 
  tranmap_master__vertex_term.writeAction(f"movrl X30 216(X26) 0 8") 
  tranmap_master__vertex_term.writeAction(f"add X17 X16 X17") 
  tranmap_master__vertex_term.writeAction(f"movir X16 0") 
  tranmap_master__vertex_term.writeAction(f"movlr 248(X26) X27 0 8") 
  tranmap_master__vertex_term.writeAction(f"movlr 240(X26) X28 0 8") 
  tranmap_master__vertex_term.writeAction(f"__while_vertex_term_6_condition: cgti X17 X29 0") 
  tranmap_master__vertex_term.writeAction(f"clt X28 X27 X30") 
  tranmap_master__vertex_term.writeAction(f"and X29 X30 X31") 
  tranmap_master__vertex_term.writeAction(f"beqi X31 0 __while_vertex_term_8_post") 
  tranmap_master__vertex_term.writeAction(f"__while_vertex_term_7_body: send_dmlm_ld_wret X18 map_master::receive_dram_split_v 2 X29") 
  tranmap_master__vertex_term.writeAction(f"addi X18 X18 16") 
  tranmap_master__vertex_term.writeAction(f"addi X28 X28 2") 
  tranmap_master__vertex_term.writeAction(f"subi X17 X17 1") 
  tranmap_master__vertex_term.writeAction(f"jmp __while_vertex_term_6_condition") 
  tranmap_master__vertex_term.writeAction(f"__while_vertex_term_8_post: movrl X28 240(X26) 0 8") 
  tranmap_master__vertex_term.writeAction(f"__if_vertex_term_5_post: jmp __if_vertex_term_2_post") 
  tranmap_master__vertex_term.writeAction(f"__if_vertex_term_1_false: movlr 240(X26) X28 0 8") 
  tranmap_master__vertex_term.writeAction(f"ble X27 X28 __if_vertex_term_10_false") 
  tranmap_master__vertex_term.writeAction(f"__if_vertex_term_9_true: subi X16 X16 1") 
  tranmap_master__vertex_term.writeAction(f"send_dmlm_ld_wret X18 map_master::receive_dram 2 X29") 
  tranmap_master__vertex_term.writeAction(f"addi X18 X18 16") 
  tranmap_master__vertex_term.writeAction(f"addi X28 X28 2") 
  tranmap_master__vertex_term.writeAction(f"jmp __if_vertex_term_11_post") 
  tranmap_master__vertex_term.writeAction(f"__if_vertex_term_10_false: subi X16 X16 1") 
  tranmap_master__vertex_term.writeAction(f"addi X17 X17 1") 
  tranmap_master__vertex_term.writeAction(f"movlr 248(X26) X27 0 8") 
  tranmap_master__vertex_term.writeAction(f"ble X27 X28 __if_vertex_term_11_post") 
  tranmap_master__vertex_term.writeAction(f"__if_vertex_term_12_true: subi X17 X17 1") 
  tranmap_master__vertex_term.writeAction(f"send_dmlm_ld_wret X18 map_master::receive_dram_split_v 2 X29") 
  tranmap_master__vertex_term.writeAction(f"addi X18 X18 16") 
  tranmap_master__vertex_term.writeAction(f"addi X28 X28 2") 
  tranmap_master__vertex_term.writeAction(f"__if_vertex_term_11_post: movrl X28 240(X26) 0 8") 
  tranmap_master__vertex_term.writeAction(f"__if_vertex_term_2_post: yield") 
  
  # Writing code for event map_master::vertex_term_split_v
  tranmap_master__vertex_term_split_v = efa.writeEvent('map_master::vertex_term_split_v')
  ## vertex thread terminated
  tranmap_master__vertex_term_split_v.writeAction(f"entry: addi X7 X26 0") 
  tranmap_master__vertex_term_split_v.writeAction(f"addi X22 X22 2") 
  tranmap_master__vertex_term_split_v.writeAction(f"addi X17 X17 1") 
  tranmap_master__vertex_term_split_v.writeAction(f"movlr 208(X26) X27 0 8") 
  tranmap_master__vertex_term_split_v.writeAction(f"movlr 264(X26) X28 0 8") 
  tranmap_master__vertex_term_split_v.writeAction(f"add X27 X28 X27") 
  ## #ifdef DEBUG
  ## print("[DEBUG][NWID %lu] <vertex_term>: map_count_finish1 %lu, map_count2 %lu, num_threads %lu", NETID, map_count_finish1, map_count, num_threads);
  ## #endif
  ## Check if map finished
  tranmap_master__vertex_term_split_v.writeAction(f"bneu X22 X27 __if_vertex_term_split_v_2_post") 
  tranmap_master__vertex_term_split_v.writeAction(f"__if_vertex_term_split_v_0_true: movlr 216(X26) X28 0 8") 
  tranmap_master__vertex_term_split_v.writeAction(f"bneiu X28 4 __if_vertex_term_split_v_2_post") 
  tranmap_master__vertex_term_split_v.writeAction(f"__if_vertex_term_split_v_3_true: movlr 168(X26) X28 0 8") 
  tranmap_master__vertex_term_split_v.writeAction(f"movir X29 -1") 
  tranmap_master__vertex_term_split_v.writeAction(f"sri X29 X29 1") 
  tranmap_master__vertex_term_split_v.writeAction(f"sendr_wcont X28 X29 X27 X0") 
  ## #ifdef DEBUG
  ## print("[DEBUG][NWID %lu] <vertex_term>: cont %lu", NETID, cont);
  ## #endif
  tranmap_master__vertex_term_split_v.writeAction(f"movir X30 5") 
  tranmap_master__vertex_term_split_v.writeAction(f"movrl X30 216(X26) 0 8") 
  tranmap_master__vertex_term_split_v.writeAction(f"__if_vertex_term_split_v_2_post: movlr 240(X26) X28 0 8") 
  tranmap_master__vertex_term_split_v.writeAction(f"movlr 248(X26) X27 0 8") 
  tranmap_master__vertex_term_split_v.writeAction(f"ble X27 X28 __if_vertex_term_split_v_8_post") 
  tranmap_master__vertex_term_split_v.writeAction(f"__if_vertex_term_split_v_6_true: send_dmlm_ld_wret X18 map_master::receive_dram_split_v 2 X29") 
  tranmap_master__vertex_term_split_v.writeAction(f"addi X18 X18 16") 
  tranmap_master__vertex_term_split_v.writeAction(f"addi X28 X28 2") 
  tranmap_master__vertex_term_split_v.writeAction(f"subi X17 X17 1") 
  tranmap_master__vertex_term_split_v.writeAction(f"movrl X28 240(X26) 0 8") 
  tranmap_master__vertex_term_split_v.writeAction(f"__if_vertex_term_split_v_8_post: yield") 
  
  # Writing code for event map_master::map_all_launched
  tranmap_master__map_all_launched = efa.writeEvent('map_master::map_all_launched')
  tranmap_master__map_all_launched.writeAction(f"entry: addi X7 X26 0") 
  tranmap_master__map_all_launched.writeAction(f"movlr 232(X26) X27 0 8") 
  tranmap_master__map_all_launched.writeAction(f"evi X2 X28 map_master::start_split_v 1") 
  tranmap_master__map_all_launched.writeAction(f"sendr_wret X28 map_master::vertex_term_split_v X27 X27 X29") 
  tranmap_master__map_all_launched.writeAction(f"movir X30 4") 
  tranmap_master__map_all_launched.writeAction(f"movrl X30 216(X26) 0 8") 
  tranmap_master__map_all_launched.writeAction(f"yield") 
  
  # Writing code for event map_master::map_split_all_launched
  tranmap_master__map_split_all_launched = efa.writeEvent('map_master::map_split_all_launched')
  ##print("[DEBUG][NWID %lu] <all_launched (v)>: master v all launch received", NETID);
  tranmap_master__map_split_all_launched.writeAction(f"entry: addi X7 X26 0") 
  tranmap_master__map_split_all_launched.writeAction(f"addi X24 X24 1") 
  tranmap_master__map_split_all_launched.writeAction(f"movlr 224(X26) X27 0 8") 
  tranmap_master__map_split_all_launched.writeAction(f"movir X29 6") 
  tranmap_master__map_split_all_launched.writeAction(f"movrl X29 216(X26) 0 8") 
  tranmap_master__map_split_all_launched.writeAction(f"addi X27 X28 1") 
  tranmap_master__map_split_all_launched.writeAction(f"bneu X24 X28 __if_map_split_all_launched_2_post") 
  tranmap_master__map_split_all_launched.writeAction(f"__if_map_split_all_launched_0_true: movlr 216(X26) X28 0 8") 
  tranmap_master__map_split_all_launched.writeAction(f"bneiu X28 6 __if_map_split_all_launched_2_post") 
  tranmap_master__map_split_all_launched.writeAction(f"__if_map_split_all_launched_3_true: movir X29 7") 
  tranmap_master__map_split_all_launched.writeAction(f"movrl X29 216(X26) 0 8") 
  tranmap_master__map_split_all_launched.writeAction(f"movlr 304(X26) X28 0 8") 
  tranmap_master__map_split_all_launched.writeAction(f"bleu X27 X28 __if_map_split_all_launched_8_post") 
  tranmap_master__map_split_all_launched.writeAction(f"__if_map_split_all_launched_6_true: movlr 304(X26) X28 0 8") 
  tranmap_master__map_split_all_launched.writeAction(f"print 'Reduce queue length %lu > malloc size %lu' X27 X28") 
  ## #ifdef DEBUG
  ## print("[DEBUG][NWID %lu] <map_split_all_launched> len:%lu", NETID, reduce_count);
  ## #endif
  tranmap_master__map_split_all_launched.writeAction(f"__if_map_split_all_launched_8_post: movlr 232(X26) X28 0 8") 
  tranmap_master__map_split_all_launched.writeAction(f"andi X28 X29 1") 
  tranmap_master__map_split_all_launched.writeAction(f"bneiu X29 0 __if_map_split_all_launched_10_false") 
  tranmap_master__map_split_all_launched.writeAction(f"__if_map_split_all_launched_9_true: movlr 192(X26) X29 0 8") 
  tranmap_master__map_split_all_launched.writeAction(f"subi X29 X29 8") 
  tranmap_master__map_split_all_launched.writeAction(f"sendr_dmlm_wret X29 map_master::wrtie_reduce_length X27 X30") 
  tranmap_master__map_split_all_launched.writeAction(f"yield") 
  tranmap_master__map_split_all_launched.writeAction(f"jmp __if_map_split_all_launched_2_post") 
  tranmap_master__map_split_all_launched.writeAction(f"__if_map_split_all_launched_10_false: subi X19 X29 16") 
  tranmap_master__map_split_all_launched.writeAction(f"sendr_dmlm_wret X29 map_master::wrtie_reduce_length X27 X30") 
  tranmap_master__map_split_all_launched.writeAction(f"yield") 
  tranmap_master__map_split_all_launched.writeAction(f"__if_map_split_all_launched_2_post: yield") 
  
  # Writing code for event map_master::wrtie_reduce_length
  tranmap_master__wrtie_reduce_length = efa.writeEvent('map_master::wrtie_reduce_length')
  tranmap_master__wrtie_reduce_length.writeAction(f"entry: addi X7 X26 0") 
  tranmap_master__wrtie_reduce_length.writeAction(f"movlr 168(X26) X27 0 8") 
  tranmap_master__wrtie_reduce_length.writeAction(f"movlr 224(X26) X28 0 8") 
  tranmap_master__wrtie_reduce_length.writeAction(f"movir X29 -1") 
  tranmap_master__wrtie_reduce_length.writeAction(f"sri X29 X29 1") 
  tranmap_master__wrtie_reduce_length.writeAction(f"sendr_wcont X27 X29 X28 X25") 
  tranmap_master__wrtie_reduce_length.writeAction(f"yield_terminate") 
  
  # Writing code for event map_master::add_v
  tranmap_master__add_v = efa.writeEvent('map_master::add_v')
  ## if(previous_vid == vid){
  ##     send_event(CCONT, vid, IGNRCONT);
  ##     #ifdef DEBUG
  ##     print("[DEBUG][NWID %lu] <add_v> vid:%lu, parent:%lu", NETID, vid, parent);
  ##     #endif
  ##     yield;
  ## }
  ## previous_vid = vid;
  tranmap_master__add_v.writeAction(f"entry: addi X25 X25 1") 
  tranmap_master__add_v.writeAction(f"addi X7 X26 0") 
  tranmap_master__add_v.writeAction(f"movir X27 0") 
  tranmap_master__add_v.writeAction(f"hash X8 X27") 
  tranmap_master__add_v.writeAction(f"movlr 320(X26) X28 0 8") 
  tranmap_master__add_v.writeAction(f"div X27 X28 X27") 
  tranmap_master__add_v.writeAction(f"andi X27 X27 2047") 
  tranmap_master__add_v.writeAction(f"addi X7 X26 16384") 
  tranmap_master__add_v.writeAction(f"sli X27 X29 1") 
  tranmap_master__add_v.writeAction(f"movwlr X26(X29,0,0) X28") 
  tranmap_master__add_v.writeAction(f"movir X27 -1") 
  tranmap_master__add_v.writeAction(f"bne X8 X28 __if_add_v_2_post") 
  tranmap_master__add_v.writeAction(f"__if_add_v_0_true: movir X30 -1") 
  tranmap_master__add_v.writeAction(f"sri X30 X30 1") 
  tranmap_master__add_v.writeAction(f"sendr_wcont X1 X30 X8 X8") 
  tranmap_master__add_v.writeAction(f"yield") 
  tranmap_master__add_v.writeAction(f"__if_add_v_2_post: bne X28 X27 __if_add_v_5_post") 
  tranmap_master__add_v.writeAction(f"__if_add_v_3_true: movwrl X8 X26(X29,0,0)") 
  tranmap_master__add_v.writeAction(f"addi X29 X30 1") 
  tranmap_master__add_v.writeAction(f"movwrl X27 X26(X30,0,0)") 
  tranmap_master__add_v.writeAction(f"__if_add_v_5_post: addi X7 X26 0") 
  tranmap_master__add_v.writeAction(f"movlr 224(X26) X27 0 8") 
  tranmap_master__add_v.writeAction(f"sli X27 X30 3") 
  tranmap_master__add_v.writeAction(f"add X19 X30 X30") 
  tranmap_master__add_v.writeAction(f"sendr2_dmlm_wret X30 map_master::wrtie_reduce_queue_return X8 X9 X31") 
  tranmap_master__add_v.writeAction(f"addi X27 X27 2") 
  tranmap_master__add_v.writeAction(f"movrl X27 224(X26) 0 8") 
  tranmap_master__add_v.writeAction(f"movir X31 -1") 
  tranmap_master__add_v.writeAction(f"sri X31 X31 1") 
  tranmap_master__add_v.writeAction(f"sendr_wcont X1 X31 X8 X8") 
  tranmap_master__add_v.writeAction(f"yield") 
  
  # Writing code for event map_master::add_vertex
  tranmap_master__add_vertex = efa.writeEvent('map_master::add_vertex')
  tranmap_master__add_vertex.writeAction(f"entry: addi X7 X26 0") 
  tranmap_master__add_vertex.writeAction(f"movlr 160(X26) X28 0 8") 
  tranmap_master__add_vertex.writeAction(f"addi X28 X27 0")  # This is for casting. May be used later on
  tranmap_master__add_vertex.writeAction(f"evi X2 X28 map_master::add_v 1") 
  tranmap_master__add_vertex.writeAction(f"ev X28 X29 X27 X27 4") 
  tranmap_master__add_vertex.writeAction(f"sendr_wcont X29 X1 X8 X9") 
  tranmap_master__add_vertex.writeAction(f"yield_terminate") 
  
  # Writing code for event map_master::add_split_vertex
  tranmap_master__add_split_vertex = efa.writeEvent('map_master::add_split_vertex')
  tranmap_master__add_split_vertex.writeAction(f"entry: addi X7 X26 0") 
  tranmap_master__add_split_vertex.writeAction(f"movlr 160(X26) X28 0 8") 
  tranmap_master__add_split_vertex.writeAction(f"addi X28 X27 0")  # This is for casting. May be used later on
  tranmap_master__add_split_vertex.writeAction(f"evi X2 X28 map_master::add_split_v 1") 
  tranmap_master__add_split_vertex.writeAction(f"ev X28 X29 X27 X27 4") 
  tranmap_master__add_split_vertex.writeAction(f"sendr_wcont X29 X1 X8 X9") 
  tranmap_master__add_split_vertex.writeAction(f"yield_terminate") 
  
  # Writing code for event map_master::add_split_v
  tranmap_master__add_split_v = efa.writeEvent('map_master::add_split_v')
  tranmap_master__add_split_v.writeAction(f"entry: movir X31 -1") 
  tranmap_master__add_split_v.writeAction(f"sri X31 X31 1") 
  tranmap_master__add_split_v.writeAction(f"sendr_wcont X1 X31 X8 X8") 
  ## if(previous_split_vid == vid){
  ##     #ifdef DEBUG
  ##     print("[DEBUG][NWID %lu] <add_split_v> vid:%lu, parent:%lu", NETID, vid, parent);
  ##     #endif
  ##     yield;
  ## }
  ## previous_split_vid = vid;
  tranmap_master__add_split_v.writeAction(f"addi X7 X26 0") 
  tranmap_master__add_split_v.writeAction(f"movir X27 0") 
  tranmap_master__add_split_v.writeAction(f"hash X8 X27") 
  tranmap_master__add_split_v.writeAction(f"movlr 320(X26) X28 0 8") 
  tranmap_master__add_split_v.writeAction(f"div X27 X28 X27") 
  tranmap_master__add_split_v.writeAction(f"andi X27 X27 2047") 
  tranmap_master__add_split_v.writeAction(f"sli X27 X27 1") 
  tranmap_master__add_split_v.writeAction(f"addi X7 X26 16384") 
  tranmap_master__add_split_v.writeAction(f"movwlr X26(X27,0,0) X29") 
  tranmap_master__add_split_v.writeAction(f"movir X28 -1") 
  tranmap_master__add_split_v.writeAction(f"bne X8 X29 __if_add_split_v_2_post") 
  tranmap_master__add_split_v.writeAction(f"__if_add_split_v_0_true: addi X27 X30 1") 
  tranmap_master__add_split_v.writeAction(f"movwlr X26(X30,0,0) X31") 
  tranmap_master__add_split_v.writeAction(f"beq X31 X28 __if_add_split_v_2_post") 
  tranmap_master__add_split_v.writeAction(f"__if_add_split_v_3_true: yield") 
  tranmap_master__add_split_v.writeAction(f"__if_add_split_v_2_post: bneu X29 X28 __if_add_split_v_8_post") 
  tranmap_master__add_split_v.writeAction(f"__if_add_split_v_6_true: movwrl X8 X26(X27,0,0)") 
  tranmap_master__add_split_v.writeAction(f"subi X28 X28 1") 
  tranmap_master__add_split_v.writeAction(f"addi X27 X30 1") 
  tranmap_master__add_split_v.writeAction(f"movwrl X28 X26(X30,0,0)") 
  tranmap_master__add_split_v.writeAction(f"__if_add_split_v_8_post: addi X7 X26 0") 
  ## if(num_threads_split_v > 0){
  ##         num_threads_split_v = num_threads_split_v - 1;
  ##         #ifdef DEBUG
  ##         if(NETID == LANEID){
  ##             print("[DEBUG][NWID %lu] <add_split_v> vid = %lu, parent = %lu", NETID, vid, parent);
  ##         }
  ##         #endif
  ##         long evword = evw_update_event(CEVNT, receive_dram_split_v);
  ##         send_event(evword, vid, parent, IGNRCONT);
  ##         tmp = lmbuff[MAP_COUNT_INFLIGHT];
  ##         lmbuff[MAP_COUNT_INFLIGHT] = tmp + 2;
  ##         yield;
  ## }
  tranmap_master__add_split_v.writeAction(f"movlr 192(X26) X30 0 8") 
  tranmap_master__add_split_v.writeAction(f"movlr 208(X26) X29 0 8") 
  tranmap_master__add_split_v.writeAction(f"sli X29 X31 3") 
  tranmap_master__add_split_v.writeAction(f"add X30 X31 X30") 
  tranmap_master__add_split_v.writeAction(f"addi X29 X29 2") 
  tranmap_master__add_split_v.writeAction(f"movrl X29 208(X26) 0 8") 
  tranmap_master__add_split_v.writeAction(f"movlr 304(X26) X31 0 8") 
  tranmap_master__add_split_v.writeAction(f"bleu X29 X31 __if_add_split_v_11_post") 
  tranmap_master__add_split_v.writeAction(f"__if_add_split_v_9_true: movlr 304(X26) X31 0 8") 
  tranmap_master__add_split_v.writeAction(f"print 'Error, queue length not long enough, please increase queue length, current queue length is %lu, need queue length is %lu' X31 X29") 
  tranmap_master__add_split_v.writeAction(f"__if_add_split_v_11_post: sendr2_dmlm_wret X30 map_master::write_map_queue_return X8 X9 X31") 
  tranmap_master__add_split_v.writeAction(f"yield") 
  
  # Writing code for event map_master::write_map_queue_return
  tranmap_master__write_map_queue_return = efa.writeEvent('map_master::write_map_queue_return')
  tranmap_master__write_map_queue_return.writeAction(f"entry: addi X7 X26 0") 
  tranmap_master__write_map_queue_return.writeAction(f"movlr 256(X26) X28 0 8") 
  tranmap_master__write_map_queue_return.writeAction(f"addi X28 X27 2") 
  tranmap_master__write_map_queue_return.writeAction(f"movrl X27 256(X26) 0 8") 
  tranmap_master__write_map_queue_return.writeAction(f"movlr 208(X26) X28 0 8") 
  tranmap_master__write_map_queue_return.writeAction(f"bneu X27 X28 __if_write_map_queue_return_2_post") 
  tranmap_master__write_map_queue_return.writeAction(f"__if_write_map_queue_return_0_true: movrl X27 248(X26) 0 8") 
  tranmap_master__write_map_queue_return.writeAction(f"bleiu X17 0 __if_write_map_queue_return_2_post") 
  tranmap_master__write_map_queue_return.writeAction(f"__if_write_map_queue_return_3_true: movlr 240(X26) X28 0 8") 
  tranmap_master__write_map_queue_return.writeAction(f"__while_write_map_queue_return_6_condition: cgti X17 X29 0") 
  tranmap_master__write_map_queue_return.writeAction(f"clt X28 X27 X30") 
  tranmap_master__write_map_queue_return.writeAction(f"and X29 X30 X31") 
  tranmap_master__write_map_queue_return.writeAction(f"beqiu X31 0 __while_write_map_queue_return_8_post") 
  tranmap_master__write_map_queue_return.writeAction(f"__while_write_map_queue_return_7_body: send_dmlm_ld_wret X18 map_master::receive_dram_split_v 2 X29") 
  tranmap_master__write_map_queue_return.writeAction(f"addi X18 X18 16") 
  tranmap_master__write_map_queue_return.writeAction(f"addi X28 X28 2") 
  tranmap_master__write_map_queue_return.writeAction(f"subi X17 X17 1") 
  tranmap_master__write_map_queue_return.writeAction(f"jmp __while_write_map_queue_return_6_condition") 
  tranmap_master__write_map_queue_return.writeAction(f"__while_write_map_queue_return_8_post: movrl X28 240(X26) 0 8") 
  tranmap_master__write_map_queue_return.writeAction(f"__if_write_map_queue_return_2_post: yield") 
  
  # Writing code for event map_master::wrtie_reduce_queue_return
  tranmap_master__wrtie_reduce_queue_return = efa.writeEvent('map_master::wrtie_reduce_queue_return')
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"entry: addi X7 X26 0") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"addi X24 X24 2") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"movlr 224(X26) X27 0 8") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"addi X27 X28 1") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"bneu X24 X28 __if_wrtie_reduce_queue_return_2_post") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"__if_wrtie_reduce_queue_return_0_true: movlr 216(X26) X28 0 8") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"bneiu X28 6 __if_wrtie_reduce_queue_return_2_post") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"__if_wrtie_reduce_queue_return_3_true: movir X29 7") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"movrl X29 216(X26) 0 8") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"movlr 304(X26) X28 0 8") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"bleu X27 X28 __if_wrtie_reduce_queue_return_8_post") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"__if_wrtie_reduce_queue_return_6_true: movlr 304(X26) X28 0 8") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"print 'Reduce queue length %lu > malloc size %lu' X27 X28") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"__if_wrtie_reduce_queue_return_8_post: movlr 232(X26) X28 0 8") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"andi X28 X29 1") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"bneiu X29 0 __if_wrtie_reduce_queue_return_10_false") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"__if_wrtie_reduce_queue_return_9_true: movlr 192(X26) X29 0 8") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"subi X29 X29 8") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"sendr_dmlm_wret X29 map_master::wrtie_reduce_length X27 X30") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"yield") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"jmp __if_wrtie_reduce_queue_return_2_post") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"__if_wrtie_reduce_queue_return_10_false: subi X19 X29 16") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"sendr_dmlm_wret X29 map_master::wrtie_reduce_length X27 X30") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"yield") 
  tranmap_master__wrtie_reduce_queue_return.writeAction(f"__if_wrtie_reduce_queue_return_2_post: yield") 
  
