var value="";
$(function() {
	$("#report").tablesorter({widthFixed:true});
	$("tbody>tr:has(td:nth-child(3):contains('false'))>td").css('color','red');
	$("tbody>tr").hide();
	$("tbody>tr:contains('>>')").show();
});

function filter(){
	$("tr").show();
	$("#datasheet").html("");
	value = $("#filter").val();
	if (value.length > 0 ){
		$("tbody>tr:not(:contains(" + value+ "))").hide();
		var count = $("tr:not(:contains(" + value+ "))").size();
		if (count != 0){
			var html = "<p style='color:red'>" + count + " rows are hidden</p>";
			$("#datasheet").html(html);
		}
	}
}