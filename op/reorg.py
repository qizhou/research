# Definition of L2 heads
# - Safe: included in an L1 safe block, can be reorg
# - Finalized: included in an L1 finalized block, cannot be reorg
# - Unsafe: not included in L1

# Config
# cfg.PlasmaEnabled() == true
# - Use plasma finalizer https://github.com/ethstorage/optimism/blob/5a4fbce2bc780a908afeab255513aa38ca3c49b8/op-node/rollup/driver/driver.go#L204
#   -> contains a inner finalizer
# - calcFinalityLookback() https://github.com/ethstorage/optimism/blob/5a4fbce2bc780a908afeab255513aa38ca3c49b8/op-node/rollup/finality/finalizer.go#L39
# - NewPlasmaDataSource() as data source https://github.com/ethstorage/optimism/blob/5a4fbce2bc780a908afeab255513aa38ca3c49b8/op-node/rollup/derive/data_source.go#L81

# fetch safe/unsafe/finalized l1 block: https://github.com/ethstorage/optimism/blob/5a4fbce2bc780a908afeab255513aa38ca3c49b8/op-service/sources/l1_client.go#L81
# polling for safe/finalized l1 block: https://github.com/ethstorage/optimism/blob/5a4fbce2bc780a908afeab255513aa38ca3c49b8/op-service/eth/heads.go#L68
# unsafe/finalize l1 handle -> step(): https://github.com/ethstorage/optimism/blob/5a4fbce2bc780a908afeab255513aa38ca3c49b8/op-node/rollup/driver/state.go#L259
# -> PlasmaFinalizer: https://github.com/ethstorage/optimism/blob/5a4fbce2bc780a908afeab255513aa38ca3c49b8/op-node/rollup/finality/plasma.go#L51
# -> PlasmaFinalizer, find a L1 finalized block passed the challenge window: https://github.com/ethstorage/optimism/blob/5a4fbce2bc780a908afeab255513aa38ca3c49b8/op-plasma/damgr.go#L121
# -> InnerFinializer: https://github.com/ethstorage/optimism/blob/5a4fbce2bc780a908afeab255513aa38ca3c49b8/op-node/rollup/finality/finalizer.go#L140

# challenge not resolve path (need reorg)
# -> AdvanceL1Origin: https://github.com/ethstorage/optimism/blob/5a4fbce2bc780a908afeab255513aa38ca3c49b8/op-plasma/damgr.go#L311
# -> AdvanceCommitmentOrigin: https://github.com/ethstorage/optimism/blob/5a4fbce2bc780a908afeab255513aa38ca3c49b8/op-plasma/damgr.go#L285
# -> Next() will reorg: https://github.com/ethstorage/optimism/blob/5a4fbce2bc780a908afeab255513aa38ca3c49b8/op-node/rollup/derive/plasma_data_source.go#L41
# After reorg
# -> skip challenged batch: https://github.com/ethstorage/optimism/blob/5a4fbce2bc780a908afeab255513aa38ca3c49b8/op-node/rollup/derive/plasma_data_source.go#L79
# -> reorg challenged batch: https://github.com/ethstorage/optimism/blob/5a4fbce2bc780a908afeab255513aa38ca3c49b8/op-plasma/dastate.go#L178