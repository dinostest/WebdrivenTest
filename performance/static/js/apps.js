var apps=[];
var funcs_is_running ={};
var cfg_lists={};
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
			collapsible:true,
			heightStyle: "content",
			activate: function(event,ui){
			}
		});
//		console.log(accordion_items[i]);
	}
	$.ajaxSetup({
            headers: { "X-CSRFToken": $.cookie("csrftoken") }
    });
	$("#varName").autocomplete({
		source: varArray
	});
	loadApp();
});

function loadApp(){
	$.ajax({
		url: "/performance/loadapps",
		dataType:"json",
		type:"GET",
		success:function (res){
			apps=res;
			//console.log(apps);
			prepareCFGTables();
		}
	});	
}

function prepareCFGTables(){
	for (var i=0; i < apps.length; i++){
		var app = apps[i];
		for (var j=0; j < app.modules.length; j++){
			var module = app.modules[j];
			loadModule(app.name,module.name)
		}
	}
}

function loadModule(app,module){
	$.ajax({
		url: "/performance/loadcfg?app="+app+"&module=" + module,
		dataType:"json",
		type:"GET",
		success:function (res){
			var app = res.app;
			var item = res.name + "-cfg";
			var func = res.name + "-funcs";
			var table = res.name + "-table";
			var func_name = res.func.replace(/\s/g,"_");
			var data = res.data;
			var module = res.module;
			var module_header = Object.keys(module);					
			var module_data = [];
			if (res.settings){
				var html = "Load setting : <select id=\""+ res.name + "-select\" onchange=\"loadfunc('"+ app +"','" + res.name+ "','" + func_name +"')\"><option>None</option>";
				for (var i=0; i < res.settings.length;i++){
					html = html + "<option>" + res.settings[i] +"</option>";
				}
				html = html + "</select>";
				$("#"+res.name+"-load").html(html);
			}
			for (var k = 0; k < module_header.length; k++){
				module_data.push(module[module_header[k]]);
			}
			module_data = [module_data];

			$("#"+table).handsontable({
				data:module_data,
				minSpareRows:0,
				colHeaders: module_header
			});

			var cfg_data = [];
			var keys = Object.keys(data);
			keys.sort();
			var functions = "";
			var filelist = [];
			var datalist = [];
			
			for (var k = 0; k < keys.length; k++){
				if (keys[k] != "functions"){
					cfg_data.push({"Key":keys[k], "Value":data[keys[k]]});
					if (keys[k] == "filelist"){
						filelist = data[keys[k]].split(",");
					}
					if (keys[k] == "thread_datalist"){
						datalist = data[keys[k]].split(",");
					}
				}else{
					functions = data[keys[k]];
				}
			}
			cfg_lists[app +"_"+res.name] = cfg_data;
			$("#"+ item).handsontable({
				data:cfg_lists[app+"_"+res.name],
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
			if (res.resource){
				renderResouceList(res.resource,res.name);
			}
			if (filelist.length > 0){
				$.ajax({
					url: "/performance/loadfiletable?module=" + res.name + "&func_name=" + func_name,
					dataType:"json",
					type: "GET",
					success: function(res){
						renderFileList(res);
					}
				});
				
			}
			if (datalist.length > 0){
				$.ajax({
					url: "/performance/threaddatatable?module=" + res.name + "&func_name=" + func_name,
					dataType:"json",
					type: "GET",
					success: function(res){
						renderFileList(res);
					}
				});						
			}
			html = "<table class=\"handsontable\" ><tr><th><input id=\"" +res.name +"-select\" type='radio' disabled=\"disabled\" class=\"" + res.name +"\"></input>";
			html = html + "</th><th>Function</th><th>Status</th><th>Report</th><th>Log</th><th>History</th></tr>";
			functions = functions.replace(/\s/g,"_");
			var funcs = functions.split(",");
			
			for (var k = 0; k < funcs.length; k++)
			{
				html = html + "<tr><td><input type='radio' name='"+ res.name + "_func_name' value='" + funcs[k] +"' class=\"" + res.name + " " + funcs[k] + "-func\""
				if (k == 0){
					html = html + " checked='checked'";
				}
				html = html +	"onClick=\"loadfunc('" +app + "','" + res.name + "','" + funcs[k] + "')\"></input></td>";
				html = html + "<td>" + funcs[k];
				html = html + "</td><td><div id=\"" + funcs[k] + "-status\">Active</div></td>";
				html = html + "<td><div id=\"" + funcs[k] + "-report\"></div></td>";
				html = html + "<td><div id=\"" + funcs[k] + "-log\"></div></td>";
				html = html + "<td><div id=\"" + funcs[k] + "-history\"><a style=\"text-decoration:underline\" target='_blank' href='/performance/history/"+funcs[k]+"'>History</a></div></td></tr>";
				getStatus(res.name, funcs[k],"");
			}
			
			html = html + "</table><button class=\"" + res.name + "\">execute</button>";
		
			
			html = html + "<input type='checkbox' id=" + res.name +"-parallel>run in parallel</input>"
			$("#"+func).html(html);
			$("#" + res.name + "-label").html(funcs[0] + " function settings");
			$("."+funcs[0]+"-func").attr("checked","checked");
			$("button."+res.name).on("click", function(){
				var module = this.className;
				var checked = $("." + module + ":checked");						
				for(var i = 0; i < checked.length; i++){
					if (checked[i].value && !checked[i].id){ 
						runTest(module, checked[i].value);
					}
				}
			});
			if (!dinosLogin){
			$("button:not(:contains('Data'))").attr("disabled","disabled");
			}	
		}
	});
}

function loadfunc(app,module,func){
	var url = "/performance/loadcfg?app="+app+"&module=" + module + "&func=" + func;
	if ($("#" + module + "-select")){
		var name = $("#" + module + "-select").val();
		if (name.length > 0 && name != "None"){
			url = url + "&name=" + encodeURIComponent(name) ;
		}
		$("#" + module + "-setting").val(name);
	}
	
	$.ajax({
		url: url,
		dataType:"json",
		type:"GET",
		success:function (res){
			var data = res.data;
			var app = res.app;
			var func = res.func;
			var module = res.module;
			var module_header = Object.keys(module);					
			var module_data = [];
			var table = res.name + "-table";
			var tableData = $("#" + table).data("handsontable");
			var tableHeader = tableData.getColHeader();
			var moduledata = tableData.getData();
			for (var i = 0; i < tableHeader.length; i++){
				moduledata[0][i]=module[tableHeader[i]];
			}
			
			tableData.render();
			
			if (res.settings){
				updateSelect(app,res.name,func,res)
			}			
			renderFunction(app, res.name, func, data);
		}
	});
}

function updateSelect(app,module,func,res){
	var html = "Load setting : <select id=\""+ module + "-select\" onchange=\"loadfunc('"+ app +"','" + module+ "','" + func +"')\"><option>None</option>";
	for (var i=0; i < res.settings.length;i++){
		if(res.selected && res.selected == res.settings[i]){
			html = html + "<option selected value=\""+ res.settings[i] + "\">" + res.settings[i] +"</option>";
		}else{
			html = html + "<option value=\""+ res.settings[i] + "\">" + res.settings[i] +"</option>";
		}
	}
	html = html + "</select>";
	$("#" + module + "-load").html(html);
}

function renderFunction(app,module, func, data){
	var keys = Object.keys(data);
	keys.sort();
	var functions = "";
	var filelist = [];
	var datalist = [];
	var cfg_data = cfg_lists[app + "_" + module];
	var data_size = cfg_data.length;
	for (var i = 0; i < data_size; i++){
		cfg_data.pop();
	}
	var func_name = func.replace(/\s/g,"_");
	$("#" + module + "-label").html(func + " function settings");
	for (var k = 0; k < keys.length; k++){
		if (keys[k] != "functions"){
			cfg_data.push({"Key":keys[k], "Value":data[keys[k]]});
			if (keys[k] == "filelist"){
				filelist = data[keys[k]].split(",");
			}
			if (keys[k] == "thread_datalist"){
				datalist = data[keys[k]].split(",");
			}
		}else{
			functions = data[keys[k]];
		}
	}
	item = module + "-cfg";
	$("#"+item).handsontable('render');
	if (filelist.length > 0){
		$.ajax({
			url: "/performance/loadfiletable?module=" + res.name + "&func_name=" + func_name,
			dataType:"json",
			type: "GET",
			success: function(res){
				renderFileList(res);
			}
		});
		
	}
	if (datalist.length > 0){
		$.ajax({
			url: "/performance/threaddatatable?module=" + res.name + "&func_name=" + func_name,
			dataType:"json",
			type: "GET",
			success: function(res){
				renderFileList(res);
			}
		});						
	}

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
	var m = {};
	console.log(header);
	for (var i = 0; i < header.length; i++){
		m[header[i]]= m_setting[0][i];
	}
	result.cfg = $cfg.getData();
	result.module = m;
	func = $("input[name="+module+"_func_name]:checked").val();
	$("#" + module + "-btn").attr("disabled","disabled");
	var url = "/performance/savecfg?app="+app+"&module=" + module + "&func=" + func;
	if ($("#" + module + "-setting")){
		name = $.trim($("#" + module + "-setting").val());
		if (name.length > 0){
			url = url + "&name=" + encodeURIComponent(name) ;
		}
	}
	
	$.ajax({
		url: url,
		dataType: "json",
		data: JSON.stringify(result),
		type: "POST",
		success:function (res){
			var item = res.module;
			var app = res.app;
			var func_name = res.func;
			if (res.settings){
				updateSelect(app,item,func_name,res);
			}
			
			console.log(item);
			$("#" + item + "-btn").removeAttr("disabled");
			if (res.filelist){
				$.ajax({
					url: "/performance/loadfiletable?module=" + item + "&func_name=" + func_name,
					dataType:"json",
					type: "GET",
					success: function(res){
						renderFileList(res);
					}
				});
			}
			if (res.thread_datalist){
				$.ajax({
					url: "/performance/threaddatatable?module=" + item + "&func_name=" + func_name,
					dataType:"json",
					type: "GET",
					success: function(res){
						renderFileList(res);
					}
				});
			}
			loadfunc(app,item,func_name);
			
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

			if (status != "running" && status != "Queued" ){				
				$("."+func_id ).removeAttr("disabled");
				
			}else{
				setTimeout(function(){
						getStatus(test, res.func, ts_f );
				}, 3000);
//				$("."+func_id ).prop("checked", false);
				$("."+func_id ).attr("disabled", "disabled");
			}
			if (status != "completed"){
				html="<b style='color:red'>" + status + "</b>";
			}
			$("#" + func + "-status").html(html);
			if (ts_f){
				html = "<a style=\"text-decoration:underline\" target='_blank' href='/performance/report/"+func+"?ts=" + ts_f +"' >report</a>";
				$("#"+func+"-report").html(html);
				html = html.replace(/report/g,"log");
				$("#"+func+"-log").html(html);
			}
		}
	});
}

function renderFileList(data){
	var module = data.name;
	if (data.data){
		var html = "<h3>File List</h3><table class=\"handsontable\" ><tr>";
		for (var i = 0; i < data.data[0].length; i++){
			html = html + "<th>" + data.data[0][i] + "</th>"	
		}
		html = html + "</tr>";
		for (var i = 1; i < data.data.length; i++){
			html = html + "<tr>";
			for (var j = 0; j < data.data[i].length; j++){
				html = html + "<td>" + data.data[i][j] + "</td>"
			}
			html = html + "</tr>";
		}
		html = html + "</table>";
		var item = module + "-files";
		$("#" + item).html(html);
	}
}

function renderResouceList(data,module){
	var name = data.name;
	var html = "<h3>" + name + " List</h3><div id='" + module + "-resource-table'></div>";
	$("#" + module + "-resources").html(html);
	var data_list = [];
	for(var i = 0; i < data.list.length; i++){
		var item = {};
		item[name] = data.list[i];
		item["Upload"] = "<button onclick=\"window.open('/performance/uploadresource?module=" + module + "&file=" + item[name] + "&resource=" + name + "&action=overwrite','Upload','toolbar=no, scrollbars=no, resizable=no, top=100, left=300, width=400, height=400')\">overwrite</button>";
		item["module"] = module;
		data_list.push(item);
	}
	var item = {};
	item[name] = "Add new " + name;
	item["Upload"] = "";
	item["module"] = module;
	data_list.push(item);
	console.log(data_list);
	$("#" + module + "-resource-table").handsontable({
		data:data_list,
		minSpareRows:0,
		colHeaders:[name, "Upload"],
		columns: [
			{
				data:name,
				readOnly:true
			},
			{
				data:"Upload",
				renderer:"html"
			}
		],
		cells:function (row,col,prop){
			var cellProperties = {};
			if (row == data_list.length - 1 && col == 0){
				cellProperties.readOnly = false;
			}
			return cellProperties;
		},
		afterChange:function(changes,source){
			
			if (changes && changes[0][0] == data_list.length - 1){
					var row = data_list.length - 1;
					var item = data_list[row];
				
					
					item["Upload"] = "<button onclick=\"window.open('/performance/uploadresource?module=" + item["module"] + "&file=" + item[name] + "&resource=" + changes[0][1] + "&action=new','Upload','toolbar=no, scrollbars=no, resizable=no, top=100, left=300, width=400, height=400')\">Save</button>";
					this.render();
			}
		}
	});

}

function updateResourceList(module,resource){
	var handsontable = $("#" + module + "-resource-table").data("handsontable");
	var data_list = handsontable.getData();
	var item = data_list[data_list.length - 1];
	
	item["Upload"] = "<button onclick=\"window.open('/performance/uploadresource?module=" + module + "&file=" + item[name] + "&resource=" + resource + "&action=overwrite','Upload','toolbar=no, scrollbars=no, resizable=no, top=100, left=300, width=400, height=400')\">overwrite</button>";
	item = {};
	item[resource] = "Add new " + resource;
	item["module"] = module;
	item["Upload"] = "";
	data_list.push(item);
	handsontable.updateSettings({
		cells:function (row,col,prop){
			var cellProperties = {};
			if (row == data_list.length - 1 && col == 0){
				cellProperties.readOnly = false;
			}
			return cellProperties;
		},

	})
	handsontable.render();
}

function updateVar(){
	var varName = $("#varName").val();
	var varValue = $("#varValue").val();
	var appName = $("#appName").val();
	var data={};
	data["varName"] = varName;
	data["varValue"] = varValue;
	data["appName"] = appName;
	$.ajax({
		url: "/performance/savevar",
		dataType: "json",
		data: data,
		type: "POST",
		success:function (res){
			loadApp();
		}
	});
}