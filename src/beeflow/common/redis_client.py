import redis 
import jsonpickle
from beeflow.common.config_driver import BeeConfig
import beeflow.common.wf_interface
import beeflow.common.gdb_interface
import neobolt 

# Encode a value with jsonpickle
def encode(val):
    print(f'This is type: {type(val)}')
    encoded_val = jsonpickle.encode(val)
    return encoded_val

def decode(val):
    decoded_val = jsonpickle.decode(val)
    return decoded_val

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class RedisClient(metaclass=Singleton):
    def __init__(self):
        config_params = {}
        bc = BeeConfig(**config_params)
        try:
            bc.userconfig['redis']
        except KeyError:
            redis_dict = {
                'listen_port': bc.default_redis_port
            }
            bc.modify_section('user', 'redis', redis_dict)

        port = bc.userconfig.get('redis', 'listen_port')
        self.pool = redis.ConnectionPool(port=port)

    # Set connecton if not set
    @property
    def conn(self):
        if not hasattr(self, '_conn'):
            self.getConnection()
        return self._conn
    
    # Set up connection pool
    def getConnection(self):
        self._conn = redis.Redis(connection_pool = self.pool)

    # Add to hash
    def hset(self, key, id, value):
        self.conn.hset(key, id, encode(value))

    # Get hash set 
    def hget(self, key, id):
        h = decode(self.conn.hget(key, id))
        return h

    # Get hash set 
    def hgetall(self, key):
        h = self.conn.hgetall(key)
        decoded_h = {decode(key):decode(value) for key, value in h.items()}
        return decoded_h

    # Update value for key and id
    def hupdate(self, key, id, entry, value): 
        new_h = self.hget(key, id)
        new_h[entry] = value
        self.conn.hset(key, id, encode(new_h))

    # Remove id from hash set
    def hremove(self, key, id):
        self.conn.hdel(key, id)

    # Pop from list
    def lpop(self, key):
        return decode(self.conn.lpop(key))

    # Push into a list
    def lpush(self, key, val):
        self.conn.rpush(key, encode(val))

    # Set redis "string"
    def sset(self, key, val):
        self.conn.set(key, encode(val))

    # Get value of a redis "string"
    def sget(self, key):
        return decode(self.conn.get(key))

    # Get length of list
    def llen(self, key):
        return self.conn.llen(key)

    # Get length of hashset
    def hlen(self, key):
        return self.conn.hlen(key)

    def delete(self, key):
        self.conn.delete(key)
