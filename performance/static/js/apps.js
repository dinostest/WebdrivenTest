var apps=[];
var funcs_is_running ={};
funcs_is_running.set = function (module,func,ts, value){
	var func_key = [module,func,ts].join("-");
	funcs_is_running[func_key] = value;
	if (!value){
		var keys = Object.keys(this);
		var is_running = false;
		for (var i = 0; i < keys.length; i++){
			if (keys[i] != "is_running" && funcs_is_running[keys[i]]){
				is_running = true;
				break;
			}
		}
		funcs_is_running.is_running = is_running;
	}else{
		if (!funcs_is_running.is_running){
			funcs_is_running.is_running = true;
			getStatus(module,func,ts);
		}
	}
}
$(function() {
	$("#tabs").tabs({heightStyle: "content"});
	for (var i=0; i < tab_items.length; i++){
		$("#"+tab_items[i]).tabs({heightStyle: "content"});
	}
	for (var i=0; i < accordion_items.length; i++){
		$("#"+accordion_items[i]).accordion( {
			heightStyle: "content",
			activate: function(event,ui){
			}
		});
		console.log(accordion_items[i]);
	}
	$.ajaxSetup({
            headers: { "X-CSRFToken": $.cookie("csrftoken") }
    });
	$.ajax({
		url: "/performance/loadapps",
		dataType:"json",
		type:"GET",
		success:function (res){
			apps=res;
			console.log(apps);
			prepareCFGTables();
		}
	});	

});

function prepareCFGTables(){
	for (var i=0; i < apps.length; i++){
		var app = apps[i];
		for (var j=0; j < app.modules.length; j++){
			var module = app.modules[j];
			$.ajax({
				url: "/performance/loadcfg?app="+app.name+"&test=" + module.name,
				dataType:"json",
				type:"GET",
				success:function (res){
					var item = res.name + "-cfg";
					var func = res.name + "-funcs";
					var table = res.name + "-table";
					var data = res.data;
					var module = res.module;
					var module_header = Object.keys(module);					
					var module_data = [];
					for (var k = 0; k < module_header.length; k++){
						module_data.push(module[module_header[k]]);
					}
					module_data = [module_data];

					$("#"+table).handsontable({
						data:module_data,
						minSpareRows:0,
						colHeaders: module_header
					});

					var keys = Object.keys(data);
					keys.sort();
					var functions = "";
					var cfg_data = [];
					for (var k = 0; k < keys.length; k++){
						if (keys[k] != "functions"){
							cfg_data.push({"Key":keys[k], "Value":data[keys[k]]});
						}else{
							functions = data[keys[k]];
						}
					}
					$("#"+ item).handsontable({
						data:cfg_data,
						minSpareRows:0,
						colHeaders:["Key", "Value"],
						columns: [
							{
								data:"Key",
								readOnly:true
							},
							{
								data:"Value"
							}
						]
					});
					$(".ht_clone_top").hide();
					$(".ht_clone_left").hide();
					$(".ht_clone_corner").hide();
					
					html = "<table class=\"handsontable\" ><tr><th><input id=\"" +res.name +"-select\" type='checkbox' class=\"" + res.name +"\"></input>";
					html = html + "</th><th>Function</th><th>Status</th><th>Report</th><th>Log</th></tr>";
					functions = functions.replace(/\s/g,"_");
					console.log(functions);
					var funcs = functions.split(",");
					
					for (var k = 0; k < funcs.length; k++)
					{
						html = html + "<tr><td><input type='checkbox' value='" + funcs[k] +"' class=\"" + res.name + " " + funcs[k] + "-func\"></input></td>"
						html = html + "<td>" + funcs[k];
						html = html + "</td><td><div id=\"" + funcs[k] + "-status\">Active</div></td>";
						html = html + "<td><div id=\"" + funcs[k] + "-report\"></div></td>";
						html = html + "<td><div id=\"" + funcs[k] + "-log\"></div></td></tr>";
						getStatus(res.name, funcs[k],"");
					}
					html = html + "</table><button class=\"" + res.name + "\">execute</button>";
					$("#"+func).html(html);
					$("#"+res.name+"-select").on("click", function(){
						$("input."+this.className +":enabled").prop("checked",this.checked);
					});
					$("button."+res.name).on("click", function(){
						var module = this.className;
						var checked = $("." + module + ":checked");						
						for(var i = 0; i < checked.length; i++){
							if (checked[i].value && !checked[i].id){ 
								runTest(module, checked[i].value);
							}
						}
					});
						
				}
			});
		}
	}
}

function loaddata(app, data_file){
	var url = "/performance/loadscenario?app=" + app + "&file=" + data_file;
	$("#" + scenario.name + "-data").on("click", function(){
		window.open(url,"_blank","toolbar=no,menubar=no,location=no,scrollbars=yes");
	});

}
var url_list={};
function prepareDataButtons(){
	for (var i = 0; i < apps.length; i++){
		var app = apps[i];
		for(var j = 0; j < app.modules.length; j++){
			var module = app.modules[j];
			for (var k = 0; k < module.scenarios.length; k++){
				var scenario = module.scenarios[k];
				var url = "/performance/loadscenario?app=" + app.name + "&file=" + scenario.data_file;
				url_list[scenario.name] = url;
				$("#" + scenario.name + "-data").click(function (){
					window.open(url,"_blank","toolbar=no,menubar=no,location=no,scrollbars=yes");
				});
			}
		}
	}
}

function click_func(app, data_file){
	var url = "/performance/loadscenario?app=" + app + "&file=" + data_file;
	window.open(url,"_blank",'directories=no,titlebar=no,toolbar=no,location=no,status=no');
}
function createHandsonTables(){
	for (var i = 0; i < apps.length; i++){
		var app = apps[i];
		for(var j = 0; j < app.modules.length; j++){
			var module = app.modules[j];
			for (var k = 0; k < module.scenarios.length; k++){
				var scenario = module.scenarios[k];
				$.ajax({
					url: "/performance/loaddata?app=" + app.name +"&file=" + scenario.data_file,
					dataType:"json",
					type:"GET",
					success:function (res){
						data=res;
						console.log(data);
						createHandsonTable(scenario.name + "-data", data);
					}
				});	
			}
		}
	}
}

function saveCfg(app,module){
	var $cfg = $("#"+module+"-cfg").data("handsontable");
	var $setting = $("#"+module+"-table").data("handsontable");
	var header= $("#"+module+"-table").handsontable("getColHeader");
	var m_setting = $setting.getData();
	var result = {};
	var m = {}
	console.log(header);
	for (var i = 0; i < header.length; i++){
		m[header[i]]= m_setting[0][i];
	}
	result.cfg = $cfg.getData();
	result.module = m;
	$("#" + module + "-btn").attr("disabled","disabled");
	$.ajax({
		url: "/performance/savecfg?app=" + app +"&test=" + module,
		dataType: "json",
		data: JSON.stringify(result),
		type: "POST",
		success:function (res){
			var item = res.module;
			console.log(item);
			$("#" + item + "-btn").removeAttr("disabled");
		}
	});

}

function getStatus(module, func, ts_f){
	var url ="/performance/loadstatus/" + module + "/" + func;
	if (ts_f && ts_f.length > 0){
		url= url + "?ts_f=" + ts_f;
	}
	
	$.ajax({
		url: url,
		dataType:"json",
		type:"GET",
		success:function (res){
			var status=res.status;
			var func_id = res.func + "-func";
			var app = res.app;
			var test = res.module
			var ts_f = res.ts_f;
			var html = status;
			var in_runnings = false;

			if (status != "running"){				
				$("."+func_id ).removeAttr("disabled");
				
			}else{
				setTimeout(function(){
						getStatus(test, res.func, ts_f );
				}, 3000);
				$("."+func_id ).prop("checked", false);
				$("."+func_id ).attr("disabled", "disabled");
			}
			if (status != "completed"){
				html="<b style='color:red'>" + status + "</b>";
			}
			$("#" + func + "-status").html(html);
			if (ts_f){
				html = "<a style=\"text-decoration:underline\" targ='_blank' href='/performance/report/"+func+"?ts=" + ts_f +"' >report</a>";
				$("#"+func+"-report").html(html);
				html = html.replace(/report/g,"log");
				$("#"+func+"-log").html(html);
			}
		}
	});
}

function runTest(module,func){
	var data={};
	data.module=module;
	data.func=func;
	$.ajax({
		url: "/performance/runtest/",
		dataType:"json",
		data:JSON.stringify(data),
		type:"POST",
		success:function(res){
			var module = res.module;
			var func = res.func;
			var ts_f = res.ts_f;
			setTimeout(getStatus(module,func,ts_f),3000);
		}
	});
}