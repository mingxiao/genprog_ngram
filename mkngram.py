import os
import glob
import shutil
import subprocess
import random
import re
from pprint import pprint
import operator
import threading
import signal
import matplotlib.pyplot as plt
import sys
import tarfile
import matplotlib.image as mpimg

class Command(object):
    def __init__(self, cmd):
        self.cmd = cmd
        self.process = None
        self.output = None
        self.retcode = None

    def run(self, timeout):
        def target():
            print 'Thread started'
            self.process = subprocess.Popen(self.cmd,stdout=subprocess.PIPE,shell=True,preexec_fn=os.setsid)
            self.output,self.err = self.process.communicate()
            self.retcode = self.process.returncode
            print 'Thread finished'

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            print 'Terminating process'
            os.killpg(self.process.pid, signal.SIGTERM)
            thread.join()
            print 'process terminated'
            

TOP='/home/saasbook/Documents/my-genprog-test'
USERS = '/home/saasbook/Documents/my-genprog-test/user'
CIL_SPEC= '/home/saasbook/Documents/cil-1.3.7'
CILLY = '/home/saasbook/Documents/cil-1.3.7/bin/cilly'
ANTLR = '/home/saasbook/Documents/antlr-3.4-complete-no-antlrv2.jar'
PARSE_CLASS = '/home/saasbook/workspace/cParser/bin'
REPAIR = '/home/saasbook/Documents/genprog-source-v2/src/repair' #path to repair binary
TEST = '/home/saasbook/Documents/my-genprog-test/tests' #Directory where all the tests are
TIME_OUT = 1 #abort if programs takes more than this many seconds
LIMIT = '/home/saasbook/Documents/my-genprog-test/limit'
#location of the function that limits the time a program can run. (default = 1s)
"""
The flow
1. Collect all programs into prog_name/raw/all
2. Separate into correct and buggy programs
3. apply cilly on the correct and buggy code and move them into ciled/correct and ciled/buggy
4. Process the files, by removing the comments and collecting them into processed/correct and processed/buggy
5. Then remove the #line directives and store files in hash_removed/correct and hash_removed/buggy
6. Once the lines added are copied from the VM, can we can compute the entropy of those added lines

"""

def create_folder(prog_name):
    """
    prog_name - name of the program (without the .c extension)
    Creates the file structure of our program (within the TOP directory)
    prog_name
        -repair
            -mutants
            -mutants_processed
            -lines_added
                -results
            -tests
            -real_bugs
        -ngram
        -hash_removed
            -correct
            -buggy
        -processed
            -correct
            -buggy
        -ciled
            -correct
            -buggy
        -raw
            -all
            -correct
            -buggy
            -correct_spaced
            -buggy_spaced
        -plots
    """
    assert len(prog_name) > 0
    os.chdir(TOP)
    print os.getcwd()
    if not os.path.isdir('./%s'%prog_name):
        os.mkdir(prog_name)
    # ngram directory ====
    if not os.path.isdir('./%s/ngram'%prog_name):
        os.mkdir(prog_name+'/ngram')
##    if not os.path.isdir(os.path.join('.',prog_name,'ngram','lines_added')):
##        os.mkdir(os.path.join('.',prog_name,'ngram','lines_added'))
##    if not os.path.isdir(os.path.join('.',prog_name,'ngram','lines_added','mutant')):
##        os.mkdir(os.path.join('.',prog_name,'ngram','lines_added','mutant'))
##    if not os.path.isdir(os.path.join('.',prog_name,'ngram','lines_added','correct')):
##        os.mkdir(os.path.join('.',prog_name,'ngram','lines_added','correct'))

    #====== hash_removed directory
    if not os.path.isdir(os.path.join(TOP,prog_name,'hash_removed')):
        os.mkdir(os.path.join(TOP,prog_name,'hash_removed'))
    if not os.path.isdir(os.path.join(TOP,prog_name,'hash_removed','correct')):
        os.mkdir(os.path.join(TOP,prog_name,'hash_removed','correct'))
    if not os.path.isdir(os.path.join(TOP,prog_name,'hash_removed','buggy')):
        os.mkdir(os.path.join(TOP,prog_name,'hash_removed','buggy'))
    
    #===== processed directory ====
    if not os.path.isdir('./%s/processed'%prog_name):
        os.mkdir(prog_name+'/processed')
    if not os.path.isdir('./%s/processed/correct'%prog_name):
        os.mkdir(prog_name+'/processed/correct')
    if not os.path.isdir('./%s/processed/buggy'%prog_name):
        os.mkdir(prog_name+'/processed/buggy')

    #==== ciled directory =====
    if not os.path.isdir('./%s/ciled'%prog_name):
        os.mkdir(prog_name+'/ciled')
    if not os.path.isdir('./%s/ciled/correct'%prog_name):
        os.mkdir(prog_name+'/ciled/correct')
    if not os.path.isdir('./%s/ciled/buggy'%prog_name):
        os.mkdir(prog_name+'/ciled/buggy')
        

    #===== raw directory ======
    if not os.path.isdir('./%s/raw'%prog_name):
        os.mkdir(prog_name+'/raw')
    if not os.path.isdir('./%s/raw/all'%prog_name):
        os.mkdir(prog_name+'/raw/all')
    if not os.path.isdir('./%s/raw/correct'%prog_name):
        os.mkdir(prog_name+'/raw/correct')
    if not os.path.isdir('./%s/raw/buggy'%prog_name):
        os.mkdir(prog_name+'/raw/buggy')
    if not os.path.isdir(os.path.join(TOP,prog_name,'raw','correct_spaced')):
        os.mkdir(os.path.join(TOP,prog_name,'raw','correct_spaced'))
    if not os.path.isdir(os.path.join(TOP,prog_name,'raw','buggy_spaced')):
        os.mkdir(os.path.join(TOP,prog_name,'raw','buggy_spaced'))

    # ==== repair directory ====
    if not os.path.isdir(os.path.join(TOP,prog_name,'repair')):
        os.mkdir(os.path.join(TOP,prog_name,'repair'))
    if not os.path.isdir(os.path.join(TOP,prog_name,'repair','mutants')):
        os.mkdir(os.path.join(TOP,prog_name,'repair','mutants'))
    if not os.path.isdir(os.path.join(TOP,prog_name,'repair','mutants_processed')):
        os.mkdir(os.path.join(TOP,prog_name,'repair','mutants_processed'))
    if not os.path.isdir(os.path.join(TOP,prog_name,'repair','real_bugs')):
        os.mkdir(os.path.join(TOP,prog_name,'repair','real_bugs'))
    if not os.path.isdir(os.path.join(TOP,prog_name,'repair','tests')):
        os.mkdir(os.path.join(TOP,prog_name,'repair','tests'))
    if not os.path.isdir(os.path.join(TOP,prog_name,'repair','lines_added')):
        os.mkdir(os.path.join(TOP,prog_name,'repair','lines_added'))
    if not os.path.isdir(os.path.join(TOP,prog_name,'repair','lines_added','results')):
        os.mkdir(os.path.join(TOP,prog_name,'repair','lines_added','results'))

    #=== plots ===
    if not os.path.isdir(os.path.join(TOP,prog_name,'plots')):
        os.mkdir(os.path.join(TOP,prog_name,'plots'))
        

def extract_program(prog_name,folder_num):
    """
    prog_name  - name of the program, with the .c extention
    folder_num  -  folder number or .git folder which the program resides in
    Goes to the USERS folder. Extracts all the prog_name programs from each student directory and puts
    them into the corresponding TOP/<prog_name>/raw/all folder. The program will be name <student_name>_<prog_name>
    """
    assert folder_num > 0
    assert len(prog_name) > 0
    assert prog_name.find('.') >= 0
    folder_name = os.path.splitext(prog_name)[0]
    #removes all previous files in TOP/<prog_name>/raw/all
    purge(os.path.join(TOP,folder_name,'raw','all'),r'.*')
    
    os.chdir(USERS)
    sdir = glob.glob('*') #glob ignores hidden files
    print os.getcwd()
    print len(sdir)
    # all student folders should have the /2 folder
    for student in sdir:
        os.chdir(os.path.join(USERS,student))
        #print os.getcwd()
        if os.path.isdir('./2'):
            os.chdir('./2')
            std_content = glob.glob('*')
            print os.getcwd()
            print std_content
            if str(folder_num) in std_content:
                print 'Folder %i found' %folder_num
                # go into the folder
                os.chdir('./%s' %folder_num)
                folder_content = glob.glob('*')
                if prog_name in folder_content:
                    print '%s found' %prog_name
                    #copy in TOP/<prog_name>/raw/all
                    shutil.copy(prog_name,'%s/%s/raw/all/%s_%s'%(TOP,folder_name,student,prog_name))
                else:
                    print '%s not found' %prog_name
            elif '%s.git'%folder_num in std_content:
                print 'Git %i found' %folder_num
                #clone the git repository
                ret = subprocess.call('git clone %s.git'%folder_num, shell = True)
                if ret == 0:
                    os.chdir('./%s'%folder_num)
                    folder_content = glob.glob('*')
                    if prog_name in folder_content:
                        print '%s found' %prog_name
                        #copy in TOP/<prog_name>/raw/all
                        shutil.copy(prog_name,os.path.join(TOP,folder_name,'raw','all','%s_%s'%(student,prog_name)))
                    else:
                        print '%s not found' %prog_name
                else:
                    print 'Failed to clone git repo %s.git'%folder_num
                    pass
            else:
                print 'Neither folder or git %s found' %folder_num
        else:
            print '%s is missing the 2 folder' % os.getcwd()

def compare(a, b):
    """Compare two basestrings compressing multiple consecutive spaces into a single space"""
    return re.sub("\s+", " ", a) == re.sub("\s+", " ", b)

def det_input_output(all_raw_dir,test_dir):
    """
    all_raw_dir - the directory where all the raw files are located
    test_dir - the directory of the associated test files

    Select a test from test_dir
    Run it against all the programs in all_raw_dir
    Select the most commmon output as the correct output for that test
    """ 
    answers = {}
    tests = glob.glob(os.path.join(test_dir,'*'))
    #print 'TESTS',tests
    #idx = random.randint(0,len(tests)-1)
    #test = tests[len(tests)-1]
    test = tests[0]
    #print test
    os.chdir(all_raw_dir)
    progs = glob.glob('*.c')
    progs.sort()
    #assert len(progs) > 30
    #print progs
    
    # get outputs from all programs and store them, and their count in answers dictionary
    for prog in progs:
        print 'PROG',prog
        # == generate the output
        cmd_compile = Command('gcc %s'%prog)
        cmd_compile.run(timeout=TIME_OUT)
        if cmd_compile.retcode == 0:
            #compile so gather output if it executes within TIME_OUT
            cmd_run = Command('./a.out < %s'%test)
            cmd_run.run(timeout=TIME_OUT)
            if cmd_run.retcode == 0:
                p = cmd_run.output
                print prog,p
            else:
                # command took too long, so skip to next program
                print '%s ran for too long' %prog
                continue
        else:
            #failed to compile so skip to the next one
            print '%s failed to compile'%prog
            continue
        # === compare output with previous outputs
        match = False
        for answer in answers.keys():
            if compare(answer,p):
                answers[answer] +=1
                match = True
        if not match:
            answers[p] = 1
    assert len(answers)>0
    print 'ans================'
    pprint(answers)
    print 'ans==============='
    #==========
    # take the most frequent answer and use that as the correct answer
    # copy the input and ouput into the prog/raw dir
    best_ans = max(answers.iteritems(), key=operator.itemgetter(1))[0]
    print 'BEST',best_ans,answers[best_ans]
    print os.path.dirname(all_raw_dir)
    shutil.copy(test,os.path.join(os.path.dirname(all_raw_dir),'input.txt'))
    fid = open(os.path.join(os.path.dirname(all_raw_dir),'output.txt'),'w')
    fid.write(re.sub("\s+", " ", best_ans)) #write out answer where spaces are compressed
    fid.close()
    
    

def test_program(raw_dir,inputfile,outputfile,prog_name):
    """
    raw_dir - the directory where all the original programs are ..../<progname>/raw/all
    inputfile - location of the input test file
    outputfile - location of the correct output file to compare against
    prog_name - name of the program, with the extension
    
    Goes to into the prog_name/raw/all folder and separates correct programs
    into /raw/correct and the buggy programs into /raw/buggy
    """
    #remove all programs in the previously in raw/buggy and rawy/correct
    purge(os.path.join(raw_dir,'buggy'),r'.*')
    purge(os.path.join(raw_dir,'correct'),r'.*')
    
    os.chdir(os.path.join(raw_dir,'all')) # move into the raw/all directory
    progs = glob.glob('*%s'%prog_name)
    #make sure its has some files, say more than 30
    #assert len(progs) > 30
    for prog in progs:
        #compile the program
        cmd_compile = Command('gcc %s'%prog)
        cmd_compile.run(timeout=TIME_OUT)
        print cmd_compile.retcode
        if cmd_compile.retcode == 0:
            cmd_run = Command("./a.out < %s |tr -s ' '|wdiff %s - "%(inputfile,outputfile)) #use tr to compress spaces
            cmd_run.run(timeout=TIME_OUT)
            if cmd_run.retcode == 0:
                print '%s moved to correct directory'%prog
                shutil.copy(prog,os.path.join(raw_dir,'correct'))
            else:
                print '%s ran for too long, or is incorrect. Move to buggy directory'%prog
                shutil.copy(prog,os.path.join(raw_dir,'buggy'))
        else:
            print '%s failed to compile, move to buggy directory'%prog
            shutil.copy(prog,os.path.join(raw_dir,'buggy'))

def cil_folder(src_folder, dest_folder,prog_name):
    """
    src_folder - the folder containing the programs to run cilly on
    dest_folder - the folder store all the .cil.c file
    prog_name - name of the program, with the extension
    (This is so that we do not cilly files that already have the .cil.c ending)
    
    Runs cilly on the prog_name/raw/buggy and /raw/correct and puts them in
    the /ciled/buggy and /ciled/correct folder.
    cilly --merge --keepmerged --save-temps FILENAME.c
    """
    print 'CILLY %s'%src_folder
    #remove all files previously in the dest_folder
    purge(dest_folder,r'.*')
    
    os.chdir(src_folder)
    progs = glob.glob('*%s'%prog_name)
    #assert len(progs) > 30
    #print progs
    for prog in progs:
        base_name = os.path.splitext(prog)[0]
        #print base_name
        subprocess.call('%s --merge --keepmerged --save-temps %s'%(CILLY,prog),shell=True)
        #sometimes cilly fails on the program, so check that .cil.c file exists
        if '%s.cil.c'%base_name in os.listdir(os.getcwd()):
            shutil.copy('%s.cil.c'%base_name,dest_folder)
        else:
            print '%s.cil.c does not exist'%base_name

def process_folder(src_folder, dest_folder):
    """
    Go through all the programs in the src_folder and
    1. remove comments
    2. puts a space between each token
    , and puts them in the dest_folder
    """
    print 'PROCESS %s'%src_folder
    #remove all files previously in dest_folder
    purge(dest_folder, r'.*')
    
    os.chdir(PARSE_CLASS)
    ret = subprocess.call('java -cp %s:%s ParseFiles %s %s'
                          %(ANTLR, PARSE_CLASS,src_folder, dest_folder),shell=True)
    print ret

def remove_hash(src_folder,dest_folder):
    """
    Go through all the C programs in src_folder and remove all the #line directives in each of them.
    Also removes blank lines
    Removing the #line directives does not seem to disallow compilations
    """
    print 'REMOVE HASH %s'%src_folder
    #remove all .c files previously in dest_folder
    purge(dest_folder, r'.*\.c')
    os.chdir(src_folder)

    progs = glob.glob('*.c')
    for prog in progs:
        subprocess.call("sed 's/^#line.*//' %s | sed '/^$/d'> %s"%(prog,os.path.join(dest_folder,prog)),shell=True)

def partition(prog_name,folder_num):
    """
    prog_name - name of the program (with or without the .c extension
    folder_num - the folder number which this program resides (ie. users/<name>/2/folder_num

    1. Create directory structure
    2. Extract the programs from the USERS directory
    3. Test the programs and separate into buggy/correct
    4. Run cilly on the buggy/correct programs
    5. Process the program (Remove whitespace)
    6. Remove the #line directives
    """
    #folder_name is the prog_name without the .c extension
    if prog_name.find('.') < 0:
        folder_name = prog_name
        prog_name = prog_name +'.c'
    else:
        folder_name = prog_name.split('.')[0]
    create_folder(folder_name)
    #extract
    extract_program(prog_name,folder_num)
    #test =====
    det_input_output(os.path.join(TOP,folder_name,'raw','all'),
                     os.path.join(TEST,'hw'+str(folder_num),folder_name+'.test'))
    #make sure the input/output files exist
    assert os.path.exists(os.path.join(TOP,folder_name,'raw','input.txt'))
    assert os.path.exists(os.path.join(TOP,folder_name,'raw','output.txt'))
    test_program(os.path.join(TOP,folder_name,'raw'),os.path.join(TOP,folder_name,'raw','input.txt'),
                 os.path.join(TOP,folder_name,'raw','output.txt'),prog_name)
    # space/remove comments in raw/correct and raw/buggy and output those
    # files to raw/correct_spaced, raw/buggy_spaced
    process_folder(os.path.join(TOP,folder_name,'raw','correct'),
               os.path.join(TOP,folder_name,'raw','correct_spaced'))
    process_folder(os.path.join(TOP,folder_name,'raw','buggy'),
               os.path.join(TOP,folder_name,'raw','buggy_spaced'))
    #======
    # === cilly the buggy and correct folders
    cil_folder(os.path.join(TOP,folder_name,'raw','buggy'), os.path.join(TOP,folder_name,'ciled','buggy'),prog_name)
    cil_folder(os.path.join(TOP,folder_name,'raw','correct'), os.path.join(TOP,folder_name,'ciled','correct'),prog_name)
    #=====
    # === remove comments from ciled programs
    assert os.path.exists(os.path.join(TOP,folder_name,'processed','buggy'))
    assert os.path.exists(os.path.join(TOP,folder_name,'processed','correct'))
    assert os.path.exists(os.path.join(TOP,folder_name,'ciled','buggy'))
    assert os.path.exists(os.path.join(TOP,folder_name,'ciled','buggy'))
    
    process_folder(os.path.join(TOP,folder_name,'ciled','buggy'),
                   os.path.join(TOP,folder_name,'processed','buggy'))
    process_folder(os.path.join(TOP,folder_name,'ciled','correct'),
                   os.path.join(TOP,folder_name,'processed','correct'))
    #=====
    #=== remove the #line directives
    assert os.path.exists(os.path.join(TOP,folder_name,'hash_removed','correct'))
    assert os.path.exists(os.path.join(TOP,folder_name,'hash_removed','buggy'))

    remove_hash(os.path.join(TOP,folder_name,'processed','correct'),
                os.path.join(TOP,folder_name,'hash_removed','correct'))
    remove_hash(os.path.join(TOP,folder_name,'processed','buggy'),
                os.path.join(TOP,folder_name,'hash_removed','buggy'))
    

def create_lm(corpus_folder, lm_folder,prog_name):
    """
    corpus_folder - location of the corpus (ie. /<prog name>/processed/correct
    lm_folder - desired location of the resulting language model (absolute file path)
    prog_name - name of the program (without the extension)

    Creates a language model from all the .c files from the corpus_folder, and puts them in the lm_folder
    """
    print 'CREATE LM %s'%corpus_folder
    #removes previous language model
    purge(lm_folder,r'.*')
    #gets rid of extension in prog_name, if there is an extension
    if prog_name.find('.') >= 0:
        prog_name = os.splitext(prog_name)[0]
    #=======
    # creates the corpus =====
    dest = open(os.path.join(lm_folder,prog_name+'.corpus'),'wb')
    for filename in glob.glob(os.path.join(corpus_folder,'*.c')):
        shutil.copyfileobj(open(filename, 'rb'), dest)
    dest.close()
    #=======
    # creates the intermediate files and .arpa file
    os.chdir(lm_folder)
    subprocess.call('cat %s.corpus | text2wfreq | wfreq2vocab -top 20000 > %s.vocab'
                    %(prog_name,prog_name),shell=True)
    subprocess.call('text2idngram -vocab %s.vocab -idngram %s.idngram < %s.corpus'
                    %(prog_name,prog_name,prog_name),shell= True)
    subprocess.call('idngram2lm -idngram %s.idngram -vocab %s.vocab -arpa %s.arpa'
                    %(prog_name,prog_name,prog_name),shell=True)
    # =======

def create_config(repair_folder, buggy_prog, pos_test, neg_test, overwrite = True):
    """
    repair_folder - absolute path of the repair folder
    buggy_prog - name of the buggy program (should already be in repair folder
    overwrite - whether we want to overwrite the old config file
    pos_test - number of positive test cases
    neg_test - number of negative test cases

    Creates the configuration file in repair_folder, if one does not already
    exist or we want to overwrite
    """
    print 'CREATE CONFIG %s'%repair_folder
    os.chdir(repair_folder)
    if 'configuration' in os.listdir('.') and not overwrite:
        #config file already exist and we do not want to overwrite
        print 'already exist'
        return
    fid = open('configuration','w')
    fid.write('--program %s\n'%buggy_prog)
    fid.write('--pos-tests %i\n'%pos_test)
    fid.write('--neg-tests %i\n'%neg_test)
    fid.write('--keep-source\n')
    fid.write('--no-rep-cache\n')
    fid.write('--search ga\n')
    fid.close()

def select_buggy(buggy_folder,repair_folder):
    """
    buggy_folder - absolute path of the folder of buggy programs
    repair_folder - absolute path of the repair folder

    Select a buggy program at random from the buggy_folder (prog/processed/buggy) and copies it to repair_folder.

    Returns the name of the selected buggy program
    """
    print 'SELECT BUGGY %s'%buggy_folder
    buggy_progs = os.listdir(buggy_folder)
    assert len(buggy_progs) > 0
    #print buggy_progs
    idx = random.randint(0,len(buggy_progs)-1)
    shutil.copy(os.path.join(buggy_folder,buggy_progs[idx]),repair_folder)
    return buggy_progs[idx]

def create_testcases(test_folder,repair_folder, correct_folder):
    """
    test_folder - absolute path of the test folder (ie. ../my-genprog-test/tests/hw4/gcd.test)
    repair_folder - absolute path of the repair folder
    correct_folder - path of the correct processed folder

    Go into the test_folder
    For each test get the output and copy them both into the repair/test directory

    If the test directory looks like:
    -test
        -1
        -2
        -3

    Then the repair folder should look like:
    -repair
        -tests
            -1_input.txt
            -2_input.txt
            -3_input.txt
            -1_output.txt
            -2_output.txt
            -3_output.txt
            cmd_compile = Command('gcc %s'%prog)
        cmd_compile.run(timeout=TIME_OUT)
        if cmd_compile.retcode == 0:
    """
    print 'CREATE TESTCASES %s'%test_folder
    testfiles = os.listdir(test_folder)
    correct_prog = os.listdir(correct_folder)[0] # use the first program in the correct program
    os.chdir(TOP)
    for test in testfiles:
        #compile the correct program
        cmd_compile = Command('gcc %s'%(os.path.join(correct_folder,correct_prog)))
        cmd_compile.run(timeout=TIME_OUT)
        if cmd_compile.retcode == 0:
            cmd_run = Command("./a.out <%s |tr -s ' '> %s"
                              %(os.path.join(test_folder,test),
                                os.path.join(repair_folder,'tests',test+'_output.txt')))
            cmd_run.run(timeout=TIME_OUT)
            if cmd_run.retcode == 0:
                shutil.copy(os.path.join(test_folder,test),
                            os.path.join(repair_folder,'tests',test+'_input.txt'))
            else:
                print 'ran for too long'

        else:
            print 'failed to compile'


def create_testscript(repair_folder,buggy_prog,overwrite = True):
    """
    repair_folder - absolute path of the repair folder
    buggy_prog - 
    overwrite - determines whether or not to overwrite the existing test.sh
    
    Create test.sh in repair_folder. The repair_folder/tests should be populated.
    """
    #assert len(os.listdir(os.path.join(repair_folder,'tests'))) > 0
    print 'CREATE TESTSCRIPT %s'%repair_folder
    if 'test.sh' in os.listdir(repair_folder) and not overwrite:
        print 'test.sh already exist and not overwriting'
        return
    os.chdir(repair_folder)
    assert buggy_prog in os.listdir(repair_folder)
    pos_counter = 0
    neg_counter = 0
    fid = open('test.sh','w')
    # write header ===
    fid.write('#!/bin/bash \n')
    fid.write('# $1 = EXE \n')
    fid.write('# $2 = test name \n')
    fid.write('# $3 = port \n')
    fid.write('# $4 = source name \n')
    fid.write('# $5 = single-fitness-file name \n')
    fid.write('# exit 0 = success \n')
    #===========

    #fid.write('ulimit -t 1 \n') #set the time limit to 1
    fid.write('echo $1 $2 $3 $4 $5 >> testruns.txt \n')
    fid.write('case $2 in \n')
    # determine cases =========
    inputs = glob.glob('./tests/*input.txt')
    outputs = glob.glob('./tests/*output.txt')
    inputs.sort()
    outputs.sort()
    assert len(inputs) == len(outputs)
    #print inputs, outputs
    # insert a dummy positive test case
    pos_counter += 1
    fid.write('\tp%i) exit 0;;\n'%pos_counter)
    #===
    subprocess.call('gcc %s'%buggy_prog,shell=True)
    for testin, testout in zip(inputs,outputs):
        #print testin,testout
        cmd = Command("%s ./a.out < %s | tr -s ' '| wdiff --ignore-case - %s"%(LIMIT,testin,testout))
        cmd.run(TIME_OUT)
        print cmd.output
        #ret = subprocess.call("%s ./a.out < %s | tr -s ' '| wdiff --ignore-case - %s"%(LIMIT,testin,testout),shell=True)
        if cmd.retcode == 0:
            #positive test case
            pos_counter += 1
            fid.write("\tp%i) %s $1 < %s | tr -s ' ' | wdiff --ignore-case - %s && exit 0;;\n"%(pos_counter,LIMIT,testin,testout))
        else:
            #negative test case
            neg_counter += 1
            fid.write("\tn%i) %s $1 < %s | tr -s ' '| wdiff --ignore-case - %s && exit 0;;\n"%(neg_counter,LIMIT,testin,testout))
    #=================
    fid.write('esac \n')
    fid.write('exit 1')
    fid.close()

    # make the testscript executable
    os.chmod(os.path.join(os.getcwd(),'test.sh'),0777)
    #===
    return pos_counter, neg_counter
    

def run_repair(repair_folder):
    """
    repair_folder - absolute path of the repair folder

    Runs the genprog repair program on the configuration file.
    """
    print 'RUN REPAIR %s'%repair_folder
    assert 'configuration' in os.listdir(repair_folder)
    assert 'test.sh' in os.listdir(repair_folder)
    os.chdir(repair_folder)
    # remove files that pertain to any previous runs of genprog
    # 000*, repair.*
    purge(repair_folder,r'[0-9]{6}.*')
    purge(repair_folder,r'repair.*')
    purge(repair_folder,r'coverage.*')
    purge(repair_folder,r'.*cache.*')
    #===
    subprocess.call('%s configuration' %REPAIR,shell=True)
    

def purge(directory, pattern):
    """
    Removes all files in directory that matches pattern
    """
    for f in os.listdir(directory):
    	if re.search(pattern, f):
    		os.remove(os.path.join(directory, f))

def separate_mutants(repair_folder):
    """
    repair_folder - path to the repair folder

    Moves all the mutants in the repair folder into the repair_folder/mutants folder
    The mutant files are of the form XXXXX.c where X in [0-9].
    We also move their binary as well.

    Move the repair folder as well
    """
    assert 'mutants' in os.listdir(repair_folder)
    print 'SEPARATE %s' %repair_folder
    # remove mutant file already in repair_folder/mutants, if any exist. Do not want to contaminate
    purge(os.path.join(repair_folder,'mutants'),r'.*')
    #===
    os.chdir(repair_folder)
    mutants = glob.glob('0*')
    for mutant in mutants:
        shutil.move(mutant,os.path.join(repair_folder,'mutants'))
    shutil.copy(os.path.join(repair_folder,'repair.c'),os.path.join(repair_folder,'mutants'))

def extract_lines_added(mutant_folder, lines_folder, original_prog):
    """
    mutant_folder - folder containing the mutants
    lines_folder - folder where to store the lines added per mutant
    original_prog - path to the original program
    For each mutant, compare against the original program, and extract the lines
    added.
    """
    print 'EXTRACT %s'%mutant_folder
    #removes all files previously in lines_folder
    purge(lines_folder,r'.*txt')
    
    os.chdir(mutant_folder)
    mutants = glob.glob('*.c')
    assert len(mutants) > 0
    for mutant in mutants:
        base=os.path.splitext(mutant)[0] #basename
        # extract the lines there were added
        # if you are in linux diff uses '+' to indicate lines added
        # whereas in mac diff uses '>'
        # To make it more confusing, when calling diff through subprocess, '>' is used
        # whereas if you call diff through terminal, '+' is used
        print mutant
        subprocess.call("diff --ignore-all-space %s %s |grep '^>\{1\}.*' |sed 's/^>//' > %s"
                        %(original_prog,
                          mutant,
                          os.path.join(lines_folder,
                                       base+'_lines_added.txt')
                          ),
                          shell=True)

def extract_correct_lines(repaired_prog, original_prog,dest_dir):
    """
    repaired_prog - the path to the repaired program
    original_prog - the path to the original buggy program
    dest_dir - path to the file where we store the lines added (../repair/lines_added/results/correct.txt)

    Extract the correct lines added by the repair program
    """
    base = os.path.splitext(original_prog)[0]
    subprocess.call("diff --ignore-all-space %s %s |grep '^>\{1\}.*' |sed 's/^>//' > %s"
                    %(original_prog,
                      repaired_prog,
                      os.path.join(dest_dir,base+'_lines_added.txt')),
                    shell=True)
    return dest_dir

def setup_repair(folder_name, hw_num,buggy_prog=''):
    """
    folder_name - name of the folder (the program name without the extension)
    hw_num - the homework number this assignment belongs to
    buggy_file - path to the buggy program (optional). If empty then call select_buggy
    
    Selects the buggy file, creates test cases, creates test.sh, create configuration file

    Returns the name of the buggy program selected, just the basename (not the path)
    """
    print 'SETUP REPAIR %s'%folder_name
    #remove previous *.c files
    purge(os.path.join(TOP,folder_name,'repair'),r'.*\.c')
    #select buggy file ====
    bug_dir = os.path.join(TOP,folder_name,'hash_removed','buggy')
    if buggy_prog == '':
        assert os.path.exists(bug_dir)
        assert os.path.exists(os.path.join(TOP,folder_name,'repair'))
        buggy_prog = select_buggy(bug_dir,
                                  os.path.join(TOP,folder_name,'repair'))
        print 'BUGGY', buggy_prog
    else:
        #print 'HEREE'
        #copies the buggy program into the repair folder
        assert os.path.exists(os.path.join(bug_dir,buggy_prog))
        shutil.copy(os.path.join(bug_dir,buggy_prog),os.path.join(TOP,folder_name,'repair'))
    #=====
    #create test cases ====
    assert os.path.exists(os.path.join(TEST,'hw'+str(hw_num),folder_name+'.test'))
    assert os.path.exists(os.path.join(TOP,folder_name,'repair'))
    assert os.path.exists(os.path.join(TOP,folder_name,'processed','correct'))
    create_testcases(os.path.join(TEST,'hw'+str(hw_num),folder_name+'.test'),
                 os.path.join(TOP,folder_name,'repair'),
                 os.path.join(TOP,folder_name,'processed','correct'))
    #====
    #create test script
    num_pos,num_neg = create_testscript(os.path.join(TOP,folder_name,'repair'),
                      os.path.basename(buggy_prog))
    #===

    # create configuration file
    create_config(os.path.join(TOP,folder_name,'repair'),buggy_prog,num_pos,num_neg)
    #====
    print buggy_prog
    return os.path.basename(buggy_prog)


def run_extraction(repair_folder,original_prog):
    """
    repair_folder - path to the repair folder
    original_prog - path to the program under test
    """
    print 'RUN EXTRACTION'
    assert 'mutants' in os.listdir(repair_folder)
    #move the mutants into the mutants folder
    separate_mutants(repair_folder)

    assert 'mutants_processed' in os.listdir(repair_folder)
    #process the mutants, meaning insert spaces in between each token
    process_folder(os.path.join(repair_folder,'mutants'),
                   os.path.join(repair_folder,'mutants_processed'))

    assert os.path.exists(original_prog)
    #extract the mutant lines
    extract_lines_added(os.path.join(repair_folder,'mutants_processed'),
                        os.path.join(repair_folder,'lines_added'),
                        original_prog)
    #extract the correct lines added
    assert 'repair.c' in os.listdir(repair_folder)
    extract_correct_lines(os.path.join(repair_folder,'mutants_processed','repair.c'),
                          original_prog,
                          os.path.join(repair_folder,'lines_added'))

def get_entropy(lines_folder,model=''):
    """
    lines_folder - folder of the lines added by the mutants
    model - path to the language model

    Get the entropy of all the lines added (by the mutants) in lines_folder.
    Stores the entropy in lines_folder/results/mutant_results.txt

    Returns a list of the entropy values
    """
    print "GET ENTROPY %s"%lines_folder
    os.chdir(lines_folder)
    assert len(os.listdir(os.getcwd())) > 0
    progs = glob.glob('0*')
    result = []
    print progs
    #create output file
    fid = open(os.path.join(lines_folder,'results','mutant_results.txt'),'w')
    for prog in progs:
        output = subprocess.check_output('echo "perplexity -text %s" | evallm -arpa %s'
                        %(prog,model),shell=True)
        print output, type(output)
        #extract the entropy from those files
        pat = r'Entropy = (\d+\.\d+) bits'
        match = re.search(pat,output)
        entropy = match.group(1)
        result.append(float(entropy))
        fid.write(entropy+'\n')
    fid.close()
    return result
    #return os.path.join(lines_folder,'results','mutant_results.txt')

def get_repaired_entropy(correct_lines_added,model=''):
    """
    correct_lines_added - path to the file containing the correct lines added
    model - path to the language model to use
    """
    print 'GET REPAIRED ENTROPY'
    output = subprocess.check_output('echo "perplexity -text %s" | evallm -arpa %s'
                        %(correct_lines_added,model),shell=True)
    pat = r'Entropy = (.*) bits'
    match = re.search(pat,output)
    entropy = match.group(1)
    return float(entropy)

def create_boxplot(data, save_dir,correct_entropy=1):
    """
    data_file - path file containing entropy values for the lines added by the mutant files
    save_directory - directory to save the plot in, not including the name of the plot itself
    correct_entropy - the entropy of the lines added by the repair program
    """
    print 'CREATE BOXPLOT'
    #fid = open(data_file,'r')
    #data=[float(l.strip()) for l in fid.readlines()]
    print data
    assert len(data) > 0
    #plot mutant entropy
    plt.boxplot(data)
    #plot correct entropy
    p1 = plt.plot([0,2],[correct_entropy,correct_entropy],color ='g')
    #label the repaired program
    l1 = plt.legend([p1],['repaired program'])

    #annotate the plot
    plt.ylabel('Entropy (bits)')
    plt.title('Entropy of lines added in mutant programs')

    #generate a random number as the name of the plot
    name = str(random.randint(0,sys.maxint))
    plt.savefig(os.path.join(save_dir,name+'.png'),bbox_inches=0)
    print os.path.join(save_dir,name+'.png')
    return name
    #plt.show()

def save_setup(prog_folder, save_dir,name='run'):
    """
    prog_folder - path to the program folder (ie. TOP/<program name>)
    save_dir - the directory to save the tarball
    name - name of the tarball

    Create a tarball of the entire prog_folder/repair directory and saves it as save_dir/name.tar
    """
    tarball = tarfile.open(os.path.join(save_dir,name),'w:gz')
    #print prog_folder
    os.chdir(prog_folder)
    tarball.add('repair')
    #print os.path.join(prog_folder,'repair')
    tarball.close()
    

def run_analysis(prog_folder,lines_folder,model):
    """
    prog_folder - path to the program folder (ie. TOP/<program name>
    lines_folder - absolute path to the folder containing the lines added per
    mutant and repair program
    model - absolute path to the language model

    Calculates the entropy of each mutant file and the repair file
    """
    data = get_entropy(lines_folder,model)
    correct_ent = get_repaired_entropy(os.path.join(lines_folder,'repair_lines_added.txt'),model)
    plotname = create_boxplot(data,os.path.join(TOP,prog_folder,'plots'),correct_ent)
    save_setup(os.path.join(TOP,prog_folder),
               os.path.join(TOP,prog_folder,'plots'),
               plotname+'.tar')
    

##def run_entire(prog_name,hw_num,buggy_prog=''):
##    """
##    Runs the entire flow from extraction to repair to analysis
##    """
##    #folder_name is the prog_name without the .c extension
##    if prog_name.find('.') < 0:
##        folder_name = prog_name
##        prog_name = prog_name +'.c'
##    else:
##        folder_name = prog_name.split('.')[0]
##    partition(prog_name,hw_num)
##    create_lm(os.path.join(TOP,folder_name,'processed','correct'),
##              os.path.join(TOP,folder_name,'ngram'),
##              prog_name)
##    orig_prog = setup_repair(folder_name,hw_num)
##    run_repair(os.path.join(TOP,folder_name,'repair'))
##    #if the repair program is found, run the extraction and analysis
##    if 'repair.c' in os.listdir(os.path.join(TOP,folder_name,'repair')):
##        run_extraction(os.path.join(TOP,folder_name,'repair'),
##                       os.path.join(TOP,folder_name,'repair',orig_prog))
##        run_analysis(os.path.join(TOP,folder_name,'repair','lines_added'),
##                     os.path.join(TOP,folder_name,'ngram',folder_name+'.arpa'))

def phase1(prog_name,hw_num):
    """
    The first phase where we gather all the programs, filter them, and create a language model
    """
    if prog_name.find('.') < 0:
        folder_name = prog_name
        prog_name = prog_name +'.c'
    else:
        folder_name = prog_name.split('.')[0]
    partition(prog_name,hw_num)
    create_lm(os.path.join(TOP,folder_name,'hash_removed','correct'),
              os.path.join(TOP,folder_name,'ngram'),
              folder_name)
    
def phase2(prog_name, hw_num,buggy=''):
    """
    The second phase where we setup the repair, run the repair, and if a repair is found, create the plot
    and save the setup
    """
    if prog_name.find('.') < 0:
        folder_name = prog_name
        prog_name = prog_name +'.c'
    else:
        folder_name = prog_name.split('.')[0]
    buggy_prog = setup_repair(folder_name,hw_num,buggy)
    run_repair(os.path.join(TOP,folder_name,'repair'))
    if 'repair.c' in os.listdir(os.path.join(TOP,folder_name,'repair')):
        run_extraction(os.path.join(TOP,folder_name,'repair'),
                       os.path.join(TOP,folder_name,'repair',buggy_prog))
        run_analysis(os.path.join(TOP,folder_name),
                 os.path.join(TOP,folder_name,'repair','lines_added'),
                 os.path.join(TOP,folder_name,'ngram',folder_name+'.arpa'))

def n_runs(prog_name, hw_num,buggy='',num_runs=2):
    """
    This is a generalization of phase2. Instead of running repair just once, we run it num_runs times.
    After all the repairs are run, we gather the entropy values and create boxplots of the mutant and repair
    entropys. Save the plot and write the entropy values to a file.
    """
    if prog_name.find('.') < 0:
        folder_name = prog_name
        prog_name = prog_name +'.c'
    else:
        folder_name = prog_name.split('.')[0]
    
    repair_count = 0
    itr = 0
    lines_folder = os.path.join(TOP,folder_name,'repair','lines_added')
    model = os.path.join(TOP,folder_name,'ngram',folder_name+'.arpa')
    #keep track of the entropy values
    all_mutant = []
    all_correct = []
    #keep running repair on the same buggy file, until we've reach the desired number of repaired runs
    while repair_count < num_runs:
        print 'REPAIR #%i, TRIAL #%i'%(repair_count,itr)
        if repair_count == 0 and itr > 5:
            print '!! Have not found repair within first 5 iterations, exiting'
            return
        buggy_prog = setup_repair(folder_name,hw_num,buggy)
        run_repair(os.path.join(TOP,folder_name,'repair'))
        if 'repair.c' in os.listdir(os.path.join(TOP,folder_name,'repair')):
            repair_count+=1
            run_extraction(os.path.join(TOP,folder_name,'repair'),
                       os.path.join(TOP,folder_name,'repair',buggy_prog))
            mutant_ent = get_entropy(lines_folder,
                               model)
            correct_ent = get_repaired_entropy(os.path.join(lines_folder,'repair_lines_added.txt'),
                                               model)
            all_mutant += mutant_ent
            all_correct.append(correct_ent)
        itr += 1
    #we've gathered the data so now create the appropriate plots
    assert len(all_mutant) > 0
    assert len(all_correct) > 0
    assert len(all_mutant) > len(all_correct)
    assert len(all_correct) == num_runs
    print 'Number of mutants: ',len(all_mutant)
    print 'Number of repairs: ',len(all_correct)
    fig = plt.figure()  #creates a figure
    handle = fig.add_subplot(1,2,1) # indicate that we want 1x2 subplots and refering to the 1st one
    handle.boxplot(all_mutant)
    handle.set_title('Mutant entropy (pop = %i)'%len(all_mutant))
    handle.set_ylabel('Entropy (bits)')
    p1y1,p1y2 = handle.get_ylim()

    handle = fig.add_subplot(1,2,2)
    handle.boxplot(all_correct)
    handle.set_title('Repaired entropy (pop = %i)'%num_runs)
    p2y1,p2y2 = handle.get_ylim()

    # match the y-axis of the subplots
    handle = fig.add_subplot(1,2,1)
    handle.set_ylim(min(p1y1,p2y1)-1, max(p1y2,p2y2)+1)
    handle = fig.add_subplot(1,2,2)
    handle.set_ylim(min(p1y1,p2y1)-1, max(p1y2,p2y2)+1)
    
    #plt.show()
    title = '%s_%i_runs'%(buggy,num_runs)
    os.chdir(os.path.join(TOP,folder_name))
    plt.savefig('%s.png'%title,bboxinches=0)

    #write out the mutant entropies
    fid = open('%s_mutant.txt'%title,'w')
    for ent in all_mutant:
        fid.write('%s\n'%ent)
    fid.close()
    #write out the correct entropies
    fid = open('%s_correct.txt'%title,'w')
    for ent in all_correct:
        fid.write('%s\n'%ent)
    fid.close()

def compile_images(img_dir,extension='png'):
    """
    img_dir - the path to the directory containing the images
    extension - the image extension we are interested in

    Gathers all the images in img_dir into one plot
    """
    assert os.path.exists(img_dir)
    os.chdir(img_dir)
    images = glob.glob('*.png')
    #plt.imshow(images[1])
    print images
    fig = plt.figure()
    for i in range(len(images)):
        ax = fig.add_subplot(1,len(images),i)
        img = mpimg.imread(images[i])
        plt.imshow(img)
    
##    ax = fig.add_subplot(1,2,1)
##    img=mpimg.imread(images[0])
##    plt.imshow(img)
##
##    ax = fig.add_subplot(1,2,2)
##    img = mpimg.imread(images[1])
##    plt.imshow(img)
    #plt.savefig('all.png',bbox_inches='tight')
    #plt.show()


#phase1('top3',6)
#phase2('top3',6,'jmanker_top3_bar.cil.c')

#phase2('square_root',4,'abagana_square_root_bar.cil.c')
#n_runs('square_root',4,'abagana_square_root_bar.cil.c',50)

#phase1('palin_recursive',8)
#n_runs('palin_recursive',8,'calchiu_palin_recursive_bar.cil.c',25)
#n_runs('palin_recursive',8,'shiwu_palin_recursive_bar.cil.c',25)
#n_runs('palin_recursive',8,'gachu_palin_recursive_bar.cil.c',25)
#n_runs('palin_recursive',8,'dtho_palin_recursive_bar.cil.c',25)


#phase1('makepalin',7)
#n_runs('makepalin',7,'fyquader_makepalin_bar.cil.c',25)

os.chdir(os.path.join(TOP,'square_root','hash_removed','buggy'))
buggys = glob.glob('*.c')
random.shuffle(buggys)
print buggys
for bug in buggys:
    n_runs('square_root',4,bug,25)



