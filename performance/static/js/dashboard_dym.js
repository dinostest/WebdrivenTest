var apps=[];
var running = 0;
$(function(){
	$("#table").tabelize();
	$.ajaxSetup({
        headers: { "X-CSRFToken": $.cookie("csrftoken") }
    });
	loadall();
	$("#select-all").on("click",function(event){
		$("input[type='checkbox']:enabled").prop("checked",$("#select-all").prop("checked"));
	});
	$("#runtest").on("click",function(event){
		$("input[type='checkbox']:enabled:checked").each(function(){
			var pos = this.id.indexOf("-select");
			execTest(this.id.substr(0,pos));
		});
	});
})

function loadall(){
	priority = $("#dinosPty").val();
	$.ajax({
		url: "/performance/loadall?priority=" + priority,
		dataType:"json",
		type:"GET",
		success:function (res){
			for (var propertyName in res){
				if(propertyName == "data"){
					apps=res.data;
					
					prepareStatusTables();
					if (res.status == "running" || res.status == "Queued"){
						setTimeout(function(){
							loadall();
						},3000);
					}else{
						running = 0;
					}
				}else{
					$("#" + propertyName).html(res[propertyName]); 
				}
			}
		}
	});	

}

function createStatusRow(level,name,idName){
	var html = "<tr data-level=\"" + level + "\" id=\"level_" + level + "_" + name + "\">" 
			+ "<td class=\"data\">" + name + "</td><td class=\"data\"><div id=\"" + idName + "-status\"></div></td>" 
			+ "<td class=\"data\"><div id=\"" + idName + "-responsetime\"></div></td>" 
			+ "<td class=\"data\"><div id=\"" + idName + "-avgtime\"></div></td>"
			+ "<td class=\"data\"><div id=\"" + idName + "-total\"></div></td>"
			+ "<td class=\"data\"><div id=\"" + idName + "-failed\"></div></td>"
			+ "<td class=\"data\"><div id=\"" + idName + "-report\"></div></td>"
			+ "<td class=\"data\"><div id=\"" + idName + "-log\"></div></td>"
			+ "<td class=\"data\"><div id=\"" + idName + "-data\"></div></td>";
	if (level < 4){
		html = html + "<td class=\"data\"><input id=\"" + idName + "-select\" type=\"checkbox\"></input></td>";
	}else{
		html = html + "<td class=\"data\"></td>";
	}
	html = html + "</tr>"; 
	return html
}

function createStatusTable(){
	var html = "";
	$("tbody").html();
	for (var i = 0; i < apps.length; i++){
		var app = apps[i];
		html = html + createStatusRow(1,app.name,app.name);
		for (var j = 0; j < app.modules.length; j++){
			var module = app.modules[j];
			var mID = app.name + "-" + module.name;
			html = html + createStatusRow(2,module.name,mID);
			for (var k = 0; k < module.funcs.length; k++){
				var func = module.funcs[k];
				var fID = mID + "-" + func.name.replace(/ /g,"_");
				html = html + createStatusRow(3,func.name,fID);
				for (var l = 0; l < func.scenarios.length; l++){
					var scenario = func.scenarios[l];
					var sID = fID + "-" + scenario.name.replace(/ /g,"_");
					html = html + createStatusRow(4,scenario.name,sID);
				}
			}
		}
	}
	$("tbody").html(html);
	$("#table").tabelize();
}
function prepareStatusTables(){
	var result = "";
	createStatusTable();
	for (var i = 0; i < apps.length; i++){
		var app = apps[i];
		showItemStatus(app,app.name);
		for (var j = 0; j < app.modules.length; j++){
			var module = app.modules[j];
			var mID = app.name + "-" + module.name;
			showItemStatus(module,mID);
			for (var k = 0; k < module.funcs.length; k++){
				var func = module.funcs[k];
				var fID = mID + "-" + func.name.replace(/ /g,"_");
				showItemStatus(func,fID);
				for (var l = 0; l < func.scenarios.length; l++){
					var scenario = func.scenarios[l];
					var sID = fID + "-" + scenario.name.replace(/ /g,"_");
					showItemStatus(scenario,sID);
				}
				reg_select(fID);
			}
			reg_select(mID);
		}
		reg_select(app.name);
	}
	$("tbody>tr:has(td:nth-child(2):contains('failed'))>td").css('color','red');
	$("tbody>tr:has(td:nth-child(2):not(:contains('failed')))>td").css('color','black');
}

function reg_select(name){
	$("#" + name + "-select").on("click",function(event){
		var items = this.id.split("-");
		var prefix = "";
		for(var i = 0; i < items.length - 1; i++){
			if (i == 0){
				prefix = items[i];
			}
			else{
				prefix = prefix + "-" + items[i];
			}
		}		
		$("[id^=" + prefix + "][type='checkbox']").each(function(){
			$(this).prop("checked",$("#" + prefix + "-select").prop("checked"));
		});
		if (! this.checked){
			unchecked(items);
		}
	});

}

function showItemStatus(item,prefix){
	var items = prefix.split("-");
	var app_name = items[0];
	if (item.status == "running" || item.status == "Queued"){
		$("#"+prefix + "-select").attr("disabled","disabled");
	}else{
		$("#"+prefix + "-select").removeAttr("disabled");
	}
	$("#" + prefix + "-status").html(item.status);
	if (item.responsetime){
		$("#" + prefix + "-responsetime").html(item.responsetime);
	}
	if (item.avgtime){
		$("#" + prefix + "-avgtime").html(item.avgtime);
	}
	if (item.total){
		$("#" + prefix + "-total").html(item.total);
		$("tr:has(#" + prefix +"-total)").show();
	}else{
		$("tr:has(#" + prefix +"-total)").hide();
	}
	if (item.hasOwnProperty("failed")){
		$("#" + prefix + "-failed").html(item.failed);
	}
	if (item.log){
		var module_name = items[1];
		var func_name = items[2];
		var html = "";
		if (item.level && item.level == "scenario"){
			html = "<a style=\"text-decoration:underline\" target='_blank' href='/performance/report/"+func_name+"?ts=" + item.log + "&scenario=" + encodeURIComponent(item.name) + "' >report</a>";
		}else{
			html = "<a style=\"text-decoration:underline\" target='_blank' href='/performance/report/"+func_name+"?ts=" + item.log +"' >report</a>";
		}
		$("#"+prefix+"-report").html(html);
		html = html.replace(/report/g,"log");
		$("#" + prefix + "-log").html(html);		
	}
	if (item.data){
		var html = "<button onclick=\"click_func('" + app_name + "','" + item.name + "','" + item.data + "')\">Data</button>";
		$("#" + prefix + "-data").html(html);		
	}
}

function execTest(prefix){
	var items = prefix.split("-");
	console.log(prefix);
	if(items.length == 3){
		var module = items[1];
		var func = items[2];
		var data={};
		data.module=module;
		data.func=func;
		html = "<b style='color:red'>Starting</b>";
		$("#" + prefix + "-select" ).attr("disabled", "disabled");
		$("#" + prefix + "-select" ).prop("checked", false);
		unchecked(items);
		$("#" + prefix + "-status").html(html);
		$.ajax({
			url: "/performance/runtest/",
			dataType:"json",
			data:JSON.stringify(data),
			type:"POST",
			success:function(res){
				var module = res.module;
				var func = res.func;
				var ts_f = res.ts_f;
				register_exec();
			}
		});
	}
}

function register_exec(){
	if(!running){
		setTimeout(function (){
				loadall();
		}
		,3000);
	}
	running++;
}

function unchecked(items){
	var prefix = "";
	for(var i = 0; i < items.length - 1; i++){
		if (i == 0){
			prefix = items[i];
		}
		else{
			prefix = prefix + "-" + items[i];
		}
		$("#" + prefix + "-select").prop("checked",false);
	}			
	$("#select-all").prop("checked",false);
}