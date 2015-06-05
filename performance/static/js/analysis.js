$(function(){
    var progressbar = $( "#progressbar" ),
    progressLabel = $( ".progress-label" );
 
    progressbar.progressbar({
      value: false,
      change: function() {
        progressLabel.text( progressbar.progressbar( "value" ) + "%" );
      },
      complete: function() {
        progressLabel.text( "Complete!" );
		$( "#progressbar" ).hide();
      }
    });
    function progress() {
      var val = progressbar.progressbar( "value" ) || 0;
 
      progressbar.progressbar( "value", val + 2 );
 
      if ( val < 99 ) {
        setTimeout( progress, 80 );
      }
    }	
	$("#tabs").tabs({heightStyle: "content"}).on('tabsactivate', function(event, ui) {
		var index = ui.newTab.index();
		$("#analysis_"+analysis_set[index] + "_canvas").html("");
		$("#analysis_"+analysis_set[index] + "_canvas").append("<canvas id=\"analysis_" + analysis_set[index] + "\" height=\"450\" width=\"600\"></canvas>");
		window["analysis_" + analysis_set[index] + "_line"].clear();
		window["analysis_" + analysis_set[index] + "_line"].destroy();
		window["analysis_" + analysis_set[index] + "_ctx"]= document.getElementById("analysis_" + analysis_set[index]).getContext("2d");
		window["analysis_" + analysis_set[index] + "_line"]= new Chart(window["analysis_" + analysis_set[index] + "_ctx"]).Line(window["analysis_" + analysis_set[index]],
		{
			responsive: true,
			bezierCurve: false,
			datasetFill: false,
			multiTooltipTemplate: "<%= datasetLabel %> - <%= value %>",
			legendTemplate : '<ul class="legend">'
				  +'<% for (var i=0; i<datasets.length; i++) { %>'
					+'<li>'
					+'<span style=\"color:<%=datasets[i].strokeColor%>\">---</span>'
					+'<% if (datasets[i].label) { %><%= datasets[i].label %><% } %>'
				  +'</li>'
				  +'<% if ((i + 1) % 6 == 0) { %>' + '</ul><ul class="legend">' + '<% } %>'
				+'<% } %>'
				+'<% if (datasets.length % 6 != 0) {%>'
					+'<% for(var i = datasets.length % 6; i < 6; i++){%>'
					+'<li><span style=\"color:rgba(255,255,255,1)\">---'
					+'<% for(var j =0; j < datasets[0].label.length-2; j++){%>_'
					+'<% } %>'
					+'</span></li>'
					+'<% } %>'
				+'<% } %>'
			  +'</ul>'
		}
	);
	});
	$.ajaxSetup({
        headers: { "X-CSRFToken": $.cookie("csrftoken") }
    });
	for (var i = 0; i < analysis_set.length; i++){
		$( "#analysis_"+analysis_set[i] + "_from" ).datepicker({
		  defaultDate: "+1w",
		  changeMonth: true,
		  numberOfMonths: 3,
		  onClose: function( selectedDate ) {
			$( "#"  + this.id.replace("from","to") ).datepicker( "option", "minDate", selectedDate );
		  }
		});
		$( "#analysis_"+analysis_set[i] + "_to" ).datepicker({
		  defaultDate: "+1w",
		  changeMonth: true,
		  numberOfMonths: 3,
		  onClose: function( selectedDate ) {
			$( "#"  + this.id.replace("to","from") ).datepicker( "option", "maxDate", selectedDate );
		  }
		});
		$("#analysis_" +analysis_set[i] + "_load").on("click",function(){
			var prefix = this.id.replace("load","");
			var index = prefix.substring(9).split("_")[0]
			var fromDate = $("#" + prefix + "from").datepicker('getDate');
			var toDate = $("#" + prefix + "to").datepicker('getDate');
			var progressbar = $( "#progressbar" ),
			progressLabel = $( ".progress-label" );
			progressLabel.text( "Loading..." );
			progressbar.progressbar("destroy");
			
			progressbar.progressbar({
			  value: false,
			  change: function() {
				progressLabel.text( progressbar.progressbar( "value" ) + "%" );
			  },
			  complete: function() {
				progressLabel.text( "Complete!" );
				$( "#progressbar" ).hide();
			  }
			});
			
			if ( fromDate && toDate ){
				$( "#progressbar" ).show();
				var	urlstr = "/performance/loadanalysis?scope="+analysis_scope+"&analysis=" + index;
				if (fromDate){
					urlstr = urlstr + "&from=" +fromDate.getFullYear() + "-" + (fromDate.getMonth() + 1)+"-"+fromDate.getDate();
				}
				if (toDate){
					urlstr = urlstr + "&to=" + toDate.getFullYear() + "-" + (toDate.getMonth() + 1)+"-" +toDate.getDate();
				}
				$("#" + prefix + "doc_set").html("");
				$("#" + prefix + "time_set").html("");
				$("#" + prefix + "site_set").html("");
				window[prefix + "line"].clear();
				window[prefix + "line"].destroy();
				$.ajax({
					url: urlstr,
					dataType:"json",
					type:"GET",
					success:function (res){
						progress();
						data=res;
						//console.log(apps);
						renderChart(data);
						show_table(data);
						
						
					}
				});	
				
			}else{
				alert("Please select both from date and to date for checking performance result.");
			}
		});
		$.ajax({
			url: "/performance/loadanalysis?analysis=" + analysis_set[i] + "&scope=" + analysis_scope,
			dataType:"json",
			type:"GET",
			success:function (res){
				data=res;
				if (data.id == analysis_set[0]){
					progress();
				}
				
				//console.log(apps);
				renderChart(data);
				show_table(data);
		}
	});	
	}
});
	

function renderChart(data){
	//{{result.id}}_ctx = document.getElementById("{{result.id}}").getContext("2d");
	window["analysis_"+data.id] = new Object();
	window["analysis_"+data.id].labels = data.label;
	window["analysis_"+data.id+ "_origin"] = new Object();
	window["analysis_"+data.id+ "_origin"].labels = data.label;
	window["analysis_"+data.id+ "_origin"].datasets= [];
	for (var i = 0; i < data.group.length; i++){
		var item = new Object();
		item.label = data.group[i].module + " " +data.group[i].name + " " + data.group[i].ts_string + " " +data.group[i].machine;
		item.fillColor = "rgba(" + data.group[i].red +"," + data.group[i].green + "," + data.group[i].blue+ ",0.2)";
		item.strokeColor = "rgba(" + data.group[i].red +"," + data.group[i].green + "," + data.group[i].blue+ ",1)";
		item.pointColor = "rgba(" + data.group[i].red +"," + data.group[i].green + "," + data.group[i].blue+ ",1)";
		item.pointStrokeColor = "#fff";
		item.pointHighlightFill = "#fff";
		item.pointHighlightStroke = "rgba(" + data.group[i].red +"," + data.group[i].green + "," + data.group[i].blue+ ",1)";
		item.data = data.group[i].data;
		window["analysis_"+data.id+ "_origin"].datasets.push(item);
	}
	inject_check_box("module",data);
	inject_check_box("doc",data);
	inject_check_box("time",data);
	inject_check_box("site",data);
	$("#analysis_"+data.id+"_show").on("click", function(){
		var varname = this.id.replace("show", "line");
		var num = this.id.split("_")[1];
		window[varname].clear();
		window[varname].destroy();
		show_chart(parseInt(num));
	});
	
	show_chart(data.id);
}

function show_chart(index){
	var target_docs = [];
	var target_time = [];
	var target_site = [];
	var target_module = [];
	window["analysis_"+index].datasets=[];
	if ($("[id^=analysis_"+index+ "_module_]:checked").length == 0){
		alert("No item for modules from is selected.Select all items");
		$("[id^=analysis_"+index+ "_module_]").prop("checked","checked");
	}
	$("[id^=analysis_"+index+ "_module_]:checked").each(function(){
		target_module.push(this.id.substring(("analysis_"+index+ "_module_").length));
	});

	
	if ($("[id^=analysis_"+index+ "_doc_]:checked").length == 0){
		alert("No item for docs from is selected.Select all items");
		$("[id^=analysis_"+index+ "_doc_]").prop("checked","checked");
	}
	$("[id^=analysis_"+index+ "_doc_]:checked").each(function(){
		target_docs.push(this.id.substring(("analysis_"+index+ "_doc_").length));
	});
	if ($("[id^=analysis_"+index+ "_time_]:checked").length == 0){
		alert("No item for result at time is selected.Select all items");
		$("[id^=analysis_"+index+ "_time_]").prop("checked","checked");
	}
	
	$("[id^=analysis_"+index+ "_time_]:checked").each(function(){
		target_time.push(this.id.substring(("analysis_"+index+ "_time_").length));
	});
	if ($("[id^=analysis_"+index+ "_site_]:checked").length == 0){
		alert("No item for the test running from is selected.Select all items");
		$("[id^=analysis_"+index+ "_site_]").prop("checked","checked");
	}
	
	$("[id^=analysis_"+index+ "_site_]:checked").each(function(){
		target_site.push(this.id.substring(("analysis_"+index+ "_site_").length));
	});
	var targets = [];
	for (var i = 0; i < target_docs.length; i++){
		for (var j = 0; j < target_time.length; j++){
			for (var k = 0; k < target_site.length; k++){
				for (var l=0; l < target_module.length; l++){
					targets.push(target_module[l] + " " + target_docs[i] + " " +
					target_time[j] + " " + target_site[k]);
				}
			}
		}
	}
	$("#analysis_"+index+"_report>tbody>tr").hide();
	for (var i=0; i < targets.length; i++){
		$("#analysis_" + index +"_report>tbody>tr:contains('"+ targets[i] +"')").show();
		for(var j=0; j < window["analysis_"+index+ "_origin"].datasets.length; j++){
			if (window["analysis_"+index+ "_origin"].datasets[j].label == targets[i]){
				window["analysis_"+index].datasets.push(window["analysis_"+index+ "_origin"].datasets[j]);
			}
		}
	}
	window["analysis_"+index + "_ctx"] = document.getElementById("analysis_"+index).getContext("2d");
	window["analysis_"+index + "_line"] = new Chart(window["analysis_"+index + "_ctx"]).Line(window["analysis_"+index],
		{
			responsive: true,
			bezierCurve: false,
			datasetFill: false,
			multiTooltipTemplate: "<%= datasetLabel %> - <%= value %>",
			legendTemplate : '<ul class="legend">'
				  +'<% for (var i=0; i<datasets.length; i++) { %>'
					+'<li>'
					+'<span style=\"color:<%=datasets[i].strokeColor%>\">---</span>'
					+'<% if (datasets[i].label) { %><%= datasets[i].label %><% } %>'
				  +'</li>'
				  +'<% if ((i + 1) % 6 == 0) { %>' + '</ul><ul class="legend">' + '<% } %>'
				+'<% } %>'
				+'<% if (datasets.length % 6 != 0) {%>'
					+'<% for(var i = datasets.length % 6; i < 6; i++){%>'
					+'<li><span style=\"color:rgba(255,255,255,1)\">---'
					+'<% for(var j =0; j < datasets[0].label.length-2; j++){%>_'
					+'<% } %>'
					+'</span></li>'
					+'<% } %>'
				+'<% } %>'
			  +'</ul>'
		}
	);
	var legend = window["analysis_"+index + "_line"].generateLegend();
	$("#analysis_"+index+ "_legend").html("");
	$("#analysis_"+index+ "_legend").append(legend);
}

function show_table(data){
	var html = "<table id=\"analysis_" + data.id + "_report\"  cellspacing=\"1\" class=\"tablesorter\">" + "<thead><tr><th class=\"header\" >Label</th>";
	for (var i = 0; i < data.label.length; i++){
		html = html + "<th class=\"header\" >" + data.label[i] + "</th>";
	}
	html = html + "<th class=\"header\" >Report</th></tr></thead><tbody>";
		
	for (var i = 0; i < data.group.length; i++){
		html = html + "<tr><td>" + data.group[i].module + " " + data.group[i].name + " " + data.group[i].ts_string + " " + data.group[i].machine + "</td>";
		for (var j = 0; j < data.group[i].data.length; j++){
				html = html + "<td>" + data.group[i].data[j] + "</td>"
		}
		if (data.samedate){
			html = html + "<td><a href=\"/performance/report/"+data.group[i].func_name + "?ts="+data.group[i].ts_string + "&machine=" + encodeURIComponent(data.group[i].machine) +"\">failed:" + data.group[i].failed + "</a></td></tr>"
		}else{
			html = html + "<td>failed:" + data.group[i].failed + "</td></tr>"
		}
	}
	html = html + "</tbody></table>"
	$("#analysis_"+ data.id + "_table").html("");
	$("#analysis_"+ data.id + "_table").append(html);
	$("#analysis_"+ data.id +"_report").tablesorter({widthFixed:true});
	$("#analysis_"+ data.id +"_report>tbody>tr:not(:contains('failed:0'))>td").css('color','red');
}

function inject_check_box(type,data){
	if (type == "doc"){
		item_set = data.types;
	}
	if (type == "time"){
		item_set = data.start_time;
	}
	if (type == "site"){
		item_set = data.location;
	}
	if (type == "module"){
		item_set = data.module;
	}
	var html = "";
	for(var i = 0; i < item_set.length; i++){
		html = html + item_set[i] + "<input type=\"checkbox\" id=\"analysis_" + data.id + "_" + type + "_" + item_set[i] +"\" class=\"anlaysis_" + data.id + "_" + type + "\" checked=\"checked\"></input>";
		if ( (i + 1) % 6 == 0){
			html = html + "</br>";
		}
	}
	$("#analysis_"+data.id + "_" + type+ "_set").html("");
	$("#analysis_"+data.id + "_" + type+ "_set").html(html);
	$("#analysis_"+data.id +"_" + type).on("click", function(){
		if (this.checked){
			$("[id^='" + this.id +"']").prop("checked","checked");
		}else{
			$("[id^='" + this.id +"']").removeAttr("checked");
		}
	});
	$("[id^=analysis_"+data.id + "_" + type + "_]").on("click", function(){
		if ($("[id^=analysis_"+data.id + "_" + type + "_]").length != $("[id^=analysis_"+data.id + "_" + type + "_]:checked").length){
			$("#analysis_"+data.id +"_" + type).removeAttr("checked");
		}else{
			$("#analysis_"+data.id +"_" + type).prop("checked","checked");
		}
	});
	
}	