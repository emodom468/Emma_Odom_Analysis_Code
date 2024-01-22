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
var referenceSlice = 10;
var useAutomaticROI = true; // Set to false to manually draw the ROI

// Get arguments from the command line
file_path = getArgument();
// Find the last slash to separate the directory
lastSlashIndex = lastIndexOf(file_path, "/");
// Extract the directory path
directory = substring(file_path, 0, lastSlashIndex);
//directory = File.directory(file_path);
processImage(file_path, directory, referenceSlice);
 
function processImage(file_path, directory, referenceSlice) {
	run("Bio-Formats Importer", "open=" + file_path + " autoscale color_mode=Default rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT");
	imagesName = getTitle();
	print("Opening: " + imagesName);
	
	// Create and save initial Z projection
    run("Z Project...", "projection=[Average Intensity]");
    saveAs("Tiff", directory + "/" + imagesName + "_initial_z_projection.tif");
    close();
    
	//roi = getUserROI();
	roi = getAutomaticROI();
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
    saveAs("Tiff", directory + "/" + imagesName + "_post_correction_z_projection.tif");
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
    roiWidth = Math.floor(width * 0.8);
    roiHeight = Math.floor(height * 0.8);
    roiX = Math.floor((width - roiWidth) / 2);
    roiY = Math.floor((height - roiHeight) / 2);
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
        saveAs("Results", directory + "/stab 1_refSlice_" + referenceSlice + ".csv");
    } else {
        saveAs("Results", directory + "/stab " + passNumber + ".csv");
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