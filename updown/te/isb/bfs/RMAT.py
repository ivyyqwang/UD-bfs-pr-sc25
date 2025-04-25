#!/usr/bin/python3
import numpy as np 
from scipy.sparse import coo_matrix
import os 
import sys
import argparse



def generate_n_write_RMAT(outdir,scale,seed,a=.59,b=.19,c=.19,avg_degree=16,clip_n_flip=False):

    assert outdir[-1] == '/'
    assert os.path.isdir(outdir)
    assert (a + b + c) <= 1.0 

    # filename = f"RMAT_a:{a}_b:{b}_c:{c}_avgDegree:{avg_degree}_clipnflip:{clip_n_flip}_scale:{scale}_seed:{seed}_edges.txt"
    filename = f"scale_{scale}_seed_{seed}_edges.txt"
    A = RMAT_coo_mat(scale, avg_degree, a, b, c, seed, clip_n_flip)

    with open(outdir + filename,"w") as f:    
        for (i,j) in zip(*A.nonzero()):
            f.write(f"{i} {j}\n")

    return A, filename

def RMAT_coo_mat(*args):

    n, m, Is, Js = RMAT(*args)     

    A = coo_matrix((np.ones(m),(Is,Js)),shape=(n,n))
    A = coo_matrix(A + A.T)
    A.sum_duplicates()
    A.data[:]=1
    return A 

def RMAT(scale, avg_deg=16, a = .57, b = .19, c = .19, seed=None, clip_n_flip=False):
    #graph 500 specifications

    if seed is not None: 
        np.random.seed(seed)

    n = 2**scale 

    m = int(avg_deg*n)

    Is = np.ones(m,dtype=int)
    Js = np.ones(m,dtype=int)

    ab = a + b
    c_norm = c/(1 - ab)
    a_norm = a/ab

    for ib in range(1,scale+1):
        
        for e_idx in range(m):
            i_bit = np.random.rand() > ab

            if i_bit:
                val_check = c_norm
            else: 
                val_check = a_norm
            j_bit = np.random.rand() > val_check#((c_norm if i_bit else 0.0) + (a_norm if not(i_bit) else 0.0))

            if i_bit:
                Is[e_idx] += 2**(ib-1)
            
            if j_bit:
                Js[e_idx] += 2**(ib-1)

    p = np.random.permutation(n)

    for e_idx in range(m):
        Is[e_idx] = p[Is[e_idx]-1]
        Js[e_idx] = p[Js[e_idx]-1]

    if clip_n_flip:
        #from (section 3.4,R-MAT: A Recursive Model for Graph Mining  Chakrabarti et al.)
        
        new_edge_count = 0
        for e_idx in range(m):
            if Is[e_idx] < Js[e_idx]:
                new_edge_count += 2 
            # get rid of self loops

        new_Is = np.empty(new_edge_count,dtype=int)
        new_Js = np.empty(new_edge_count,dtype=int)
        new_idx = 0

        for e_idx in range(m):

            if Is[e_idx] < Js[e_idx]:

                new_Is[new_idx] = Is[e_idx]
                new_Js[new_idx] = Js[e_idx]
                new_idx += 1

                new_Is[new_idx] = Js[e_idx]
                new_Js[new_idx] = Is[e_idx]
                new_idx += 1

        return n, new_edge_count, new_Is, new_Js  
    else:
        new_edge_count = 0
        for e_idx in range(m):
            if Is[e_idx] != Js[e_idx]:
                new_edge_count += 1 
            # get rid of self loops

        new_Is = np.empty(new_edge_count,dtype=int)
        new_Js = np.empty(new_edge_count,dtype=int)
        new_idx = 0 
        for e_idx in range(m):

            if Is[e_idx] != Js[e_idx]:

                new_Is[new_idx] = Is[e_idx]
                new_Js[new_idx] = Js[e_idx]
                new_idx += 1

        return n, new_edge_count, new_Is, new_Js  



if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Generate RMAT graph')
    
    outdir = os.path.join(f"./graphs/")
    parser.add_argument('--outdir', help='Output directory', default=outdir)
    parser.add_argument('--scale', type=int, help='Scale of the graph, two to the power of n')
    parser.add_argument('--seed', type=int, help='Seed')

    args = parser.parse_args()

    generate_n_write_RMAT(args.outdir, args.scale, seed=args.seed)
    
    