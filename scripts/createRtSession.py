##############################################
### createRtSession.py
### sasen@mit.edu   (created 2012-07-23 as cond_and_XML_gen.py)
###
### Workflow: Before using psychopy or murfi, run this script to
### auto-generate the directory + files needed for an RT session,
### including condition_files (for psychopy) and XML run config files
### (for murfi). The subject's main directory (including ROI localizer
### run, and input niftis (roi, background, and study_ref) must
### already exist.
###
### Currently set up for audio attention control neurofeedback
### experiments. Of the 6 runs, 1 and 6 are no-feedback.
import os, sys, csv, re, random
import numpy as np
import xml.etree.ElementTree as ET
import nibabel.nifti1 as nib

randomStimOrder = True  
############## condition file globals!
condFile_base = "mTBIconditions"
header_row_titles = ["arrow","image","q_or_r"]
up_arrow_img_filename = "images/up.jpg"
down_arrow_img_filename = "images/down.jpg"
qtext = ["Rate your ability to control your brain activation at this time.","Rate your ability to concentrate at this time.","Rate how much you relied on your strategy during this trial.","Rest"]
###############  XML file globals!
roiName = 'roi.nii'   ## this has to be in subjID/mask/
bgName = 'background.nii'  ## this has to be in subjID/mask/
studyrefName = 'study_ref.nii'  ## this has to be in subjID/xfm/
xmlInputName = "template.xml" ### must be in the same dir as this script.
xmlFile_base = "run"

## the 4 possible stimuli for this experiment.
## -- 1=up, 0=down
## -- the order will be permuted
## -- all 4 get used for FB. rows 1&2 are also noFB, runs 1&6 respectively
## -- question vectors are associated with stimulus vectors. 
stimuli = [[1,1,0,1,0,0],
           [0,1,1,0,0,1],
           [0,0,1,0,1,1],
           [1,0,0,1,1,0]]
questions = [[1,3,2,4,1,3],   # see question text above
             [2,1,3,4,2,4],
             [1,3,2,4,1,3],
             [2,1,3,4,2,4]]

########################## NO MORE USER-EDITABLE STUFF BELOW THIS POINT

########### DEFINE FUNCTIONS 
def matrixMaker(fb_run,stimulusVec,questionVec):
    # TRs= "        1 2 3 4 5 6 7 8 9101112131415161718192021222324"
    data = "        1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 0 0 0 0 0 0 0 0 0"
    null = "        0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"
    q123 = "        0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 1 0 0 0 0 0 0 0"
    #feedback runs (1 in varname means FB)
    fbk1 = "        0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0"
    # no feedback runs (0 in varname means noFB)
    fbk0 = "        0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"
    # rests for trials with questions
    rst1 = "        0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1"
    rst0 = "        0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1 1"
    # rests for trials where q4 = rest (_ in varname means q4=rest)
    rs_1 = "        0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 1 0 1 1 1 1 1 1"
    rs_0 = "        0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1 1 1 1"

    if fb_run:
        feedback = [fbk1,fbk1,fbk1,fbk1,fbk1,fbk1]
    else:  ## not a feedback run
        feedback = [fbk0,fbk0,fbk0,fbk0,fbk0,fbk0]

    dataup = []
    datadown = []
    rest = []
    q1 = []
    q2 = []
    q3 = []
    for (s,q) in zip(stimulusVec,questionVec):
        if s:
            dataup.append(data)
            datadown.append(null)
        else:
            dataup.append(null)
            datadown.append(data)

        if q == 4:
            q1.append(null)
            q2.append(null)
            q3.append(null)
            if fb_run:
                rest.append(rs_1)
            else:
                rest.append(rs_0)
        else:
            if fb_run:
                rest.append(rst1)
            else:
                rest.append(rst0)
                
            if q == 1:
                q1.append(q123)
                q2.append(null)
                q3.append(null)
            elif q == 2:
                q1.append(null)
                q2.append(q123)
                q3.append(null)
            elif q == 3:
                q1.append(null)
                q2.append(null)
                q3.append(q123)

    #### this dict depends on the condition names!!!
    dictofMats = {'data-up': "\n"+"\n".join(dataup)+"\n      ",
                  'data-down':"\n"+"\n".join(datadown)+"\n      ",
                  'q1': "\n"+"\n".join(q1)+"\n      ",
                  'q2': "\n"+"\n".join(q2)+"\n      ",
                  'q3': "\n"+"\n".join(q3)+"\n      ",
                  'feedback': "\n"+"\n".join(feedback)+"\n      ",
                  'rest': "\n"+"\n".join(rest)+"\n      "}
    return dictofMats


################## DONE WITH FUNCTIONS, MAIN BODY FOLLOWS

########## Step 0: Ensure valid inputs/setup (args, env vars, dir structure). 

## Step 0.1: Parsing arguments, generate usage error.
if len(sys.argv) != 5:
    print "Usage: python "+sys.argv[0]+" SUBJECTID SESSIONNUM GUI GROUP"
    print "   eg: python "+sys.argv[0]+" pilot17 2 none high"
    print "   GUI = none | oldgui"
    print " group = high or low"
    print "ERROR in " + sys.argv[0] + ": Incorrect number of arguments."
    sys.exit(1)
subjID = sys.argv[1]
sessNum = int(sys.argv[2])
gui = sys.argv[3]
group = sys.argv[4]

if gui == 'none':
    disableOldgui = True
elif gui == 'oldgui':
    disableOldgui = False
else:   # yeah, this should really be a usage function
    print "Usage: python "+sys.argv[0]+" SUBJECTID SESSIONNUM GUI"
    print "   eg: python "+sys.argv[0]+" pilot17 2 none"
    print "   GUI = none | oldgui"
    print "ERROR in " + sys.argv[0] + ": %s is not a valid GUI argument."%gui
    sys.exit(1)



## Step 0.1-1: Permute the stimulus rows (and corresponding question rows)
##  -- not sure why i put this here
##  -- for fakedata, don't randomize stimuli
##  -- session9 is also reserved for subject-tailored fakedata
if subjID == 'fakedata' or sessNum==9:
    randomStimOrder = False  ## fixed stimulus order for testing
if randomStimOrder:
    sq_zip = zip(stimuli,questions)
    random.shuffle(sq_zip)
    [stimPerm,questPerm] = zip(*sq_zip)
    stimuli = list(stimPerm)
    questions = list(questPerm)


## Step 0.2: Ensure valid directory structure + environment variables

## Step 0.2-1: Check environment variables
## -- murfi location (+ has it been built?)
murfiloc = os.environ['SOFTWAREDIR']+'bin/murfi'
if not os.path.exists(murfiloc):
    print "ERROR in sys.argv[0]: can't find murfi at %s"%murfiloc
    print "Check SOFTWAREDIR in your bash environment (~/.bashrc), or remake murfi."
    sys.exit(1)

## Step 0.2-2: Ensure we have a valid directory structure
## -- get subjects dir location from username
subjDir = "/home/%s/subjects/"%os.environ['USER'] + subjID + "/"
sessDir = subjDir + 'session%d/'%sessNum
condDir = sessDir + 'conditions/'
xmlDir = sessDir + 'scripts/'
roiFile = 'mask/'+ subjID + '_' + roiName
bgFile = 'mask/' + subjID + '_' + bgName
studyrefFile = 'xfm/' + subjID + '_' + studyrefName

## Step 0.2-2a: Ensure input niftis are in place
if  not os.path.isdir(subjDir):   
    print 'ERROR in sys.argv[0]: ' + subjDir + " does not exist!"
    exit(1)
elif not os.path.isfile(subjDir + roiFile):
    print 'ERROR in sys.argv[0]: ' + roiFile + " does not exist in " + subjDir
    exit(1)
elif not os.path.isfile(subjDir + bgFile):    
    print 'ERROR in sys.argv[0]: ' + bgFile + " does not exist in" + subjDir
    exit(1)
elif not os.path.isfile(subjDir + studyrefFile):    
    print 'ERROR in sys.argv[0]: '+studyrefFile+" does not exist in "+subjDir
    exit(1)

## Step 0.2-2b: Verify/create session dir w/ symlinks to relevant input niftis
if not os.path.isdir(sessDir):  # see if session dir needs to be made
    os.mkdir(sessDir)
if  not os.path.isdir(xmlDir):   # see if scripts dir needs to be made
    os.mkdir(xmlDir)
if not os.path.isdir(condDir):  # see if conditions dir needs to be made
    os.mkdir(condDir)
if not os.path.isfile(sessDir + studyrefFile):    
    if not os.path.isdir(sessDir+'xfm'):  # does xfm need to be created?
        os.mkdir(sessDir+'xfm')
    os.symlink(subjDir+studyrefFile,sessDir+studyrefFile)
if not os.path.isdir(sessDir+'mask'):  # does mask need to be created?
    os.mkdir(sessDir+'mask')
if not os.path.isfile(sessDir + roiFile):
    os.symlink(subjDir+roiFile,sessDir+roiFile)
if not os.path.isfile(sessDir + bgFile):
    os.symlink(subjDir+bgFile,sessDir+bgFile)


################### Step 1: Parse input murfi config XML file

## Step 1.1: open input file, add XML root, parse XML into etree
## i. currently cribbing off rtsmoking & the murfi example XML files.
## -- may eventually use a different input file
## ii. need root element because murfi doesn't like valid xml
## -- otherwise, we could've just use ET.parse(xmlInputName) !
## -- must strip root off during XML output creation 

inXMLfile = open(xmlInputName,'rb')
xmlStrings = inXMLfile.readlines()
inXMLfile.close()
xmlStrings.insert(1,'<root>\n')
xmlStrings.append('</root>\n')
inElement = ET.fromstringlist(xmlStrings)  # Element object
inET = ET.ElementTree(inElement)   # ElementTree object

## Step 1.2: Set murfi softwareDir + subjectsDir + subject/name
## -- (optional) use environment variables to set infoclient ports
inElement.find("study/option[@name='subjectsDir']").text = "../../"
inElement.find("study/option[@name='softwareDir']").text = os.environ['SOFTWAREDIR']
inElement.find("study/subject/option[@name='name']").text = subjID + "/session%d"%sessNum
inElement.find("study/xfm/option[@name='referenceVol']").text = studyrefFile

## Set infoclient/infoserver ports (for multiuser computers running murfi)
## NB: env vars don't have to be defined; template defaults are fine.
## Also, murfi has defaults for scanner + infoserver, though not for infoclient
if os.environ.has_key('SCANNERPORT'):
    inElement.find("scanner/option[@name='port']").text = os.environ['SCANNERPORT']
if os.environ.has_key('INFOSERVERPORT'):
    inElement.find("infoserver/option[@name='port']").text = os.environ['INFOSERVERPORT']
if os.environ.has_key('ICLOCALPORT'):
    inElement.find("infoclient/option[@name='localPort']").text = os.environ['ICLOCALPORT']
if os.environ.has_key('ICREMOTEPORT'):
    inElement.find("infoclient/option[@name='remotePort']").text = os.environ['ICREMOTEPORT']

## run displayless in texas
if disableOldgui:
    inElement.find("oldgui/option[@name='disabled']").text = 'true'

## Step 1.3: verify roi and background/roi maskfiles
## -- could do some more error checking here
## -- haven't error checked study_ref.nii
for elem in inElement.findall("processor/module[@name='mask-load']"):
    masktype = elem.find("option[@name='filename']").text.strip()
    # add the subject ID to the mask filename in the XML
    elem.find("option[@name='filename']").text = subjID + '_' + masktype
    mask = sessDir + 'mask/'+ subjID + '_'+ masktype + '.nii'
    # verify that it points to the right place
    if elem.find("option[@name='roiID']").text.strip() == 'active':
        if not os.path.samefile(sessDir+roiFile , mask):
            print "ERROR in sys.argv[0]: roi name disagreement!"
            print mask + " vs. " + sessDir + roiFile
            exit(1)    
    elif elem.find("option[@name='roiID']").text.strip() == 'reference':
        if not os.path.samefile(sessDir+bgFile , mask):
            print "ERROR in sys.argv[0]: background name disagreement!"
            print mask + " vs. " + sessDir + bgFile
            exit(1)    

    # verify it's the right data type
    mask_dtype = nib.Nifti1Image.load(mask).get_data_dtype()
    if  mask_dtype == "int16":   ## murfi needs datatype=short, AKA int16
        print "Found valid int16 nifti mask:" + mask
    else:
        print "ERROR in sys.argv[0]: mask data type is " + str(mask_dtype) + ", should be int16!"
        exit(1)

    if not os.path.isfile(mask):   ## verify that the file exists
        # replace with nifti files above... maybe this should be an error.
        if elem.find("option[@name='roiID']").text.strip() == 'active':
            elem.find("option[@name='filename']").text = roiName
            print "Warning in sys.argv[0]: no mask file " + mask + ", replaced with " + roiFile
        elif elem.find("option[@name='roiID']").text.strip() == 'reference':
            elem.find("option[@name='filename']").text = bgName
            print "Warning in sys.argv[0]: no mask file " + mask + ", replaced with " + bgFile

        
## Step 1.4: make sure all conditions have been created 
## -- i know, this should have better logic
## -- also, condition creation should be a function. but not today.
designNode = inElement.find("processor/module/design")  # this is the parent element
if not designNode.find("option[@conditionName='q2']"):
    q1Elem = designNode.find("option[@conditionName='q1']")
    q2Elem = ET.Element.copy(q1Elem)
    q2Elem.set('conditionName','q2')
    designNode.append(q2Elem)
if not designNode.find("option[@conditionName='q3']"):
    q1Elem = designNode.find("option[@conditionName='q1']")
    q3Elem = ET.Element.copy(q1Elem)
    q3Elem.set('conditionName','q3')
    designNode.append(q3Elem)

condNames = [c.get('conditionName') for c in designNode.findall("option[@conditionName]")]   # complete list of condition name keys

## Step 1.??? TODO
## i. let scanner/option->name=port be settable
## ii. let scanner/option->name=tr be settable
## iii.  ... and name=measurements (# seconds)
## iv.  ... and all the resolution & voxel dimensions 
## v. maybe set infoclient port/host parameters too?

#################### end Step 1


numRuns=6
for r in range(0,numRuns):    # r is a run
    ## check for feedback
    if r in [0,numRuns-1]:
        fb_run = 0   ## first or last is NOT a feedback run
    else:
        if group == "high":
            fb_run = 1   ## feedback run
        elif group == "low":
            fb_run = 0
        else:
            raise Exception("feedback run not defined. Is group correct?")

    ###  runNum = r  # zero-indexed
    runNum = r+1   # one-indexed
    # row lookup is (r mod 4) because rows 1 & 2 are repeated in runs 5 & 6
    # ERRR all my comments have one-indexed row #s. sorry.
    stimulusVec = stimuli[r%4]
    questionVec = questions[r%4]

    ############## Step 2: Generate psychopy CSV condition files
    csvOutfile = condDir + condFile_base + '%d.csv'%runNum
    with open(csvOutfile, 'wb') as csv_fileh:
        csvFileWriter = csv.writer(csv_fileh)
        csvFileWriter.writerow(header_row_titles)
        
        for i in range(len(stimulusVec)):   # i is an up/down trial
            if stimulusVec[i]:
                dirtext = 'up'
                img = up_arrow_img_filename
            else:
                dirtext = 'down'
                img = down_arrow_img_filename
            ## </if stimulusVec>
            csvFileWriter.writerow([dirtext, img, qtext[questionVec[i]-1]]) 
        ## </for>
        csv_fileh.close()  
        print "wrote out " + csvOutfile
    ## </with>    ################### end Step 2

    ############## Step 3: Generate output XML files
    ## do processing here!
    
    matrixDict = matrixMaker(fb_run,stimulusVec,questionVec)

    ## Step 3.2: put output matrices into inElement's condition nodes
    for cond in designNode.findall("option[@conditionName]"):
        cond.text = matrixDict[cond.get('conditionName')]
    
    ## Step 3.3: Writing the output
    ## -- ok, inElement now contains the right stuff for this run.
    ## -- but wait, we need to remove root elements!!!!
    outXMLstr = ET.tostring(inElement)
    (outStr,num) = re.subn("</?root>","",outXMLstr)
    ## finally, dump that string to the output file
    outXMLfile = xmlDir + xmlFile_base + '%d.xml'%(r+1)
    with open(outXMLfile,'wb') as out_fileh:
        out_fileh.write(outStr)
        out_fileh.close()
        print "wrote out " + outXMLfile

    ## Step 3.4: Create debug xml (with shorter tr)
    ## -- same process as above
    ## -- put this in an 'if debug:' block?
    inElement.find("scanner/option[@name='tr']").text = str(0.5)
    debugXMLstr = ET.tostring(inElement)
    (debugStr,num) = re.subn("</?root>","",debugXMLstr)
    debugXMLfile = xmlDir + xmlFile_base + 'Debug%d.xml'%(r+1)
    with open(debugXMLfile,'wb') as db_fileh:
        db_fileh.write(debugStr)
        db_fileh.close()
        print "wrote out " + debugXMLfile
    ################### end Step 3
## print sq
## </for r> 




