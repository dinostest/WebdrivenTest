var origin = [];
var curData;
var dialog;
var curCoords;
function click_func(app,module,scenario,func){
	if (!func){
		func = $("input[name="+module+"_func_name]:checked").val();
	}
	var url = "/performance/loadscenario?app="+app+ "&module=" + module + "&scenario=" + scenario + "&func=" + func;
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
	
//	$("." + func_id ).prop("checked", false);
//	$("#" + module + "-select").prop("checked", false);
	
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
		result.push(csv.data[i]["dinos_pkid"]);
		results.push(result);
	}
	return results;
}

function createHandsonTable(tableId, csv){
	var res = false;
	if (csv.data && csv.header){
		data_lists = sort_csv_data(csv);
		origin = data_lists;
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
			datacols=[];
			for (var i = 0; i < csv.header.length; i++){
				datacols.push({data:i});
			}
			curData = $.extend(true,[],data_lists); 
			$("#"+tableId).handsontable({
				data: curData,
				minSpareRows:1,
				colHeaders: csv.header,
				contextMenu: ['row_above','row_below','remove_row'],
				columns: datacols,
				afterOnCellMouseDown: function(event,coords,TD){
					console.log(coords);
					if (coords.col == (datacols.length -1)){
						var value = curData[coords.row][coords.col]
						
						$("input[id$=tag]:checked").each(function(){
							$(this).removeAttr("checked");
						});
						if (value){
							var items = value.split(",");	
							for(var i = 0; i < items.length; i++){
								$("#"+items[i]+"-tag").attr("checked","checked");
							}
						}	
						dialog.dialog("open");
						curCoords = coords;
					}
					
				}
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

function checkChange(data){
	var res = {}
	res.removeList=[];
	res.changeList=[];
	data.sort(sortList);
	origin.sort(sortList);
	var i = 0;
	var j = 0;
	var pkid_pos = header.length;
	while (i < origin.length && j < data.length){
		if(data[j].length == pkid_pos || !data[j][pkid_pos]){
			j++;
		}else if(origin[i][pkid_pos] == data[j][pkid_pos]){
			if (origin[i].join() != data[j].join()){
				res.changeList.push(data[j][pkid_pos]);
			}
			i++;
			j++;
		}else if(origin[i][pkid_pos] < data[j][pkid_pos]){
			res.removeList.push(origin[i][pkid_pos]);
			i++;
		}
	}
	while (i < origin.length){
		res.removeList.push(origin[i][pkid_pos]);
		i++;
	}
	return res;
}

function sortList(a,b){
	if (a.length == header.length){
		return 1;
	}else{
		return parseInt(a[header.length]) - parseInt(b[header.length]);
	}
	
}