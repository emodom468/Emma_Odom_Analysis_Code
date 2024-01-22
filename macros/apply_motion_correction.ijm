//Open first stab file
	lineseparator = "\n";
     cellseparator = ",\t";

     // copies the whole RT to an array of lines
     lines=split(File.openAsString(""), lineseparator);

     // recreates the columns headers
     labels=split(lines[0], cellseparator);
     if (labels[0]==" ")
        k=1; // it is an ImageJ Results table, skip first column
     else
        k=0; // it is not a Results table, load all columns
     for (j=k; j<labels.length; j++)
        setResult(labels[j],0,0);

     // dispatches the data into the new RT
     run("Clear Results");
     for (i=1; i<lines.length; i++) {
        items=split(lines[i], cellseparator);
        for (j=k; j<items.length; j++)
           setResult(labels[j],i-1,items[j]);
     }
     updateResults();


//translate open image based on stab file
	for(i=0; i<nResults;i++) {
		x1 = getResult("dX",i);
			if (isNaN(x1)){
				x1=0;}
			y1 = getResult("dY",i);
			if (isNaN(y1)){
				y1=0;
			}
		slicenum = getResult("Slice",i);
		print (slicenum);
		setSlice(slicenum); 
		run("Translate...", "x=x1 y=y1 interpolation=Bicubic slice"); 
	}
	//open second stab file
 // copies the whole RT to an array of lines
     lines=split(File.openAsString(""), lineseparator);

     // recreates the columns headers
     labels=split(lines[0], cellseparator);
     if (labels[0]==" ")
        k=1; // it is an ImageJ Results table, skip first column
     else
        k=0; // it is not a Results table, load all columns
     for (j=k; j<labels.length; j++)
        setResult(labels[j],0,0);

     // dispatches the data into the new RT
     run("Clear Results");
     for (i=1; i<lines.length; i++) {
        items=split(lines[i], cellseparator);
        for (j=k; j<items.length; j++)
           setResult(labels[j],i-1,items[j]);
     }
     updateResults();
     //run second stab
	for(i=0; i<nResults;i++) {
		x1 = getResult("dX",i);
			if (isNaN(x1)){
				x1=0;}
			y1 = getResult("dY",i);
			if (isNaN(y1)){
				y1=0;
			}
		slicenum = getResult("Slice",i);
		print (slicenum);
		setSlice(slicenum); 
		run("Translate...", "x=x1 y=y1 interpolation=Bicubic slice"); 
	}
selectWindow("Log"); 
   	run("Close"); 
   	selectWindow("Results"); 
   	run("Close"); 

