

# pyWolf3D

https://github.com/user-attachments/assets/08ba57ab-13c0-46ac-b9da-38720674c9ba


Please excuse my mouse sounds in the demo :sweat_smile:



## What is pyWolf3D?
PYWOLF3D is a [Wolfenstein 3D](https://en.wikipedia.org/wiki/Wolfenstein_3D) engine, game clone written from scratch in pygame, Python. 


## Why?
I am a huge Doom and Wolfenstein fan so I just decided to rewrite one of the originals myself :sunglasses:. It was mostly for fun and learning. 


## Code authorship
All code present in this project was written by me, without AI code generation or coding agents. AI tools were used for discussion, research, and help locating existing game assets and resources. The implementation, including map parsing, rendering, actor behavior, and game logic is entirely my own work. But don't take my word for it: https://isvibecoded.com/.

## Some screenshots
<img width="401" height="316" alt="ss5" src="https://github.com/user-attachments/assets/6fb449fb-2550-4b86-bb63-cab538fd5f79" />
<img width="401" height="316" alt="ss4" src="https://github.com/user-attachments/assets/3450b257-dbd7-4388-be90-366c568cd97e" />
<img width="401" height="316" alt="ss3" src="https://github.com/user-attachments/assets/63286186-6e3e-41f0-a770-2a410becaec6" />
<img width="401" height="316" alt="ss2" src="https://github.com/user-attachments/assets/6c85836e-ea27-42ed-a191-792aed1f9c3e" />
<img width="401" height="316" alt="ss1" src="https://github.com/user-attachments/assets/fe2d7534-f7e1-466a-9399-553d2f54795e" />
<img width="401" height="316" alt="ss7" src="https://github.com/user-attachments/assets/2bc2bbd6-d64a-4578-a40d-49b1bf9fdc7c" />

## How to play?

### Episode 1 shareware version
To play the shareware version of episode 1, simply clone this repository:

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
### Original Maps

You can now play all 6 episodes, but they aren't quite complete: the bosses and the music aren't there (but will be completed in the near future).
If you still want to play, you will need to drop the `GAMEMAPS.wl6` and `MAPHEAD.wl6`from your 
purchased installation into the `./wolfenstein3D/assets/maps folder.


## Info on the project

I tried to keep this clone as accurate as possible (compared to the original)
but some things are probably different. The damage model and actor behaviour are mostly similar.
The clone currently supports playing the original 6 episodes but it is incomplete as mentioned. It extracts the original maps from the shareware version files MAPHEAD.WL1 and MAP. If you want to play the original episodes, as previously stated, you will need to drop the `GAMEMAPS.wl6` and `MAPHEAD.wl6`from your 
purchased installation into the `./wolfenstein3D/assets/maps` folder.

### Technical stuff

#### Rendering
The game employs a raycaster just like the original for rendering, there is no actual rasterization.
The default amount of rays cast are 160 and
the default fov is 54 degrees. You can play around with it.
It is simple and reusable.

The maps are 64 to 64 grids and the raycaster uses the DDA algorithm to
find collisions with the non empty tiles. The special cases are doors and pushwalls,
which the raycaster handles explicitly.

Sprites, projectiles are rendered via perspective projection.

#### Sound
The sound engine is responsible for attenuation and directional sound.
Directional sound is achieved by panning the audio via hardcoded configurations.
The sound propagation is done via the preprocessed area tiles.
Some of the sound effects, like treasure pickup, were actually synthesized during runtime
in the original, this version uses .wav files for all sound and .ogg files for music.

## Credits
- Code: All of the components, WL1, WL6 file parsing, rendering, sound and game logic were implemented by me, as mentioned; AI wasn't used in anyway for code generation.
- Sprites, sounds: The sprites, sounds of the original were obtained from the internet, sometimes via LLM's (some sprites are relatively obscure \[like fake hitler sprites\])
- Pacman sprites from Ultimecia


## Resources
- [game engine black book Wolf3D](https://fabiensanglard.net/gebbwolf3d/) is an awesome book
and I have read it extensively during the development of this clone. Chase state chains, sprite rendering, sound propagation and many other aspects, I understood from this book and enjoyed its every page, it truly is awesome.
- https://www.spriters-resource.com/ms_dos/wolfenstein3d/ for the original sprites.
- https://sounds.spriters-resource.com/ms_dos/wolfenstein3d for general sound effects.
- https://forum.zdoom.org/viewtopic.php?t=46658 this forum post for adlib sound effects in .wav format.


## Features yet to be implemented
- ~Baby difficulty damage reduction~ done
- Floor finish screen (working on it)
- Projectiles, more episode sprites and texture support (working on it)
- ~Hans Grösse sound effects~ done
- Episode 1 ending animation
- Spear of destiny 

## Bugs
I have been working on this for some time now, so I decided to just put it out there before it was
well... perfect. There are some non game breaking (in my opinion :D) bugs that I am aware of and will fix it in the future. If you notice any, let me know.





