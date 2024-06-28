# Dice roller DTOs

Seeing as they are central to both client and server, let's cover them first.
## [dtos/roll.py](../../../examples/dice_roller/dtos/roll.py)
```python
from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class RollRequestDto(PydanticBaseModel):
    sides: int


# --------------------------------------------------------------------------------
class RollResponseDto(PydanticBaseModel):
    result: int
```
There is nothing special here. We have a request and a response DTO. The end.

## [dtos/guess.py](../../../examples/dice_roller/dtos/guess.py)
```python
from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class GuessResponseDto(PydanticBaseModel):
    number: int
```
Here you might ask: "Why is there only a response DTO here?"

Good question, make a note of that, we'll be answering it later.

## [dtos/roll_times.py](../../../examples/dice_roller/dtos/roll_times.py)
```python
from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class RollTimesRequestDto(PydanticBaseModel):
    sides   : int
    how_many: int
```

And here you might ask: "Wait what! There's only a request DTO here?"

Good observation. Again, make a note of that. The reasons are coming.

For now though, go ahead and take a look at [the server](./server.md).
