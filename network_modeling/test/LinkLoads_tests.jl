@testset "LinkLoads" begin 
  nnodes = 4
  nrouters = 5
  rmap = make_node2router_map(4, 5, 1)
  LL = LinkLoads(rmap, Int32(5))
  add_messages(LL, Int32(1), Int32(5))
  add_messages(LL, Int32(5), Int32(1))
  @test get_load(LL, Int32(1), Int32(5)) == 1
  @test get_load(LL, Int32(5), Int32(1)) == 1
  clear!(LL)
  @test get_load(LL, Int32(1), Int32(5)) == 0
  @test get_load(LL, Int32(5), Int32(1)) == 0
end 