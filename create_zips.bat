@echo off
rem #####################################################################
rem # create_zips.bat
rem # zip creation batch file
rem # Willster419
rem # 2020-08-08
rem # Creates zip files of all targets listed. Make sure that the 7zip
rem # executable is in your %PATH%, or the full path is 
rem # specified in the SEVEN_ZIP_BIN var.
rem #####################################################################

rem # useful links ######################################################
rem # https://www.tutorialspoint.com/batch_script/batch_script_variables.htm
rem # https://stackoverflow.com/questions/14810544/get-date-in-yyyymmdd-format-in-windows-batch-file
rem # https://code-examples.net/en/q/191d13
rem # https://www.tutorialspoint.com/batch_script/batch_script_arrays.htm
rem # https://www.robvanderwoude.com/variableexpansion.php
rem # https://www.robvanderwoude.com/for.php
rem # https://stackoverflow.com/questions/30335159/windows-cmd-batch-for-r-with-delayedexpansion
rem #####################################################################

rem # get the date in the form YYYY-MM-DD ###############################
set YEAR=%date:~10,4%
set MONTH=%date:~7,2%
set DAY=%date:~4,2%
set DATE_FORMAT=%YEAR%-%MONTH%-%DAY%
echo Using date format %DATE_FORMAT%
rem #####################################################################

rem # set paths #########################################################
set REPO_ROOT=%CD%
set PY_ROOT=%REPO_ROOT%\PY
set XC_ROOT=%REPO_ROOT%\XC
rem # you can give an absolute value to the 7zip binary here, make sure
rem # that it's in quotes
rem #set SEVEN_ZIP_BIN="C:\Program Files\7-Zip\7z.exe"
set SEVEN_ZIP_BIN="7z"
echo REPO_ROOT: %REPO_ROOT%
echo PY_ROOT:   %PY_ROOT%
echo XC_ROOT:   %XC_ROOT%
rem #####################################################################

SETLOCAL ENABLEDELAYEDEXPANSION
rem # get folders to make zip files from ################################
set DIRS=
set ZIPS=
set /A INDEX=0
rem echo Folders to act on

rem XC FILES
rem for loop vars can only be one character because reasons.
for /d %%D in ("%XC_ROOT%"\*) do (
  rem for debug
  rem echo %%~fD
  set DIRS=!DIRS! "%%~fD"
  set ZIPS[!INDEX!]="%%~fD_%DATE_FORMAT%.zip"
  rem echo !INDEX!
  set /A INDEX=!INDEX!+1
)

rem for debug, how to print array
rem echo !ZIPS[0]!

rem PY FILES
for /d %%E in ("%PY_ROOT%"\*) do (
  set DIRS=!DIRS! "%%~fE"
  set ZIPS[!INDEX!]="%%~fE_%DATE_FORMAT%.zip"
  set /A INDEX=!INDEX!+1
)
rem #####################################################################

rem # for each folder, call a task to get all files in it and run 7zip ##
set /A INDEX=0
for %%F in (%DIRS%) do (
  echo PROCESSING DIRECTORY %%F
  set TEST=%%F
  call :fileLoop TEST ZIPS[!INDEX!]
  set /A INDEX=!INDEX!+1
)

echo Script is done
GOTO :eof
rem #####################################################################

rem # fileLoop: function declaration ####################################
rem # find all files in a given folder, and add to a specified zip file.
rem # Use the 7zip command line utility to perform the zipping.
rem # In theory you could use any zip program, just change the SEVEN
rem # var to match it's arguements.
:fileLoop
set "FOLDER=!%1!"
set "ZIP_FILE=!%2!"
set FILES=
rem for debug
rem echo !FOLDER!
rem echo !ZIP_FILE!
for /r %FOLDER% %%G in (*) do (
  rem for debug
  rem echo %%G
  set FILES=!FILES! "%%G"
)
rem for debug
rem echo !FILES!
rem # "7zip command: 7z u '$$TARGET' $$FILES"
set SEVEN=!SEVEN_ZIP_BIN! u !ZIP_FILE!!FILES!
echo DEBUG: 7zip command:
echo !SEVEN!
!SEVEN!
EXIT /B
rem #####################################################################

ENDLOCAL
