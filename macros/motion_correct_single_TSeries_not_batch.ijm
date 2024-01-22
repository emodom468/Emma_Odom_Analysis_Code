//change set number to referenceSliceNumber 

/* Motion correction macro for single T Series
 * This code performs two-pass motion correction using Align slice method.
 * INPUT: Path to directory having only a single tif stack T series.
 * OUTPUT: Returns stab1.csv and stab2.csv with x,y translations for motion correction.
*/

// Close all images and reset ROI manager and Results table
close("*");
roiManager("reset");
run("Clear Results");

// Global variables
var referenceSlice;
var useAutomaticROI = true; // Set to false to manually draw the ROI

inputDir = getDirectory("Select the folder with T-Series stack");
referenceSlice = getNumber("Enter the reference slice number for this batch:", 10);
processImage(directory, fileName)
/*processFolder(inputDir);

//need to add more exclusion criteria on top of being a tiff, 
//as other nonoriginal tiffs might be saved in some of these folders 
function processFolder(directory) {
	fileList = getFileList(directory);
	for (i = 0; i < fileList.length; i++) {
		if (matches(fileList[i], ".*\\.tif")) {
			processImage(directory, fileList[i]);
		}
	}
}*/

//If integrated to python, I can just use processImage probs? it will be simpler to implement 
//seelction criteria in python string processing than in imageJ... 
function processImage(directory, fileName) {
	filePath = directory + fileName;
	run("Bio-Formats Importer", "open=" + filePath + " autoscale color_mode=Default rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT");
	imagesName = getTitle();
	print("Opening: " + imagesName);
	
	// Create and save initial Z projection
    run("Z Project...", "projection=[Average Intensity]");
    saveAs("Tiff", directory + imagesName + "_initial_z_projection.tif");
    close();
    
	//roi = getUserROI();
	roi = useAutomaticROI ? getAutomaticROI() : getUserROI();
	//referenceSlice = getUserDefinedSlice(); // User defines the reference slice //replaced by global var for batch processing
	
	// First pass alignment
	pass = 1;
	alignSlices(roi, referenceSlice, pass);

	// Second pass alignment
	run("Z Project...", "projection=[Average Intensity]");
	run("Concatenate...", "all_open title=[Together]");
	pass = 2;
	alignSlices(roi, nSlices, pass);
	deleteLastSlice();
	
	// Create and save post-correction Z projection
    run("Z Project...", "projection=[Average Intensity]");
    saveAs("Tiff", directory + imagesName + "_post_correction_z_projection.tif");
    close();

	// Optional: save motion corrected TIFF
	// saveAs("tiff", directory + imagesName + "_motion_corrected");

	write("Motion correction complete for " + imagesName);
	close("*");
}

function getAutomaticROI() {
    //returns dim for rectangle that is 80% of the fov and centered. 
    // Assuming the image is already open
    getDimensions(width, height, channels, slices, frames);
    roiWidth = width * 0.8;
    roiHeight = height * 0.8;
    roiX = (width - roiWidth) / 2;
    roiY = (height - roiHeight) / 2;
    return newArray(roiX, roiY, roiWidth, roiHeight);
}

function getUserROI() {
	setTool("rectangle");
	waitForUser("Draw the ROI!");
	roiManager("Add");
	roiManager("Select", 0);
	getSelectionBounds(x, y, width, height);
	return newArray(x, y, width, height);
}

function alignSlices(roi, referenceSlice, passNumber) {
	run("Align slices in stack...", "method=5 windowsizex=" + roi[2] + " windowsizey=" + roi[3] + " x0=" + roi[0] + " y0=" + roi[1] + " swindow=0 subpixel=false itpmethod=0 ref.slice=" + referenceSlice + " show=true");
	saveResults(directory, passNumber, referenceSlice);
}

function deleteLastSlice() {
	setSlice(nSlices);
	run("Delete Slice");
}

function saveResults(directory, passNumber, referenceSlice) {
    if (passNumber == 1) {
        saveAs("Results", directory + "stab 1_refSlice_" + referenceSlice + ".csv");
    } else {
        saveAs("Results", directory + "stab " + passNumber + ".csv");
    }
    selectWindow("Results");
    run("Close");
}

function getUserDefinedSlice() {
	return getNumber("Enter the reference slice number:", 10);
}

//reset
close("*");
roiManager("reset");
run("Clear Results");
run("Quit");