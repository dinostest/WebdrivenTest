var app = angular.module("dinostree",["treeControl"]);

app.controller('dinosctrl',function($scope,$http) {
	$http.get('/performance/loadtree').success(
	function(data,status,headers,config){
		$scope.treedata = [data];
		$scope.snode = $scope.treedata;
	});

	$scope.showSelected = function(sel) {
		$scope.selected = sel;
	};

	$scope.opt = {
		nodeChildren: "children",
		dirSelectable: true
	};

});
