var header=[];
$(function() {
	$.ajaxSetup({
            headers: { "X-CSRFToken": $.cookie("csrftoken") }
    });

	$.ajax({
		url: "/performance/loaddata?app=" + app +"&file=" + data_file,
		dataType:"json",
		type:"GET",
		success:function (res){
			data=res;
			console.log(data);
			createHandsonTable("datasheet", data);
		}
	});	
	$("#save").on("click",function(){
		var $container = $("#datasheet");
		var handsontable = $container.data("handsontable");
		var sheet = {}
		console.log("save");
		sheet.header=header;
		sheet.data = handsontable.getData();
		$.ajax({
			url: "/performance/savedata?app=" + app +"&file=" + data_file,
			dataType: "json",
			data: JSON.stringify(sheet),
			type: "POST",
			success:function (res){
				//window.close();
			}
		});
	});
});

function createHandsonTable(tableId, csv){
	data_lists = sort_csv_data(csv);
	$("#"+tableId).handsontable({
		data:data_lists,
		minSpareRows:1,
		colHeaders: csv.header,
		contextMenu: ['row_above','row_below','remove_row']
	});
}

function sort_csv_data(csv){
	results = [];
	header = csv.header;
	for(var i = 0; i < csv.data.length; i++){
		result = [];
		for (var j = 0; j< csv.header.length; j++){
			result.push(csv.data[i][csv.header[j]]);
		}
		results.push(result);
	}
	return results;
}