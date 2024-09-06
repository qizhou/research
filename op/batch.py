# a simple code to demostrate how to batch off-chain data to on-chain data and clarify some key concepts
# - frames
# - batch
# - channel

import rlp

class Frame:
    def __init__(self, channel_id, frame_number, frame_data, is_last):
        self.channel_id = channel_id
        self.frame_number = frame_number
        self.frame_data = frame_data
        self.is_last = is_last

    def to_bytes(self):
        # https://specs.optimism.io/protocol/derivation.html#frame-format
        return self.channel_id.to_bytes(16, "big") + self.frame_number.to_bytes(2, "big"), self.frame_data.to_bytes(4, "big") + self.frame_data + self.is_last.to_bytes(1, "big")


class Batch:
    def __init__(self, parent_hash, epoch_number, epoch_hash, timestamp, transaction_list):
        self.parent_hash = parent_hash
        self.epoch_number = epoch_number
        self.epoch_hash = epoch_hash
        self.timestamp = timestamp
        self.transaction_list = self.transaction_list

    def to_bytes(self):
        # https://specs.optimism.io/protocol/derivation.html#batch-format
        return b"\0" + rlp.encode([self.parent_hash, self.epoch_number, self.epoch_hash, self.timestamp, self.transaction_list])


class ChannelBuilder:
    def __init__(self):
        self.channel_size = 0
        self.batches = []

    def addBlock(self, block):
        # add a L2 block to the channel
        batch = Batch(b"\0" * 32, 0, b"\0" * 32, 0, block)
        self.batches.append(batch)
        # TODO: close the channel and slice the data to frames

        
# Key code:
# - Create a Frame (none span): https://github.com/ethstorage/optimism/blob/8b173d268bb72738c47f173ebf70f6a9ceaa1985/op-node/rollup/derive/channel_out.go#L190
# - Output a Frame: https://github.com/ethstorage/optimism/blob/8b173d268bb72738c47f173ebf70f6a9ceaa1985/op-batcher/batcher/channel_builder.go#L347
# - Frames to Txdata: https://github.com/ethstorage/optimism/blob/8b173d268bb72738c47f173ebf70f6a9ceaa1985/op-batcher/batcher/channel.go#L161
# - Txdata to calldata or BLOBs: https://github.com/ethstorage/optimism/blob/8b173d268bb72738c47f173ebf70f6a9ceaa1985/op-batcher/batcher/tx_data.go#L44
# - Default compression ratio: https://github.com/ethstorage/optimism/blob/8b173d268bb72738c47f173ebf70f6a9ceaa1985/op-batcher/flags/flags.go#L88

