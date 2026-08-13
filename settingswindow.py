import os
import sys
from tkinter import *
from config import settings, saveConfig
from uiutil import ToolTip, palette

# Settings metadata: grouped by section, each entry is:
#   (key, label, type, default, tooltip)
# type is "check" (0/1), "scale" (float slider), or "scale_int" (int slider)
# All settings require a restart to take effect.
SETTINGS_META = [
   ("Audio & Normalization", [
      ("normalize_volume", "Normalize volume", "check", 1,
       "When enabled, rigdio analyzes every song's loudness and applies gain\n"
       "so they all play at a consistent volume level. Replaces individual\n"
       "volume sliders with a single Master Volume slider."),
   ]),
   ("Display & UI", [
      ("dark_mode_enabled", "Dark mode", "check", 0,
       "Switches the interface to a dark colour scheme."),
      ("show_goalhorn_volume_default", "Show volume sliders by default", "check", 1,
       "[Only considered when normalization is disabled]\n"
       "This controls whether each goalhorn's individual volume\n"
       "slider is visible by default when a team is loaded.\n"
       "They can still be toggled per-goalhorn with the speaker icon."),
      ("alphabetical_sort_goalhorns", "Sort goalhorns alphabetically", "check", 0,
       "Sorts player goalhorn buttons alphabetically by player name when a\n"
       "team is loaded. When disabled, goalhorns appear in file order."),
      ("alphabetical_sort_chants", "Sort chants alphabetically", "check", 0,
       "Sorts the chant list alphabetically by filename when a team is loaded.\n"
       "When disabled, chants appear in file order."),
   ]),
   ("Chants", [
      ("chant_timer_enabled_default", "Enable chant timer by default", "check", 1,
       "Sets the default state of the chant timer checkbox in the chants\n"
       "window. When on, chants automatically fade out after the timer\n"
       "duration."),
      ("chant_random_decay_weight", "Chant repeat decay weight", "scale", 0.3,
       "Controls how quickly repeated chants become less likely to be picked\n"
       "again when using random chant selection. Lower values = less repetition.\n"
       "Set to 0.0 to prevent repeats completely. Set to 1.0 for uniform random."),
   ]),
   ("Logging & Files", [
      ("write_to_log", "Write to log file", "check", 1,
       "Allows rigdio to write diagnostic messages to rigdio.log.\n"
       "Disable this if your system doesn't allow file writing and rigdio\n"
       "crashes on startup."),
      ("write_song_title_log", "Write song title to title.log", "scale_int", 0,
       "Writes the currently playing song's title/filename to title.log,\n"
       "useful for OBS overlays. Set to 0 to disable. Set to a number of\n"
       "seconds (e.g. 30) to keep the title visible for that duration after\n"
       "the song starts, before clearing it."),
   ]),
]

class SettingsWindow:
   """Modal settings window for rigdio. Edits config.yml settings with
   explanations and Save/Cancel buttons. All settings require restart."""

   def __init__(self, parent):
      self.parent = parent
      self.win = Toplevel(parent)
      self.win.title("Settings")
      self.win.transient(parent)
      self.win.grab_set()
      self.win.resizable(False, False)
      # colours
      self.colours = palette()
      # store the current config values so Cancel can discard changes
      self.original = dict(settings.configs["config"])
      # store the widgets for each setting
      self.widgets = {}
      self.vars = {}
      self._buildUI()

   def _buildUI(self):
      dark = settings.config["dark_mode_enabled"]
      row = 0
      for section_name, items in SETTINGS_META:
         # section header
         Label(self.win, text=section_name, font="TkDefaultFont 9 bold",
               fg=self.colours["fg"]).grid(row=row, column=0, columnspan=3,
                  sticky=W, padx=10, pady=(10,2))
         row += 1
         for key, label, typ, default, tooltip in items:
            current = settings.configs["config"].get(key, default)
            # info icon (left of label) with tooltip
            info = Label(self.win, text="ⓘ", fg=self.colours["fg"], cursor="question_arrow")
            info.grid(row=row, column=0, sticky=W, padx=(15,2), pady=2)
            ToolTip(info, tooltip)
            # label
            lbl = Label(self.win, text=label)
            lbl.grid(row=row, column=1, sticky=W, padx=(0,5), pady=2)
            # control
            if typ == "check":
               var = IntVar(value=current)
               # in dark mode the foreground is white, which makes the
               # checkmark invisible on the white indicator; force black
               cb = Checkbutton(self.win, variable=var,
                  fg="black" if dark else None)
               cb.grid(row=row, column=2, sticky=W, padx=(0,12), pady=2)
               self.widgets[key] = cb
               self.vars[key] = var
            elif typ == "scale":
               var = DoubleVar(value=current)
               sc = Scale(self.win, from_=0.0, to=1.0, resolution=0.05,
                  orient=HORIZONTAL, variable=var, showvalue=1, length=120)
               sc.grid(row=row, column=2, sticky=W, padx=(0,12), pady=2)
               self.widgets[key] = sc
               self.vars[key] = var
            elif typ == "scale_int":
               var = IntVar(value=current)
               sc = Scale(self.win, from_=0, to=300, resolution=1,
                  orient=HORIZONTAL, variable=var, showvalue=1, length=120)
               sc.grid(row=row, column=2, sticky=W, padx=(0,12), pady=2)
               self.widgets[key] = sc
               self.vars[key] = var
            row += 1
      # restart note
      Label(self.win, text="All settings require restarting rigdio to take effect",
            fg="grey").grid(row=row, column=0, columnspan=3, sticky=W,
               padx=10, pady=(5,0))
      row += 1
      # Save / Save & Restart / Cancel buttons
      btnFrame = Frame(self.win)
      btnFrame.grid(row=row, column=0, columnspan=3, pady=10)
      Button(btnFrame, text="Save", command=self.save,
         bg=self.colours["reset"]).pack(side=LEFT, padx=5)
      Button(btnFrame, text="Save and Restart", command=self.saveAndRestart,
         bg=self.colours["reset"]).pack(side=LEFT, padx=5)
      Button(btnFrame, text="Cancel", command=self.cancel).pack(side=LEFT, padx=5)

   def _collectValues(self):
      """Write all setting values from the widgets into the live config."""
      for section_name, items in SETTINGS_META:
         for key, label, typ, default, tooltip in items:
            newval = self.vars[key].get()
            settings.configs["config"][key] = newval

   def save(self):
      """Persist all settings to config.yml."""
      self._collectValues()
      saveConfig()
      print("Settings saved. Restart rigdio to apply changes.")
      self.win.destroy()

   def saveAndRestart(self):
      """Persist settings and restart rigdio immediately."""
      self._collectValues()
      saveConfig()
      print("Settings saved. Restarting rigdio...")
      # close the settings window and main window, then relaunch
      self.win.destroy()
      root = self.parent.winfo_toplevel()
      root.destroy()
      os.execv(sys.executable, [sys.executable] + sys.argv)

   def cancel(self):
      # restore original values (in case any were modified in the live config)
      settings.configs["config"] = dict(self.original)
      self.win.destroy()
