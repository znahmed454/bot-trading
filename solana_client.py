from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solders.signature import Signature
import base58
import requests
import json
from typing import Dict, Tuple

class SolanaClient:
    def __init__(self, rpc_url: str, private_key: str):
        self.client = Client(rpc_url, commitment=Confirmed)
        self.keypair = Keypair.from_bytes(base58.b58decode(private_key))
        self.public_key = self.keypair.public_key
        
    def get_balance(self) -> float:
        """Get SOL balance in SOL"""
        response = self.client.get_balance(self.public_key)
        return response['result']['value'] / 1e9
    
    async def get_token_price(self, token_mint: str) -> float:
        """Get token price in USD via Jupiter"""
        try:
            # Get SOL price first
            sol_price = await self.get_sol_price()
            
            # Get token/SOL rate from Jupiter
            url = f"https://quote-api.jup.ag/v6/quote"
            params = {
                "inputMint": token_mint,
                "outputMint": "So11111111111111111111111111111111111111112",  # SOL
                "amount": 10**6,  # 1 token (with 6 decimals)
                "slippageBps": 100
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    token_to_sol = float(data['data'][0]['outAmount']) / 10**9
                    return token_to_sol * sol_price
            return 0
        except Exception as e:
            print(f"Error getting price: {e}")
            return 0
    
    async def get_sol_price(self) -> float:
        """Get SOL price in USD"""
        try:
            response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd")
            return response.json()['solana']['usd']
        except:
            return 150  # Fallback
    
    async def swap_to_token(self, token_mint: str, amount_sol: float) -> str:
        """Swap SOL to token, returns transaction signature"""
        try:
            amount_lamports = int(amount_sol * 1e9)
            
            # Get quote
            quote_url = f"{config.JUPITER_API}/quote"
            params = {
                "inputMint": "So11111111111111111111111111111111111111112",
                "outputMint": token_mint,
                "amount": amount_lamports,
                "slippageBps": 300
            }
            quote_response = requests.get(quote_url, params=params)
            quote = quote_response.json()
            
            # Get swap transaction
            swap_url = f"{config.JUPITER_API}/swap"
            swap_payload = {
                "quoteResponse": quote,
                "userPublicKey": str(self.public_key),
                "wrapAndUnwrapSol": True,
                "dynamicComputeUnitLimit": True
            }
            swap_response = requests.post(swap_url, json=swap_payload)
            swap_data = swap_response.json()
            
            # Sign and send
            from solders.transaction import VersionedTransaction
            tx_bytes = base64.b64decode(swap_data['swapTransaction'])
            tx = VersionedTransaction.from_bytes(tx_bytes)
            signed_tx = Signature.sign(tx, self.keypair)
            
            result = self.client.send_transaction(signed_tx)
            return str(result['result'])
            
        except Exception as e:
            print(f"Swap error: {e}")
            return None
    
    async def swap_to_sol(self, token_mint: str, token_amount: float, decimals: int = 9) -> str:
        """Swap token to SOL"""
        try:
            amount_units = int(token_amount * (10 ** decimals))
            
            # Get quote
            quote_url = f"{config.JUPITER_API}/quote"
            params = {
                "inputMint": token_mint,
                "outputMint": "So11111111111111111111111111111111111111112",
                "amount": amount_units,
                "slippageBps": 300
            }
            quote_response = requests.get(quote_url, params=params)
            quote = quote_response.json()
            
            # Get swap transaction
            swap_url = f"{config.JUPITER_API}/swap"
            swap_payload = {
                "quoteResponse": quote,
                "userPublicKey": str(self.public_key),
                "wrapAndUnwrapSol": True
            }
            swap_response = requests.post(swap_url, json=swap_payload)
            swap_data = swap_response.json()
            
            # Sign and send
            from solders.transaction import VersionedTransaction
            import base64
            tx_bytes = base64.b64decode(swap_data['swapTransaction'])
            tx = VersionedTransaction.from_bytes(tx_bytes)
            signed_tx = Signature.sign(tx, self.keypair)
            
            result = self.client.send_transaction(signed_tx)
            return str(result['result'])
            
        except Exception as e:
            print(f"Swap to SOL error: {e}")
            return None

from config import config
solana_client = SolanaClient(config.SOLANA_RPC_URL, config.SOLANA_PRIVATE_KEY)