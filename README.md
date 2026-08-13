Rigdio (with RigDJ)
================
**Rigdio** is an automated goalhorn/anthem player designed to ease the burden on streamers during cup events, and increase the options available to managers/caretakers for the team's music exports.<br>
**RigDJ** is the GUI editor for .4ccm files, released along with Rigdio. It allows for graphical editing of anthem and player songs as well as the various conditions you can set for them. If you intend to use more complex instructions for your music, it is recommended you use RigDJ to avoid needing to know the .4ccm formatting for every condition type.

If you're just looking for the program, you can find it [here](https://github.com/the4chancup/rigdio/releases). Information on how to use Rigdio/RigDJ themselves can also be found [here](https://implyingrigged.info/wiki/Rigdio).

## Build Guide
If you're interested in building Rigdio/RigDJ yourself, here's some info that'll help.

### Requirements
* [Python 3.13](https://github.com/adang1345/PythonVista) - Programming language required to run and build the code. You must use the Windows 7-compatible Python 3.13 builds from PythonVista, not the official Python releases. The official Python 3.9+ releases dropped Windows 7 support, but PythonVista provides backported builds that work on Windows 7 while giving you access to modern Python features. Any 3.13.x version from PythonVista will do.
* [libmpv (64-bit)](https://github.com/eko5624/mpv-win64/releases/tag/2024-04-29) - The mpv media library DLL required to play songs on Rigdio. You must use a Windows 7-compatible build — recent mpv builds from the official source require Windows 8.1+ or 10+. Download `git-libmpv.7z` from the [last Win7-compatible release](https://github.com/eko5624/mpv-win64/releases/tag/2024-04-29) (April 2024, mpv v0.38.0), extract `libmpv-2.dll` from it, and place it in the project and release folders.
* [python-mpv](https://pypi.org/project/python-mpv/) - Python module used for utilising the mpv media library functions to play songs on Rigdio.
* [PyYAML](https://pypi.org/project/PyYAML/) - Python module used for parsing the default settings used in Rigdio.
* [pyinstaller](https://pypi.org/project/pyinstaller/) - Python module used for building the executable files.
* [ffmpeg](https://www.ffmpeg.org/download.html) - Multimedia framework required for loudness analysis. A minimal `ffmpeg.exe` (~1.8 MB) is included in the repository. If you need to rebuild it, see the instructions below.

### Running the Python file
If you've made any changes to the code and wish to test them out without having to build the whole program, you can run it directly through Command Prompt. Open up Command Prompt in your project folder and enter `python (name of code file)`. This also allows you to see whatever messages/errors Rigdio/RigDJ spits out while it's running, making it easier to debug.

For example, the command line to run Rigdio is
```
python rigdio.py
```

Similarly, the command line to run RigDJ is
```
python rigdj.py
```

### Building a Minimal ffmpeg.exe
Rigdio only uses ffmpeg for loudness analysis via the `volumedetect` filter. The full ffmpeg build is ~140 MB, but a minimal build with only the required components is ~1.8 MB. A build script is provided to automate this process.

Run the following batch file:
```
build-ffmpeg.bat
```

This will:
1. Download and install [MSYS2](https://www.msys2.org/) automatically if not already present.
2. Install the required MSYS2 packages (GCC, make, nasm, etc.) automatically.
3. Clone the ffmpeg source (tag n4.4.1, for Windows 7 compatibility).
4. Configure and build a minimal `ffmpeg.exe` with only the decoders, demuxers, parsers, filters, and protocols that Rigdio needs.
5. Copy the built `ffmpeg.exe` to the project folder.

**Notes:**
* On the first run with a fresh MSYS2 installation, the core system update may terminate the MSYS2 terminal. This is normal — just re-run `build-ffmpeg.bat` and it will continue from where it left off.
* The build uses `--disable-asm` to work around GCC 14 incompatibilities with ffmpeg n4.4.1's inline assembly. The performance impact is negligible for loudness analysis.
* The resulting `ffmpeg.exe` is statically linked and has no external DLL dependencies beyond standard Windows system libraries.
* You can pass `--jobs N` to control parallelism: `python build-ffmpeg.py --jobs 4`.

### Building Rigdio/RigDJ
Once you've fully made and tested out your code changes, you can start building the executables. Simply run the batch file for whichever executable you wish to build (**compile-rigdio.bat** for Rigdio, **compile-rigdj.bat** for RigDJ) and wait for the process to finish. Assuming the build process went smoothly and without error, you will see a couple new files and folders. The built executable will be stored in the `dist` folder, alongside a `_internal` folder containing the bundled Python runtime and dependencies. Both the executable and its `_internal` folder are required to run the program.<br>
**TIP:** Replace the executable and `_internal` folder in the Rigdio release folder with your own built ones before testing it out to have a more accurate runtime environment.

If you're on Mac/Linux then you will need to run the command line manually; Fortunately it's short and only a single line.<br>
The command line to build the Rigdio executable is
```
pyinstaller --noconsole --icon=rigdio.ico --add-data "rigdio.ico;." rigdio.py
```

And the command line to build the RigDJ executable is
```
pyinstaller --noconsole --icon=rigdj.ico --add-data "rigdj.ico;." rigdj.py
```

### Assembling a Release
To create a complete Rigdio release package, you will need the following files in a single folder:
* `rigdio.exe` and its `_internal` folder - Built from `compile-rigdio.bat`
* `rigdj.exe` and its `_internal` folder - Built from `compile-rigdj.bat`
* `libmpv-2.dll` - The 64-bit mpv library DLL
* `ffmpeg.exe` - Minimal ffmpeg build (included in the repo, or rebuild with `build-ffmpeg.bat`)
* `config.yml` - Default configuration file
