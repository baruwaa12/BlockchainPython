import hashlib
import json
from time import time 
from uuid import uuid4
from flask import Flask, jsonify, request


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
    # The block/dict must be ordered or there will be inconsistent hashes
    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
        

    @property
    def last_block(self):
        # Returns the last block in the chain
        return self.chain[-1]
        pass



# Create an instant of our Node
app = Flask(__name__)

# Generate a globally unique address for our node
node_identifier = str(uuid4)

# Instatiate the blockchain
blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    # Run the proof of work algorithm to get the next proof
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # A reward must be gifted for finding the proof
    # The sender is "0" to show that the node has mined a new coin

    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Create a new block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    print(block['index'])
    print(block['transactions'])
    print(block['proof'])
    previousHash = block['previous_hash']


    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': 'proof',
        'previous_hash': previousHash,
    }
    result = jsonify(response), 200
    return result

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POSTED data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['sender'],
    values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to the block{index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
