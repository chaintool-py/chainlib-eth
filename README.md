# chainlib-eth

# Overview

This is the Ethereum (EVM) implementation of the `chainlib` block
interface.

It contains implementations for:

- RPC client implementation.

- Nonce and fee generators.

- Transaction and block objects.

- EVM ABI encoding and decoding.

- CLI tool suite for common operations.

Please refer to the documentation for the `chainlib` package to achieve
a broader context of what `chainlib-eth implements`.

# CLI tooling

When installed, the python package `chainlib-eth` will install a
selection of CLI tools in the python executable script path.

It will also install man pages for each tool in the man path. The man
pages describe arguments, configurations and environment variables
relevant for each tool. They will not be repeated here.

The man pages have been generated using the `chainlib-man.py` script
from the `chainlib` package. Please refer to the `chainlib` package
documentation for further details on the logical structure of the
applicable arguments.

`eth-balance`  
Gas token balance of a specific address.

`eth-block`  
Retrieve a block by number or hash.

`eth-checksum`  
Transform an ethereum address to a checksummed address.

`eth-count`  
Get the amount of confirmed transactions on network for an account.
Corresponds to the nonce of the next future transaction.

`eth-decode`  
Decode a transaction from its serialized (wire) format.

`eth-encode`  
Sncode method calls and/or individual arguments for the EVM ABI. Can be
used to interface with smart contracts and generate constructor
arguments.

`eth-gas`  
Generate transactions for private accounts and smart contracts, with or
without gas token value.

`eth-get`  
Retrieve a transaction, or bytecode for an address.

`eth-info`  
Retrieve general stats for a blockchain network.

`eth-raw`  
Covert a signed wire format transaction to raw transaction for RPC.

`eth-wait`  
Block until transaction has been completed (transaction "receipt"
exists).
