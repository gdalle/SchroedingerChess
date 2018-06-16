# Boxes Game

# Rules

See https://www.raywenderlich.com/38732/multiplayer-game-programming-for-teens-with-python

## Creation of the environment

```shell
conda create --name heisenberg-chess
conda install -n heisenberg-chess pip
conda install -n heisenberg-chess twisted
conda install -n heisenberg-chess pip
conda install python.app

source activate heisenberg-chess
pip install pygame
source deactivate heisenberg-chess
```
## Launching the server

```shell
source activate heisenberg-chess
python server.py
```

## Launching a client

```shell
source activate heisenberg-chess
pythonw boxes.py
```



