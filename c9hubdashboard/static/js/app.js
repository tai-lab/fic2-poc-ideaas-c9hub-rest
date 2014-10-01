var app = angular.module("app", ["oauth"]).config(
    function($locationProvider) {
	$locationProvider.html5Mode(true).hashPrefix('!');
    });