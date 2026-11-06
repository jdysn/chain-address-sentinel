# chain-address-sentinel

A tiny, dependency-free, **read-only** multi-chain address monitor for security
triage and incident response.

Given EVM / Bitcoin / Solana addresses it returns a JSON snapshot of:

- **EVM** (any EVM chain via an `eth` JSON-RPC): balance (wei + ETH), nonce (has the
  address ever signed?), latest block.
- **Bitcoin** (mempool.space API): funded/spent txo counts, tx count, balance.
- **Solana** (Solana JSON-RPC): lamports, whether the account exists, slot.

It **never signs, never broadcasts, never touches the chain state**. Pure public-RPC
reads — safe to run against mainnet.

## Why

When triaging a wallet (e.g. "is this address real / funded / ever used / frozen by a
chain policy") you often can't trust a single explorer. This tool gives a minimal,
auditable, reproducible snapshot you can pipe into your own runbooks.

## Usage

```bash
python3 chain_sentinel.py \
  --evm 0x145D9e9AA38dD9d201730006C155edC3F3A916e7 \
  --btc bc1p2xw4h3jvldm99a0s0mh6hqe656c8qt6pwemdnmu05w72patuzn3q5y37kk \
  --sol 4Ui333ETer1T5bne1MzwkUdnbWY9VVGeCxCG7d4QwYqV
```

Continuous mode (every 300 s, append to file):

```bash
python3 chain_sentinel.py --config watchlist.json --interval 300 --out snapshots.jsonl
```

`watchlist.json`:

```json
{ "evm": ["0x..."], "btc": ["bc1p..."], "sol": ["..."], }
```

## License

MIT — free for everyone. If it saves you time on a security triage, tips are welcome
at the project's self-custodied address (EVM): `0x7eEdd039C5928E7D93CD4054A5EbC537c6Ae4B88`
(ETH / USDC-any-EVM). No account, no KYC — a plain on-chain transfer.
