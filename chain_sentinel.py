#!/usr/bin/env python3
"""chain-address-sentinel — read-only multi-chain address monitor for security / forensics triage.

Purpose: given a set of EVM / Bitcoin / Solana addresses, take a read-only snapshot
of balances and activity, so an auditor or incident-responder can quickly triage
"has funds moved / has this address ever signed / was it funded" without trusting
a single explorer UI.

It never signs, never broadcasts, never writes to chain. Pure public-RPC reads.

Usage:
  python3 chain_sentinel.py --evm 0xabc... --btc bc1p... --sol 4Ui3... 
  python3 chain_sentinel.py --config watchlist.json --interval 300

License: MIT. Public good.
"""
import argparse, json, sys, time, urllib.request

ETH_RPC_DEFAULT = "https://ethereum-rpc.publicnode.com"
SOL_RPC_DEFAULT = "https://solana-rpc.publicnode.com"
BTC_API_DEFAULT = "https://mempool.space/api"


def _http_json(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (chain-sentinel)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _rpc(url, method, params, timeout=25):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/json",
                                          "User-Agent": "Mozilla/5.0 (chain-sentinel)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        j = json.loads(r.read())
    if "error" in j:
        raise RuntimeError(f"{method}: {j['error']}")
    return j["result"]


def evm_snapshot(addr, rpc=ETH_RPC_DEFAULT):
    bal = int(_rpc(rpc, "eth_getBalance", [addr, "latest"]), 16)
    nonce = int(_rpc(rpc, "eth_getTransactionCount", [addr, "latest"]), 16)
    blk = int(_rpc(rpc, "eth_blockNumber", []), 16)
    return {"chain": "evm", "address": addr, "weiz": str(bal),
            "eth": bal / 1e18, "nonce": nonce, "block": blk}


def btc_snapshot(addr, api=BTC_API_DEFAULT):
    d = _http_json(f"{api}/address/{addr}")
    cs = d.get("chain_stats", {}) if isinstance(d, dict) else {}
    return {"chain": "btc", "address": addr,
            "funded_txo_count": cs.get("funded_txo_count", 0),
            "spent_txo_count": cs.get("spent_txo_count", 0),
            "tx_count": cs.get("tx_count", 0),
            "funded_txo_sum_sat": cs.get("funded_txo_sum", 0),
            "balance_sat": cs.get("funded_txo_sum", 0) - cs.get("spent_txo_sum", 0)}


def sol_snapshot(addr, rpc=SOL_RPC_DEFAULT):
    res = _rpc(rpc, "getBalance", [addr])
    acct = _rpc(rpc, "getAccountInfo", [addr, {"encoding": "base58"}])
    return {"chain": "sol", "address": addr, "lamports": res.get("value", 0),
            "exists": acct.get("value") is not None,
            "slot": res.get("context", {}).get("slot")}


def snapshot(conf, interval=None, once=True):
    out = {"ts": int(time.time())}
    for addr in conf.get("evm", []):
        try: out.setdefault("evm", []).append(evm_snapshot(addr))
        except Exception as e: out.setdefault("evm", []).append({"address": addr, "error": str(e)})
    for addr in conf.get("btc", []):
        try: out.setdefault("btc", []).append(btc_snapshot(addr))
        except Exception as e: out.setdefault("btc", []).append({"address": addr, "error": str(e)})
    for addr in conf.get("sol", []):
        try: out.setdefault("sol", []).append(sol_snapshot(addr))
        except Exception as e: out.setdefault("sol", []).append({"address": addr, "error": str(e)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evm", action="append", default=[])
    ap.add_argument("--btc", action="append", default=[])
    ap.add_argument("--sol", action="append", default=[])
    ap.add_argument("--config")
    ap.add_argument("--interval", type=int)
    ap.add_argument("--out")
    a = ap.parse_args()
    conf = {"evm": a.evm, "btc": a.btc, "sol": a.sol}
    if a.config:
        conf = json.load(open(a.config))
    while True:
        snap = snapshot(conf)
        line = json.dumps(snap, ensure_ascii=False)
        print(line)
        if a.out:
            with open(a.out, "a") as f:
                f.write(line + "\n")
        if not a.interval:
            break
        time.sleep(a.interval)


if __name__ == "__main__":
    main()
