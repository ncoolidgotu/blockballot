from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from uuid import uuid4
import json
import hashlib
import requests
from urllib.parse import urlparse

class Blockchain:

    def __init__(self):
        self.transactions = []
        self.chain = []
        self.nodes = set()
        self.node_id = str(uuid4()).replace('-', '')
        # Create the genesis block
        self.create_block(0, '00')