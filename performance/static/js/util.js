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