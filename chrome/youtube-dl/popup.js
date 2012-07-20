// Copyright (c) 2012 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

chrome.tabs.getSelected(null, function(tab) {
  	var req = new XMLHttpRequest();
	req.open(
	    "GET",
	    "http://kerplunk/youtube-dl/?url="+tab.url,
	    true);
	req.onload = showMsg;
	req.send(null);
});

function showMsg() {
  var msg = document.createElement("span");
  msg.innerText = "Done. Your tune should appear in MPD a couple of minutes.";
  document.body.appendChild(msg);
  var br = document.createElement("br");
  document.body.appendChild(br);
  var ok = document.createElement("input");
  ok.type = "button";
  ok.value = "Close";
  ok.onclick = function() {
	window.close();
  }
  document.body.appendChild(ok);
}
