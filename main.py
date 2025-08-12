import time
import pygetwindow as gw

from core.execute import career_lobby

def focus_umamusume():
  windows = gw.getWindowsWithTitle("Umamusume")
  if not windows:
    raise Exception("Umamusume not found.")
  win = windows[0]
  if win.isMinimized:
    win.restore()
  win.activate()
  win.maximize()
  time.sleep(0.5)

def main():
  print("Uma Auto!")
  focus_umamusume()
  
  career_lobby()

if __name__ == "__main__":
  main()
