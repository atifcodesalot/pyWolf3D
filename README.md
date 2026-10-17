

# pyWolf3D

https://github.com/user-attachments/assets/5e6a4363-d74f-4169-80cf-a0231394a414

## What is pyWolf3D?
PYWOLF3D is a [Wolfenstein 3D](https://en.wikipedia.org/wiki/Wolfenstein_3D) engine, game clone written from scratch in pygame, Python. 


## Why?
I am a huge Doom and Wolfenstein fan so I just decided to rewrite one of the originals myself :sunglasses:. It was mostly for fun and learning. 


## How to play?
Simply clone this repository:

```
git clone https://github.com/atifcodesalot/pyWolf3D
```
change the directory to the root of the project:

```
cd pyWolf3D
```

Then install the required packages;

For `Windows`:

```
py -m pip install -r requirements.txt
```


For `Unix`:
```
python3 -m pip install -r requirements.txt
```

Then run;

For `Windows`:

```
py -m wolfenstein3D
```

For `Unix`:

```
python3 -m wolfenstein3D
```


## Info on the project

I tried to keep this clone as accurate as possible (compared to the original)
but some things are probably different. The damage model and actor behaviour are mostly similar.
The clone currently doesn't support beyond episode 1, there is no projectile or texture support for, e.g
Spear of Destiny. It extracts the original maps from the shareware version files MAPHEAD.WL1 and MAP. In the near future, I plan to complete it.

### Technical stuff

#### Rendering
The game employs a raycaster just like the original for rendering, there is no actual rasterization.
The default amount of rays cast are 160 and
the default fov is 54 degrees. You can play around with it.
It is simple and reusable.

The maps are 64 to 64 grids and the raycaster uses the DDA algorithm to
find collisions with the non empty tiles. The special cases are doors and pushwalls,
which the raycaster handles explicitly.

#### Sound
The sound engine doesn't do much, apart from attenuation.
Directional sound is not there yet but I will implement it soon.
The sound propagation is done via the preprocessed area tiles.

Some of the sound effects, like treasure pickup, were actually synthesized during runtim
in the original, this version uses .wav files for all sound and .ogg files for music.

## Credits
- Code: All of the components, WL1 file parsing, rendering, sound and game logic were implemented by me, AI wasn't used in anyway for code generation.
- Sprites, sounds: The sprites, sounds of the original were obtained from the internet, sometimes via LLM's (some sprites are relatively obscure)


## Resources
- [game engine black book Wolf3D](https://fabiensanglard.net/gebbwolf3d/) is an awesome book
and I have read it extensively during the development of this clone. Chase state chains, sprite rendering, sound propagation and many other aspects, I understood from this book and enjoyed its every page, it truly is awesome.
- https://www.spriters-resource.com/ms_dos/wolfenstein3d/ for the original sprites.
- https://sounds.spriters-resource.com/ms_dos/wolfenstein3d for general sound effects.
- https://forum.zdoom.org/viewtopic.php?t=46658 this forum post for adlib sound effects in .wav format.


## Features yet to be implemented
- Baby difficulty damage reduction
- Floor finish screen
- Projectiles, more episode sprites and texture support
- Hans Grösse sound effects
- Episode 1 ending animation

## Bugs
I have been working on this for some time now, so I decided to just put it out there before it was
well... perfect. There are some non game breaking (in my opinion :D) bugs that I am aware of and will fix it in the future. If you notice any, let me know.





