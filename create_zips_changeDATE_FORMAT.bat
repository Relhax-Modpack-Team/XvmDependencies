@echo off
rem #####################################################################
rem # create_zips.bat
rem # zip creation batch file
rem # Willster419
rem # 2020-08-09
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
rem # https://stackoverflow.com/a/3123194/3128017
rem #####################################################################

rem # get the date in the form YYYY-MM-DD ###############################
#set YEAR=%date:~10,4%
#set DAY=%date:~7,2%
#set MONTH=%date:~4,2%
#set DATE_FORMAT=%YEAR%-%MONTH%-%DAY%
rem # autochange the format
rem # doesnt work with german/austrian date format 
rem # its changed to a variable 
rem # set it manually each patchday!
rem # -elektro-
set "DATE_FORMAT=2020-12-05"
echo Using date format %DATE_FORMAT%
rem #####################################################################

rem # set paths #########################################################
set REPO_ROOT=%CD%

rem # you can give an absolute value to the 7zip binary here, make sure
rem # that it's in quotes
rem #set SEVEN_ZIP_BIN="C:\Program Files\7-Zip\7z.exe"
set SEVEN_ZIP_BIN="7z"

echo REPO_ROOT: %REPO_ROOT%

SETLOCAL ENABLEDELAYEDEXPANSION
echo DIRS TO PROCESS:
for /d %%D in ("!CD!"\*) do (
  echo "%%~fD"
)
echo:
rem #####################################################################

rem # get folders to make zip files from ################################
set ZIPS=
set SEVEN_SEARCH_COMMAND=
set /A INDEX=0
set /A OUTTERINDEX=0

rem create 7zip zip and folder search arguments
for /d %%D in ("!CD!"\*) do (
  rem for debug
  rem echo %%~fD
  rem set the zip to the cd path, then the name of the folder, then
  rem date and .zip
  set ZIPS[!INDEX!]="!CD!\%%~nD_%DATE_FORMAT%.zip"
  set SEVEN_SEARCH_COMMAND[!INDEX!]="%%~fD\*"

  rem echo !INDEX!
  set /A INDEX=!INDEX!+1
)
rem #####################################################################

rem #for each zip file, run 7zip to collect files and keep structure ####
set /A INDEX=0
:CreateZipsLoop
if defined ZIPS[!INDEX!] (
  rem for debug
  rem echo !ZIPS[%INDEX%]!

  set ZIP=!ZIPS[%INDEX%]!
  set SEARCH=!SEVEN_SEARCH_COMMAND[%INDEX%]!
  rem for debug
  echo ZIP:    !ZIP!
  echo SEARCH: !SEARCH!

  rem "7zip command: 7z u 'TARGET_ZIP' TARGET_DIR\*"
  set SEVEN=!SEVEN_ZIP_BIN! u !ZIP! !SEARCH!
  rem for debug
  echo DEBUG: 7zip command:
  echo !SEVEN!
  !SEVEN!

  set /A INDEX=!INDEX!+1
  GOTO :CreateZipsLoop
)

echo Script is done
GOTO :eof
rem #####################################################################

ENDLOCAL
