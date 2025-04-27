from web3 import Web3

# Connect to Ganache
ganache_url = "http://127.0.0.1:8545"
web3 = Web3(Web3.HTTPProvider(ganache_url))

# Check connection
if not web3.is_connected():
    print("Failed to connect to Ganache")
    exit()

print("Connected to Ganache successfully!")
