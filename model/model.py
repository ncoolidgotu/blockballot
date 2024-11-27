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

class Blockchain:
    def __init__(self):
        # single block for single vote - due to proof of concept
        self.vote = []
        self.chain = []
        self.nodes = set()
        self.node_id = str(uuid4()).replace('-', '')
        # manually set for easier implementation
        self.genesis_block = []

class Database:
    def __init__(self):
        self.database_url = "sqlite:///ballot_ledger_database.db"
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

    def insert_block(self, block_data):
        # Calculate SHA-512 hash of the block data
        block_json = str(block_data)
        block_hash = hashlib.sha512(block_json.encode('utf-8')).hexdigest()
        
        # Insert the block and its hash into the database
        session = self.get_session()
        insert_stmt = self.block_table.insert().values(block=block_data, hash=block_hash)
        session.execute(insert_stmt)
        session.commit()
    
    def drop_table(self):
        self.block_table.drop(self.engine)

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