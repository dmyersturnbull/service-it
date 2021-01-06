# Service-it

[![Latest version on PyPi](https://badge.fury.io/py/serviceit.svg)](https://pypi.org/project/serviceit/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/serviceit.svg)](https://pypi.org/project/serviceit/)
[![Documentation status](https://readthedocs.org/projects/service-it/badge/?version=latest&style=flat-square)](https://readthedocs.org/projects/service-it)
[![Build & test](https://github.com/dmyersturnbull/service-it/workflows/Build%20&%20test/badge.svg)](https://github.com/dmyersturnbull/service-it/actions)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Build status](https://img.shields.io/pypi/status/serviceit)](https://pypi.org/project/serviceit/)
[![Maintainability](https://api.codeclimate.com/v1/badges/6b804351b6ba5e7694af/maintainability)](https://codeclimate.com/github/dmyersturnbull/service-it/maintainability)
[![Coverage Status](https://coveralls.io/repos/github/dmyersturnbull/service-it/badge.svg?branch=master&service=github)](https://coveralls.io/github/dmyersturnbull/service-it?branch=master)

Turn any Python function into a service that receives JSON payloads on some port.

Here’s a trivial example:

```python
import serviceit
def receiver(payload):
    print(payload)
server = serviceit.server(1533, receiver)
# Now it will receive JSON on 1533. For convenience:
server.client().send(dict(message="hi"))
print(server.bytes_processed)
```

#### More complex example: isolate code
You can use this to isolate a component of you code.
For example, rdkit can be installed through Conda but not Pip (or Poetry).
So, create a service and import it in an Anaconda environment to create a server,
and in your pip-installed client code.

**In a Conda environment**, create a service that listens on port 1533:

```python
import serviceit

def _receiver(payload):
    # noinspection PyUnresolvedReferences
    from rdkit.Chem.inchi import InchiToInchiKey
    inchikey = InchiToInchiKey(payload["inchi"])
    print(inchikey)

server = serviceit.server(1533, _receiver)
```

**On your pip-install client side:**

```python
import serviceit
client = serviceit.client(1533)
client.send(dict(inchi="InChI=1S/H2O/h1H2"))
```


[New issues](https://github.com/dmyersturnbull/service-it/issues) and pull requests are welcome.
Please refer to the [contributing guide](https://github.com/dmyersturnbull/service-it/blob/master/CONTRIBUTING.md).  
Generated with [Tyrannosaurus](https://github.com/dmyersturnbull/tyrannosaurus).
