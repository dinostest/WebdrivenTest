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
		url: "/performance/loaddata?app=" + app + "&module=" + module + "&scenario=" + scenario + "&func=" + func ,
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
		$("#save").html("Saving");
		$("#save").attr("disabled","disabled");
//		console.log("save");
		sheet.header=header;
		data = handsontable.getData();
		sheet.data = data;
		sheet.changes = checkChange(data);
		if (validate(sheet.data)){
			$.ajax({
				url: "/performance/savedata?app=" + app + "&module=" + module + "&scenario=" + scenario + "&func=" + func,
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