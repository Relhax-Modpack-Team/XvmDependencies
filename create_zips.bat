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
rem # https://stackoverflow.com/a/25791900/3128017
rem # https://stackoverflow.com/a/20385978/3128017
rem #####################################################################

rem # get the date in the form YYYY-MM-DD ###############################
set YEAR=%date:~10,4%
set DAY=%date:~7,2%
set MONTH=%date:~4,2%
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
set ZIPS=
set SEVEN_SEARCH_COMMAND=
set /A INDEX=0
rem echo Folders to act on

rem XC FILES
rem for loop vars can only be one character because reasons.
for /d %%D in ("%XC_ROOT%"\*) do (
  rem for debug
  rem echo %%~fD
  rem set the zip to the cd path, then the name of the folder, then
  rem date and .zip
  set ZIPS[!INDEX!]="!CD!\%%~nD_%DATE_FORMAT%.zip"
  set SEVEN_SEARCH_COMMAND[!INDEX!]="%%~fD\*"

  rem echo !INDEX!
  set /A INDEX=!INDEX!+1
)

rem for debug, how to print array
rem echo ZIP:    !ZIPS[0]!
rem echo SEARCH: !SEVEN_SEARCH_COMMAND[0]!

rem PY FILES
for /d %%D in ("%PY_ROOT%"\*) do (
  set ZIPS[!INDEX!]="!CD!\%%~nD_%DATE_FORMAT%.zip"
  set SEVEN_SEARCH_COMMAND[!INDEX!]="%%~fD\*"

  set /A INDEX=!INDEX!+1
)
rem #####################################################################

rem #for each zip file, run 7zip to collect files and keep structure ####
set /A INDEX=0
:SymLoop
if defined ZIPS[!INDEX!] (
  rem for debug
  rem echo !ZIPS[%INDEX%]!

  set ZIP=!ZIPS[%INDEX%]!
  set SEARCH=!SEVEN_SEARCH_COMMAND[%INDEX%]!
  rem for debug
  rem echo ZIP:    !ZIP!
  rem echo SEARCH: !SEARCH!

  rem "7zip command: 7z u 'TARGET_ZIP' TARGET_DIR\*"
  set SEVEN=!SEVEN_ZIP_BIN! u !ZIP! !SEARCH!
  rem for debug
  rem echo DEBUG: 7zip command:
  rem echo !SEVEN!
  !SEVEN!

  set /A INDEX=!INDEX!+1
  GOTO :SymLoop
)

echo Script is done
GOTO :eof
rem #####################################################################

ENDLOCAL
