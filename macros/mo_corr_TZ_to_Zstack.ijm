//first clean up!
// close all images
close("*");
// empty the ROI manager
roiManager("reset");
// empty the results table
run("Clear Results");

inputDir = getDirectory("");
//inputDir (directory) is the folder with TSeries stack for each z slice from TZSeries session

MoCorr_transforms = inputDir + "/MoCorr_transforms/" //this directory has the results of motion corr for each t series of a single z slice 
MoCorr_mean = inputDir + "/MoCorr_mean/" //subdirectory to save mean projected image 
//make subdirectory if does not exist 
if (File.isDirectory(MoCorr_transforms)){ 
 	print("motion correction transforms directory exists");
} else {
 	File.makeDirectory(MoCorr_transforms);
}
if (File.isDirectory(MoCorr_mean)){ 
 	print("motion correction mean img directory exists");
} else {
 	File.makeDirectory(MoCorr_mean);
}

apply_mo_corr_generate_ZStack(inputDir);
generate_Zstack(MoCorr_mean);

//apply_mo_corr_generate_ZStack takes in TZSereis and outputs motion corrected mean projected Z stack (compress time dimension)
function apply_mo_corr_generate_ZStack(directory) {
	fileList = getFileList(directory);
	for (i=0; i < fileList.length; i++){
		if (matches(fileList[i],".*tif.*")) {
			//Open tif //old: open(directory + fileList[i]);
			filePath = directory + fileList[i];
			run("Bio-Formats Importer","open=filePath autoscale color_mode=Default rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT");
			//Get file name without .tif extension
			imageName=File.getNameWithoutExtension(filePath); 
			print("Opening: " + imageName);
			if (i==0){
			//make rectangle and save to roi manager to apply for all slices
				setTool("rectangle");
				waitForUser("Draw the roi!"); // user draws roi then clicks ok 
				roiManager("Add");
				//move inside to reduce computations if it works lol
				//roiManager("Select",0);
				//getSelectionBounds(x, y, w, h);
			}
		roiManager("Select",0);
		//may be necessary to get attributes x0,y0,w,h of user defined rectangle to automate running of align slices in stack
		getSelectionBounds(x, y, width, height);
		run("Align slices in stack...", "method=5 windowsizex=" + width + " windowsizey=" + height + " x0=" + x + " y0=" + y + " swindow=0 subpixel=false itpmethod=0 ref.slice=1 show=true");
		//Save results
		saveAs("Results",MoCorr_transforms+imageName+"_results.csv");
		selectWindow("Results");
		run("Close");
		//save motion corrected mean image for z slice
		run("Z Project...", "projection=[Average Intensity]");
		saveAs("tiff",MoCorr_mean + imageName + "_mean");
		//close tif
		while (nImages>0) { 
		selectImage(nImages); 
		close();}
		}
	}
	run("Close All");
}

function generate_Zstack(directory){
	fileList = getFileList(directory);
	for (i=0; i < fileList.length; i++){ 
		if (matches(fileList[i],".*tif.*")) {
			//Open tif
			open(directory + fileList[i]);
		}
	}
	run("Concatenate...", "all_open title=[Together]");
	saveAs("tiff", directory+ "mo_corr_mean_ZStack");
	run("Close All");
}
	



