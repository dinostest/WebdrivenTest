var selected_item = 0;
$(function() {
	$.ajaxSetup({
            headers: { "X-CSRFToken": $.cookie("csrftoken") }
    });

	$.ajax({
		url: "/performance/loadplandata",
		dataType:"json",
		type:"GET",
		success:function (res){
			datacols=[];
			data=res;
			for (var i = 0; i < data.length; i++){
				data[i].push("<input name=\"plan_select_radio\" id=\"plan_select_" + i + "\" type='radio'></input>");
			}
			for (var i = 0; i < header.length; i++){
				if (header[i].indexOf("Name") >= 0){
					datacols.push({data:i, readOnly:true});
				}else if (i == header.length - 1){
					datacols.push({data:i, readOnly:true, renderer:'html'});					
				}else{
					datacols.push({data:i});
				}
			}
			
			console.log(data);
			$("#datasheet").handsontable({
				data:data,
				colHeaders: header,
				columns: datacols,

			});		
			$("[id^=plan_select]").each(function(index){
				$(this).on("click",function(){
					$("[id^=plan_select]").each(function(index){
						$(this).attr("disabled","disabled");
					});
					selected_item = index;
					loadhistory(index);
					$("[id^=plan_select]").each(function(index){
						$(this).removeAttr("disabled");
					});
				});
			})
		}
	});	
	$("#test_plan_run").on("click",function(){
		var selectItems = $("input:checked");
		if (selectItems.length > 0){
			var selectItem = selectItems[0];
			var index = selectItem.id.split("_")[2];
			var $container = $("#datasheet");
			var handsontable = $container.data("handsontable");
			var item = {}
//		console.log("save");
			var data = handsontable.getData();
			var data_line = data[parseInt(index)];

			for (var i = 0; i < header.length; i++){
				item[header[i]] = data_line[i];
			}
			item["times"] = $("#dinosTimes").val();
			if (item){
				$.ajax({
					url: "/performance/runplan",
					dataType: "json",
					data: JSON.stringify(item),
					type: "POST",
					success:function (res){
						loaddata(res);
						if (res.status = "running"){
							setTimeout(function(){
								loadhistory(selected_item);
							},3000);
						}
					}
				});
			}
		}
		

	});
});

function loadhistory(index){
	var $container = $("#datasheet");
	var handsontable = $container.data("handsontable");
	var planname = data[index][0]
	$.ajax({
		url: "/performance/loadplanrun?testplan=" + encodeURIComponent(planname),
		dataType: "json",
		type: "GET",
		success:function (res){
			loaddata(res);
			if (res.status && res.status == "running"){
				setTimeout(function(){
					loadhistory(selected_item);
				},3000);
			}
			if (res.status){
				if (res.status != data[selected_item][8]){
					data[selected_item][8] = res.status;
					$("#datasheet").data("handsontable").render();
					$("#plan_select_" + selected_item).attr("checked","checked");
				}
			}
		}
	});
 
}

function loaddata(res){
	var html = "<table class=\"handsontable\" ><tr>";
	var data = res.data;
	for (var i = 0; i < res.header.length; i++){
		html = html + "<th>" + res.header[i] + "</th>";
	}
	html = html + "</tr>";
	for (var i = 0; i < data.length; i++){
		html = html + "<tr>";
		var line = data[i];
		for (var j =0; j < line.length; j++){
			html = html + "<td>" + line[j] + "</td>";
		}
		html = html + "</tr>"
	}
	html = html + "</table>"
	$("#history").html(html);
}