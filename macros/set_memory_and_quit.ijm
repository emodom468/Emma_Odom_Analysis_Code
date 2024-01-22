//Set memory capacity to 12GB RAM, this requires a restart to imlpement
run("Memory & Threads...", "maximum=13500 parallel=8");
//reset
close("*");
roiManager("reset");
run("Clear Results");
run("Quit");