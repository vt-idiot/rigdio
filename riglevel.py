from version import riglevel_version as version
from tkinter import *
import tkinter.messagebox as messagebox
from config import settings

import os
from threading import Thread
from glob import glob
from pydub import AudioSegment

from tkinter import ttk
import tkinter.filedialog as filedialog

from logger import startLog
if __name__ == '__main__':
   # allow/forbid riglevel to write to log depending on user's configs
   if settings.config["write_to_log"]:
      startLog("riglevel.log")
   print("riglevel {}".format(version))

class Riglevel (Frame):
   def __init__(self, master):
      super().__init__(master)
      Label(self, text="Use this program to normalize music sound levels.").grid(columnspan=2)
      Label(self, text="").grid(row=1)

      # text box widget to change desired sound levels to normalize to
      targetFrame = Frame(self)
      targetFrame.grid(row=2, columnspan=2)
      Label(targetFrame, text="Target sound level: ").pack(side=LEFT)
      self.targetLevelVar = StringVar()
      self.targetAudioInput = Entry(targetFrame, textvariable=self.targetLevelVar, width=10)
      self.targetLevelVar.set(settings.level["target"])
      self.targetAudioInput.pack(side=LEFT)
      # note: dBFS (decibel full scale) is not the same as dB
      Label(targetFrame, text="dBFS").pack(side=LEFT)

      importFolderBtn = Button(self, text="Import music folder", command=self.loadMusic, bg="#e0fcea")
      importFolderBtn.grid(row=3, column=0, pady=5)
      importFileBtn = Button(self, text="Import music file", command=lambda: self.loadMusic(False), bg="#e0fcea")
      importFileBtn.grid(row=3, column=1, pady=5)

      self.countLbl = Label(self, text="0 out of 0 songs to normalize")
      self.countLbl.grid(row=4, columnspan=2, pady=2)

      #normalizeBtn = Button(self, text="Normalize music", command=self.normalizeMusic, bg="#eae0fc")
      normalizeBtn = Button(self, text="Normalize music", command=self.startNormalizeThread, bg="#eae0fc")
      normalizeBtn.grid(row=5, columnspan=2, pady=2)

      # to show progress of normalization process
      self.progress = IntVar()
      self.progressbar = ttk.Progressbar(self, variable=self.progress, length=250)
      self.progressbar.grid(row=6, columnspan=2, pady=5)

      self.audioFileTypes = [".mp3", ".ogg", ".flac", ".m4a", ".wav"]
      self.validArr = []
      self.thread = None

   # load music and identify which song(s) need to be normalized
   # folder argument to differentiate between importing folder or file
   def loadMusic(self, folder = True):
      songArr = []
      if (folder):
         f = filedialog.askdirectory()
         # leave function if user cancels dialog
         if f == "": return

         # go through files in directory, only count non-normalized songs
         for path, _, files in os.walk(f):
            for file in files:
               file = os.path.join(path, file)
               name, ext = os.path.splitext(file)
               if ext in self.audioFileTypes and not name.endswith("_normalized"):
                  songArr.append(file)
      else:
         f = filedialog.askopenfilename(filetypes = (("Music files", "*.mp3, *.ogg, *.opus, *.flac, *.m4a, *.wav"),("All files","*")))
         # leave function if user cancels dialog
         if f == "": return

         name, ext = os.path.splitext(f)
         if ext in self.audioFileTypes and not name.endswith("_normalized"):
            songArr.append(f)
      
      # copy list of song names to filter out already normalized songs
      self.validArr = songArr.copy()
      for song in songArr:
         # if song already has a normalized equivalent, remove it from the valid list
         if glob(os.path.splitext(song)[0] + "_normalized.*"):
            self.validArr.remove(song)
      # display number of songs that need to be normalized out of how many were scanned
      self.countLbl['text'] = "{} out of {} songs to normalize".format(len(self.validArr), len(songArr))

   def startNormalizeThread(self):
      if self.thread is not None:
         message = "Unable to start normalization due to currently ongoing process. Please wait for it to finish first."
         print(message)
         messagebox.showwarning("Process Error", message)
         return
      self.thread = Thread(target=self.normalizeMusic)
      self.thread.start()

   def normalizeMusic(self):
      # if there's zero valid songs to normalize, do nothing
      if len(self.validArr) == 0:
         print("Normalize button pressed but no songs to normalize.")
         self.countLbl['text'] = "No songs to normalize"
         self.thread = None
         return
      
      # create a copy of the valid songs array before clearing it for future use
      copyArr = self.validArr.copy()
      self.validArr.clear()

      self.progress.set(0)
      failedArr = []
      count, max = 0, len(copyArr)
      for song in copyArr:
         # if the user exits the program in the middle of the process, kill the thread
         if killThread:
            print("Normalization process ended early.")
            self.thread = None
            return

         print("Processing file " + song)
         name, ext = os.path.splitext(song)
         ext = ext[1:]
         try:
            sound = AudioSegment.from_file(song, format=ext)
         except Exception:
            # if song file could not be read, skip it while noting down the name
            print("Pydub failed to read {}. This is highly likely due to the " \
            "song file using an audio codec that isn't supported.".format(song))
            failedArr.append(song)
            count += 1
            self.updateProgress(count, max)
            continue

         # get target audio level, return error if invalid input
         try:
            target = float(self.targetLevelVar.get())
            if (target > 0):
               message = "Audio level cannot be more than 0 dBFS."
               print(message)
               messagebox.showwarning("Input Error", message)
               self.thread = None
               return
         except ValueError:
            message = "Invalid audio level input, enter only numbers for the audio level."
            print(message)
            messagebox.showwarning("Input Error", message)
            self.thread = None
            return
         # normalize song to specified dBFS level
         change = target - sound.max_dBFS
         print("   File has peak of {} dBFS, target is {} dBFS; applying {} dBFS gain.".format(sound.max_dBFS, target, change))
         output = sound.apply_gain(change)

         # export normalized song
         outfile = name + "_normalized.opus"
         print("   Writing normalised file to {}".format(outfile))
         output.export(outfile, format="opus", parameters=["-c:a", "libopus", "-b:a", "160k"])

         # tick up the counter and update progress bar accordingly
         count += 1
         self.updateProgress(count, max)
      
      # change text to show process complete
      message = "Normalization complete"
      # if there are songs that failed to be normalized, display warning window
      # listing the affected songs
      if failedArr:
         message += " with {} failed songs".format(len(failedArr))
         failed = "One or more songs could not be normalized, this is likely " \
         "due to the file using an audio codec that isn't supported. " \
         "It's recommended that you normalize the affected songs yourself " \
         "or reencode them and try again.\n" \
         "List of songs that could not be normalized:\n\n"
         for song in failedArr:
            failed += song + "\n"
         print(failed)
         messagebox.showwarning("Incomplete Normalization", failed)
      print(message)
      self.countLbl['text'] = message
      self.thread = None

   def updateProgress(self, count, max):
      if count == max:
         self.progress.set(99.9)
      else:
         self.progressbar.step(round((1 / max) * 100, 1))

def main():
   master = Tk()
   # exit protocol to ensure normalization thread is killed
   def close():
      global killThread
      killThread = True
      master.destroy()

   master.title("riglevel {}".format(version))
   riglevel = Riglevel(master)
   riglevel.pack()
   master.protocol("WM_DELETE_WINDOW", close)
   mainloop()

killThread = False
if __name__ == '__main__':
   main()
