#!/usr/bin/python

import os
import subprocess
import sys

def test_invalid_input(logfile):
    tc_count = 0
    passed_count = 0

    directory = "test/invalid_input"
    logfile.write("INVALID INPUT GROUP\n")
    for f in sorted(os.listdir(directory)):
        if ".hgr" not in f:
            continue
        
        tc_count += 1
        
        basename = os.path.splitext(f)[0]
        htd_file = basename + ".htd"
        
        tc_pass = False
        out = "ERROR"
        try:
            out = subprocess.check_output('./htd_validate {} {}'.format(os.path.join(directory, f), os.path.join(directory, htd_file)), stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            out = e.output
            if "Instance Error" in out:
                passed_count += 1
                tc_pass = True
        
        logfile.write(("#" if tc_pass else "x") * 10 + " {}: {}".format(basename, out))
    
    logfile.write("#" * 10 + " Passed {}/{} testcase\n".format(passed_count, tc_count))
    logfile.write("\n")
    return passed_count, tc_count


def test_invalid_solution(logfile):
    tc_count = 0
    passed_count = 0

    directory = "test/invalid_solution"
    logfile.write("INVALID SOLUTION GROUP\n")
    for f in sorted(os.listdir(directory)):
        if ".hgr" not in f:
            continue
        
        tc_count += 1
        
        basename = os.path.splitext(f)[0]
        htd_file = basename + ".htd"
        
        tc_pass = False
        out = "ERROR"
        try:
            out = subprocess.check_output('./htd_validate {} {}'.format(os.path.join(directory, f), os.path.join(directory, htd_file)), shell=True)
            if "SUCCESS" not in out:
                passed_count += 1
                tc_pass = True
        except subprocess.CalledProcessError as e:
            print(e)
        
        logfile.write(("#" if tc_pass else "x") * 10 + " {}: {}".format(basename, out))
    
    logfile.write("#" * 10 + " Passed {}/{} testcase\n".format(passed_count, tc_count))
    logfile.write("\n")
    return passed_count, tc_count

def test_valid(logfile):
    tc_count = 0
    passed_count = 0

    directory = "test/valid"
    logfile.write("VALID GROUP\n")
    for f in sorted(os.listdir(directory)):
        if ".hgr" not in f:
            continue
        
        tc_count += 1
        
        basename = os.path.splitext(f)[0]
        htd_file = basename + ".htd"
        
        tc_pass = False
        out = "ERROR"
        try:
            out = subprocess.check_output('./htd_validate {} {}'.format(os.path.join(directory, f), os.path.join(directory, htd_file)), shell=True)
            if "SUCCESS" in out:
                passed_count += 1
                tc_pass = True
        except subprocess.CalledProcessError as e:
            print(e)
        
        logfile.write(("#" if tc_pass else "x") * 10 + " {}: {}".format(basename, out))
    
    logfile.write("#" * 10 + " Passed {}/{} testcase\n".format(passed_count, tc_count))
    logfile.write("\n")
    return passed_count, tc_count

def main():
    os.system("make verbose")
    passed_count = 0
    tc_count = 0

    with open("test_htd.log", "w") as logfile:
        invalid_input_passed_count, invalid_input_tc_count = test_invalid_input(logfile)
        invalid_solution_passed_count, invalid_solution_tc_count = test_invalid_solution(logfile)
        valid_passed_count, valid_tc_count = test_valid(logfile)

        passed_count = invalid_input_passed_count + invalid_solution_passed_count + valid_passed_count
        tc_count = invalid_input_tc_count + invalid_solution_tc_count + valid_tc_count
    
    print("Passed {}/{} testcase".format(passed_count, tc_count))
    print("Log written in test_htd.log")
    os.system("make clean")

if __name__ == "__main__":
    main()