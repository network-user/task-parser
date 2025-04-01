import os
from pathlib import Path

from dotenv import load_dotenv
from rest_framework.decorators import api_view
from rest_framework.response import Response
from web3 import Web3

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

POLYGONSCAN_API_KEY = os.getenv('POLYGONSCAN_API_KEY')
TOKEN_ADDRESS = Web3.to_checksum_address("0x1a9b54a3075119f1546c52ca0940551a6ce5d2d0")
W3_PROVIDER = "https://polygon-rpc.com"

w3 = Web3(Web3.HTTPProvider(W3_PROVIDER))
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}],
     "name": "balanceOf",
     "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals",
     "outputs": [{"name": "", "type": "uint8"}],
     "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol",
     "outputs": [{"name": "", "type": "string"}],
     "type": "function"},
    {"constant": True, "inputs": [], "name": "name",
     "outputs": [{"name": "", "type": "string"}],
     "type": "function"}
]
contract = w3.eth.contract(address=TOKEN_ADDRESS, abi=ERC20_ABI)


def validate_address(address):
    if not Web3.is_address(address):
        raise ValueError("Invalid Ethereum address")


def get_balance_from_chain(address):
    return contract.functions.balanceOf(Web3.to_checksum_address(address)).call()


def get_decimals():
    return contract.functions.decimals().call()


def build_polygonscan_url(module, action, **params):
    base_url = "https://api.polygonscan.com/api"
    params.update({'module': module, 'action': action, 'apikey': POLYGONSCAN_API_KEY})
    return f"{base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"


@api_view(['GET'])
def get_balance(request, address):
    try:
        validate_address(address)
        balance = get_balance_from_chain(address) / (10 ** get_decimals())
        return Response({"address": address, "balance": balance, "unit": "TBY"})
    except ValueError as e:
        return Response({"error": str(e)}, status=400)
    except Exception as e:
        return Response({"error": str(e)}, status=503)


@api_view(['POST'])
def get_balance_batch(request):
    try:
        addresses = request.data.get("addresses", [])
        if not addresses:
            return Response({"error": "Addresses list is required"}, status=400)

        balances = []
        for addr in addresses:
            try:
                validate_address(addr)
                balance = get_balance_from_chain(addr) / (10 ** get_decimals())
                balances.append({"address": addr, "balance": balance})
            except ValueError:
                balances.append(
                    {"address": addr, "balance": None, "error": "Invalid address"})

        return Response({"balances": balances})
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
def get_token_info(request):
    try:
        symbol = contract.functions.symbol().call()
        name = contract.functions.name().call()
        decimals = get_decimals()

        try:
            total_supply = contract.functions.totalSupply().call() / (10 ** decimals)
        except:
            total_supply = "Not available"

        return Response({
            "symbol": symbol,
            "name": name,
            "decimals": decimals,
            "total_supply": total_supply,
            "contract_address": TOKEN_ADDRESS
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)
