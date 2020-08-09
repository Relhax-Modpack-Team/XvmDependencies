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
echo Folders to act on

for /d %%D in ("%XC_ROOT%"\*) do (
  rem echo %%~fD # was for debug
  set DIRS=!DIRS! "%%~fD"
)

rem for /d %%D in ("%PY_ROOT%"\*) do (
rem  set DIRS=!DIRS! "%%~fD"
rem )

for %%D in (%DIRS%) do (
  echo %%D
)
rem #####################################################################

rem # for each folder, get all files in it and run 7zip #################
rem set FILES=
rem dir /a:d "%PY_ROOT%"
for %%D in (%DIRS%) do (
  echo PROCESSING DIRECTORY "%%D"
  rem for %%FILES in ('dir ')
)
rem #####################################################################

ENDLOCAL
echo Script is done