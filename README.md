![LCDN Logo][logo]

# LCDN: Low Cost Deterministic Networking Controller
---

## Status of the Git repository
--- 
This repository contains the source code for the controller logic that was used in the LCDN paper. The repo mainly offers
the business logic for now. LCDN also has an implementation that directly works with hardware. However, the code quality
is not in a state that we feel comfortable to publish it yet.

## Structure
---
The Repo follows the structure of LCDN. Below the most important parts are listed.

```commandline
-- LCDN
    |-- core
    |-- Network
    |-- Network Calculus
    |-- Routing
    |-- manager.py
```

The `core` folder represent our efforts to refactor LCDN's business logic and include the hardware interface.
`Network` contains all functions and classes for building and managing the topology. 
`Network Calculus` contains the implementation of the DNC framework
`Routing` offers the Routing Manager and all auxiliary functions.
`maanger.py` contains the main LCDN implementation

## Usage
--- 
The file `example.py` in the root of the directory contains a simple example on how to use LCDN's business logic.

## Code Status
---
Track the progess of the `core` unification for LCDN.
 - [ ] Move current Business Logic to new Interface (core)
 - [ ] HTTP API for LCDN
 - [ ] Hardware Interface Refactoring
   - [ ] LLDP Module
   - [ ] Raspberry Pi Middleware
   - [ ] Switch Controller

## Questions?
---
If you have any questions regarding the state of LCDN or its functionality, feel free to contact per mail philip.diederich@tum.de

## Help us and Cite us!
---
The Controller was primarily introduced in the paper: "LCDN: Providing Network Determinism with Low-Cost Switches".
If you use LCDN, please cite our paper

```
@inprceedings{diederich_lcdn_2025,
    title = {{LCDN}: {Providing} {Network} {Determinism} with {Low-Cost} {Switches}},
    author = {Diederich, Philip and Deshpande, Yash and Becker, Laura and Raunecker, David and Alexej, Grigorjew and Hoßfeld, Tobias and Kellerer, Wolfgang},
    year = {2025},
    booktitle = {2025 21st International Conference on Network and Service Management (CNSM)}
}
```

[logo]: ./Images/LCDN_logo_small.png
