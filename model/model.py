from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA #remember to use sha512
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
        '''
        final_block, final_hash = self.Proof_of_Work(block)
        self.block_db.insert_block(final_block,final_hash)
    
    def build_block(self, name, voter_id, state, vote):
        '''
        Retrieve block information from frontend
        
        '''
    
        index = self.block_db.get_count()
        previous_hash = self.block_db.get_last_hash()
        
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
            Column('hash', String))
        self.metadata.create_all(self.engine)

    def get_session(self):
        return self.Session()

    def insert_block(self, block_data,block_hash):
        # Insert the block and its hash into the database
        session = self.get_session()
        insert_stmt = self.block_table.insert().values(block=block_data, hash=block_hash)
        session.execute(insert_stmt)
        session.commit()
    
    def get_last_hash(self):
        session = self.get_session()
        try:
            # Query to get the hash with the highest block_id
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
#block_to_add = testing.build_block("Rick Astley","635181u2631ut2", "CA", "Donald Trump")
#block_to_add = testing.build_block("Joe Biden","839247823947938247j3", "AB", "Donald Trump")
#print(testing.check_dupes("Rick Astley","635181u2631ut2", "CA"))
#testing.add_block(block_to_add)

#("Freddy Fazbear","5nightshahaha","TX")