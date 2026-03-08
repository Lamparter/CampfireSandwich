> [!IMPORTANT]
> Campfire Sandwich is currently in active development for Hack Club's **Campfire Flagship** programme.
>
> The deadline for the completion of this project is *Sunday 22nd March 2026*.
> There is no guarantee for support or continued development after this date.

<p align="left">
  <img src="https://raw.githubusercontent.com/Lamparter/CampfireSandwich/main/sprites/title_logo.png" alt="Campfire Sandwich Logo" width="340">
</p>
<h4>A nostalgic, fast-paced endless-scroller rhythm game built with Python & Pygame.</h4>

---

Introducing **Campfire Sandwich**, an **endless-scroller rhythm game** that blends nostalgic art styles with **fast-paced, music-driven gameplay**.
It reimagines **classic endless-runner aesthetics** - from **cozy farming vibes** to **retro browser-game minimalism** - through a rhythmic twist that keeps every moment engaging.  
Players **jump**, **dodge**, and **sync their actions to the beat** as the world shifts between styles inspired by beloved games like *Stardew Valley*, the *Chrome Dino game*, and *Go Go! Pogo Cat*.  

This game was initially created for **Hackclub's [Campfire Flagship](https://flagship.hackclub.com)** hackathon alongside its sister project *'Grand Throw Auto V'*, but is still being worked on both for fun and also to qualify for future in-person [Hackclub](https://hackclub.com/) events.

---

## Playing the game

<p align="left">
    <!--<a href="">
      <img src="https://github.com/Rise-Software/Rise-Media-Player/assets/74561130/3d7edcaf-26d8-4453-a751-29b851721abd" alt="Get it from Microsoft" />
    </a>-->
    <a href="https://github.com/Lamparter/CampfireSandwich/releases/latest">
      <img src="https://github.com/Rise-Software/Rise-Media-Player/assets/74561130/60deb402-0c8e-4579-80e6-69cb7b19cd43" alt="Get it from GitHub" />
    </a>
</p>

> If you'd like to learn more about previous versions of Campfire Sandwich, look no further than the [demo document](https://gist.github.com/Lamparter/f8bbbeb5fe32a89783621a7a018a0d20) I created for the Hackclub review team :)

### Building from source

#### 1. Prerequisites

- Python 3.10+ including `pip`
- Git
- Pygame and other associated dependencies
- Microsoft Visual Studio Code or other Python-compatible IDE

> [!TIP]
> Using VS Code is recommended for development on Campfire Sandwich because it makes debugging easiest.

#### 2. Clone the repository

```bash
git clone https://github.com/Lamparter/CampfireSandwich
cd CampfireSandwich
```

#### 3. Run the game

```bash
python src/main.py
```

...or simply press <kbd>F5</kbd> if in a compatible IDE.

### How to play the game

> *Scroll down to the bottom of this page to see a demo of the game in action.*

After opening the game for the first time, **press 'Start'** to enter the song selection screen.
You should then see a menu like this:

<img width="640" height="360" alt="Screenshot of song selection screen" src="https://github.com/user-attachments/assets/15aef1ce-271c-4e42-babf-3305aaae1631" />

You can then **choose a song** using either the mouse or keyboard, for example *California Gurls* by *Katy Perry*.

<img width="640" height="360" alt="Screenshot of game in action" src="https://github.com/user-attachments/assets/2335d5e7-944d-43d3-9de7-48aab348122d" />

You will then enter the endless runner game, where you need to **avoid obstacles that run towards the player** sprite (in this case, cacti, because this is the Chrome Dinosaur game theme) by jumping to dodge them.
There may also be a count-in timer on the screen; this will count you into the song so you can prepare yourself to play and enjoy the song at the same time.
You can **jump by pressing <kbd>SPACE</kbd>** like in any classic endless runner game.

The musical twist of Campfire Sandwich is that you must also match your jumps to the beat of the song.
If you can't hear the beat well, **there is a beat bar at the top** that will show you exactly when you must press the space button to score more points.
Every time you jump, a judgement of how accurate your jump was to the beat of the song will be displayed below the beat bar and **the screen will flash if you jump precisely** on the beat.
You should aim to **jump right as the progress of the beat bar reaches the end** (right side) of the bar.

https://github.com/user-attachments/assets/ca4c34cd-d516-4e04-9922-5749d50a7b75

At any point in the game, you can press <kbd>ESC</kbd> to pause the game, this will dim the screen although the music will continue to play in the background.
Some songs have a higher BPM than others: a **higher BPM generally means a more difficult song** to play as you need to jump to avoid obstacles more often.

### Themes

Campfire Sandwich has multiple custom themes that allow you to experience the game in unique ways, including:
- *Stardew Valley* (classic theme), the original pixel-art theme of Campfire Sandwich
- *Below the Surface*, the theme designed at Hackclub's Campfire London event on Saturday 28th February 2026 at Ada, the National College for Digital Skills in Victoria, London
- *Santa Monica*, a theme inspired by Campfire Sandwich's sister project, *Grand Throw Auto V*, which is set by the Santa Monica pier
- *Chrome Dinosaur*, a theme inspired by the [Chrome dinosaur endless runner game](https://pwa-dino.github.io/) (scroll down to see a demo of this theme at the bottom of the page!)
- *Campfire Flagship*, a creative theme inspired by the art and branding used by Hackclub for its Campfire event series
- *Go Go! Pogo Cat*, a theme inspired by the endless runner game of the same name by the Japanese indie game studio PONOS

## Contributing

**Contributions are welcome** - please feel free to add **new rhythm mechanics**, **design sprites**, or **fix bugs**.
And of course, open as many issues or pull requests as you like. *Every contribution is helpful in its own way.*

> Due to how unorganised the Python programming language itself is, a lot of the codebase is unorganised too!
> Therefore, a lot of the codebase may not make a lot of sense as a lot of information about the way it works is stored in my head and not written down.
> Please be patient while I write documentation comments and refactor code so it makes more sense to the lay person.
> **(this problem would not exist if the game was written in an *Actually Good* programming language like C#...)**

*If you're a member of Hackclub, hello! Enjoy playing my game :)*

### Project structure

```
CampfireSandwich/
│
├── art/                   # Album art from songs
├── fonts/                 # Fonts used in game
├── music/                 # Song files used in the rhythm game, in OGG format
├── sfx/                   # Sound effects used by the game
├── sprites/               # Game UI elements and spritesheets
├── src/                   # Game source code
└── README.md
```

### Game design choices

The Campfire Sandwich game is **programmed in Python** (CPython) and uses **Pygame** as its game engine.
A rewrite in IronPython (Python on .NET) was originally planned but would be impossible due to the design of the Pygame framework and its heavy reliance on C extensions.

The game's architecture follows an **MVVM-like design pattern**, with user controls, views and models mostly separated.
This MVVM practice *also* applies to the game's theming system, which requires that every theme be in the same format and means that there is no need to change any line of code to introduce a new theme.

### Custom UI library

Campfire Sandwich uses a custom written UI library that I have spent a long time working on.
Most of the controls from Campfire Sandwich's built-in UI library can be found in [`ui.py`](https://github.com/Lamparter/CampfireSandwich/blob/main/src/ui.py).

These controls include:
- `Button`: a flexible button control

  <img width="240" height="126" alt="Button control demo screenshot" src="https://github.com/user-attachments/assets/5e31c320-2649-4cf5-88d1-3766cec902ff" />

- `ToggleSwitch`: a toggle control that allows switching between "YES" and "NO" enumeration state

  <img width="113" height="70" alt="Toggle switch control demo screenshot" src="https://github.com/user-attachments/assets/05397d25-ab76-424c-9b9b-e9db4b2589ac" />

- `Slider`: a slider control that allows choosing a value within a selected range

  <img width="260" height="53" alt="Slider control demo screenshot" src="https://github.com/user-attachments/assets/2045fa1d-cef0-446d-94fb-dd9a736b9e6b" />

- `TextInput`: a dynamic text input control with full Unicode integration

  <img width="253" height="112" alt="Text input control demo screenshot" src="https://github.com/user-attachments/assets/02710edf-f08e-4621-b3e4-e3f5c6d82c7c" />

- `TileLayout`: a horizontally stacked layout (used in the settings screen) that allows encapsulating controls

  <img width="288" height="73" alt="Tile layout control demo screenshot" src="https://github.com/user-attachments/assets/2bf00fc0-f3f5-4088-b73a-507cf6be7c41" />

- `ParallaxLayout`: an image view that overlays multiple images on top of eachother and applies a parallax scrolling effect
- `Panel`: a smart content dialogue, used to present the pause and game-over overlays, as well as the settings screen
- `ScrollViewer`: a content container (built-in to `TileLayout`) that allows scrolling and navigation by both mouse and keyboard

These controls are custom written for this game, but are detached from the actual game UI and can be reused in any pygame project.
Every UI control accepts input from both the pointer and the keyboard.

## License

This project is **free, open source software** licensed under the MIT License.
Please contact `@Lamparter` on Slack if you have legal questions.

> [!NOTE]
> The source code contains copyrighted material that has been modified.
> *This copyrighted material is intended for personal use only.*

---

https://github.com/user-attachments/assets/6aff3ec4-2417-4944-a214-f252464a2ea7

---

<p align="center">
  <sub>Made with &lt;3 by teenagers, for teenagers. <a href="https://hackclub.com">Learn more about Hackclub.</a></sub>
</p>