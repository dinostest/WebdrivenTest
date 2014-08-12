var value="";
$(function() {
	$("#report").tablesorter();
});

function filter(){
	$("tr").show();
	$("#datasheet").html("");
	value = $("#filter").val();
	if (value.length > 0 ){
		$("tbody>tr:contains(" + value+ ")").hide();
		var count = $("tr:contains(" + value+ ")").size();
		if (count != 0){
			var html = "<p style='color:red'>" + count + " rows are hidden</p>";
			$("#datasheet").html(html);
		}
	}
}