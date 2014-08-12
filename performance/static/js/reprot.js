var header=[];
$(function() {
	$.ajax({
		url: "/performance/loadreport?app=" + app +"&file=" + data_file,
		dataType:"json",
		type:"GET",
		success:function (res){
			data=res;
			console.log(data);
			createHandsonTable("datasheet", data);
		}
	});	
});

function createHandsonTable(tableId, csv){
	data_lists = sort_csv_data(csv);
	$("#"+tableId).handsontable({
		data:data_lists,
		minSpareRows:1,
		colHeaders: csv.header,
		columnSorting: true
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