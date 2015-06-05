(function(){

var app = angular.module("scenario",[]);

app.controller("TabController",['$http','$scope',function($http,$scope){
	$scope.tab = 1;
	$scope.keywords = [];
	$scope.settings = [];
	$scope.header = [];
	$scope.data = [];
	$scope.originalData = [];
	$scope.setTab = function(tab){
		$scope.tab = tab;
	};
	$scope.isSet = function(tab){
		return $scope.tab == tab;
	};
	$scope.caseItem = {};
	$scope.$watch('tab',
		function(newValue,oldValue){
		if (newValue == 3 && oldValue != 3){
			setTimeout(checkDesc,100);
		}
		if (newValue == 2 && oldValue != 2){
			setTimeout(checkSettings,100);
		}
		if (newValue == 1 && oldValue != 1){
			setTimeout(checkData,100);
		}

	});
	
	
	$scope.$watch('header',function(newValue,oldValue){
		
	});
	
	$scope.show = function(keyword){
		if (keyword && keyword.keyword.length > 0){
			items = keyword.keyword.split("\"");
			for (var j = 1; j < items.length; j = j + 2){
				if ($scope.caseItem[items[j]]){
					items[j] = "\"" + $scope.caseItem[items[j]] + "\"";
				}else{
					items[j] = "\"" + items[j] + "\"";
				}
			}
			return items.join("");
		}
	};

/* 	this.table.columns = columns;
	this.colHeaders = true;
	this.table = {};
	this.table.items = [];
	var that = this;
 */	
/* 	$http.get("/automation/loaddata?app=" + dinosApp + "&module=" + module + "&scenario=" + scenario + "&func=" + func)
	.success(function(data,status,headers,config){
		console.log(data);
		that.table.columns = data.columns;
		that.table.items = data.data;		
	});
 */}]);
})();

function	checkDesc(){
	console.log($("#description").is(":visible"));
	if ($("#description").is(":visible")){
		var scope = angular.element($("#scenario_data")).scope();
		var keywords_list = [];
		for (var i = 0; i < scope.keywords.length ; i++){
			keywords_list.push([scope.keywords[i].keyword,scope.keywords[i].dinos_pkid]);
		}
		console.log(keywords_list);
		$("#description").handsontable({
			data: keywords_list,
			minSpareRows:1,
			rowHeaders: true,
			colHeaders: "Description",
			contextMenu: ['row_above','row_below','remove_row'],
			columns: [{data:0}],
			afterChange : function(changes,source){
				var keywords = [];
				var keywords_list = this.getData();
				var scope = angular.element($("#scenario_data")).scope();
				for (var i = 0; i < keywords_list.length; i++){
					if (keywords_list[i][0] && keywords_list[i][0].length > 0){
						var item = {};
						item["keyword"] = keywords_list[i][0];
						if (keywords_list[i][1]){
							item["dinos_pkid"] = keywords_list[i][1];
						}else{
							item["dinos_pkid"] = "";
						}
						keywords.push(item);						
					}					
				}
				for (x in keywords){
					var items = keywords[x].keyword.split("\"");
					for (var i = 1; i < items.length; i=i+2){
						if (scope.header.indexOf(items[i]) < 0){
							scope.header.splice(scope.header.length - 2,0,items[i]);
							for (var j = 0; j < scope.data.length; j++){
								scope.data[j][items[i]] = "";
							}
						}
					}
				}
				
				

				scope.$apply(function(){
					scope.keywords= keywords;
				});
			}

		});
	}else{
		setTimeout(checkDesc,100);
	}
}	

function	checkData(){
	console.log($("#datasheet").is(":visible"));
	if ($("#datasheet").is(":visible")){
		var scope = angular.element($("#scenario_data")).scope();
		var header = scope["header"];
		var data = scope["data"];
		var data_list = sort_csv_data(scope);
		var collist = [];
		for (var i = 0; i < header.length ; i++){
			collist.push({data:i});
		}
		console.log(data_list);
		$("#datasheet").handsontable({
			data: data_list,
			minSpareRows:1,
			rowHeaders: true,
			colHeaders: header,
			contextMenu: ['row_above','row_below','remove_row'],
			columns: collist,
			afterOnCellMouseDown: function(event,coords,TD){
				if (coords.row >= 0){
					var scope = angular.element($("#scenario_data")).scope();
					var caseitem = {};
					var tableData = this.getData();
					for (var x in scope.header){
						caseitem[scope.header[x]] = tableData[coords.row][x];
					}


					scope.$apply(function(){
						scope.caseItem= caseitem;
					});


	//					$("#scenario_name").html(caseitem['Test Cases']);
	//					change_content(keywords,caseitem,tableId);
					if (coords.col == (this.countCols() -1)){
						var value = tableData[coords.row][coords.col]
						
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
					
			},
			afterChange : function(changes,source){
				var scope = angular.element($("#scenario_data")).scope();
				var tableData = this.getData();
				var newData = [];
				for (var i = 0; i < tableData.length; i++){
					var item = {};
					for(var j = 0; j < tableData[i].length; j++){
						
						if (j < scope.header.length){
							item[scope.header[j]]=tableData[i][j];
						}else{
							item["dinos_pkid"]=tableData[i][j];
						}
					}
					newData.push(item);
				}
				scope.data = newData;
			}

		});
	}else{
		setTimeout(checkDesc,100);
	}
}	

function	checkSettings(){
	if ($("#setting").is(":visible")){
		var scope = angular.element($("#scenario_data")).scope();
		var settings_list = [];
		console.log(scope.settings);
			
		for (x in scope.settings){
			if (scope.settings.hasOwnProperty(x)){
				settings_list.push([x,scope.settings[x]]);
			}
		}
		console.log(settings_list);
		$("#setting").handsontable({
			data: settings_list,
			minSpareRows:1,
			rowHeaders: true,
			colHeaders: ["Key","Value"],
			contextMenu: ['row_above','row_below','remove_row'],
			columns: [{data:0},{data:1}],
		});
	}
	
}
var header=[];
var rules = ["Sample name can't contain the comma","Sample must have '>>' to indicate the module name"];
var errMsg = {};
$(function() {
	dialog = $("#dialog-select").dialog({
		autoOpen:false,
		height:300,
		width:350,
		modal:false,
		buttons:{
			"Save": saveTag,
			Cancel:function(){
			dialog.dialog("close");
			}
		},
	});
	for ( var i = 0; i < rules.length; i++){
		errMsg[rules[i]] = false;
	}
	$.ajaxSetup({
            headers: { "X-CSRFToken": $.cookie("csrftoken") }
    });

	$.ajax({
		url: "/automation/loaddata?app=" + dinosApp + "&module=" + module + "&scenario=" + scenario + "&func=" + func ,
		dataType:"json",
		type:"GET",
		success:function (res){
			data=res;
			console.log(data);
			//createHandsonTable("datasheet", data);
			
			var scope = angular.element($("#scenario_data")).scope();
			scope.$apply(function(){
				scope["keywords"] = data["keywords"];
				scope["settings"] = data["settings"];
				scope["header"] = data["header"];
				scope["data"] = data["data"];
				scope["originalData"] = data["data"];
			});
			checkData();
		}
	});	
	$(window).resize(function(){
		$("#datasheet").handsontable("render");
	
	});

	$("#save").on("click",function(){
//		var $container = $("#datasheet");
		var scope = angular.element($("#scenario_data")).scope();
//		var handsontable = $container.data("handsontable");
		var sheet = {}
		$("#save").html("Saving");
		$("#save").attr("disabled","disabled");
//		console.log("save");
		sheet.header=scope.header;
		sheet.data=scope.data;
		sheet.keywords=scope.keywords;
		sheet.setting=scope.settings;
/* 		var data = handsontable.getData();
		var sortedData = [];
 		for (var i =0; i < data.length; i++){
			sortedData.push(handsontable.getSourceDataAtRow(i));
		}
		sheet.data = sortedData;
		sheet.changes = checkChange(data);
*/		if (validate(sheet.data)){
			$.ajax({
				url: "/automation/savedata?app=" + dinosApp + "&module=" + module + "&scenario=" + scenario + "&func=" + func,
				dataType: "json",
				data: JSON.stringify(sheet),
				type: "POST",
				success:function (res){
					self.close();
					window.close();
				}
			});
		}else{
			var errMsgs = "Data validation failed, please follow the below rules:";
			for (var i = 0; i < rules.length; i++){
				if (errMsg[rules[i]])
					errMsgs = errMsgs + "\n" + rules[i];
			}
			alert(errMsgs);
		}
	});
});

function validate(data){
	var result = true;
	for( var i = 0; i < data.length; i++){
		var line = data[i];
		for (var j = 0; j < line.length; j++){
			var item = line[j];
			var itemRes = true;
			if (j == 0 && item ){
				if( item.indexOf(">>") < 0){
					itemRes = false;
					errMsg[rules[1]] = true;
					result = false;
				}
				if (item.indexOf(",") >= 0){
					itemRes = false;
					errMsg[rules[0]] = true;
					result = false;
				}
			}
			if (!itemRes){
				var  cell = $("#datasheet").handsontable("getCell",i,j);
				cell.style.color = "red";				
			}
		}
	}
	return result;
}	

function saveTag(){
	var value = $("input[id$=tag]:checked").val();
	for (var i = 1; i < $("input[id$=tag]:checked").length ; i++){
		value = value + "," + $("input[id$=tag]:checked")[i].value;
	}
	curData[curCoords.row][curCoords.col] = value;
	$("#datasheet").handsontable("render");
	dialog.dialog("close");
}


