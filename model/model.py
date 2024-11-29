from Crypto.Signature import PKCS1_v1_5
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from uuid import uuid4
import json
import hashlib
import requests
from urllib.parse import urlparse
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine, Column, Integer, Sequence, MetaData, Table, String
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker
import time
import os
from Crypto.Hash import SHA512
import binascii
import random

'''
Block{
    "Block ID / Index": ,
    "Previous Block Hash":  ,
    "Timestamp":  ,
    "Nonce":    ,

    "Hash_of_voter":    , #name + voter id hashed
    "State":    ,
    "Vote":     ,
}
'''

class Blockchain:
    def __init__(self):
        # single block for single vote - due to proof of concept
        self.block_db = Database()
        self.vote = []
        self.chain = []
        self.nodes = set()
        self.node_id = str(uuid4()).replace('-', '')
        self.difficulty_level = 3 # this means "000"

        if self.block_db.is_table_empty():
            self.genesis_block = {
                "index":0,
                "previous_hash":"0"*128,
                "timestamp":0,
                "nonce":0,
                "hash_of_voter":"0"*128,
                "state":"genesis",
                "vote":"genesis",
            }
            self.add_block(self.genesis_block)

    def Block_Hash_512(self,block):
        '''
        block = dictionary of a block
        create a hash function using sha 512, encoding the block using json.dump
        '''
        TempBlock = block.copy() #We need to remove the timestamp before hashing, but do not want to touch the original block, so we copy it first
        TempBlock.pop('timestamp', None) # Remove the timestamp for consistent hashing
        blockEncoder = json.dumps(TempBlock,sort_keys=True).encode() #we want to sort by keys
        return hashlib.sha512(blockEncoder).hexdigest() #hexdigest converts into hexa, so it´s more manageable


    def Proof_of_Work(self,block):
        '''
        block = a block in the blockchain with a nonce of 0
        modifies nonce until correct hash, then returns said hash
        '''
        while True:
            # loop continues until block is valid
            current_hash = self.Block_Hash_512(block)
            if current_hash[:self.difficulty_level] == "0"*self.difficulty_level:
                block["timestamp"] = time.time()
                return [block,current_hash]
            else:
                block["nonce"]+=1

    def add_block(self,block):
        '''
        Adds a block to the blockchain, after calculating nonce
        It also signs the block and returns the public key, to hand to the user
        '''
        final_block, final_hash = self.Proof_of_Work(block)
        private_key, public_key = self.create_key_pair()
        voter_signature = self.sign_block(final_hash,private_key)

        valid_vote = True
        valid_hash_check = final_block["hash_of_voter"]
        block_list = self.block_db.get_jsons()
        for i in block_list:
            if i[0]["hash_of_voter"] == valid_hash_check:
                valid_vote = False
                print("duplicate voter hash!")
                break

        # if no duplicate voter hash on the db (can vote just fine)
        if valid_vote:
            # if the signature can be verified
            if self.check_signature(final_hash,voter_signature,public_key):
                self.block_db.insert_block(final_block,final_hash,voter_signature)
                #print("HELLO", public_key)
                return public_key
    
    def build_block(self, name, voter_id, state, vote):
        '''
        Retrieve block information from frontend to then create a new block
        '''
        # calculate its own index
        index = self.block_db.get_count()
        # Here we get both the hash from the previous block in the database
        # but also we calculate the hash again to compare it - ensure no modifications
        previous_hash = self.block_db.get_last_hash()
        compare_previous_hash = self.block_db.get_last_block()
        compare_previous_hash = self.Block_Hash_512(compare_previous_hash)

        if previous_hash == compare_previous_hash:
            hash_of_voter = self.get_voter_hash(name, voter_id, state)
            block = {
                "index":index,
                "previous_hash":previous_hash,
                "timestamp":0,
                "nonce":0,
                "hash_of_voter":hash_of_voter,
                "state":state,
                "vote":vote
            }
        
        else:
            block = {}
            print("ERROR - BLOCKCHAIN COMPROMISED")

        return block
    
    def get_voter_hash(self, name, voter_id, state):
        
        # Ensure the data being hashed is in the correct format (bytes) 
        hash_input = (name + voter_id + state).encode()
        hash_of_voter = hashlib.sha512(hash_input).hexdigest()
        
        return hash_of_voter
    
    def retrieve_record(self, name, voter_id, state):
        voter_hash = self.get_voter_hash(name, voter_id, state)        
        block_list = self.block_db.get_jsons()
        
        for block in block_list:
            if block[0]["hash_of_voter"] == voter_hash:
                return True, block[0]
        
        return False, {}
    
    def retrieve_record_by_hash(self, hash_of_voter):      
        block_list = self.block_db.get_all()
        
        for block in block_list:
            if block[0]["hash_of_voter"] == hash_of_voter:
                to_return = block[0]
                to_return["own_hash"] = block[1]
                to_return["signature"] = block[2]
                
                return True, to_return
        
        return False, {}
    
    def retrieve_all(self):
        db_dump = self.block_db.get_all()
        ledger = []
        for block in db_dump:
            to_add = block[0]
            to_add["own_hash"] = block[1]
            to_add["signature"] = block[2]
            ledger.append(to_add)
        
        return ledger
    
    def verify_vote(self, public_key, hash_of_voter):
        public_key = public_key
        hash_of_voter = hash_of_voter
        
        block_exists, block = self.retrieve_record_by_hash(hash_of_voter)
        
        if block_exists:
            signature_valid = self.check_signature(block["own_hash"], block["signature"], public_key)
            #print(block)
            #print(signature_valid)
            
            if signature_valid:
                return block, "SIGNATURE VERIFIED"
            else:
                return block, "INCORRECT KEY"
        else:
            return block, "INCORRECT HASH"
            
    
    
    '''
    self.genesis_block = {
                "index":0,
                "previous_hash":"0"*128,
                "timestamp":0,
                "nonce":0,
                "hash_of_voter":"0"*128,
                "state":"genesis",
                "vote":"genesis",
            }
    '''

    def create_key_pair(self):
        key = RSA.generate(2048)
        private_key = key.export_key()
        public_key = key.publickey().export_key()
        return private_key, public_key


    def sign_block(self,block_hash,private_key):
        block_hash = SHA512.new(binascii.unhexlify(block_hash))
        private_key = RSA.import_key(private_key)
        signature = PKCS1_v1_5.new(private_key).sign(block_hash)
        return signature
    
    def check_signature(self, block_hash, signature, public_key):
        binary_hash = binascii.unhexlify(block_hash)
        h = SHA512.new(binary_hash)
        public_key = RSA.import_key(public_key)
        try:
            pkcs1_15.new(public_key).verify(h, signature)
            return True
        except (ValueError, TypeError) as e:
            print(f"An error occurred: {e}")
            return False
    
class Database:
    def __init__(self):
        self.database_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../model/ballot_ledger_database.db"))
        self.database_url = f"sqlite:///{self.database_path}"
        self.engine = create_engine(self.database_url)
        self.metadata = MetaData()
        self.Session = sessionmaker(bind=self.engine)
        self.create_table()

    def create_table(self):
        self.block_table = Table(
            'ballots_blockchain', self.metadata,
            Column('block_id', Integer, Sequence('block_id_seq'), primary_key=True),
            Column('block', JSON),
            Column('hash', String),
            Column('voter_signature',String))
        self.metadata.create_all(self.engine)

    def get_session(self):
        return self.Session()

    def insert_block(self, block_data,block_hash,block_signature):
        # Insert the block and its hash into the database
        session = self.get_session()
        insert_stmt = self.block_table.insert().values(block=block_data, hash=block_hash,voter_signature=block_signature)
        session.execute(insert_stmt)
        session.commit()
    
    def get_last_hash(self):
        session = self.get_session()
        try:
            # Query to get the hash with the highest block_id from the blockchain hash information
            result = session.query(self.block_table.c.hash).order_by(self.block_table.c.block_id.desc()).first()
            return result[0] if result else None
        finally:
            session.close()
    
    def drop_table(self):
        self.block_table.drop(self.engine)

    def is_table_empty(self):
        count = self.get_count()
        return count == 0
    
    def get_count(self):
        session = self.get_session()
        count = session.query(self.block_table).count()
        session.close()
        return count

    def get_jsons(self):
        session = self.get_session()
        try:
            # Query to get the hash with the highest block_id
            result = session.query(self.block_table.c.block)
            return result
        finally:
            session.close()

    def get_all(self):
        session = self.get_session()
        try:
            result = session.query(self.block_table.c.block, self.block_table.c.hash, self.block_table.c.voter_signature)
            return result
        finally:
            session.close()
    
    def get_last_block(self):
        session = self.get_session()
        try:
            # Query to get the hash with the highest block_id
            result = session.query(self.block_table.c.block).order_by(self.block_table.c.block_id.desc()).first()
            return result[0]
        finally:
            session.close()
        
        
########################################################################
############################## TEST CODE ###############################
########################################################################

'''
# Example usage
db = Database()

# Adding a new entry
db.insert_block({"data": "example"})


### db.drop_table()  ## WARNING - FOR TESTING PURPOSES DELETE


# Querying entries
session = db.get_session()
select_stmt = db.block_table.select()
result = session.execute(select_stmt)
for row in result:
    print(row['block_id'], row['block'], row['hash'])

'''


#testing = Blockchain()
#print (testing.create_key_pair())

#block_to_add = testing.build_block("Rick Astley","635181u2631ut2", "CA", "Donald Trump")
#block_to_add = testing.build_block("Joe Biden","839247823947938247j3", "AZ", "Donald Trump")
#block_to_add = testing.build_block("Freddy Fazbear","5nightshahaha","TX","Donald Trump")
#print(testing.check_dupes("Rick Astley","635181u2631ut2", "CA"))
#testing.add_block(block_to_add)

#("Freddy Fazbear","5nightshahaha","TX")

#print(testing.retrieve_all())
#print(testing.block_db.get_last_block())

#for i in testing.block_db.get_all():
#    print (i)

#print(testing.retrieve_all())