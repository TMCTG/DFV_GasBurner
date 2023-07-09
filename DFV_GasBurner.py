import threading, time, re, datetime, math
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware


show_errors = False
def settings():
    private_key = "2333bf2262226610f7d38952d8bdf8c03e4fb76755248158ca36ae52d09454f8"  # This is a dummy 'vanity address' for 0xc0ffee...
    target_chains = [1, 56, 137, 250, 43114]  # Check https://chainlist.org/ for ChainIDs
    num_rpcs_per_chain = 100  # High means more errors from non-standard RPCs, but also better protection (So keep it high). A thread will be created for each RPC to ensure that if you hit rate limits of one RPC, your defense will stay up by polling others.
    delay = 5  # In seconds. Setting too low will result in your IP address being rate limited or temporarily banned from RPCs. Suggest higher than 1, lower than 15.
    return private_key, target_chains, num_rpcs_per_chain, delay


def get_rpcs(chain, amount):
    # 2023-07-08 pulled from https://raw.githubusercontent.com/DefiLlama/chainlist/main/constants/extraRpcs.js
    # Feel free to edit. Weed out problematic RPCs, add your own and/or put your preferred RPCs at the top of each chain's list.
    all_rpcs_by_chainId = {
        1: [
          'https://endpoints.omniatech.io/v1/eth/mainnet/public',
          'https://rpc.ankr.com/eth',
          'https://eth-mainnet.nodereal.io/v1/1659dfb40aa24bbb8153a677b98064d7',
          'https://ethereum.publicnode.com',
          'https://1rpc.io/eth',
          'https://rpc.builder0x69.io/',
          'https://rpc.mevblocker.io',
          'https://rpc.flashbots.net/',
          'https://virginia.rpc.blxrbdn.com/',
          'https://uk.rpc.blxrbdn.com/',
          'https://singapore.rpc.blxrbdn.com/',
          'https://eth.rpc.blxrbdn.com/',
          'https://cloudflare-eth.com/',
          'https://eth-mainnet.public.blastapi.io',
          'https://api.securerpc.com/v1',
          'https://api.bitstack.com/v1/wNFxbiJyQsSeLrX8RRCHi7NpRxrlErZk/DjShIqLishPCTB9HiMkPHXjUM9CNM9Na/ETH/mainnet',
          'https://eth-rpc.gateway.pokt.network',
          'https://eth-mainnet-public.unifra.io',
          'https://ethereum.blockpi.network/v1/rpc/public',
          'https://rpc.payload.de',
          'https://api.zmok.io/mainnet/oaen6dy8ff6hju9k',
          'https://eth-mainnet.g.alchemy.com/v2/demo',
          'https://eth.api.onfinality.io/public',
          'https://core.gashawk.io/rpc',
          'https://rpc.eth.gateway.fm',
          'https://rpc.chain49.com/ethereum?api_key=14d1a8b86d8a4b4797938332394203dc',
          'https://eth.meowrpc.com',
          'https://eth.drpc.org',
          'https://mainnet.gateway.tenderly.co',
          'https://gateway.tenderly.co/public/mainnet',
          'https://api.zan.top/node/v1/eth/mainnet/public'],
        80001: [
          'https://endpoints.omniatech.io/v1/matic/mumbai/public',
          'https://rpc.ankr.com/polygon_mumbai',
          'https://polygon-testnet.public.blastapi.io',
          'https://polygon-mumbai.g.alchemy.com/v2/demo',
          'https://polygon-mumbai.blockpi.network/v1/rpc/public',
          'https://polygon-mumbai-bor.publicnode.com',
          'https://polygon-mumbai.gateway.tenderly.co',
          'https://gateway.tenderly.co/public/polygon-mumbai',
          'https://api.zan.top/node/v1/polygon/mumbai/public'],
        5: [
          'https://rpc.ankr.com/eth_goerli',
          'https://endpoints.omniatech.io/v1/eth/goerli/public',
          'https://goerli.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161',
          'https://eth-goerli.public.blastapi.io',
          'https://eth-goerli.g.alchemy.com/v2/demo',
          'https://goerli.blockpi.network/v1/rpc/public',
          'https://eth-goerli.api.onfinality.io/public',
          'https://rpc.goerli.eth.gateway.fm',
          'https://ethereum-goerli.publicnode.com',
          'https://goerli.gateway.tenderly.co',
          'https://gateway.tenderly.co/public/goerli',
          'https://api.zan.top/node/v1/eth/goerli/public'],
        4002: [
          'https://endpoints.omniatech.io/v1/fantom/testnet/public',
          'https://rpc.ankr.com/fantom_testnet',
          'https://fantom-testnet.public.blastapi.io',
          'https://fantom-testnet.publicnode.com'],
        43113: [
          'https://endpoints.omniatech.io/v1/avax/fuji/public',
          'https://rpc.ankr.com/avalanche_fuji',
          'https://rpc.ankr.com/avalanche_fuji-c',
          'https://ava-testnet.public.blastapi.io/ext/bc/C/rpc',
          'https://avalanche-fuji-c-chain.publicnode.com'],
        56: [
          'https://rpc-bsc.48.club',
          'https://koge-rpc-bsc.48.club',
          'https://endpoints.omniatech.io/v1/bsc/mainnet/public',
          'https://bsc-mainnet.gateway.pokt.network/v1/lb/6136201a7bad1500343e248d',
          'https://bsc-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3',
          'https://rpc.ankr.com/bsc',
          'https://binance.nodereal.io',
          'https://1rpc.io/bnb',
          'https://bsc.rpc.blxrbdn.com/',
          'https://bsc.blockpi.network/v1/rpc/public',
          'https://bnb.api.onfinality.io/public',
          'https://bsc.publicnode.com',
          'https://bsc-mainnet.public.blastapi.io',
          'https://bsc.meowrpc.com',
          'https://api.zan.top/node/v1/bsc/mainnet/public'],
        97: [
          'https://endpoints.omniatech.io/v1/bsc/testnet/public',
          'https://bsc-testnet.public.blastapi.io',
          'https://bsc-testnet.publicnode.com',
          'https://api.zan.top/node/v1/bsc/testnet/public'],
        43114: [
          'https://rpc.ankr.com/avalanche',
          'https://blastapi.io/public-api/avalanche',
          'https://ava-mainnet.public.blastapi.io/ext/bc/C/rpc',
          'https://avalanche-c-chain.publicnode.com',
          'https://1rpc.io/avax/c',
          'https://avalanche.blockpi.network/v1/rpc/public',
          'https://avax-mainnet.gateway.pokt.network/v1/lb/605238bf6b986eea7cf36d5e/ext/bc/C/rpc',
          'https://avalanche.api.onfinality.io/public/ext/bc/C/rpc',
          'https://endpoints.omniatech.io/v1/avax/mainnet/public',
          'https://avax.meowrpc.com'],
        250: [
          'https://endpoints.omniatech.io/v1/fantom/mainnet/public',
          'https://rpc.ankr.com/fantom',
          'https://fantom-mainnet.public.blastapi.io',
          'https://1rpc.io/ftm',
          'https://fantom.blockpi.network/v1/rpc/public',
          'https://fantom.publicnode.com',
          'https://fantom.api.onfinality.io/public',
          'https://rpc.fantom.gateway.fm'],
        137: [
          'https://endpoints.omniatech.io/v1/matic/mainnet/public',
          'https://rpc.ankr.com/polygon',
          'https://polygon-mainnet.public.blastapi.io',
          'https://1rpc.io/matic',
          'https://polygon-bor.publicnode.com',
          'https://polygon-mainnet.g.alchemy.com/v2/demo',
          'https://polygon.blockpi.network/v1/rpc/public',
          'https://polygon.api.onfinality.io/public',
          'https://polygon.rpc.blxrbdn.com/',
          'https://polygon.drpc.org',
          'https://polygon.gateway.tenderly.co',
          'https://gateway.tenderly.co/public/polygon',
          'https://api.zan.top/node/v1/polygon/mainnet/public',
          'https://polygon.meowrpc.com'],
        25: [
          'https://node.croswap.com/rpc',
          'https://cronos.blockpi.network/v1/rpc/public',
          'https://cronos-evm.publicnode.com'],
        142857: [
          'https://rpc1.icplaza.pro/'],
        42161: [
          'https://arb1.croswap.com/rpc',
          'https://rpc.ankr.com/arbitrum',
          'https://1rpc.io/arb',
          'https://arbitrum.getblock.io/api_key/mainnet/',
          'https://arb-mainnet.g.alchemy.com/v2/demo',
          'https://arbitrum.blockpi.network/v1/rpc/public',
          'https://arbitrum-one.public.blastapi.io',
          'https://endpoints.omniatech.io/v1/arbitrum/one/public',
          'https://arb-mainnet-public.unifra.io',
          'https://arbitrum.api.onfinality.io/public',
          'https://rpc.arb1.arbitrum.gateway.fm',
          'https://arbitrum-one.publicnode.com',
          'https://arbitrum.meowrpc.com'],
        421613: [
          'https://endpoints.omniatech.io/v1/arbitrum/goerli/public',
          'https://arb-goerli.g.alchemy.com/v2/demo',
          'https://arbitrum-goerli.public.blastapi.io',
          'https://rpc.goerli.arbitrum.gateway.fm',
          'https://arbitrum-goerli.publicnode.com',
          'https://arbitrum-goerli.blockpi.network/v1/rpc/public'],
        42170: [
          'https://arbitrum-nova.public.blastapi.io',
          'https://arbitrum-nova.blockpi.network/v1/rpc/public',
          'https://arbitrum-nova.publicnode.com'],
        8217: [
          'https://klaytn.blockpi.network/v1/rpc/public',
          'https://klaytn.api.onfinality.io/public',
          'https://1rpc.io/klay'],
        1666600000: [
          'https://rpc.ankr.com/harmony',
          'https://harmony.api.onfinality.io/public',
          'https://1rpc.io/one'],
        1313161554: [
          'https://endpoints.omniatech.io/v1/aurora/mainnet/public',
          'https://1rpc.io/aurora'],
        1313161555: [
          'https://endpoints.omniatech.io/v1/aurora/testnet/public'],
        42220: [
          'https://rpc.ankr.com/celo',
          'https://1rpc.io/celo',
          'https://celo.api.onfinality.io/public'],
        10: [
          'https://optimism-mainnet.public.blastapi.io',
          'https://rpc.ankr.com/optimism',
          'https://1rpc.io/op',
          'https://opt-mainnet.g.alchemy.com/v2/demo',
          'https://optimism.blockpi.network/v1/rpc/public',
          'https://endpoints.omniatech.io/v1/op/mainnet/public',
          'https://optimism.api.onfinality.io/public',
          'https://rpc.optimism.gateway.fm',
          'https://optimism.publicnode.com',
          'https://optimism.meowrpc.com'],
        1881: [
          'https://rpc.cartenz.works'],
        420: [
          'https://endpoints.omniatech.io/v1/op/goerli/public',
          'https://opt-goerli.g.alchemy.com/v2/demo',
          'https://optimism-goerli.public.blastapi.io',
          'https://rpc.goerli.optimism.gateway.fm',
          'https://optimism-goerli.publicnode.com',
          'https://optimism-goerli.blockpi.network/v1/rpc/public'],
        100: [
          'https://rpc.gnosis.gateway.fm',
          'https://gnosis-mainnet.public.blastapi.io',
          'https://rpc.ankr.com/gnosis',
          'https://rpc.ap-southeast-1.gateway.fm/v4/gnosis/non-archival/mainnet',
          'https://gnosis.blockpi.network/v1/rpc/public',
          'https://gnosis.api.onfinality.io/public'],
        10200: [
          'https://rpc.chiado.gnosis.gateway.fm'],
        1285: [
          'wss://moonriver.api.onfinality.io/public-ws',
          'https://moonriver.api.onfinality.io/public',
          'https://moonriver.unitedbloc.com:2000',
          'wss://moonriver.unitedbloc.com:2001',
          'https://moonriver.public.blastapi.io',
          'https://moonriver-rpc.dwellir.com',
          'wss://moonriver-rpc.dwellir.com'],
        1284: [
          'https://moonbeam.api.onfinality.io/public',
          'wss://moonbeam.api.onfinality.io/public-ws',
          'https://moonbeam.unitedbloc.com:3000',
          'wss://moonbeam.unitedbloc.com:3001',
          'https://moonbeam.public.blastapi.io',
          'https://rpc.ankr.com/moonbeam',
          'https://1rpc.io/glmr',
          'https://moonbeam-rpc.dwellir.com',
          'wss://moonbeam-rpc.dwellir.com'],
        4689: [
          'https://rpc.ankr.com/iotex'],
        288: [
          'https://boba-mainnet.gateway.pokt.network/v1/lb/623ad21b20354900396fed7f',
          'https://boba-ethereum.gateway.tenderly.co',
          'https://gateway.tenderly.co/public/boba-ethereum'],
        122: [
          'https://fuse.api.onfinality.io/public'],
        336: [
          'https://shiden.public.blastapi.io',
          'https://shiden-rpc.dwellir.com',
          'wss://shiden-rpc.dwellir.com'],
        592: [
          'https://astar.public.blastapi.io',
          'https://1rpc.io/astr',
          'https://astar-mainnet.g.alchemy.com/v2/demo',
          'https://astar.api.onfinality.io/public',
          'wss://astar.api.onfinality.io/public-ws',
          'https://astar-rpc.dwellir.com',
          'wss://astar-rpc.dwellir.com'],
        82: [
          'https://rpc-meter.jellypool.xyz/',
          'https://meter.blockpi.network/v1/rpc/public'],
        57: [
          'https://rpc.ankr.com/syscoin'],
        11297108109: [
          'https://palm-mainnet.infura.io/v3/3a961d6501e54add9a41aa53f15de99b',
          'https://palm-mainnet.public.blastapi.io'],
        44: [
          'https://crab.api.onfinality.io/public'],
        15557: [
          'https://api.testnet.evm.eosnetwork.com'],
        17777: [
          'https://api.evm.eosnetwork.com'],
        6: [
          'https://geth-kotti.etc-network.info'],
        61: [
          'https://besu-de.etc-network.info',
          'https://geth-de.etc-network.info',
          'https://erigon-de.etc-network.info',
          'https://besu-at.etc-network.info',
          'https://geth-at.etc-network.info',
          'https://erigon-at.etc-network.info'],
        63: [
          'https://geth-mordor.etc-network.info'],
        87: [
          'https://rpc.novanetwork.io:9070',
          'https://dev.rpc.novanetwork.io/'],
        686: [
          'https://karura.api.onfinality.io/public'],
        787: [
          'https://acala-polkadot.api.onfinality.io/public'],
        1001: [
          'https://klaytn-baobab.blockpi.network/v1/rpc/public'],
        1287: [
          'https://moonbase.unitedbloc.com:1000',
          'wss://moonbase.unitedbloc.com:1001',
          'https://moonbase-alpha.public.blastapi.io',
          'https://moonbeam-alpha.api.onfinality.io/public',
          'wss://moonbeam-alpha.api.onfinality.io/public-ws'],
        1440: [
          'https://beta.mainnet.livingassets.io/rpc',
          'https://gamma.mainnet.livingassets.io/rpc'],
        2000: [
          'https://dogechain.ankr.com',
          'https://dogechain-sj.ankr.com'],
        2021: [
          'https://edgeware.api.onfinality.io/public'],
        7001: [
          'https://zetachain-athens-evm.blockpi.network/v1/rpc/public'],
        9001: [
          'https://evmos-mainnet.public.blastapi.io',
          'https://evmos-evm.publicnode.com',
          'https://evmos.api.onfinality.io/public'],
        84531: [
          'https://base-goerli.public.blastapi.io',
          'https://1rpc.io/base-goerli',
          'https://base-goerli.blockpi.network/v1/rpc/public'],
        534353: [
          'https://scroll-alpha-public.unifra.io',
          'https://scroll-alphanet.public.blastapi.io',
          'https://scroll-testnet.blockpi.network/v1/rpc/public'],
        11155111: [
          'https://eth-sepolia.g.alchemy.com/v2/demo',
          'https://endpoints.omniatech.io/v1/eth/sepolia/public',
          'https://ethereum-sepolia.blockpi.network/v1/rpc/public',
          'https://eth-sepolia.public.blastapi.io',
          'https://eth-sepolia-public.unifra.io',
          'https://sepolia.gateway.tenderly.co',
          'https://gateway.tenderly.co/public/sepolia',
          'https://api.zan.top/node/v1/eth/sepolia/public'],
        11297108099: [
          'https://palm-testnet.public.blastapi.io'],
        53935: [
          'https://dfkchain.api.onfinality.io/public'],
        314: [
          'https://rpc.ankr.com/filecoin',
          'https://filecoin.chainup.net/rpc/v1',
          'https://infura.sftproject.io/filecoin/rpc/v1'],
        314159: [
          'https://filecoin-calibration.chainup.net/rpc/v1'],
        3141: [
          'https://filecoin-hyperspace.chainup.net/rpc/v1'],
        50001: [
          'https://rpc.oracle.liveplex.io'],
        15551: [
          'https://api.mainnetloop.com'],
        88888888: [
          'https://rpc.teamblockchain.team'],
        1071: [
          'https://json-rpc.evm.testnet.shimmer.network/'],
        1101: [
          'https://rpc.ankr.com/polygon_zkevm',
          'https://rpc.polygon-zkevm.gateway.fm',
          'https://1rpc.io/zkevm'],
        431140: [
          'https://rpc.markr.io/ext/'],
        248: [
          'https://oasys-rpc.gateway.pokt.network',
          'https://oasys.blockpi.network/v1/rpc/public'],
        3501: [
          'https://rpc.jfinchain.com'],
        35011: [
          'https://rpc.j2o.io'],
        2323: [
          'https://data-testnet-v1.somanetwork.io',
          'https://block-testnet-v1.somanetwork.io'],
        2332: [
          'https://data-mainnet-v1.somanetwork.io',
          'https://block-mainnet-v1.somanetwork.io'],
    }
    return all_rpcs_by_chainId[chain][0:amount]


def thread_rpc_check_and_burn(private_key, rpc_url, delay, error_threshold=10):
    errors=0
    try:
        w3 = Web3(HTTPProvider(rpc_url))
        account = w3.eth.account.privateKeyToAccount(private_key)
        abbreviated_wallet = "[" + re.sub("(^.{6})(.*)(.{4}$)", "\g<1>..\g<3>", account.address) + "]"  # eg. [0xa51B..F41c]
        txn = {  # Set up txn fields that won't change
            'chainId': w3.eth.chain_id,
            'to': account.address,
            'from': account.address,
            'gas': 27000,
            'value': 0,
            'data': '',
            }
        if txn['chainId'] == 1 or txn['chainId'] == 43114:  txn['type'] = 2  # ETH and AVAX use EIP-1559 Type 2 Transactions
        try:
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        except:
            pass
        while errors <= error_threshold:  # Do this continuously for each RPC url
            try:
                wallet_balance = w3.eth.get_balance(account.address)
                if 'type' in txn and txn['type'] == 2:
                    block_data = w3.eth.get_block('pending')
                    if 'baseFeePerGas' in block_data:  # If this key exists then the chain supports Type 2 EIP 1559 Transactions
                        current_baseFee = block_data.baseFeePerGas
                        min_gas_to_send_tx = current_baseFee * txn['gas']
                    else:
                        current_gasPrice = w3.eth.gas_price
                        min_gas_to_send_tx = current_gasPrice * txn['gas']
                else:
                    current_gasPrice = w3.eth.gas_price
                    min_gas_to_send_tx = current_gasPrice * txn['gas']

                if wallet_balance >= min_gas_to_send_tx:
                    try:
                        txn['nonce'] = w3.eth.get_transaction_count(account.address)
                        if 'type' in txn and txn['type'] == 2:
                            maxFeePerGas = math.floor(wallet_balance / 27000)
                            maxPriorityFeePerGas = maxFeePerGas - current_baseFee
                            txn['maxFeePerGas'] = maxFeePerGas
                            txn['maxPriorityFeePerGas'] = maxPriorityFeePerGas
                            txn_t2 = {**{k: txn[k] for k in txn if k in ('nonce', 'to', 'data', 'value', 'chainId', 'maxPriorityFeePerGas', 'maxFeePerGas', 'gas', 'type')}, "accessList": []}
                            signed_txn = account.sign_transaction(txn_t2)
                        else:
                            txn['gasPrice'] = math.floor(wallet_balance / 27000)
                            txn_t0 = {**{k: txn[k] for k in txn if k in ('nonce', 'to', 'data', 'value', 'chainId', 'gasPrice', 'gas')}}
                            signed_txn = account.sign_transaction(txn_t0)
                        txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction).hex()
                        print(f"{str(math.floor(time.time()))} | {format(datetime.datetime.now(), '%H:%M')} , Chain: {txn['chainId']}, RPC: {rpc_url}, {abbreviated_wallet} - Burning gas - Transaction hash: {str(txn_hash)} - {str(txn)}")
                    except Exception as err:
                        if show_errors: print(f"Error sending tx: [{err} on RPC: {rpc_url}")
                        time.sleep(delay)
            except Exception as err:
                if show_errors: print(f"Error #{errors}: [{str(err)}] on RPC: {rpc_url}")
                errors += 1
                time.sleep(delay)
        if errors >= error_threshold: print(f"Stopping Thread. Too many errors on RPC: {rpc_url}")
    except Exception as err:
        if show_errors: print(f"Error #{errors}: [{str(err)}] on RPC: {rpc_url}")
        print(f"Thread stopped for RPC: {rpc_url}")


def main(private_key, target_chains, num_rpcs_per_chain, delay):
    thread_dict = {}
    for chain in target_chains:
        chain_rpcs = get_rpcs(chain, num_rpcs_per_chain)
        if len(chain_rpcs) > 0:
            thread_dict[chain] = []
        for rpc_url in chain_rpcs:
            thread_dict[chain].append(threading.Thread(target=thread_rpc_check_and_burn, name=rpc_url, args=(private_key, rpc_url, delay, 10)))
    for chain in target_chains:
        for thread in thread_dict[chain]:
            thread.start()
    while True:
        print()
        for chain in target_chains:
            total_chain_threads = len(thread_dict[chain])
            alive_threads = 0
            alive_RPCs = []
            for thread in thread_dict[chain]:
                if thread.is_alive():
                    alive_threads += 1
                    alive_RPCs.append(thread.name)
            print(f"Chain #{chain}: Threads running {alive_threads} of {total_chain_threads}: {str(alive_RPCs)}")
            if alive_threads == 0: print(f"NO THREADS RUNNING ON CHAIN #{chain} - Increase the number of RPCs per chain and/or the delay then re-run")
        time.sleep(60)  # Check if threads are alive every 60 seconds


if __name__ == "__main__":
    private_key, target_chains, num_rpcs_per_chain, delay = settings()
    main(private_key, target_chains, num_rpcs_per_chain, delay)
