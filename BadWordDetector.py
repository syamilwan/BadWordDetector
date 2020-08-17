from __future__ import unicode_literals
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import *
import youtube_dl
import subprocess
#from selenium import webdriver
#import multiprocessing as mp
import threading as th
import time
import speech_recognition as sr
from pywinauto import Application
from pywinauto.keyboard import send_keys
from os import path
import os
from PIL import Image
from pystray import MenuItem as item
import pystray
from functools import partial


## Global Flags

app = Application(backend='uia')
app.connect(title_re=".*Chrome.*", top_level_only=True)
dlg = app.top_window()
element_name="Address and search bar"

win = tk.Tk()
win.title("Bad Word Detector")
win.geometry("350x170")
running = False
Llink = tk.StringVar()
LStatus = tk.StringVar()
LStatus.set("Inactive")
count = 0

## Items Definitions

with open ("bad-words.dat", "r") as myfile:     ## Load bad words
    data=myfile.read().split('\n')

with open ("bad-words2.dat", "r") as myfile:     ## Load ok words
    data2=myfile.read().split('\n')

def GetURL():
    return dlg.child_window(title=element_name, control_type="Edit").get_value()

link = None

def ChkConnection():
    if (GetURL() == None):
        print("Chrome is not Detected")
        LStatus.set("Inactive")
        return False
    else:
        print("Connected")
        LStatus.set("Activated")
        return True

def Run():      ## recursively capture browser's current link and download if its a youtube video link
    global count
    global link
    
    if (running == True and link != GetURL()):
        print(GetURL())
        Llink.set(GetURL())
        
        with open ("checked.dat", "r") as myfile2:      ## Load/Update checked videos
            checked=myfile2.read().split('\n')
        with open ("warn.dat", "r") as myfile3:      ## Load/Update blocked videos
            warned=myfile3.read().split('\n')  
        with open ("blocked.dat", "r") as myfile3:      ## Load/Update blocked videos
            blocked=myfile3.read().split('\n')  
        
        link = GetURL()
        if (link[:19] == "youtube.com/watch?v") :
            chk = False
            wrn = False
            blk = False
            for y in blocked:       ## Checking for if video is blocked
                if link == y:
                    print("#### Video is BLOCKED, redirecting...")
                    blk = True
                    time.sleep(1)
                    dlg.child_window(title=element_name, control_type="Edit").set_text("youtube.com")
                    send_keys("{ENTER}")
                    messagebox.showerror("Error", "Video is BLOCKED")
                    break
            if blk == False:
                for y in warned:       ## Checking if video is warned (only if not blocked)
                    if link == y:
                        print(" ## WARNING, contents may not be safe")
                        messagebox.showwarning("Warning","Video MAY contain UNSAFE contents")
                        wrn = True
                        break
            if blk == False and wrn == False:
                for y in checked:       ## Checking if video is already checked (only if not blocked)
                    if link == y:
                        print("#### Video was already Checked")
                        chk = True
                        break
            if chk == False and blk == False and wrn == False:
                count += 1
                SRth = th.Thread(target=runDL, args=(link, count,) )
                SRth.start()

        if (link == GetURL()):
            if (link[:19] == "youtube.com/watch?v") :
                for y in blocked:       ## Checking for if video is blocked (to keep checking blocked url)
                    if link == y:
                        print("#### Video is BLOCKED, redirecting...")
                        blk = True
                        time.sleep(1)
                        dlg.child_window(title=element_name, control_type="Edit").set_text("youtube.com")
                        send_keys("{ENTER}")
                        messagebox.showerror("Error", "Video is BLOCKED")
                        break
            pass
    
    win.after(200, Run)       ## recursive loop

os.system("youtube-dl --rm-cache-dir")          ## clear cache to avoid errors

class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)

def my_hook(d):
    global count
    if d['status'] == 'finished':
        print('## ' + str(count) + ' ## Done downloading, now converting ...')

ydl_opts = {        ## youtube-dl options
    'format': 'bestaudio/best',
    'outtmpl': '%(title)s.%(ext)s',
    'ignoreerrors': 'true',
    'restrictfilenames':True,
    'forcefilename':True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'flac',
        'preferredquality': '140',
    }],
    'logger': MyLogger(),
    'progress_hooks': [my_hook], }

def Start():    ## start scanning for youtube streaming on Chrome browser
    global running
    chkconn = ChkConnection()
    if (chkconn == False):
        print("Unable to Start")
        pass
    else:
        if running == True:
            pass
        else:
            running = True
            print("Scan Running")
            Llink.set(link)
            LStatus.set("Active")            
            bEdit["state"] = "disabled"
            dlg.child_window(title=element_name, control_type="Edit").set_text(GetURL())
            send_keys("{ENTER}")
            Run()

def Stop():     ## stop the scanning process
    global running
    if running == False:
        pass
    else:
        running = False
        print("Scan Halted")
        LStatus.set("Inactive")
        Llink.set(" ")
        bEdit["state"] = "normal"

def compare(trntext2, count3, link3):         ## loop of comparing strings. also saves video links to respective files
    trntext2 = trntext2.split(' ') 
    z = 1   # variable 'z' used as indicator of profanity seriousness in the video, 1 - safe, 2 - warning, 3 - block
    for x in trntext2:         # words from the video
        for y in data:         # from badwords.dat
            if x == y:         # immediately stop running if any word is found
                z = 3
                print("## " + str(count3) + " ## Badword: " + y + " Type: "  + str(z))
                break
        if z == 3:
            break
        else:
            for y in data2:        # from badwords2.dat
                if x == y:         # will not run if type 3 is found
                    z = 2
                    print("## " + str(count3) + " ## Badword: " + y + " Type: "  + str(z))

    if z == 1:          ## displaying resulting status of the video content
        print("## " + str(count3) + " ## Contents are SAFE")
    elif z == 2:
        print("## " + str(count3) + " ## WARNING, contents may not be safe")
        messagebox.showwarning("Warning","Video MAY contain UNSAFE contents")
        with open ("warn.dat", "a") as myfile3:          ## Append the new blocked video
            myfile3.writelines(link3 + "\n")
    elif z == 3:
        print("## " + str(count3) + " ## Video will be BLOCKED")
        with open ("blocked.dat", "a") as myfile3:          ## Append the new blocked video
            myfile3.writelines(link3 + "\n")
        print("## " + str(count3) + " ## Redirecting to homepage..")
        time.sleep(1)
        link3 = dlg.child_window(title=element_name, control_type="Edit").set_text("youtube.com")
        send_keys("{ENTER}")
        messagebox.showerror("Error", "Video is BLOCKED")

def runDL(link2, count2):         ## process youtube-dl download audio and extract to flac. also save video link to checked.dat
    print('## ' + str(count2) + ' ## ' + link2)

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link2, download=True)           ## capture video's informations
        filename = ydl.prepare_filename(info)
        print('## ' + str(count2) + ' ## Channel ' +info['uploader'])               
        print('## ' + str(count2) + ' ## Channel ID ' +info['uploader_id'])         
        if (filename[-4:] == 'webm') : 
            filename = filename.replace('webm', 'flac')
        else :
            filename = filename.replace('m4a', 'flac')          ## prepare file to audio format ; '.flac' for transcribe

    AUDIO_FILE = path.join(path.dirname(path.realpath(__file__)), filename)
    r = sr.Recognizer()
    #framerate = .1
    print('## ' + str(count2) + ' ## Reading audio..')
    with sr.AudioFile(AUDIO_FILE) as source:        ## read audio
        audio = r.record(source)

    print('## ' + str(count2) + ' ## Transcribing..')
    trntext = r.recognize_sphinx(audio)         ## start trasncribe process
    os.remove(filename)                         ## remove file after done
                                                                
    print('## ' + str(count2) + ' ## ' + trntext)
    compare(trntext,count2,link2)         ## starts scanning word by word

    with open ("checked.dat", "a") as myfile2:      ## Append the new checked video
        myfile2.writelines(link2 + "\n")


##############################################################################################################################################
###############################################                   GUI Zone                   #################################################

def PASS_WORD():
    with open ("password.dat", "r") as myfile:     ## Load bad words
        tempPass=myfile.read()
    
    def withdraw_window2():  # move to tray
        tkWindow.withdraw()
        image = Image.open("image.ico")
        menu = (item('Show', show_window), item('Quit', quit_window))
        icon = pystray.Icon("name", image, "Bad Word Detector", menu)
        icon.run()

    def validateLogin():
        if (tempPass == password.get()):
            tkWindow.withdraw()
            win.deiconify()
        else:
            pass

    #window
    tkWindow = tk.Toplevel()
    #tkWindow.geometry('400x150')  
    tkWindow.title('Authorization')

    #password label and password entry box
    passwordLabel = Label(tkWindow,text="Enter Password: ")
    password = StringVar()
    passwordEntry = Entry(tkWindow, textvariable=password, show='*')
    #validateLogin = partial(validateLogin, password)

    #login button
    loginButton = Button(tkWindow, text="Login", command=validateLogin)  

    passwordLabel.grid(row=0, column=0)
    passwordEntry.grid(row=1, column=0)
    loginButton.grid(row=2, column=0)
    tkWindow.protocol('WM_DELETE_WINDOW', withdraw_window2) 

def MenuM():     # Edit menu list
    win.withdraw() # hides main window
    
    def open1():    # Edit window for manually adding or removes blocked videos *blocked.dat
        Mtk.withdraw() # hides main window
        
        def delete1():
            sel = list1.curselection()
            # added reversed here so index deletion work for multiple selections.
            for index in reversed(sel):
                list1.delete(index)
            
            savelist = list1.get(0, tk.END)
            with open ("blocked.dat", "w") as myfile2:     
                for i in savelist:
                    myfile2.writelines( i + "\n") 

        def cancel1():
            n1.destroy()
            Mtk.deiconify()
        
        def add1():
            def close2():
                n2.destroy()
            def input2():
                cont = True
                temp = str(eInput.get())
                if (temp[:12] == "https://www."):
                    temp = temp[12:]
                
                with open ("blocked.dat", "r") as myfile2:     
                    for i in myfile2:
                        i = i.replace("\n","")
                        if (temp == i):
                            print("Existed link")
                            cont = False

                if cont == True and (temp[:19] != "youtube.com/watch?v") :
                    print("Wrong input! Must start with youtube.com/watch?v")
                elif cont == True:
                    with open ("blocked.dat", "a") as myfile2:     
                        myfile2.writelines( temp + "\n")
                        list1.insert(tk.END, temp)
                        eInput.delete(0,tk.END)
                
            n2 = tk.Toplevel()
            n2.title("Add New")
            lInput = ttk.Label(n2, text="Input : ")
            eInput = ttk.Entry(n2)
            bAdd = ttk.Button(n2, text="Add", command= input2)
            bClose = ttk.Button(n2, text="Close", command= close2)

            lInput.grid(row=0,column=0)
            eInput.grid(row=0,column=1)
            bAdd.grid(row=0,column=2)
            bClose.grid(row=0,column=3)

        ## Preload data
        with open ("blocked.dat", "r") as myfile3:      ## Load blocked videos
            blck1=myfile3.read().split('\n') 
        
        ## Labels
        n1 = tk.Toplevel()
        n1.title("Blocked videos")

        ## List Boxes
        list1 = tk.Listbox(n1, width=50)

        for i in blck1:     # insert all data from "blocked.dat" into text box
            if (i == ""):
                pass
            else:
                list1.insert(tk.END, i)
        
        ## Button
        bDelete = ttk.Button(n1, text="Delete", command= delete1)
        bAdd = ttk.Button(n1, text="Add", command= add1)
        bCancel = ttk.Button(n1, text="Close", command= cancel1)

        ## Display
        list1.grid(column=1, row=0)
        bDelete.grid(column=2,row=0)
        bAdd.grid(column=3,row=0)
        bCancel.grid(column=5,row=0)
        n1.protocol('WM_DELETE_WINDOW', cancel1)

    def open2():    # Same as open1() but for *warn.dat
        Mtk.withdraw() # hides Menu window
        
        def cancel1():
            n1.destroy()
            Mtk.deiconify()

        def delete1():
            sel = list1.curselection()
            # added reversed here so index deletion work for multiple selections.
            for index in reversed(sel):
                list1.delete(index)
            
            savelist = list1.get(0, tk.END)
            with open ("warn.dat", "w") as myfile2:     
                for i in savelist:
                    myfile2.writelines( i + "\n") 
        
        def add1():
            def close2():
                n2.destroy()
            def input2():
                cont = True
                temp = str(eInput.get())
                if (temp[:12] == "https://www."):
                    temp = temp[12:]
                
                with open ("warn.dat", "r") as myfile2:     
                    for i in myfile2:
                        i = i.replace("\n","")
                        if (temp == i):
                            print("Existed link")
                            cont = False

                if cont == True and (temp[:19] != "youtube.com/watch?v") :
                    print("Wrong input! Must start with youtube.com/watch?v")
                elif cont == True:
                    with open ("warn.dat", "a") as myfile2:     
                        myfile2.writelines( temp + "\n")
                        list1.insert(tk.END, temp)
                eInput.delete(0,tk.END)
                
            n2 = tk.Toplevel()
            n2.title("Add New")
            lInput = ttk.Label(n2, text="Input : ")
            eInput = ttk.Entry(n2)
            bAdd = ttk.Button(n2, text="Add", command= input2)
            bClose = ttk.Button(n2, text="Close", command= close2)

            lInput.grid(row=0,column=0)
            eInput.grid(row=0,column=1)
            bAdd.grid(row=0,column=2)
            bClose.grid(row=0,column=3)

        ## Preload data
        with open ("warn.dat", "r") as myfile3:      ## Load blocked videos
            blck1=myfile3.read().split('\n') 
        
        ## Labels
        n1 = tk.Toplevel()
        n1.title("Warned videos")

        ## List Boxes
        list1 = tk.Listbox(n1, width=50)

        for i in blck1:     # insert all data from "blocked.dat" into text box
            if (i == ""):
                pass
            else:
                list1.insert(tk.END, i)
        
        ## Button
        bDelete = ttk.Button(n1, text="Delete", command= delete1)
        bAdd = ttk.Button(n1, text="Add", command= add1)
        bCancel = ttk.Button(n1, text="Close", command= cancel1)

        ## Display
        list1.grid(column=1, row=0)
        bDelete.grid(column=2,row=0)
        bAdd.grid(column=3,row=0)
        bCancel.grid(column=5,row=0)
        n1.protocol('WM_DELETE_WINDOW', cancel1)

    def openWords():    # to customize profanities included to block the video *bad-words.dat and *bad-words2.dat
        Mtk.withdraw()  # hides main window
        
        ## Preload data
        with open ("bad-words.dat", "r") as myfile3:      
            words1=myfile3.read().split('\n') 
        with open ("bad-words2.dat", "r") as myfile4:      
            words2=myfile4.read().split('\n') 

        def cancel1():
            n1.destroy()
            Mtk.deiconify()

        def moveright():
            tempR = ""
            selR = ""
            selR = list1.curselection()
            tempR = list1.get(selR)
            
            #for indexR in reversed(selR):
            words1.remove(tempR)
            list1.delete(selR)

            words2.append(tempR)
            words2.sort()
            
            list2.delete(0,tk.END)
            for i in words2:     # insert all data from "bad-words.dat" into text box
                if (i == ""):
                    pass
                else:
                    list2.insert(tk.END, i)
            
            with open ("bad-words2.dat", "w") as myfile2:
                for i in words2:
                    if (i == "" or i == "\n"):
                        pass
                    else:
                        myfile2.writelines( i + "\n")
            
            #savelistR = list1.get(0, tk.END)
            with open ("bad-words.dat", "w") as myfile2:     
                for i in words1:
                    if (i == "" or i == "\n"):
                        pass
                    else:
                        myfile2.writelines( i + "\n")
                        
        def moveleft():
            tempL = ""
            selL = ""
            selL = list2.curselection()
            tempL = list2.get(selL)
            
            #for indexL in reversed(selL):
            words2.remove(tempL)
            list2.delete(selL)

            words1.append(tempL)
            words1.sort()

            list1.delete(0,tk.END)
            for i in words1:     # insert all data from "bad-words.dat" into text box
                if (i == ""):
                    pass
                else:
                    list1.insert(tk.END, i)
            
            with open ("bad-words.dat", "w") as myfile2:
                for i in words1:
                    if (i == "" or i == "\n"):
                        pass
                    else:
                        myfile2.writelines( i + "\n")
            
            #savelistL = list2.get(0, tk.END)
            with open ("bad-words2.dat", "w") as myfile2:     
                for i in words2:
                    if (i == "" or i == "\n"):
                        pass
                    else:
                        myfile2.writelines( i + "\n")
            
        def delete1():
            sel1 = list1.curselection()
            temp1 = list1.get(sel1)
            # added reversed here so index deletion work for multiple selections.
            #for index1 in reversed(sel1):
            words1.remove(temp1)
            list1.delete(sel1)

            savelist1 = list1.get(0, tk.END)
            with open ("bad-words.dat", "w") as myfile2:     
                for i in savelist1:
                    myfile2.writelines( i + "\n") 

        def add1():
            def close2():
                n2.destroy()
            def input2():
                cont = True
                temp1 = str(eInput.get())
                
                with open ("bad-words.dat", "r") as myfile2:     
                    for i in myfile2:
                        i = i.replace("\n","")
                        if (temp1 == i):
                            print("Existed")
                            cont = False
                
                if cont == True:
                    words1.append(temp1)
                    words1.sort()
                    list1.delete(0,tk.END)
                    for i in words1:
                        if (i == ""):
                            pass
                        else:
                            list1.insert(tk.END, i)
                            
                savelist1 = list1.get(0, tk.END)
                with open ("bad-words.dat", "w") as myfile2:     
                    for i in savelist1:
                        myfile2.writelines( i + "\n")

            n2 = tk.Toplevel()
            n2.title("Add New")
            lInput = ttk.Label(n2, text="Input : ")
            eInput = ttk.Entry(n2)
            bAdd = ttk.Button(n2, text="Add", command= input2)
            bClose = ttk.Button(n2, text="Close", command= close2)

            lInput.grid(row=0,column=0)
            eInput.grid(row=0,column=1)
            bAdd.grid(row=0,column=2)
            bClose.grid(row=0,column=3)
        
        def delete2():
            sel2 = list2.curselection()
            temp2 = list2.get(sel2)
            # added reversed here so index deletion work for multiple selections.
            #for index2 in reversed(sel2):
            words2.remove(temp2)
            list2.delete(sel2)
                        
            savelist2 = list2.get(0, tk.END)
            with open ("bad-words2.dat", "w") as myfile2:     
                for i in savelist2:
                    myfile2.writelines( i + "\n") 

        def add2():
            def close3():
                n2.destroy()
            def input3():
                cont = True
                temp2 = str(eInput.get())
                
                with open ("bad-words2.dat", "r") as myfile2:     
                    for i in myfile2:
                        i = i.replace("\n","")
                        if (temp2 == i):
                            print("Existed")
                            cont = False
                
                if cont == True:
                    words2.append(temp2)
                    words2.sort()
                    list2.delete(0,tk.END)
                    for i in words2:
                        if (i == ""):
                            pass
                        else:
                            list2.insert(tk.END, i)
                            
                savelist2 = list2.get(0, tk.END)
                with open ("bad-words2.dat", "w") as myfile2:     
                    for i in savelist2:
                        myfile2.writelines( i + "\n")
            
            n2 = tk.Toplevel()
            n2.title("Add New")
            lInput = ttk.Label(n2, text="Input : ")
            eInput = ttk.Entry(n2)
            bAdd = ttk.Button(n2, text="Add", command= input3)
            bClose = ttk.Button(n2, text="Close", command= close3)

            lInput.grid(row=0,column=0)
            eInput.grid(row=0,column=1)
            bAdd.grid(row=0,column=2)
            bClose.grid(row=0,column=3)

    # GUI Profanities
        n1 = tk.Toplevel()
        n1.title("Customize Profanities")

        ## Label
        label1 = tk.Label(n1, text="Bad Words")
        label2 = tk.Label(n1, text="Warn Words")

        ## List Boxes
        list1 = tk.Listbox(n1, width=50)
        list2 = tk.Listbox(n1, width=50)

        for i in words1:     # insert all data from "bad-words.dat" into text box
            if (i == ""):
                pass
            else:
                list1.insert(tk.END, i)

        for i in words2:     # insert all data from "bad-words2.dat" into text box
            if (i == ""):
                pass
            else:
                list2.insert(tk.END, i)


        ## Buttons
        bClose = ttk.Button(n1, text="Close", command= cancel1)
        bAdd1 = ttk.Button(n1, text="Add New", command= add1)
        bAdd2 = ttk.Button(n1, text="Add New", command= add2)
        bRight = ttk.Button(n1,text=">>", command=moveright)
        bLeft = ttk.Button(n1,text="<<", command=moveleft)
        bDelete1 = ttk.Button(n1,text="Delete", command=delete1)
        bDelete2 = ttk.Button(n1,text="Delete", command=delete2)

        ## Display grid
        label1.grid(row=0,column=1)
        label2.grid(row=0,column=3)

        list1.grid(row=1,column=1,rowspan = 2)
        list2.grid(row=1,column=3,rowspan = 2)

        bAdd1.grid(row=1,column=0)
        bDelete1.grid(row=2, column=0)
        bRight.grid(row=1,column=2)
        bLeft.grid(row=2,column=2)
        bAdd2.grid(row=1,column=4)
        bDelete2.grid(row=2, column=4)
        
        bClose.grid(row=3,column=2)

        n1.protocol('WM_DELETE_WINDOW', cancel1)

    def closeMenu():
        Mtk.destroy()
        win.deiconify()
    
    Mtk = tk.Toplevel()
    Mtk.title("Options")
    Mtk.geometry("350x120")
    frmMain2 = Frame(Mtk,bg="gray")
    #lMenu = ttk.Label(frmMain2, text="Options")
    bBlocked = ttk.Button(frmMain2, text="Blocked Videos", command= open1)
    bWarned = ttk.Button(frmMain2, text="Warned Videos", command= open2)
    bWords = ttk.Button(frmMain2, text="Profanities..", command= openWords)
    bClose = ttk.Button(frmMain2, text="Close", command= closeMenu)
    #bAllowed = ttk.Button(frmMain2, text="Allowed Videos")

    #lMenu.grid()
    bBlocked.grid()
    bWarned.grid()
    bWords.grid()
    bClose.grid()
        
    frmMain2.grid(row=0, column=0, sticky="NESW")
    frmMain2.grid_rowconfigure(0, weight=1)
    frmMain2.grid_columnconfigure(0, weight=1)
    Mtk.grid_rowconfigure(0, weight=1)
    Mtk.grid_columnconfigure(0, weight=1)
    Mtk.protocol('WM_DELETE_WINDOW', closeMenu)

def quit_window(icon, item):    # tray function to close program
    icon.stop()
    win.destroy()

def show_window(icon, item):    # tray function to show window
    icon.stop()
    win.after(0,PASS_WORD)

def withdraw_window():  # move to tray
    win.withdraw()
    image = Image.open("image.ico")
    menu = (item('Show', show_window), item('Quit', quit_window))
    icon = pystray.Icon("name", image, "Bad Word Detector", menu)
    icon.run()

##############################################################################################################################################
###############################################                  Main Window                 #################################################

withdraw_window()

## Frame
frmMain = Frame(win,bg="gray")

## Labels
lStatus = tk.Label(frmMain,textvariable=LStatus)
lLink = ttk.Label(frmMain,textvariable=Llink)

## Buttons
bStart = ttk.Button(frmMain,text="Start", command = Start)
bStop = ttk.Button(frmMain,text="Stop", command = Stop)
bEdit = ttk.Button(frmMain,text="Options", command = MenuM)
bTray = ttk.Button(frmMain,text="Hide to Tray", command= withdraw_window)

## Main Window
bStart.grid()
bStop.grid()
bEdit.grid()
bTray.grid()
lLink.grid()
lStatus.grid()

frmMain.grid(row=0, column=0, sticky="NESW")
frmMain.grid_rowconfigure(0, weight=1)
frmMain.grid_columnconfigure(0, weight=1)
win.grid_rowconfigure(0, weight=1)
win.grid_columnconfigure(0, weight=1)

# Main Loop
#win.protocol('WM_DELETE_WINDOW', withdraw_window)  ## if widnow closes, move to tray instead of closing program
win.mainloop()

###############################################                  Main Window                 #################################################
##############################################################################################################################################

###############################################                   GUI Zone                   #################################################
##############################################################################################################################################