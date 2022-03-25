<a id="packages.valory.skills.abstract_round_abci.utils"></a>

# packages.valory.skills.abstract`_`round`_`abci.utils

This module contains utility functions for the 'abstract_round_abci' skill.

<a id="packages.valory.skills.abstract_round_abci.utils.VerifyDrand"></a>

## VerifyDrand Objects

```python
class VerifyDrand()
```

Tool to verify Randomness retrieved from various external APIs.

The ciphersuite used is BLS_SIG_BLS12381G2_XMD:SHA-256_SSWU_RO_NUL_

https://drand.love/docs/specification/`cryptographic`-specification
https://github.com/ethereum/py_ecc

<a id="packages.valory.skills.abstract_round_abci.utils.VerifyDrand.verify"></a>

#### verify

```python
def verify(data: Dict, pubkey: str) -> Tuple[bool, Optional[str]]
```

Verify drand value retried from external APIs.

**Arguments**:

               https://drand.love/developer/http-api/`public`-endpoints
- `data`: dictionary containing drand parameters.
- `pubkey`: league of entropy public key

**Returns**:

bool, error message

