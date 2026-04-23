# Project Overview

This project, `opshin`, is a compiler for writing Cardano smart contracts in a strict subset of Python. The goal is to allow developers to write secure and efficient smart contracts using familiar Python syntax and tools. The compiled output is [UPLC](https://blog.hachi.one/post/an-introduction-to-plutus-core/), the "assembly language" of the Cardano Blockchain.

**Main Technologies:**

*   **Python:** The smart contracts are written in Python.
*   **UPLC:** The compilation target for the smart contracts.
*   **Poetry:** Used for dependency management and packaging.

**Architecture:**

The compiler works in several stages:

1.  **Static Type Inference:** An aggressive static type inferencer ensures type safety.
2.  **AST Rewriting:** Complex Python expressions are simplified.
3.  **Compilation to Pluthon:** The Python code is compiled into an intermediate language called `pluthon`.
4.  **Compilation to UPLC:** The `pluthon` code is compiled into the final UPLC.

# Building and Running

**Installation:**

```bash
python3 -m pip install opshin
```

**Compiling:**

To compile a smart contract:

```bash
opshin compile spending examples/smart_contracts/assert_sum.py
```

**Building:**

To generate all artifacts needed for deployment:

```bash
opshin build spending examples/smart_contracts/assert_sum.py
```

**Running Tests:**

The project uses `pytest` for testing. To run the tests:

```bash
pytest
```

**Evaluating a script:**

To evaluate a script in Python:
```bash
opshin eval spending examples/smart_contracts/assert_sum.py "{\"int\": 4}" "{\"int\": 38}" d8799fd8799f9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffd8799fd8799fd87a9f581cdbe769758f26efb21f008dc097bb194cffc622acc37fcefc5372eee3ffd87a80ffa140a1401a00989680d87a9f5820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dffd87a80ffffff809fd8799fd8799fd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd87a80ffa140a14000d87980d87a80ffffa140a14000a140a1400080a0d8799fd8799fd87980d87a80ffd8799fd87b80d87a80ffff80a1d87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffd87980a15820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd8799f5820746957f0eb57f2b11119684e611a98f373afea93473fefbb7632d579af2f6259ffffd87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffff
```

# Development Conventions

*   **Coding Style:** The project uses `black` for code formatting.
*   **Type Hinting:** The project relies heavily on Python's type hinting for its static analysis and compilation.
*   **Testing:** Unit tests are written using `pytest`. Property-based testing is encouraged with `hypothesis`.
*   **Contributions:** Contributions are welcome. A bug bounty program is in place to reward issue resolution.

This `GEMINI.md` file provides a good starting point for understanding and working with the `opshin` project.
