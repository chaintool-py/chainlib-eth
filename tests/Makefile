SOLC = /usr/bin/solc

all:
	$(SOLC) --bin TestContract.sol --evm-version byzantium | awk 'NR>3' > TestContract.bin
	truncate -s -1 TestContract.bin
