@echo off
rem #####################################################################
rem # delete_zips.bat
rem # zip deletion batch file
rem # Willster419
rem # 2020-08-08
rem # searches for and deletes all zip files from the repo
rem #####################################################################

rem # set paths #########################################################
set REPO_ROOT=%CD%
echo REPO_ROOT: %REPO_ROOT%
rem #####################################################################

rem # collect all zip files and delete ##################################
for %%G in (*.zip) do (
  rem for debug
  echo "Deleting %%G"
  del "%%G"
)
rem #####################################################################
