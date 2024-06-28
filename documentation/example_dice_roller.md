# Rolling the dice:
!! DRAFT !! !! DRAFT !! !! DRAFT !!

!! DRAFT !! !! DRAFT !! !! DRAFT !!

NOTES:
- Remember to:
  - Introduce concepts of `EmptyDTO` and `QueuedRequestHandlerResponseDTO`

!! DRAFT !! !! DRAFT !! !! DRAFT !!

!! DRAFT !! !! DRAFT !! !! DRAFT !!

---
If you've not looked at the [Echo-client](./example_echo_client.md) and [Echo-server](./example_echo_server.md) examples, you might want to take a look at it.

This example expands on that.

The code for this example is located in the `examples/dice_roller` directory of this repository.

Running the server can be done with: `python -m examples.dice_roller.server -i 0`

And the client with: `python -m examples.dice_roller.client`

## Project structure
Note that, from this point on, we will start exploring good project structure along with the examples. Hence, you'll find the code is distributed over several directories and files, as shown below:
- `dice_roller/`
    - `dtos/`
        - [\_\_init\_\_.py](../examples/dice_roller/dtos/__init__.py)
        - [guess.py](../examples/dice_roller/dtos/guess.py)
        - [roll.py](../examples/dice_roller/dtos/roll.py)
        - [roll_times.py](../examples/dice_roller/dtos/roll_times.py)
    - `handlers/`
        - [\_\_init\_\_.py](../examples/dice_roller/handlers/__init__.py)
        - [guess.py](../examples/dice_roller/handlers/guess.py)
        - [roll.py](../examples/dice_roller/handlers/roll.py)
        - [roll_times.py](../examples/dice_roller/handlers/roll_times.py)
    - `senders/`
        - [\_\_init\_\_.py](../examples/dice_roller/senders/__init__.py)
        - [guess.py](../examples/dice_roller/senders/guess.py)
        - [roll.py](../examples/dice_roller/senders/roll.py)
        - [roll_times.py](../examples/dice_roller/senders/roll_times.py)
        - [tcp_config.py](../examples/dice_roller/senders/tcp_config.py)
    - [\_\_init\_\_.py](../examples/dice_roller/__init__.py)
    - [client.py](../examples/dice_roller/client.py)
    - [server.py](../examples/dice_roller/server.py)

Take note: I'm keeping all my DTO declarations in one directory, a Python package to be more accurate. DTOs are typically shared between clients and servers, so it's good practice to keep them separated in a Python package, where both client and server can get to them.

Relevant packages for the example client are:
- `dtos`
- `senders`

And for the server:
- `dtos`
- `handlers`
