import hashlib
import json
from time import time 


## The blockchain class manages the chain. It stores transactions and has other functions to add
## blocks to the chain

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # Create the genesis block
        self.new_block(previous_hash=1, proof = 100)

    # This creates a new block and adds it to the chain
    def new_block(self, proof, previous_hash=None):
        ## Parameter proof: The proof given by the proof of work algorithm
        ## Parameter previous hash: Hash of the previous block
        ## Return a dictionary which is the new block

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        # Reset the current list of transactions
        self.current_transactions = []

        # Adds the current block to the chain
        self.chain.append(block)
        return block


    # This adds a new transaction to the list of transactions
    def new_transaction(self, sender, recipient, amount):
        ## Create a new transaction to go into the next mined Block
        ## Parameter sender: Address of the sender
        ## Parameter recipient: Address of the recipient
        ## Parameter amount: Amount
        ## It will return an int which is the index of the block which holds the transaction

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_block['index'] + 1


    # This is a simple proof of work algorithm
    # Find a number p such that hash(pp') contains 4 leading zeroes,
    # where p is the previous p'
    ## p is the previous proof and p' is the new proof 
    def proof_of_work(self, last_proof):
       
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof


    # This function validates the proof.
    # It will check if the hash of p and p' have 4 leading zeroes
    # and it will return True or False
    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"
        

    # This function will create a SHA-256 hash of the block
    # The block/dict must be orderd or there will be inconsistent hashes
    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest
        

    @property
    def last_block(self):
        # Returns the last block in the chain
        return self.chain[-1]
        pass

