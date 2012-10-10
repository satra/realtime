import library as lib
import time

import cherrypy
from mako.template import Template
from mako.lookup import TemplateLookup
from mako import exceptions
import subprocess
import os
import time
#from library import makeSession, SUBJS, load_json, save_json, createSubDir
#from json_template import json

def btn_node(bid,j):
    """
    Helper designed for MakoRoot.formHandler().
    Returns a dict of button properties for the desired button.
    In: * bid (str), "x.y.z"
        * j (dict-like), MakoRoot.json
    Out: * node (dict-like), subnode of j, for that button
    """
    [v,s,p] = bid.split('.')
    return lib.get_node(j,['protocol',v,'steps',s,'parts',p])

def sib_node(bid,j,z):
    """
    Button groups consist of sibling buttons. Get sibling z for the
    button bid.
    Returns a dict of button properties for the desired sibling button.
    In: * bid (str), eg "x.y.z"
        * j (dict-like), MakoRoot.json
        * z (int/str), indicating which sibling to return
    Out: * node (dict-like), subnode of j, for the sibling button
    """
    [v,s,p] = bid.split('.')
    return lib.get_node(j,['protocol',v,'steps',s,'parts',z])


def timeStamp(node):  ## store time in epoch-secs + string
    tStamp = "%f"%time.time()  ## get time in seconds in the epoch
    timeReadable = time.strftime("%H:%M:%S--%m/%d/%Y",time.localtime(float(tStamp)))
    node['history'].append(tStamp)
    lib.set_here(node,'time',timeReadable)
    return  ### end timeStamp

def clearTimeStamp(node):
    lib.set_here(node,'time',"")
    return

def nameLogfile(node,subject,useInfo=None):
    """
    Out: absolute path where stdout/stderr logfile should go
    """
    # error check: useInfo has 'run','history'; node has 'action', 'id'
    if not useInfo:     ## allow us to (optionally) use a different btn's info
        useInfo=node    ## use this btn's info by default
    run = useInfo['run']
    timeStr = time.strftime("_%b%d_%H%M%S_",time.localtime(float(lib.get_node(useInfo,'history:-1'))))

    action = node['action']
    tab = int(lib.get_node(node,'id')[0])
    filename = str(run) + timeStr + action + '.log'
    return os.path.abspath(os.path.join(lib.SUBJS, subject, "session%d"%tab, filename))
    

def buttonReuse(node,newText):
    ## When a button has been pressed, (say to start something),
    ## rename it to the opposite function (say, to end the thing)
    if node.has_key('text'):
        node['text'] = newText
    else:
        print node
        raise KeyError("Can't reuse this button")
    return


"""
def getTimeStamp(prog):
        if isinstance(prog,int):  ## RT run, add runNum to json lookup for rt runs 
            index = self.json['rtLookup'] + (prog - 1)
        elif isinstance(prog,str):  ## not an RT run 
            index = self.json[prog]
        return self.json['Protocol'][self.TabID]['Steps'][index]['time']


    clearTimeStamp.exposed = True

    def makoCheckboxHandler(self,action,program,checked,progIndex):
        # checkboxes should be enabled one at a time.
        # checkboxes should have timestamps collected
        self.timeStamp(progIndex)
        ## toggle its status from unchecked to checked, etc...
        self.json['Protocol'][self.TabID]['Steps'][progIndex]['checked'] = not self.json['Protocol'][self.TabID]['Steps'][progIndex]['checked']
        ## disable once checked, enable next step if it's a checkbox
        if self.json['Protocol'][self.TabID]['Steps'][progIndex]['checked']:
            self.json['Protocol'][self.TabID]['Steps'][progIndex]['disabled'] = True
            if self.json['Protocol'][self.TabID]['Steps'][progIndex+1]['text'][0:7] == action:
                self.json['Protocol'][self.TabID]['Steps'][progIndex+1]['disabled'] = False
        return
    makoCheckboxHandler.exposed = True

    def formHandler(self,button):
        btnArgs = button.split(' ')
        [action, program] = btnArgs[0:2]  # minimum text on any UI element
        print "%s"%button
        if action == "Acquire":   ## this is a 'checkbox', has 4 args
            [checked,stepID] = [btnArgs[-2],int(btnArgs[-1])]
            self.makoCheckboxHandler(action,program,checked,stepID)  # also disable everything else!
        elif action == "Test":  ## this is a test, has 2 args
            self.timeStamp(self.json[program])
            ##
            ### handle cases of various tests here!
            ##
        elif action == "Complete":  # Visit or RTVisit
            ## forces another FORM submit, because i don't get javascript
            self.setSuiteState("RT Run",'disabled') ## disable Redo Run buttons; "RT Run" is the step name
            self.buttonReuse("%s -"%button)  
        elif action == "Launch":  ## Functional stimulus, 2 or 3 args
            if program == "RT":  # it's mTBI_rt
                self.run == int(btnArgs[2])
                pass # self.makoDoRT(), # also disable everything else!
            elif program[2:6] == "back":
                self.timeStamp(self.json[program])
                self.makoDoNBack(program) # also disable everything else!
        elif action == "Redo":    ## Run, Visit, or RTVisit
            if program == "Run":
                self.run == int(btnArgs[2])
                self.makoRedoRun()
            else:
                self.makoRedoVisit(program)
                self.buttonReuse("Redo %s -"%program) ### breaktimes!
        elif (len(btnArgs[-1]) == 1) and btnArgs[-1][0].isdigit():
            self.run == int(btnArgs[2])
            self.buttonReuse(button)  ### too much trouble
            if program == "Murfi":
                self.makoDoMurfi(action)
            elif program == "Serve":
                self.makoDoServe(action)
        else:
            print "\n Didn't recognize button %s\n"%button

        return self.renderAndSave()
    formHandler.exposed=True

    def setSuiteState(self,suite,state):
        ## GOAL: in this tab, enable/disable all steps of a certain suite.
        ## -- suites: "Test", "Acquire","Launch","[Re]Start" (action keywords)
        ## -- -- except "RT Run" to access Redo Run buttons
        ## -- uses human readable states ("disabled", "enabled","reset")
        tab = self.TabID
        stepNames = [st['text'] for st in self.json['Protocol'][tab]['Steps']]  ## get all step names
        for n,name in enumerate(stepNames):
            args = name.split(' ')  # [action, program] or ['RT','Run']
            if args[0] == suite: # does the step action match the suite name?
                print "trying to %s %s"%(state, name)
                self.setButtonState(name,state)
                # if (suite == "Test") and (state == disable):                    
            elif name == suite:   ## RT Run
                self.setButtonState("Redo Run %d"%(n+1-self.json['rtLookup']),state)  ## inverse of runIndex computations elsewhere
        return
    setSuiteState.exposed = True
        
    def completionChecks(self):
        tab = self.TabID
        lastVisit = self.json["rtVisits"]+1   # only +1 because 0-indexed
        ##### Enable tab only if prev visit complete AND this visit incomplete 
        ### BUG: final localizer's tests are stuck enabled!
        if tab > 0:            
            if self.json['Protocol'][tab-1]['complete'] and (not self.json['Protocol'][tab]['complete']): 
                ## BUG: unless we're in the middle of running something?
                self.setSuiteState('Test','enabled') ## activate tests on this tab
                self.setSuiteState('Acquire','enabled')
            else:
                self.setSuiteState('Test','disabled') ## deactivate tests on this tab?
                self.setSuiteState('Acquire','disabled')
        ##### Create lists of Tests and Functional Scans
        # -- Based on tab, we can handle funcloc and rt runs differently.
        # -- checkList: tests should be done before any anatomical / functional runs.
        # -- funcList: functional/task scans, in sequential order
        # -- funcRoot + visitType: strings to help us handle RT runs differently
        if (tab == 0) or (tab == lastVisit):  # funcloc
            checkList = ['Display','Buttons','Trigger','BirdSounds','LetterSounds']   ## need to add scans / get programatically?
            funcList = ['1-back-localizer','1-back-transfer','2-back-transfer']  ## autoget?
            funcRoot = ""
            visitType = ""
        elif (tab > 0) and (tab < lastVisit): # rt visit
            checkList = ['Display','Buttons','Trigger']   ## eventually need to add scan Runs // get programatically?
            funcList = range(1,(self.json["runsPerRtVisit"]+1))
            funcRoot = "Murfi "
            visitType = "RT"
        ####### Ensure all pre-tests in checkList are complete (have timestamps)
        # -- list comprehension to get length of timestamp
        # -- any 0-length timestamps are incomplete. using count(0) to find them.
        emptyStamps = [len(self.getTimeStamp(test)) for test in checkList].count(0)  
        if emptyStamps == 0:
            ####### Determine progress through functional scan list in funcList
            # -- now the count of 0-length timestamps tells us how many scans are left
            # -- use scansLeft as a negative index into funcList to get name of next scan
            # -- rt runs need "Murfi" added to the runNum to produce next scan name
            # -- enable button for next scan via the scan name we just produced
            scansLeft = [len(self.getTimeStamp(scan)) for scan in funcList].count(0)
            ## BUG: 0-length doesn't work after redos.... is that OK?
            if scansLeft == 0: ## visit complete!
                self.json['Protocol'][tab]['complete'] = True 
                self.setButtonState('Complete %sVisit'%visitType,'enabled')
                self.setSuiteState('Test','disabled')
            else:
                nextScan = funcRoot + str(funcList[-scansLeft])
                self.setButtonState('null %s'%nextScan,'enabled')
        return   ## end def completionChecks()
    completionChecks.exposed=True
    
    def makoDoNBack(self,program):
        self.setButtonState("Launch %s"%program,"disabled")
        return 
    makoDoNBack.exposed = True

    def makoDoMurfi(self,action):
        run = self.run
        if (action == "End"):
            ## call endMurfi
            ## attach RT run timestamp to End Murfi
            runIndex = self.json['rtLookup'] + (run - 1)  # run is 1-indexed, so subtract 1
            self.timeStamp(runIndex)
#            tStamp = time.ctime()
            # tStamp = "%f"%time.time()
            # self.json['Protocol'][self.TabID]['Steps'][runIndex]['time'] = tStamp
            # self.json['Protocol'][self.TabID]['Steps'][runIndex]['history'].append(tStamp)
            self.setButtonState("null Murfi %d"%run,"disabled")
            self.setButtonState("null Serve %d"%run,"disabled")
            self.setButtonState("null RT %d"%run,"disabled")
            self.setButtonState("Redo Run %d"%run,"enabled")
            if (run < self.json["runsPerRtVisit"]):
                self.setButtonState("null Murfi %d"%(run+1),"enabled")
        else:
            ## call doMurfi here
            self.setButtonState("null Serve %d"%run,"enabled")
            self.setButtonState("null RT %d"%run,"enabled")
        return
    makoDoMurfi.exposed = True

    def makoDoServe(self,action):
        run = self.run
        if (action == "End"):
            ## call endServe
            self.setButtonState("null Murfi %d"%run,"enabled")
        else:
            ## call doServe
            self.setButtonState("null Murfi %d"%run,"disabled")
            return
        makoDoServe.exposed = True

    def makoRedoRun(self):  ## disable the redo button + next action, enable relevant actions
        self.setButtonState("Redo Run %d"%self.run,"disabled")
        ### BUG: actually, all other Redos and all other starts should be disabled
        if self.run < self.json['runsPerRtVisit']:
        ### BUG: couldn't get this to work in an RT visit
            self.setButtonState("null Murfi %d"%(self.run+1),"disabled")                
        self.setButtonState("Restart Murfi %d"%self.run,"enabled")
        return
    makoRedoRun.exposed = True

    def makoRedoVisit(self,prog):  ## disable the redo button + next action, enable relevant actions
        self.setButtonState("Redo %s"%prog,"disabled")
        self.buttonReuse("Redo %s -"%prog)
        self.json['Protocol'][self.TabID]['complete'] = False
        self.setSuiteState('Test','reset')  ## reactivate tests on this tab
        self.setSuiteState('Acquire','reset')  ## reactivate structurals on this tab
        ### BUG: fails to reactivate functional scans
        return
    makoRedoVisit.exposed = True
    
    def setTab(self,tab):
        self.TabID = int(tab)
        if self.TabID > len(self.json['Protocol']):  ## visit must be defined in Protocol
            self.TabID = 0
        for (i,v) in enumerate(self.json['Protocol']):
            if i==self.TabID:
                v['active'] = True
            else:
                v['active'] = False
        return self.renderAndSave()
    setTab.exposed=True


def setButtonState(self,button,state):
    ## goal: changes the value of a button's disabled value in the json.
    ## -- allows the use of "disabled" or "enabled", rather than T/F
    ## -- "reset" is a state that means "enabled", and clears the timestamp to allow Redo
    if state == "disabled":
        stateBool = True
    elif (state == "enabled") or (state == "reset"):
        stateBool = False
    btnArgs = button.split(' ')  # button could have 2 or 3 arguments
    if len(btnArgs) == 2: 
        [act,prog] = btnArgs
        try:
            progIndex = self.json[prog]
        except:
            progIndex = prog
        if state == "reset":   ## only tests and funcloc scans can be reset
            self.clearTimeStamp(prog)
        self.json['Protocol'][self.TabID]['Steps'][self.json[prog]]['disabled'] = stateBool
    elif len(btnArgs) == 3:
        [act,prog,run] = btnArgs
        runIndex = self.json['rtLookup'] + (int(run) - 1)  # run is 1-indexed, so subtract 1
        self.json['Protocol'][self.TabID]['Steps'][runIndex]['Steps'][self.json[prog]]['disabled'] = stateBool
    return
setButtonState.exposed = True
"""