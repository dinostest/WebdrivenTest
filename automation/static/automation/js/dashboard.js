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
		execTest();
	});
})

function loadall(){
	priority = $("#dinosPty").val();
	tag = $("#dinosTag").val();
	machine = $("#dinosMachine").val();
	var requestUrl = "/performance/loadall?priority=" + priority;
	if (tag != "dinosAll")
		requestUrl = requestUrl + "&tag=" + tag;
	if (machine)
		requestUrl = requestUrl + "&machine="+ encodeURIComponent(machine);
	$.ajax({
		url: requestUrl,
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

function prepareStatusTables(){
	var result = "";
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
	$("tbody>tr:has(td:nth-child(2):contains('error'))>td").css('color','red');
	$("tbody>tr:has(td:nth-child(2):contains('exception'))>td").css('color','red');
	$("tbody>tr:has(td:nth-child(2):not(:contains('failed')):not(:contains('error')):not(:contains('exception')))>td").css('color','black');
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
	var machine = $("#dinosMachine").val();
	if (item.status == "running" || item.status == "Queued"){
		$("#"+prefix + "-select").attr("disabled","disabled");
	}else{
		$("#"+prefix + "-select").removeAttr("disabled");
	}
	$("#" + prefix + "-status").html(item.status);
	if (item.responsetime){
		$("#" + prefix + "-responsetime").html(item.responsetime);
	}else{
		$("#" + prefix + "-responsetime").html("");
	}
	if (item.avgtime){
		$("#" + prefix + "-avgtime").html(item.avgtime);
	}else{
		$("#" + prefix + "-avgtime").html("");
	}
	if (item.hasOwnProperty("total")){
		$("#" + prefix + "-total").html(item.total);
		if (!item.total){
			$("#" + prefix + "-responsetime").html("N/A");
			$("#" + prefix + "-avgtime").html("N/A");
			if (item.status != "running" && item.status != "Queued"){
				$("#" + prefix + "-status").html("N/A");
			}		
		}
	}else{
		$("#" + prefix + "-total").html("");
	}
	if (item.hasOwnProperty("failed")){
		$("#" + prefix + "-failed").html(item.failed);
	}else{
		$("#" + prefix + "-failed").html("");
	}
	var module_name = items[1];
	var func_name = items[2];

	if (item.log){
		var html = "";
		if (item.level && item.level == "scenario"){
			html = "<a style=\"text-decoration:underline\" target='_blank' href='/performance/report/"+func_name+"?ts=" + item.log + "&scenario=" + encodeURIComponent(item.name) + "&machine="+ encodeURIComponent(machine)+"' >report</a>";
		}else{
			html = "<a style=\"text-decoration:underline\" target='_blank' href='/performance/report/"+func_name+"?ts=" + item.log +"&machine="+ encodeURIComponent(machine)+"' >report</a>";
		}
		$("#"+prefix+"-report").html(html);
		html = html.replace(/report/g,"log");
		$("#" + prefix + "-log").html(html);		
	}
	if (item.data){
		var html = "<button onclick=\"click_func('" + app_name + "','" + module_name + "','" + item.name + "','" + func_name+"')\">Data</button>";
		$("#" + prefix + "-data").html(html);		
	}
	
}

function execTest(prefix){
	var data={};
	data.priority=$("#dinosPty").val();
	data.machine= $("#dinosMachine").val();
	data.tests=[];
	var checkedItems = $("input[type='checkbox']:checked");
	for (var i = 0; i < checkedItems.length; i++){
		var item = checkedItems[i];
		var pos = item.id.indexOf("-select");
		var prefix = item.id.substr(0,pos);
		var items = prefix.split("-");
		console.log(item.id);
		console.log(prefix);
		if(items.length == 3){
			console.log(prefix);
			var module = items[1];
			var func = items[2];
			var test = {}
			test.module=module;
			test.func=func;
			data.tests.push(test)
			html = "<b style='color:red'>Starting</b>";
			$("#" + prefix + "-select" ).attr("disabled", "disabled");
			$("#" + prefix + "-select" ).prop("checked", false);
			unchecked(items);
			$("#" + prefix + "-status").html(html);
		}
	}
	$.ajax({
		url: "/performance/exectests",
		dataType:"json",
		data:JSON.stringify(data),
		type:"POST",
		success:function(res){
				register_exec();
		}
	});
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