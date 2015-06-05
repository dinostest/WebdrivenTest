var app = angular.module("dinostree",["treeControl"]);

app.controller('dinosctrl',function($scope,$http) {
	$scope.pagenode = {};
	$scope.pagenode["children"] = [];
	$scope.scenario={};
	$http.get('/automation/loadtree').success(
	function(data,status,headers,config){
		$scope.treedata = [data.data];
		$scope.pagenode = copyData(data.data);
		$scope.hierarchy = data.hierarchy;
		$scope.selected = data.data;
		$scope.snode = $scope.treedata;

	});

 	$scope.showSelected = function(sel) {
		if (sel != $scope.selected){
			$("#saveNode").html("Save");
			$("#saveNode").removeAttr("disabled");
		}

		$scope.selected = sel;
		if (sel){
			$scope.pagenode = copyData(sel);
			//$scope.datalist = [];
			if (sel.type == 'Scenario'){
				$http.get('/automation/fetchscenario?id='+sel.id).success(
					function(data,status,headers,config){
						$scope.pagenode.data = data;
						if ($scope.scenario.scope){
							$scope.scenario.scope["keywords"] = data["keywords"];
							$scope.scenario.scope["settings"] = data["settings"];
							$scope.scenario.scope["header"] = data["header"];
							$scope.scenario.scope["header"].push("Selected");
							$scope.scenario.scope["data"] = data["data"];
							$scope.scenario.scope["originalData"] = data["data"];
							for (var i = 0; i < $scope.scenario.scope["data"].length; i++){
								 $scope.scenario.scope.data[i]["Selected"] = false;
							}
								
							checkData();						
						}
					}
				);			
			}
			
		}

	}; 
	
	$scope.$watch('pagenode', function(){
		if ($scope.pagenode.name){
			checkChildren();			
		}		
	});
	
	
	$scope.runtest = function (){
		var scope = angular.element($("#scenario_data")).scope();
		var num = 0;
		for (var i = 0; i < scope.data.length; i++){
			if (scope.data[i]["Selected"]){
				num++;
			}
		}
		if (num == 0){
			alert("None of tests is selected. Please select the tests.");
			return ;
		}else{
			console.log("runtest");
			$("#saveNode").attr("disabled","disabled");
			
		}	
	};
/* 	$scope.$watch('pagenode.children',function(newValue,oldValue){
		console.log(newValue);
		console.log(oldValue);
 		if ($scope.pagenode){
			var newChildren = [];
			for(var i = 0; i < $scope.pagenode.children.length; i++){
				if ($scope.pagenode.children[i]["name"] && $scope.pagenode.children[0]["name"].trim().length > 0){
					newChildren.push($scope.pagenode.children[i]);
				}
			}
			newValue = newChildren;
		}
		 
	});
 */
	$scope.opt = {
		nodeChildren: "children",
		dirSelectable: true
	};
});

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
	$scope.initData = function(){
		$scope.$parent.scenario.scope = $scope;
	}
	$scope.isSet = function(tab){
		return $scope.tab == tab;
	};
	$scope.caseItem = {};
	$scope.$watch('tab',
		function(newValue,oldValue){
		if (newValue == 2 && oldValue != 2){
			setTimeout(checkDesc,100);
		}
		if (newValue == 3 && oldValue != 3){
			setTimeout(checkSettings,100);
		}
		if (newValue == 1 && oldValue != 1){
			setTimeout(checkData,100);
		}

	});
	
	$scope.selectedNum = function(){
		var num = 0;
		for (var i = 0; i < $scope.data.length; i++){
			if ($scope.data[i]["Selected"]){
				num = num + 1;
			}
		}
		if (num == 0){
			return true;
		}else{
			return false;
		}
		return num;
	};
	
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

}]);


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
			colHeaders: "Test Steps",
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
							scope.header.splice(scope.header.length - 3,0,items[i]);
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
		$(".ht_clone_left").hide();
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
		var collist = [];
		var schema = {}
		for (var i = 0; i < header.length - 1 ; i++){
			schema[header[i]] = null;
			collist.push({data:header[i]});
		}
		collist.push({data:"Selected",type:"checkbox"});
		schema["Selected"] = null;
		console.log(data);
		$("#datasheet").handsontable({
			data: data,
			dataSchema: schema,
			minSpareRows:1,
			rowHeaders: true,
			fixedColumnsLeft: 1,
			colHeaders: header,
			contextMenu: ['row_above','row_below','remove_row'],
			columns: collist,
			afterOnCellMouseDown: function(event,coords,TD){
				if (coords.row >= 0){
					var scope = angular.element($("#scenario_data")).scope();
					var caseitem = {};
					var tableData = this.getData();
					for (var x in scope.header){
						caseitem[scope.header[x]] = tableData[coords.row][scope.header[x]];
					}


					scope.$apply(function(){
						scope.caseItem= caseitem;
					});


	//					$("#scenario_name").html(caseitem['Test Cases']);
	//					change_content(keywords,caseitem,tableId);
					if (coords.col == (this.countCols() -2)){
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
				var tableData = this.getData();
				setNewData(tableData);
			},
			afterCreateRow : function(index,amount){
				var tableData = this.getData();
				setNewData(tableData);				
			},
			afterRemoveRow : function(index, amount){
				var tableData = this.getData();
				setNewData(tableData);				
			},
			cells : function (row,col,prop){
				var data = this.instance.getData();
				if (row == data.length-1 && col == header.length-1){
					return {readOnly:true};
				}else{
					return {readOnly:false};
				}
			}

		});
		$(".ht_clone_left").hide();
	}else{
		setTimeout(checkData,100);
	}
}	

function setNewData(tableData){
	var scope = angular.element($("#scenario_data")).scope();
	var newData = [];
	for (var i = 0; i < tableData.length; i++){
		var item = {};
		for (var x in tableData[i]){
			if (tableData[i].hasOwnProperty(x)){
				item[x] = tableData[i][x];
			}
		}
		if (item[scope.header[0]]){
			newData.push(item);
		}				
	}
	scope.data = newData;
	
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
		$(".ht_clone_left").hide();
	}
	
}


function checkChildren(){
	if ($("#hottable").is(":visible")){
		var scope = angular.element($("treecontrol")).scope();
			var newChildren = [];
			for(var i = 0; i < scope.pagenode.children.length; i++){
			if (scope.pagenode.children[i]["name"] && scope.pagenode.children[0]["name"].trim().length > 0){
					newChildren.push(scope.pagenode.children[i]);
				}
			}
			
			$("#hottable").handsontable({
				data: newChildren,
				minSpareRows:1,
				rowHeaders: true,
				colHeaders: ['name','description'],
				contextMenu: ['row_above','row_below','remove_row'],
				columns: [
					{data:'name'},
					{data:'description'}
				],
				});
		$(".ht_clone_left").hide();
		
	}
	else{
		setTimeout(checkChildren,100);
	}
}

function copyData(originObj){
	var pagenode = {};
	for (x in originObj){
		if (originObj.hasOwnProperty(x)){
			pagenode[x] = originObj[x];
		}
	}
	return pagenode;
}

$(function(){
	$("#splitter").width("100%").height(600).split({orientation:'vertical', limit:100, position:'25%'});
	$.ajaxSetup({
            headers: { "X-CSRFToken": $.cookie("csrftoken") }
    });	
	$("#saveNode").on("click",function(){
		var scope = angular.element($("treecontrol")).scope();
		for (x in scope.selected){
			if (scope.selected.hasOwnProperty(x)){
				scope.selected[x] = scope.pagenode[x];
			}
		}
		if (scope.pagenode.type != "Scenario"){
			var datalist =$("#hottable").data("handsontable").getData();
			var newChildren = [];
			var nodeChildren = [];
			for (var i = 0; i < datalist.length; i++){
				if (datalist[i]["name"] && datalist[i]["name"].trim().length > 0){
					var item = {}
					for (x in datalist[i]){
						if (datalist[i].hasOwnProperty(x)){
							item[x] = datalist[i][x];
						}
					}
					item["children"] = [];
					if (!datalist[i]["id"]){
						datalist[i]["type"] = scope.selected["childtype"]
						datalist[i]["children"] = [];
						datalist[i]["childtype"] = scope.hierarchy[scope.hierarchy.indexOf(datalist[i]["type"])+1];
					}
					newChildren.push(datalist[i]);
					if (item["name"]){
						nodeChildren.push(item);
					}					
				}
			}
			var node = {};
			node.name = scope.pagenode.name;
			node.description = scope.pagenode.description;
			node.children = nodeChildren;
			if (node.name){
				var url = "/automation/savenode?type=" +  scope.pagenode.type;
				scope.lastSaved = scope.selected;
				if (scope.pagenode.type != "Project"){
					url = url + "&id=" + scope.pagenode.id;
				}
				$.ajax({
					url: url,
					dataType: "json",
					data: JSON.stringify(node),
					type: "POST",
					success:function (res){
						var data = res;
						var scope = angular.element($("treecontrol")).scope();
						for (var i = 0; i < data.children.length; i++){
							scope.lastSaved.children[i].id = data.children[i].id;
						}

						$("#saveNode").html("Save");
						$("#saveNode").removeAttr("disabled");
					}
				});
				
			}
			scope.$apply(function(){
				scope.selected.children = newChildren;
			});
		}else{
			var scope = angular.element($("#scenario_data")).scope();
			var sheet = {}
			$("#saveNode").html("Saving");
			console.log("click save button");
			$("#saveNode").attr("disabled","disabled");
			sheet.name=scope.$parent.pagenode.name;
			sheet.description=scope.$parent.pagenode.description;
			sheet.resource=scope.$parent.pagenode.resource;
			sheet.header=scope.header;
			sheet.data=scope.data;
			sheet.keywords=scope.keywords;
			sheet.setting=scope.settings;
			if (sheet.data){
				$.ajax({
					url: "/automation/savescenario?id=" + scope.$parent.pagenode.id,
					dataType: "json",
					data: JSON.stringify(sheet),
					type: "POST",
					success:function (res){
						$("#saveNode").html("Save");
						$("#saveNode").removeAttr("disabled");
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

		}	
	});
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

})



function saveTag(){
	var value = $("input[id$=tag]:checked").val();
	for (var i = 1; i < $("input[id$=tag]:checked").length ; i++){
		value = value + "," + $("input[id$=tag]:checked")[i].value;
	}
	curData[curCoords.row][curCoords.col] = value;
	$("#datasheet").handsontable("render");
	dialog.dialog("close");
}