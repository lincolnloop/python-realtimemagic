var Browser = require("zombie");
var assert = require("assert");

// Load the page from localhost
browser = new Browser();
// Remember to run the webserver with: python -m SimpleHTTPServer 8080
browser.visit("http://localhost:8080/", function () {
});

