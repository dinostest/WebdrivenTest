var value="";
$(function() {
	$.ajaxSetup({
            headers: { "X-CSRFToken": $.cookie("csrftoken") }
    });

	$("#tabs").tabs({heightStyle: "content"});
	if (jobCompleted){
		$("#job_result").accordion( {
				collapsible:true,
				heightStyle: "content",
				activate: function(event,ui){
			}
		});			
		$("#server_monitor").accordion({
				collapsible:true,
				heightStyle: "content",
		}
		);
	}else{
		if (jobStatus == "processing"){
			checkJob();
			$("#dinos_check_job").html("");
			$( "#progressbar" ).progressbar({
				value: false
			});			
		}else{
			$("#dinos_end_job").on("click",function(){			
				checkJob();
				$("#dinos_check_job").html("");
				$( "#progressbar" ).progressbar({
					value: false
				});
			});
		}
	}
	$("#jmeter_report").tablesorter({
			theme: 'blue',
			showProcessing: true,
			headerTemplate : '{content} {icon}',
			widgets: [ 'uitheme', 'zebra', 'filter' ],
			headers : {'.dinos_text':{sorter: 'text'},
					},
			debug:true,
	});
	$("tbody>tr:has(td:nth-child(3):contains('false'))>td").css('color','red');
	$("tbody>tr").hide();
	$("tbody>tr:contains('>>')").show();
	
	for (var i = 0; i < jobIds.length; i++){
		
		$("#"+jobIds+"_report").tablesorter({
			theme: 'blue',
			showProcessing: true,
			headerTemplate : '{content} {icon}',
			widgets: [ 'uitheme', 'zebra', 'filter' ],
			headers : {'.dinos_text':{sorter: 'text'},
					},
		    widgetOptions : {
			  scroller_height : 800,
			  scroller_fixedColumns : 2,
			},
		});
	}
});

function checkJob(){
	var url = location.href;
	url = url.replace("report", "jobtask");
	$.ajax({
		url: url,
		dataType:"json",
		type:"POST",
		data:"{'msg':'check_status'}",
		success:function (res){
			status = res.status;
			if (status != "completed"){
				setTimeout(checkJob, 3000);
			}else{
				if (location.href.indexOf("#job_result") < 0){
					location.href = location.href + "#job_result";
				}
				location.reload();
			}
		}
	});		
}

function filter(){
	$("tr").show();
	$("#datasheet").html("");
	value = $("#filter").val();
	if (value.length > 0 ){
		$("tbody>tr:not(:contains(" + value+ "))").hide();
		var count = $("tbody>tr:not(:contains(" + value+ "))").size();
		if (count != 0){
			var html = "<p style='color:red'>" + count + " rows are hidden</p>";
			$("#datasheet").html(html);
		}
	}
}