Deadly Towers (EN) Mashou (JP) – Arbitrary Code Execution via Inventory Pointer Corruption
Overview

This document describes a method for achieving arbitrary code execution (ACE) in the Japanese and US release of Deadly Towers on the NES.

The exploit chain leverages:

Uninitialized memory across soft resets / cartridge swaps
Lack of bounds checking in inventory indexing
Password-based arbitrary memory writes
An indirect jump that resolves into RAM
Controllable object state (enemy X coordinates) as executable bytecode

The result is full control of execution flow, culminating in a clean redirection into existing game logic to trigger the ending sequence.

Root Cause
1. Uninitialized Memory

The game does not properly initialize several RAM locations on startup. Notably:

$0188 – Inventory cursor offset / pointer

This value persists across cartridge swaps when using another NES title to pre-fill RAM.

Because the game only updates $0188 when the inventory cursor is moved, it is possible to retain an attacker-controlled value during normal gameplay.

Primitive 1 – Out-of-Bounds Inventory Indexing
Relevant Memory
Inventory: $0176–$017E
Cursor offset: $0188

When interacting with the inventory, the game performs:

effective_address = base_inventory + $0188

There is no bounds checking on $0188.

Impact

If $0188 > 8, the game will:

Read outside the inventory array
Interpret arbitrary memory as item data
Use that data in subsequent control flow

This provides an arbitrary read primitive within RAM.

Primitive 2 – Password-Based Arbitrary Write

Through reversing the password encoding/decoding system, two fields were identified as directly controllable:

$01B1
$01B3

These can be set to any value from 0–255 using the in-game password system.

Impact

This provides a constrained but reliable arbitrary write primitive.

Control Flow Hijack

By setting either $01B1 or $01B3 to specific values, the game’s item-use logic can be redirected.

Key Observation

Setting the value to:

42

causes execution to follow a chain of jumps that ultimately resolves to:

JMP ($001E)

Where the pointer resolves to:

$032B
Primitive 3 – Execution in RAM

The indirect jump lands at:

$032B

This region corresponds to:

Enemy X coordinate buffer

Range observed:

$0323–$033E
Critical Insight
Each enemy X position is a byte (0–255)
These bytes are fully controllable via enemy positioning
The CPU begins executing instructions directly from this region
Impact

This converts game state into:

attacker-controlled executable byte stream

This is true arbitrary code execution.

Payload Construction

Because $0323–$033E is fully controllable, it can be used as a code buffer (~28 bytes).

Initial testing confirmed:

Instructions execute correctly
Control flow can be redirected reliably
Payload alignment is stable
Final Exploit Strategy

Rather than constructing full instruction sequences manually, the exploit leverages existing game logic.

Target Routine

A routine at:

$9EFF

performs logic that ultimately sets:

$0050 = $16

This state transition leads directly to the game’s victory condition.

Final Payload

Written into enemy X coordinate memory:

4C FF 9E

Which corresponds to:

JMP $9EFF
Execution Flow
Inventory corruption
→ Item ID 42 selected
→ Indirect jump via ($001E)
→ Execution enters $032B (enemy X buffer)
→ Payload executes: JMP $9EFF
→ Game logic sets state ($50 = $16)
→ Victory sequence triggered
Result

Successful execution produces the game’s ending screen:

YOU WON THE VICTORY.
THIS STORY IS OVER.
SEE YOU NEXT TIME !

Summary of Exploit Chain
Uninitialized memory allows control of $0188
Out-of-bounds inventory indexing enables arbitrary reads
Password system enables controlled writes to $01B1/$01B3
Item ID manipulation (42) redirects control flow
Indirect jump (JMP ($001E)) resolves into RAM
Enemy X positions provide fully controllable executable bytes
Payload (JMP $9EFF) redirects into game logic
Game state is modified → victory condition triggered
Notes
Other values besides 42 may produce different jump targets and are worth exploring
The US version shares the same vulnerability
The enemy buffer execution region is large enough to support multi-stage payloads
This technique can likely be extended into more complex ACE chains, including loaders or arbitrary state manipulation
