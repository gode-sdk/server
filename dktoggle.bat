@echo off
SET ACTION=%1

:: Check if the first argument is --on or --off
IF "%ACTION%"=="--on" (
    echo Starting the container using Docker Compose...
    docker-compose up -d
) ELSE IF "%ACTION%"=="--off" (
    echo Stopping the container using Docker Compose...
    docker-compose down
) ELSE (
    echo Invalid flag. Use --on to start or --off to stop.
)

pause
