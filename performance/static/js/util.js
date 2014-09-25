function click_func(app,scenario,data_file){
	var url = "/performance/loadscenario?app=" + app + "&scenario=" + scenario + "&file=" + data_file;
	window.open(url,"_blank",'directories=no,titlebar=no,toolbar=no,location=no,status=no');
}

function runTest(module,func){
	var data={};
	data.module=module;
	data.func=func;
	if ($("#" + module + "-parallel").prop("checked")){
		data.run_in_parallel = true;
	}
	html = "<b style='color:red'>Starting</b>";
	var func_id = func + "-func";
	$("." + func_id ).attr("disabled", "disabled");
	$("." + func_id ).prop("checked", false);
	$("#" + module + "-select").prop("checked", false);
	$("#" + func + "-status").html(html);
	$.ajax({
		url: "/performance/runtest/",
		dataType:"json",
		data:JSON.stringify(data),
		type:"POST",
		success:function(res){
			var module = res.module;
			var func = res.func;
			var ts_f = res.ts_f;
			setTimeout(function (){
			getStatus(module,func,ts_f)}
			,3000);
		}
	});
}

function sort_csv_data(csv){
	var results = [];
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

function createHandsonTable(tableId, csv){
	var res = false;
	if (csv.data && csv.header){
		data_lists = sort_csv_data(csv);
		if (csv.thread){
			$("#"+tableId).handsontable({
				data:data_lists,
				minSpareRows:1,
				colHeaders: csv.header,
				contextMenu: ['row_above','row_below','remove_row'],
				rowHeaders: function (row) {
					return "" + (row + 1);
				},
				cells: function(row,col,prop){
					var property = {};
					if (row === 0 && col === 0){
						property.readOnly = false;
					}
					return property;
				},

			});		
		}else{
			$("#"+tableId).handsontable({
				data:data_lists,
				minSpareRows:1,
				colHeaders: csv.header,
				contextMenu: ['row_above','row_below','remove_row']
			});
		}
	}else{
		$("#"+tableId).handsontable({
			startRows:2,
			startCols:2,
			rowHeaders: true,
			colHeaders: true,
			minSpareRows: 1,
			minSpareCols: 1
		});
		res = true;
	}
	return res;
}
