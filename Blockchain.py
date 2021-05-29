import hashlib
import json
import requests
from textwrap import dedent
from time import time
from uuid import uuid4

from flask import Flask, jsonify, request
from flask.wrappers import Response


class Blockchain(object):



    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)

    def register_node(self, address):

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)



    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: A blockchain
        :return: True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False

            last_block = block
            current_index += 1

        return True


    #
    def resolve_conflicts(self):
        
        # This is the consensus algorithm, it resolves conflicts by replacing the chain with
        # the longest one in the network
        # It returns true if the chain was replaced, false if not

        neighbours = self.nodes
        new_chain = None

        # We are only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

        if response.status_code == 200:
            length = response.json()['length']
            chain = response.json()['chain']

            # Check if the length is longer and the chain is valid
            if length > max_length and self.valid_chain(chain):
                max_length = length
                new_chain = chain
        
        # Replace our chain if we have discovered a new, valid chain longer than the original
        if new_chain:
            self.chain = new_chain
            return True
        
        return False
    

    def proof_of_work(self, last_block):
        ## Simple Proof of work algorithm
        ## Find a number p such that the hash(pp') contains leading 4 zeroes, where p is the previous p'
        ## p is the previous proof, and p' is the new proof

        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1
        
        return proof
    
    def valid_proof(last_proof, proof):
        ## This validates the proof, does hash(last_proof, proof) contain 4 leading zeroes
        ## last_proof - Previous Proof
        ## proof - current proof

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def new_block(self, proof, previous_hash):
        # Creates a new block and adds it the chain
        # Previous_hash - is the hash of the previous block in the chain
        
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block


    def new_transaction(self, sender, recipient, amount):
        ## Creates a new transaction to go into the next mined Block

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })


        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        # Hashes a block
        block_String = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_String).hexdigest()

    @property
    def last_block(self):
        # Returns the last Block in the chain
        pass

    def new_transaction(self, sender, recipient, amount):

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

## Instantiate our Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    ## We run the proof of work algorithmn to get the next proof
    ## The sender is "0" to signify that this node has mined a new coin.

    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    blockchain.new_transaction(
        sender = "0",
        recipient=node_identifier,
        amount=1,
    )
    # Forge the new block by adding it to the chain.
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
    }
    return jsonify(response), 200

@app.route('/chain', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are part of the POSTED data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'],
    values['amount'])

    Response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(Response)


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400
    
    for node in nodes:
        blockchain.register_node(node)
    
    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
    
    return jsonify(response), 200

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


