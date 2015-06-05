var value="";
$(function() {
	$("#tabs").tabs({heightStyle: "content"});
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