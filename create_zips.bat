@echo off
rem #####################################################################
rem # create_zips.bat
rem # zip creation batch file
rem # Willster419
rem # 2020-08-08
rem # Creates zip files of all targets listed
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

rem # for each folder, get all files in it and run 7zip #################
rem dir /a:d "%PY_ROOT%"
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
set SEVEN=7z u !ZIP_FILE!!FILES!
echo DEBUG: 7zip command:
echo !SEVEN!
!SEVEN!
EXIT /B

ENDLOCAL
