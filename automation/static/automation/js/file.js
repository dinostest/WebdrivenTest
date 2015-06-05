var header=[];
var created=false;
$(function() {
	$.ajaxSetup({
            headers: { "X-CSRFToken": $.cookie("csrftoken") }
    });

	$.ajax({
		url: "/performance/loadcsv?app=" + app + "&module=" + module + "&file=" + data_file ,
		dataType:"json",
		type:"GET",
		success:function (res){
			data=res;
			console.log(data);
			created = createHandsonTable("datasheet", data);
		}
	});	
	$("#save").on("click",function(){
		var $container = $("#datasheet");
		var handsontable = $container.data("handsontable");
		var sheet = {}
		console.log("save");
		if (!created){
			sheet.header=header;
			sheet.data = handsontable.getData();
		}else{
			var data = handsontable.getData();
			sheet.header = data.shift();
			sheet.data = data;
		}
		try{
			if (parent.window.opener != null && !parent.window.opener.closed){
				saveCfg = parent.window.opener.saveCfg;
				saveCfg(app,module);
			}
		}catch (e){ 
				alert(e.description());
		}
		$.ajax({
			url: "/performance/savecsv?app=" + app +"&file=" + data_file + "&module=" + module,
			dataType: "json",
			data: JSON.stringify(sheet),
			type: "POST",
			success:function (res){
				self.close();
				window.close();
			}
		});
	});
});


