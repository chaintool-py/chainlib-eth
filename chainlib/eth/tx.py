# standard imports
import logging
import enum
import re

# external imports
import coincurve
import sha3
from hexathon import (
        strip_0x,
        add_0x,
        compact,
        )
from rlp import decode as rlp_decode
from rlp import encode as rlp_encode
from crypto_dev_signer.eth.transaction import EIP155Transaction
from crypto_dev_signer.encoding import public_key_to_address
from crypto_dev_signer.eth.encoding import chain_id_to_v
from potaahto.symbols import snake_and_camel
from chainlib.hash import keccak256_hex_to_hex
from chainlib.status import Status
from chainlib.jsonrpc import JSONRPCRequest
from chainlib.tx import Tx as BaseTx
from chainlib.eth.nonce import (
        nonce as nonce_query,
        nonce_confirmed as nonce_query_confirmed,
        )
from chainlib.block import BlockSpec

# local imports
from .address import to_checksum
from .constant import (
        MINIMUM_FEE_UNITS,
        MINIMUM_FEE_PRICE,
        ZERO_ADDRESS,
        DEFAULT_FEE_LIMIT,
        )
from .contract import ABIContractEncoder
from .jsonrpc import to_blockheight_param

logg = logging.getLogger(__name__)



class TxFormat(enum.IntEnum):
    """Tx generator output formats
    """
    DICT = 0x00
    RAW = 0x01
    RAW_SIGNED = 0x02
    RAW_ARGS = 0x03
    RLP = 0x10
    RLP_SIGNED = 0x11
    JSONRPC = 0x10
     

field_debugs = [
        'nonce',
        'gasPrice',
        'gas',
        'to',
        'value',
        'data',
        'v',
        'r',
        's',
        ]


count = nonce_query
count_pending = nonce_query
count_confirmed = nonce_query_confirmed


def pack(tx_src, chain_spec):
    """Serialize wire format transaction from transaction representation.

    :param tx_src: Transaction source.
    :type tx_src: dict
    :param chain_spec: Chain spec to calculate EIP155 v value
    :type chain_spec: chainlib.chain.ChainSpec
    :rtype: bytes
    :returns: Serialized transaction
    """
    if isinstance(tx_src, Tx):
        tx_src = tx_src.as_dict()
    tx_src = Tx.src_normalize(tx_src)
    tx = EIP155Transaction(tx_src, tx_src['nonce'], chain_spec.chain_id())

    signature = bytearray(65)
    cursor = 0
    for a in [
            tx_src['r'],
            tx_src['s'],
            ]:
        for b in bytes.fromhex(strip_0x(a)):
            signature[cursor] = b
            cursor += 1

    #signature[cursor] = chainv_to_v(chain_spec.chain_id(), tx_src['v'])
    tx.apply_signature(chain_spec.chain_id(), signature, v=tx_src['v'])
    logg.debug('tx {}'.format(tx.serialize()))
    return tx.rlp_serialize()


def unpack(tx_raw_bytes, chain_spec):
    """Deserialize wire format transaction to transaction representation.

    :param tx_raw_bytes: Serialized transaction
    :type tx_raw_bytes: bytes
    :param chain_spec: Chain spec to calculate EIP155 v value
    :type chain_spec: chainlib.chain.ChainSpec
    :rtype: dict
    :returns: Transaction representation
    """
    chain_id = chain_spec.chain_id()
    tx = __unpack_raw(tx_raw_bytes, chain_id)
    tx['nonce'] = int.from_bytes(tx['nonce'], 'big')
    tx['gasPrice'] = int.from_bytes(tx['gasPrice'], 'big')
    tx['gas'] = int.from_bytes(tx['gas'], 'big')
    tx['value'] = int.from_bytes(tx['value'], 'big')
    return tx


def unpack_hex(tx_raw_bytes, chain_spec):
    """Deserialize wire format transaction to transaction representation, using hex values for all numeric value fields.

    :param tx_raw_bytes: Serialized transaction
    :type tx_raw_bytes: bytes
    :param chain_spec: Chain spec to calculate EIP155 v value
    :type chain_spec: chainlib.chain.ChainSpec
    :rtype: dict
    :returns: Transaction representation
    """
    chain_id = chain_spec.chain_id()
    tx = __unpack_raw(tx_raw_bytes, chain_id)
    tx['nonce'] = add_0x(hex(tx['nonce']))
    tx['gasPrice'] = add_0x(hex(tx['gasPrice']))
    tx['gas'] = add_0x(hex(tx['gas']))
    tx['value'] = add_0x(hex(tx['value']))
    tx['chainId'] = add_0x(hex(tx['chainId']))
    return tx


def __unpack_raw(tx_raw_bytes, chain_id=1):
    try:
        d = rlp_decode(tx_raw_bytes)
    except Exception as e:
        raise ValueError('RLP deserialization failed: {}'.format(e))

    logg.debug('decoding using chain id {}'.format(str(chain_id)))
    
    j = 0
    for i in d:
        v = i.hex()
        if j != 3 and v == '':
            v = '00'
        logg.debug('decoded {}: {}'.format(field_debugs[j], v))
        j += 1
    vb = chain_id
    if chain_id != 0:
        v = int.from_bytes(d[6], 'big')
        vb = v - (chain_id * 2) - 35
    r = bytearray(32)
    r[32-len(d[7]):] = d[7]
    s = bytearray(32)
    s[32-len(d[8]):] = d[8]
    logg.debug('vb {}'.format(vb))
    sig = b''.join([r, s, bytes([vb])])
    #so = KeyAPI.Signature(signature_bytes=sig)

    h = sha3.keccak_256()
    h.update(rlp_encode(d))
    signed_hash = h.digest()

    d[6] = chain_id
    d[7] = b''
    d[8] = b''

    h = sha3.keccak_256()
    h.update(rlp_encode(d))
    unsigned_hash = h.digest()
    
    #p = so.recover_public_key_from_msg_hash(unsigned_hash)
    #a = p.to_checksum_address()
    pubk = coincurve.PublicKey.from_signature_and_message(sig, unsigned_hash, hasher=None)
    a = public_key_to_address(pubk)
    logg.debug('decoded recovery byte {}'.format(vb))
    logg.debug('decoded address {}'.format(a))
    logg.debug('decoded signed hash {}'.format(signed_hash.hex()))
    logg.debug('decoded unsigned hash {}'.format(unsigned_hash.hex()))

    to = d[3].hex() or None
    if to != None:
        to = to_checksum(to)

    data = d[5].hex()
    try:
        data = add_0x(data)
    except:
        data = '0x'

    return {
        'from': a,
        'to': to, 
        'nonce': d[0],
        'gasPrice': d[1],
        'gas': d[2],
        'value': d[4],
        'data': data,
        'v': v,
        'recovery_byte': vb,
        'r': add_0x(sig[:32].hex()),
        's': add_0x(sig[32:64].hex()),
        'chainId': chain_id,
        'hash': add_0x(signed_hash.hex()),
        'hash_unsigned': add_0x(unsigned_hash.hex()),
            }


def transaction(hsh, id_generator=None):
    """Generate json-rpc query to retrieve transaction by hash from node.

    :param hsh: Transaction hash, in hex
    :type hsh: str
    :param id_generator: json-rpc id generator
    :type id_generator: JSONRPCIdGenerator
    :rtype: dict
    :returns: rpc query object
    """
    j = JSONRPCRequest(id_generator=id_generator)
    o = j.template()
    o['method'] = 'eth_getTransactionByHash'
    o['params'].append(add_0x(hsh))
    return j.finalize(o)


def transaction_by_block(hsh, idx, id_generator=None):
    """Generate json-rpc query to retrieve transaction by block hash and index.

    :param hsh: Block hash, in hex
    :type hsh: str
    :param idx: Transaction index
    :type idx: int
    :param id_generator: json-rpc id generator
    :type id_generator: JSONRPCIdGenerator
    :rtype: dict
    :returns: rpc query object
    """
    j = JSONRPCRequest(id_generator=id_generator)
    o = j.template()
    o['method'] = 'eth_getTransactionByBlockHashAndIndex'
    o['params'].append(add_0x(hsh))
    o['params'].append(hex(idx))
    return j.finalize(o)


def receipt(hsh, id_generator=None):
    """Generate json-rpc query to retrieve transaction receipt by transaction hash from node.

    :param hsh: Transaction hash, in hex
    :type hsh: str
    :param id_generator: json-rpc id generator
    :type id_generator: JSONRPCIdGenerator
    :rtype: dict
    :returns: rpc query object
    """
    j = JSONRPCRequest(id_generator=id_generator)
    o = j.template()
    o['method'] = 'eth_getTransactionReceipt'
    o['params'].append(add_0x(hsh))
    return j.finalize(o)


def raw(tx_raw_hex, id_generator=None):
    """Generator json-rpc query to send raw transaction to node.

    :param hsh: Serialized transaction, in hex
    :type hsh: str
    :param id_generator: json-rpc id generator
    :type id_generator: JSONRPCIdGenerator
    :rtype: dict
    :returns: rpc query object
    """
    j = JSONRPCRequest(id_generator=id_generator)
    o = j.template()
    o['method'] = 'eth_sendRawTransaction'
    o['params'].append(add_0x(tx_raw_hex))
    return j.finalize(o)


class TxFactory:
    """Base class for generating and signing transactions or contract calls.

    For transactions (state changes), a signer, gas oracle and nonce oracle needs to be supplied.

    Gas oracle and nonce oracle may in some cases be needed for contract calls, if the node insists on counting gas for read-only operations.

    :param chain_spec: Chain spec to use for signer.
    :type chain_spec: chainlib.chain.ChainSpec
    :param signer: Signer middleware.
    :type param: Object implementing interface ofchainlib.eth.connection.sign_transaction_to_wire
    :param gas_oracle: Backend to generate gas parameters
    :type gas_oracle: Object implementing chainlib.eth.gas.GasOracle interface
    :param nonce_oracle: Backend to generate gas parameters
    :type nonce_oracle: Object implementing chainlib.eth.nonce.NonceOracle interface
    """

    fee = DEFAULT_FEE_LIMIT

    def __init__(self, chain_spec, signer=None, gas_oracle=None, nonce_oracle=None):
        self.gas_oracle = gas_oracle
        self.nonce_oracle = nonce_oracle
        self.chain_spec = chain_spec
        self.signer = signer


    def build_raw(self, tx):
        """Sign transaction data, returning the transaction hash and serialized transaction.

        In most cases, chainlib.eth.tx.TxFactory.finalize should be used instead.

        :param tx: Transaction representation
        :type tx: dict
        :rtype: tuple
        :returns: Transaction hash (in hex), serialized transaction (in hex)
        """
        if tx['to'] == None or tx['to'] == '':
            tx['to'] = '0x'
        txe = EIP155Transaction(tx, tx['nonce'], tx['chainId'])
        tx_raw = self.signer.sign_transaction_to_wire(txe)
        tx_raw_hex = add_0x(tx_raw.hex())
        tx_hash_hex = add_0x(keccak256_hex_to_hex(tx_raw_hex))
        return (tx_hash_hex, tx_raw_hex)


    def build(self, tx, id_generator=None):
        """Sign transaction and wrap in raw transaction json-rpc query.

        In most cases, chainlib.eth.tx.TxFactory.finalize should be used instead.

        :param tx: Transaction representation
        type tx: dict
        :param id_generator: JSONRPC id generator
        :type id_generator: JSONRPCIdGenerator
        :rtype: tuple
        :returns: Transaction hash (in hex), raw transaction rpc query object
        """
        (tx_hash_hex, tx_raw_hex) = self.build_raw(tx) 
        o = raw(tx_raw_hex, id_generator=id_generator)
        return (tx_hash_hex, o)


    def template(self, sender, recipient, use_nonce=False):
        """Generate a base transaction template.

        :param sender: Sender address, in hex
        :type sender: str
        :param receipient: Recipient address, in hex
        :type recipient: str
        :param use_nonce: Use and advance nonce in nonce generator.
        :type use_nonce: bool
        :rtype: dict
        :returns: Transaction representation.
        """
        gas_price = MINIMUM_FEE_PRICE
        gas_limit = MINIMUM_FEE_UNITS
        if self.gas_oracle != None:
            (gas_price, gas_limit) = self.gas_oracle.get_gas()
        logg.debug('using gas price {} limit {}'.format(gas_price, gas_limit))
        nonce = 0
        o = {
                'from': sender,
                'to': recipient,
                'value': 0,
                'data': '0x',
                'gasPrice': gas_price,
                'gas': gas_limit,
                'chainId': self.chain_spec.chain_id(),
                }
        if self.nonce_oracle != None and use_nonce:
            nonce = self.nonce_oracle.next_nonce()
            logg.debug('using nonce {} for address {}'.format(nonce, sender))
        o['nonce'] = nonce
        return o


    def normalize(self, tx):
        """Generate field name redundancies (camel-case, snake-case).

        :param tx: Transaction representation
        :type tx: dict
        :rtype: dict:
        :returns: Transaction representation with redudant field names
        """
        txe = EIP155Transaction(tx, tx['nonce'], tx['chainId'])
        txes = txe.serialize()
        return {
            'from': tx['from'],
            'to': txes['to'],
            'gasPrice': '0x' + compact(txes['gasPrice']),
            'gas': '0x' + compact(txes['gas']),
            'data': txes['data'],
                }


    def finalize(self, tx, tx_format=TxFormat.JSONRPC, id_generator=None):
        """Sign transaction and for specified output format.

        :param tx: Transaction representation
        :type tx: dict
        :param tx_format: Transaction output format
        :type tx_format: chainlib.eth.tx.TxFormat
        :raises NotImplementedError: Unknown tx_format value
        :rtype: varies
        :returns: Transaction output in specified format.
        """
        if tx_format == TxFormat.JSONRPC:
            return self.build(tx, id_generator=id_generator)
        elif tx_format == TxFormat.RLP_SIGNED:
            return self.build_raw(tx)
        raise NotImplementedError('tx formatting {} not implemented'.format(tx_format))


    def set_code(self, tx, data, update_fee=True):
        """Apply input data to transaction.

        :param tx: Transaction representation
        :type tx: dict
        :param data: Input data to apply, in hex
        :type data: str
        :param update_fee: Recalculate gas limit based on added input
        :type update_fee: bool
        :rtype: dict
        :returns: Transaction representation
        """
        tx['data'] = data
        if update_fee:
            tx['gas'] = TxFactory.fee
            if self.gas_oracle != None:
                (price, tx['gas']) = self.gas_oracle.get_gas(code=data)
            else:
                logg.debug('using hardcoded gas limit of 8000000 until we have reliable vm executor')
        return tx

    
    def transact_noarg(self, method, contract_address, sender_address, tx_format=TxFormat.JSONRPC):
        """Convenience generator for contract transaction with no arguments.

        :param method: Method name
        :type method: str
        :param contract_address: Contract address to transaction against, in hex
        :type contract_address: str
        :param sender_address: Transaction sender, in hex
        :type sender_address: str
        :param tx_format: Transaction output format
        :type tx_format: chainlib.eth.tx.TxFormat
        :rtype: varies
        :returns: Transaction output in selected format
        """
        enc = ABIContractEncoder()
        enc.method(method)
        data = enc.get()
        tx = self.template(sender_address, contract_address, use_nonce=True)
        tx = self.set_code(tx, data)
        tx = self.finalize(tx, tx_format)
        return tx


    def call_noarg(self, method, contract_address, sender_address=ZERO_ADDRESS, height=BlockSpec.LATEST, id_generator=None):
        """Convenience generator for contract (read-only) call with no arguments.

        :param method: Method name
        :type method: str
        :param contract_address: Contract address to transaction against, in hex
        :type contract_address: str
        :param sender_address: Transaction sender, in hex
        :type sender_address: str
        :param height: Transaction height specifier
        :type height: chainlib.block.BlockSpec
        :param id_generator: json-rpc id generator
        :type id_generator: JSONRPCIdGenerator
        :rtype: varies
        :returns: Transaction output in selected format
        """
        j = JSONRPCRequest(id_generator)
        o = j.template()
        o['method'] = 'eth_call'
        enc = ABIContractEncoder()
        enc.method(method)
        data = add_0x(enc.get())
        tx = self.template(sender_address, contract_address)
        tx = self.set_code(tx, data)
        o['params'].append(self.normalize(tx))
        height = to_blockheight_param(height)
        o['params'].append(height)
        o = j.finalize(o)
        return o


class Tx(BaseTx):
    """Wraps transaction data, transaction receipt data and block data, enforces local standardization of fields, and provides useful output formats for viewing transaction contents.

    If block is applied, the transaction data or transaction hash must exist in its transactions array.

    If receipt is applied, the transaction hash in the receipt must match the hash in the transaction data.

    :param src: Transaction representation
    :type src: dict
    :param block: Apply block object in which transaction in mined.
    :type block: chainlib.block.Block
    :param rcpt: Apply receipt data 
    :type rcpt: dict
    #:todo: force tx type schema parser (whether expect hex or int etc)
    #:todo: divide up constructor method
    """

    def __init__(self, src, block=None, rcpt=None):
        self.__rcpt_block_hash = None

        src = self.src_normalize(src)
        self.index = -1
        tx_hash = add_0x(src['hash'])
        self.hash = strip_0x(tx_hash)
        if block != None:
            self.apply_block(block)
        try:
            self.value = int(strip_0x(src['value']), 16)
        except TypeError:
            self.value = int(src['value'])
        try:
            self.nonce = int(strip_0x(src['nonce']), 16)
        except TypeError:
            self.nonce = int(src['nonce'])
        address_from = strip_0x(src['from'])
        try:
            self.gas_price = int(strip_0x(src['gasPrice']), 16)
        except TypeError:
            self.gas_price = int(src['gasPrice'])
        try:
            self.gas_limit = int(strip_0x(src['gas']), 16)
        except TypeError:
            self.gas_limit = int(src['gas'])
        self.outputs = [to_checksum(address_from)]
        self.contract = None

        try:
            inpt = src['input']
        except KeyError:
            inpt = src['data']
            src['input'] = src['data']

        if inpt != '0x':
            inpt = strip_0x(inpt)
        else:
            inpt = ''
        self.payload = inpt

        to = src['to']
        if to == None:
            to = ZERO_ADDRESS
        self.inputs = [to_checksum(strip_0x(to))]

        self.block = block
        try:
            self.wire = src['raw']
        except KeyError:
            logg.warning('no inline raw tx src, and no raw rendering implemented, field will be "None"')

        self.status = Status.PENDING
        self.logs = None

        if rcpt != None:
            self.apply_receipt(rcpt)

        self.v = src.get('v')
        self.r = src.get('r')
        self.s = src.get('s')

        self.wire = None
 
        self.tx_src = src


    def src(self):
        """Retrieve normalized representation source used to construct transaction object.

        :rtype: dict
        :returns: Transaction representation
        """
        return self.tx_src
   

    @classmethod
    def src_normalize(self, src):
        """Normalizes transaction representation source data.

        :param src: Transaction representation
        :type src: dict
        :rtype: dict
        :returns: Transaction representation, normalized
        """
        src = snake_and_camel(src)

        if isinstance(src.get('v'), str):
            try:
                src['v'] = int(src['v'])
            except ValueError:
                src['v'] = int(src['v'], 16)
        return src


    def as_dict(self):
        return self.src()


    def apply_receipt(self, rcpt):
        """Apply receipt data to transaction object.

        Effect is the same as passing a receipt at construction.

        :param rcpt: Receipt data
        :type rcpt: dict
        """
        rcpt = self.src_normalize(rcpt)
        logg.debug('rcpt {}'.format(rcpt))

        tx_hash = add_0x(rcpt['transaction_hash'])
        if rcpt['transaction_hash'] != add_0x(self.hash):
            raise ValueError('rcpt hash {} does not match transaction hash {}'.format(rcpt['transaction_hash'], self.hash))

        block_hash = add_0x(rcpt['block_hash'])
        if self.block != None:
            if block_hash != add_0x(self.block.hash):
                raise ValueError('rcpt block hash {} does not match transaction block hash {}'.format(rcpt['block_hash'], self.block.hash))

        try:
            status_number = int(rcpt['status'], 16)
        except TypeError:
            status_number = int(rcpt['status'])
        if rcpt['block_number'] == None:
            self.status = Status.PENDING
        else:
            if status_number == 1:
                self.status = Status.SUCCESS
            elif status_number == 0:
                self.status = Status.ERROR
            try:
                self.tx_index = int(rcpt['transaction_index'], 16)
            except TypeError:
                self.tx_index = int(rcpt['transaction_index'])
        # TODO: replace with rpc receipt/transaction translator when available
        contract_address = rcpt.get('contractAddress')
        if contract_address == None:
            contract_address = rcpt.get('contract_address')
        if contract_address != None:
            self.contract = contract_address
        self.logs = rcpt['logs']
        try:
            self.gas_used = int(rcpt['gasUsed'], 16)
        except TypeError:
            self.gas_used = int(rcpt['gasUsed'])

        self.__rcpt_block_hash = rcpt['block_hash']


    def apply_block(self, block):
        """Apply block to transaction object.

        :param block: Block object
        :type block: chainlib.block.Block
        """
        if self.__rcpt_block_hash != None:
            if block.hash != self.__rcpt_block_hash:
                raise ValueError('block hash {} does not match already applied receipt block hash {}'.format(block.hash, self.__rcpt_block_hash))
        self.index = block.get_tx(self.hash)
        self.block = block


    def generate_wire(self, chain_spec):
        """Generate transaction wire format.

        :param chain_spec: Chain spec to interpret EIP155 v value.
        :type chain_spec: chainlib.chain.ChainSpec
        :rtype: str
        :returns: Wire format, in hex
        """
        if self.wire == None:
            b = pack(self.src(), chain_spec)
            self.wire = add_0x(b.hex())
        return self.wire


    @staticmethod
    def from_src(src, block=None, rcpt=None):
        """Creates a new Tx object.

        Alias of constructor.
        """
        return Tx(src, block=block, rcpt=rcpt)


    def __str__(self):
        if self.block != None:
            return 'tx {} status {} block {} index {}'.format(add_0x(self.hash), self.status.name, self.block.number, self.index)
        else:
            return 'tx {} status {}'.format(add_0x(self.hash), self.status.name)


    def __repr__(self):
        return self.__str__()


    def to_human(self):
        """Human-readable string dump of transaction contents.

        :rtype: str
        :returns: Contents
        """
        s = """hash {}
from {}
to {}
value {}
nonce {}
gas_price {}
gas_limit {}
input {}
""".format(
        self.hash,
        self.outputs[0],
        self.inputs[0],
        self.value,
        self.nonce,
        self.gas_price,
        self.gas_limit,
        self.payload,
        )

        if self.status != Status.PENDING:
            s += """gas_used {}
""".format(
        self.gas_used,
        )

        s += 'status ' + self.status.name + '\n'

        if self.block != None:
            s += """block_number {}
block_hash {}
tx_index {}
""".format(
        self.block.number,
        self.block.hash,
        self.tx_index,
        )


        if self.contract != None:
            s += """contract {}
""".format(
        self.contract,
        )

        if self.wire != None:
            s += """src {}
""".format(
        self.wire,
        )

        return s
