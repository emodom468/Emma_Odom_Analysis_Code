// your_macro.ijm
close("*");
roiManager("reset");
run("Clear Results");

filePath = getArgument();
run("Bio-Formats Importer", "open=" + filePath + " autoscale color_mode=Default rois_import=[ROI manager] specify_range view=Hyperstack stack_order=XYCZT t_begin=1 t_end=3 t_step=1");
imagesName = getTitle();

function getAutomaticROI() {
    getDimensions(width, height, channels, slices, frames);
    roiWidth = width * 0.8;
    roiHeight = height * 0.8;
    roiX = (width - roiWidth) / 2;
    roiY = (height - roiHeight) / 2;
    return newArray(roiX, roiY, roiWidth, roiHeight);
}

autoROI = getAutomaticROI();
makeRectangle(autoROI[0], autoROI[1], autoROI[2], autoROI[3]);
roiManager("Add");
//waitForUser("check before next!");
saveAs("Tiff", "/Users/emmaodom/Documents/test_" + imagesName + ".tif");

//reset
close("*");
roiManager("reset");
run("Clear Results");
run("Quit");