# DRAMAlloc

This library contains an implementation of the DRAMAlloc library.

Due to limitations of the simulation infrastructure, the current version can only be used for fixed sized blocks.

## Usage

DRAMAlloc runs as a top 'thread' on one of the nodes in the system.

For simplicity it assumes that it has access to an dedicated UpDown. This means that the application will not run any work on that particular UpDown.

To initialze the allocator you need to provide it the following:

1. `nrNodes`: The number of nodes available to the application

2. `minSize`: This is the size of the shared memory segment blocks that are striped across the nodes

3. `sharedSegSize`: The total size of the shared segment

4. `machineConfig`: The configuration of the machine running the UpDown application

5. `nwid`: The network id of the UpDown to which DRAMalloc has exclusive access (as described above)

6. `runtime`: The runtime


The Allocator class can be executed on the top using `Allocator::run()` after initialization.

The application also needs to write an some events that will be used by the Allocator.
These events are available in `libraries/dramalloc/dramalloc.py`.

Currently, DRAMalloc expects the following events from the library to be available at the following event ids:

1. `installer_request_sender`: Should be implemented with id 500 using `TranslationEntryInstaller::implement_installer_request_sender`

2. `installer_event`: Should be implemented with id 501 using `TranslationEntryInstaller::implement_installer_event`

3. `termination_event`: Should be implemented with id 502 using `TranslationEntryInstaller::implement_termination_event`

4. `argument_ptr_getter_event`: Should be implemented with id 503 using `TranslationEntryInstaller::implement_argument_ptr_getter_event`

Once implemented, the UpDown application can retrieve the address of the DRAMalloc arguments by sending the `argument_ptr_getter_event` on the `nwid` (provided as argument to `Allocator`).

The arguments for allocation are as follows:

1. `reqType`: An enum representing type of request. For allocation it should be 1.

2. `networkId`: The `nwid` of the lane to which the Allocator should send the resulting address.

3. `returnEvent`: The event that should be launched on `nwid` when allocation is complete.

4. `size`: The total size of the allocation required.

5. `blockSize`: The size of the blocks that should be striped across nodes.

6. `nrNodes`: The number of nodes over which to strip the allocation.

7. `startNode`: The node from which to start the allocation.


Upon request completion, the Allocator will launch event `returnEvent` on lane `nwid`.


The calling application needs to make sure that there is only one active allocation request at any given time. This can be done by hardcoding a lane and using a locked variable to indicate if there is an on going request. This would mean that only the hardcoded lane will be responsible for waiting if the variable is locked, locking the aforementioned variable when it is available and writing allocation request arguments. One could think of a number of different ways to unlock the control variable. For example, the `returnEvent` can send another event to the hardcoded lane that unlocks the variable.
