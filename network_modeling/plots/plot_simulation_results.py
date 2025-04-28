import matplotlib.pyplot as plt 
import numpy as np 
import os

from functools import reduce



def make_figure(savefig=False, figure_type="1-cdf"):

    data_path = "/Users/charlie/Documents/Code/UpDown/pagerank_bfs_paper/artifact_submissions/2025_submission/UD-bfs-pr-sc25/network_modeling/data/results/"

    trials = [
        ("simOutput-msgSize:34-inj:EachRandomNeighbor-RE:72468-V:16384-msgVol:10567680000-rt:5.0e-6-savefreq:100-PSradix:22-rtng:queue_random_reroute-npr:5-lpn:2-lpr:1-ltr:2.2e12-randRA:2123832-rtngS:1231-trfcS:52342","16K- 2.2TB","solid","tab:red",(.5,.95)),
        ("simOutput-msgSize:34-inj:EachRandomNeighbor-RE:72468-V:4096-msgVol:2641920000-rt:5.0e-6-savefreq:100-PSradix:22-rtng:queue_random_reroute-npr:5-lpn:2-lpr:1-ltr:2.2e12-randRA:2123832-rtngS:1231-trfcS:52342","4K - 2.2TB","solid","tab:green",(.175,.4)),
        ("simOutput-msgSize:34-inj:EachRandomNeighbor-RE:72468-V:8192-msgVol:5283840000-rt:5.0e-6-savefreq:100-PSradix:22-rtng:queue_random_reroute-npr:5-lpn:2-lpr:1-ltr:2.2e12-randRA:2123832-rtngS:1231-trfcS:52342","8K - 2.2TB","solid","tab:blue",(.4,.5)),        
        ("simOutput-msgSize:34-inj:EachRandomNeighbor-RE:72468-V:16384-msgVol:10649600000-rt:5.0e-6-savefreq:100-PSradix:22-rtng:queue_random_reroute-npr:5-lpn:2-lpr:1-ltr:4.0e12-randRA:2123832-rtngS:1231-trfcS:52342","16K - 4TB","dashed","tab:orange",(.11,.1)),
    ]

    use_shortened_names = True


    fig = plt.figure(figsize=(8,6)) 
    queue_len_axes = np.empty((2),object)
    
    gs = fig.add_gridspec(2,1, figure=fig, left=.1, right=.915, top=.9, bottom=.15,wspace=.15,hspace=.25)#, width_ratios=[1, 2])#, height_ratios=[4, 1])
    queue_length_gs = gs[0].subgridspec(1,2,wspace=.05)
    queue_len_axes[0] = fig.add_subplot(queue_length_gs[0,0])
    queue_len_axes[1] = fig.add_subplot(queue_length_gs[0,1])
    latency_ax = fig.add_subplot(gs[1])
    bbox = dict(boxstyle="round", ec="none", fc= latency_ax.get_facecolor(), alpha=.7,pad=.01)
    #
    # -- plot queue length data
    #
    for (file_root,label,linestyle,color,label_pos) in trials: 

        #  -- Load and Plot Queue Length data 
        time_domain, proj_rt_end_timestamp, save_freq, routing_network_edges, nodes, outqueue_lengths, r2rqueue_lengths = _load_queue_length_data(data_path + file_root,rt = 5e-6,use_shortened_argname=use_shortened_names)
        rt_end_timestamp = len(time_domain)

        percentiles_to_test = [100]
        percentile_colors = _plot_queue_lengths(queue_len_axes, time_domain, r2rqueue_lengths,routing_network_edges,  percentiles_to_test,linestyle=linestyle,colors=[color])
    
        #axes[0,0].annotate(f"{machine_size}",label_pos,xycoords="axes fraction",ha="left",va="center",c=color).set_bbox(bbox)


    queue_len_axes[0].set_ylabel("maximum bytes\non a queue")
    queue_len_axes[0].set_title("Router Max Queue Lengths")
    queue_len_axes[1].set_ylabel("% of link queues\nwith messages").set_bbox(bbox)
    queue_len_axes[1].set_title("Router Non-empty Queues")

    queue_len_axes[1].set_ylim(0,2e2)
    queue_len_axes[0].annotate("simulation\nruntime",(proj_rt_end_timestamp-.1,200000),xycoords="data",ha="right",va="top",c="k",rotation=90).set_bbox(bbox)
    #queue_len_axes[1].axhline(y = routing_network_edges, color = 'r',linestyle="dotted")
    #queue_len_axes[1].annotate(f"total router\nnetwork edges={routing_network_edges}",(4.5,routing_network_edges*1.5),xycoords="data",ha="right",va="bottom",c="r").set_bbox(bbox)
    

    queue_len_axes[0].annotate("16K\n2.2TB/s",(.01,.99),xycoords="axes fraction",c="tab:red",ha="left",va="top").set_bbox(bbox)
    queue_len_axes[0].annotate("8K 2.2TB/s",(.15,.55),xycoords="axes fraction",c="tab:blue").set_bbox(bbox)
    queue_len_axes[0].annotate("4K 2.2TB/s",(.3,.35),xycoords="axes fraction",c="tab:green").set_bbox(bbox)
    queue_len_axes[0].annotate("16K\n4TB/s",(.15,.1),xycoords="axes fraction",c="tab:orange",va="bottom").set_bbox(bbox)


    #queue_len_axes[1].set_ylim(0,2e4)
    #queue_len_axes[1].axhline(y = nodes, color = 'r',linestyle="dotted")
    #queue_len_axes[1].annotate("total compute nodes",(8,nodes*1.1),xycoords="data",ha="right",va="top",c="r").set_bbox(bbox)

    # -- Style the Axes.
    queue_len_axes[0].set_yscale("symlog")
    queue_len_axes[1].set_yscale("symlog",linthresh=1e-3)

    for ax in queue_len_axes:
        ax.grid(True)
        ax.spines[:].set_visible(False)
   
        ax.set_xlabel("time ("+r"$\mu$" + "s)")
        ax.axvline(x = proj_rt_end_timestamp, color = 'k',linestyle="dashed")
    
    y_tick_labels = ["0%"]
    y_tick_labels.extend([f"{10**(i)}%" for i in range(-3,3)])
    queue_len_axes[1].set_yticklabels(y_tick_labels)
    queue_len_axes[1].yaxis.tick_right()


    #
    #  -- plot the latency bins 
    #
    
    #  -- Set up th
    bbox = dict(boxstyle="round", ec="none", fc= latency_ax.get_facecolor(), alpha=.7,pad=.01)

  
    # -- load all the latency data to find how many bins are actually non-zero 

    msgs_per_bin = np.empty((len(trials),60))
    for (idx,(file_root,_,_,_,_)) in enumerate(trials):
        msgs_per_bin[idx,:] = _load_msgs_per_latency_bin(data_path + file_root)


    max_bin_idx = max([int(find_last_nonzero(msgs_per_bin[i,:])) for i in range(len(trials))])

    for (idx,(file_root,machine_size,_,color,xy)) in enumerate(trials):

        if figure_type == "bar":
            width = 1/len(trials)
            entries = [x + width*idx for x in range(0,max_bin_idx)]
            latency_ax.bar(entries,msgs_per_bin[idx,:max_bin_idx],align="edge",width=width,color=color)#,zorder=2),width=bar_width
        elif figure_type == "pdf":
            pass
        elif figure_type == "1-cdf":  
            cumulative_sums = np.cumsum(msgs_per_bin[idx,:max_bin_idx])
            cdf = [1 - cumulative_sum / cumulative_sums[-1] for cumulative_sum in cumulative_sums]
            latency_ax.plot(cdf,color=color)
            latency_ax.annotate(machine_size,xy,xycoords="axes fraction",ha="center",va="center",c=color).set_bbox(bbox)
            
        elif figure_type == "cdf":

            cumulative_sums = np.cumsum(msgs_per_bin[idx,:max_bin_idx])
            cdf = [cumulative_sum / cumulative_sums[-1] for cumulative_sum in cumulative_sums]
            latency_ax.plot(cdf,color=color)
            latency_ax.annotate(machine_size,xy,xycoords="axes fraction",ha="center",va="center",c=color).set_bbox(bbox)


    latency_ax.grid(True)
    latency_ax.spines[:].set_visible(False)
    if figure_type == "cdf":
        latency_ax.set_ylabel(r"$Pr(msg\_latency \leq \ell)$")
        latency_ax.set_title(f"Message Latencies CDFs")
    if figure_type == "1-cdf":
        latency_ax.set_ylabel(r"$1 - Pr(msg\_latency \leq \ell)$")
        #latency_ax.set_title(f"Message Latencies CDF complement")
        latency_ax.annotate("Message Latency\nCDF Complement",(.85,.7),fontsize=18,xycoords="axes fraction",ha="right",va="top").set_bbox(bbox)
        #latency_ax.set_title("Message Latency CDF Complement")
        latency_ax.set_yscale("log")
    elif figure_type == "pdf":
        latency_ax.set_ylabel(r"$Pr(msg\_latency = \ell)$")
    elif figure_type == "bar":
        latency_ax.set_title(f"Message Counts per Latencies bin")
        latency_ax.set_ylabel("msgs with latency " + r"$\ell$")
        latency_ax.set_yscale("log")

    latency_ax.set_xlabel("latency " + r"$\ell$" + " (% of worst case no load latency)") 
    #ax.set_yscale("symlog")

    latency_ax.axhline(y = .01, color = 'k',linestyle="dashed")
    latency_ax.annotate("99% of\nmessages",(.09,.765),fontsize=10,xycoords="axes fraction",ha="right",va="center")

    latency_ax.set_xticks(range(max_bin_idx))
    latency_ax.set_xticklabels( [f"{round(((100 + 100*i)/500)*100)}%" if i % 4 == 0 else "" for i in range(max_bin_idx)],rotation=45)


    if savefig:
        plt.savefig("network_simulation.pdf")
    else:
        plt.show()




def parse_filename_for_param(filename, param, parse_f):
    return parse_f(filename.split(f"-{param}:")[-1].split("-")[0])


#
#  Load queue length / latency data 
#

def load_array_col_major(filename, known_dims, dtype=np.float64):
    # Get total number of elements
    file_size = os.path.getsize(filename)
    num_elements = file_size // np.dtype(dtype).itemsize


    print(f"num_elements:{num_elements}")


    dim_product = reduce(lambda x,y: x*y, known_dims)
    # Compute the third dimension
    last_dim = num_elements // dim_product
    if dim_product * last_dim != num_elements:
        raise ValueError("File size does not match expected dimensions.")


    known_dims.append(last_dim)


    # Load data and reshape using Fortran ordering
    data = np.fromfile(filename, dtype=dtype)
    array = data.reshape(tuple(known_dims), order='F')  # Fortran order

    return array



def load_array_sum_col_major(filename, nodes, latency_bins, dtype=np.float64):
    # Get total number of elements
    file_size = os.path.getsize(filename)
    num_elements = file_size // np.dtype(dtype).itemsize

    print(f"num_elements:{num_elements}")
    assert latency_bins*(nodes**2) == num_elements

    msgs_per_bin = np.zeros(latency_bins,dtype=dtype)
    # read the file one byte at a time to prevent too much memory from being consumed. 

    bin_sum_idx = 0
    elements_read = 0 

    with open(filename, "rb") as f:

        while True:
            byte = f.read(np.dtype(dtype).itemsize)
            elements_read += 1 
            if elements_read > num_elements:
                break 
            else:
                msgs_per_bin[(elements_read-1) % latency_bins] += np.frombuffer(byte, dtype=dtype)[0]
                #msgs_per_bin[bin_sum_idx] += dtype(ord(byte))  # Read one byte
                
                #if elements_read % (nodes**2) == 0:
                #    bin_sum_idx += 1 

    return msgs_per_bin


def load_latency_msgs_sums(filename,dtype=np.int64):
    assert filename.endswith("msgsPerLatencyBin.bin")

    file_size = os.path.getsize(filename)
    latency_bins = file_size // np.dtype(dtype).itemsize

    msgs_per_bin = np.empty(latency_bins,dtype=dtype)
    elements_read = 0 
    with open(filename, "rb") as f:
        while True:
            msgs_per_bin[elements_read]  = np.frombuffer(f.read(np.dtype(dtype).itemsize), dtype=dtype)[0]
            elements_read += 1
            if elements_read == latency_bins:
                break 

    return msgs_per_bin


def _load_queue_length_data(file_root,save_freq=None, nodes=None, rt = None, routing_network_edges=None, use_shortened_argname=False):
    """
        parameters are provided as paramters incase parser needs to be over-ridden. 
    """
    if save_freq is None:
        save_freq = parse_filename_for_param(file_root,"savefreq",lambda x: int(x))

    if use_shortened_argname:
        runtime_argname = "rt"
        nodes_argname = "V"
        edges_argname = "RE"
    else:
        runtime_argname = "projruntime"   
        nodes_argname = "Nodes"
        edges_argname = "routerEdges"
    print(rt)
    if rt is None:
 
        proj_rt_end_timestamp =  parse_filename_for_param(file_root, runtime_argname,
                                                     lambda x: int(np.float64(x)/1e-6))
    else:
        proj_rt_end_timestamp = int(rt/1e-6)

    if nodes is None:
        print(file_root)
        nodes = parse_filename_for_param(file_root, nodes_argname,lambda param: int(param))

    if routing_network_edges is None:
        routing_network_edges = parse_filename_for_param(file_root,edges_argname,lambda param: int(param))


    #inqueue_lengths = load_array_col_major(file_root+"_inqueues.bin",[nodes])
    outqueue_lengths = load_array_col_major(file_root+"_outqueues.bin",[nodes])
    r2rqueue_lengths = load_array_col_major(file_root+"_r2rqueues.bin",[routing_network_edges])


    print(f"outqueue shape:{outqueue_lengths.shape} -- r2rqueue shape:{r2rqueue_lengths.shape}")

    time_stamps = r2rqueue_lengths.shape[-1]
    assert outqueue_lengths.shape[-1] == time_stamps

    time_domain = [(save_freq*1e-9)*i/1e-6 for i in range(time_stamps)]

    return time_domain, proj_rt_end_timestamp, save_freq, routing_network_edges, nodes, outqueue_lengths, r2rqueue_lengths

def _load_msgs_per_latency_bin(file_root, nodes = None):

    return load_latency_msgs_sums(file_root+"_msgsPerLatencyBin.bin")


def _plot_queue_lengths(axes, time_domain, queue_lengths,max_number_of_queues, percentiles_to_test = [10,25,50,75,80,90,95,100],linestyle="solid",colors=None):
    """
        same as the previous version, but plots the number of non-empty outgoing as a function of percentage 
    
    """
    time_stamps = len(time_domain)
    percentile_colors = []
    percentile_data = np.empty((len(percentiles_to_test),time_stamps))
    non_zero_count_data = np.empty((time_stamps))

    for t in range(len(time_domain)):
        non_zero_queues = list(filter(lambda x: x > 0, queue_lengths[:,t]))
        non_zero_count_data[t] = len(non_zero_queues)
        for (p_idx,p) in enumerate(percentiles_to_test):

            if len(non_zero_queues) == 0: 
                percentile_data[p_idx,t] = 0
            else: 
                percentile_data[p_idx,t] = np.percentile(non_zero_queues,p)
                #percentile_data[p_idx,t] = np.percentile(data[:,t],p)

    if colors is None:
        for (p_idx,p) in enumerate(percentiles_to_test):
   
            line = axes[0].plot(time_domain,34*percentile_data[p_idx,:],linestyle=linestyle)[0]
            percentile_colors.append(line.get_color())
                #percentile_colors = [line.get_color() for line in lines]
    else:
        for (p_idx,(p,color)) in enumerate(zip(percentiles_to_test,colors)):
            line = axes[0].plot(time_domain,34*percentile_data[p_idx,:],linestyle=linestyle,color=color)[0]
                #percentile_colors = [line.get_color() for line in lines]
    if colors is None:
        colors = percentile_colors


    axes[1].plot(time_domain,[(x/max_number_of_queues)*100 for x in non_zero_count_data],linestyle=linestyle,color=colors[0])

    return percentile_colors


def find_last_nonzero(arr):
    mask = arr != 0
    return np.where(mask.any(axis=0), mask.shape[0] - 1 - np.argmax(mask[::-1], axis=0), -1)

