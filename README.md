# SchroedingerChess

[![Join the chat at https://gitter.im/SchroedingerChess/Lobby](https://badges.gitter.im/SchroedingerChess/Lobby.svg)](https://gitter.im/SchroedingerChess/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge) [![Build Status](https://travis-ci.org/gdalle/SchroedingerChess.svg?branch=master)](https://travis-ci.org/gdalle/SchroedingerChess)

Implementation of Haft Schroedinger Chess, where chess pieces decide what they want to be...

See the docs at https://gdalle.github.io/SchroedingerChess/

To run the code, you first need to install a few dependencies:
```
conda create -n chess python=3.6.8
conda activate chess
python3 -m pip install twisted==18.9.0 pygame==1.9.4 pulp==1.6.9
```

Then, all it takes to play a game is to execute `python run.py`.
